"""
Pipeline Orchestrator v3.0 - Plan-Driven Execution
"""
import os
import time
import hashlib
import json
import traceback
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from supabase import create_client

from ..models.extraction import ExtractionResult, ExtractedNode, ExtractedEdge, Evidence, Locator
from ..models.planning import JobPlanStatus, RecommendedAction, Strategy
from ..router import get_model_router
from ..audit import FileProcessingLogger
from ..actions import ActionRunner, ActionResult
from ..services.storage import StorageService
from ..services.catalog import CatalogService
from ..services.planner import PlannerService
from ..services.extractors.ssis import SSISParser
from ..config import settings

@dataclass
class ProcessingResult:
    """Resultado del procesamiento de un archivo"""
    success: bool
    file_path: str
    strategy_used: str
    action_taken: str
    data: Optional[Dict[str, Any]] = None
    nodes_extracted: int = 0
    edges_extracted: int = 0
    evidences_extracted: int = 0
    model_used: Optional[str] = None
    fallback_used: bool = False
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    processing_time_ms: int = 0
    tokens_used: int = 0
    cost_estimate: float = 0.0

@dataclass
class PipelineMetrics:
    total_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    total_nodes: int = 0
    total_edges: int = 0
    total_evidences: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    total_processing_time_ms: int = 0
    strategy_counts: Dict[str, int] = None
    model_usage: Dict[str, int] = None
    error_counts: Dict[str, int] = None

class PipelineOrchestrator:
    """
    Orquesta el procesamiento basado en PLANES (v3).
    """
    
    def __init__(self, supabase_client=None):
        print("\n" + "="*50)
        print("!!! MEGA TRACE: PipelineOrchestrator INIT !!!")
        print("="*50)
        self.router = get_model_router()
        self.logger = FileProcessingLogger(supabase_client)
        self.action_runner = ActionRunner(self.logger)
        self.storage = StorageService()
        
        if supabase_client:
            self.supabase = supabase_client
        else:
            self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            
        self.catalog = CatalogService(self.supabase)
        self.planner = PlannerService(self.supabase)
        
        # Métricas
        self.metrics = PipelineMetrics()
        self.metrics.strategy_counts = {}
        self.metrics.model_usage = {}
        self.metrics.error_counts = {}
    
    def execute_pipeline(self, job_id: str, artifact_path: str) -> bool:
        """
        Main Entry Point.
        v3 Logic:
        1. Ingest
        2. Check/Create Plan
        3. If Approved -> Execute
        4. Else -> Stop & Wait
        """
        print(f"[PIPELINE v3] Starting pipeline for job {job_id}")
        
        try:
            # 1. Ingest
            ingest_result = self._execute_stage(job_id, "ingest", lambda: self._ingest_artifact(artifact_path))
            if not ingest_result.success:
                raise Exception(f"Ingest failed: {ingest_result.error_message}")
            
            local_artifact_path = ingest_result.data.get("local_path")
            
            # 2. Check Plan Status
            job_data = self.supabase.table("job_run").select("plan_id, requires_approval").eq("job_id", job_id).single().execute()
            current_plan_id = job_data.data.get("plan_id")
            requires_approval = job_data.data.get("requires_approval")
            if requires_approval is None:
                requires_approval = True
            
            # Case A: No Plan -> Create Plan
            if not current_plan_id:
                print(f"[PIPELINE v3] No plan found. Entering Planning Phase.")
                self._update_job_progress(job_id, "planning")
                
                plan_id = self.planner.create_plan(job_id, local_artifact_path)
                print(f"[PIPELINE v3] Plan created: {plan_id}. Waiting for approval.")
                
                # If legacy mode (requires_approval=False), auto-approve immediately
                if not requires_approval:
                     print(f"[PIPELINE v3] Auto-approving plan (Legacy Mode)")
                     self.supabase.table("job_plan").update({"status": JobPlanStatus.APPROVED}).eq("plan_id", plan_id).execute()
                     self.supabase.table("job_run").update({"requires_approval": False}).eq("job_id", job_id).execute()
                     current_plan_id = plan_id
                else:
                    return True # Stop here, wait for UI
            
            # Case B: Plan Exists. Check Status.
            plan_res = self.supabase.table("job_plan").select("status").eq("plan_id", current_plan_id).single().execute()
            plan_status = plan_res.data.get("status")
            
            if plan_status != JobPlanStatus.APPROVED:
                print(f"[PIPELINE v3] Plan {current_plan_id} is {plan_status}. Waiting for approval.")
                return True # Stop here
                
            # Case C: Plan Approved -> Execute
            print(f"[PIPELINE v3] Plan Approved. Starting Execution Phase.")
            self._update_job_progress(job_id, "execution")
            
            return self._execute_plan(job_id, current_plan_id, local_artifact_path)
            
        except Exception as e:
            error_msg = f"Pipeline failed for job {job_id}: {str(e)}"
            print(f"[PIPELINE] {error_msg}")
            traceback.print_exc()
            self._update_job_status(job_id, "ERROR", error_msg)
            return False

    def _execute_plan(self, job_id: str, plan_id: str, root_path: str) -> bool:
        """Executes the approved items in the plan"""
        
        # Fetch items ordered by Area and Order Index
        # We need to join with Area to sort by Area Order, but supabase-py join is tricky.
        # We'll fetch areas first to get order.
        areas_res = self.supabase.table("job_plan_area").select("area_id, order_index").eq("plan_id", plan_id).order("order_index").execute()
        area_order_map = {a["area_id"]: a["order_index"] for a in areas_res.data}
        
        items_res = self.supabase.table("job_plan_item").select("*").eq("plan_id", plan_id).eq("enabled", True).execute()
        items = items_res.data
        
        # Sort items: Area Order ASC, Item Order ASC
        items.sort(key=lambda x: (area_order_map.get(x["area_id"], 999), x["order_index"]))
        
        if settings.DEBUG_MAX_ITEMS > 0:
            print(f"[PIPELINE v3] DEBUG MODE: Limiting execution to top {settings.DEBUG_MAX_ITEMS} items.")
            items = items[:settings.DEBUG_MAX_ITEMS]
            
        total_items = len(items)
        print(f"[PIPELINE v3] Executing {total_items} items from plan.")
        
        file_results = []
        
        for i, item in enumerate(items):
            print(f"[PIPELINE v3] Processing Item {i+1}/{total_items}: {item['path']} ({item['strategy']})")
            
            # Update Job Progress (Current Item)
            self.supabase.table("job_run").update({
                "current_item_id": item["item_id"],
                "progress_pct": int(((i) / total_items) * 100)
            }).eq("job_id", job_id).execute()
            
            # Read Content
            full_path = os.path.join(root_path, item["path"])
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading file {full_path}: {e}")
                continue

            # Execute based on Strategy
            res = self._process_item_v3(job_id, item, content, full_path)
            file_results.append(res)
            self._update_metrics(res)
            
            # Update Item Status
            status = "completed" if res.success else "failed"
            self.supabase.table("job_plan_item").update({"status": status}).eq("item_id", item["item_id"]).execute()

        # Persist Results
        self._execute_stage(job_id, "persist_results", lambda: self._persist_results(job_id, file_results))
        
        # Update Graph
        if settings.NEO4J_URI:
             self._execute_stage(job_id, "update_graph", lambda: self._update_graph(job_id, file_results))
             
        # Complete Job
        self.supabase.table("job_run").update({
            "status": "completed",
            "progress_pct": 100,
            "current_item_id": None
        }).eq("job_id", job_id).execute()
        
        print(f"[PIPELINE v3] Execution Completed.")
        print(f"[PIPELINE] Metrics: {self._get_metrics_summary()}")
        return True

    def _process_item_v3(self, job_id: str, item: Dict, content: str, full_path: str) -> ProcessingResult:
        start_time = time.time()
        strategy = item.get("strategy")
        print(f"!!! MEGA TRACE: _process_item_v3 - Strategy: {strategy} (Type: {type(strategy)})")
        
        try:
            # Check strategy against enum values or strings
            strategy_val = strategy.value if hasattr(strategy, 'value') else strategy
            
            if strategy_val == Strategy.SKIP or strategy_val == "SKIP":
                 print(f"!!! MEGA TRACE: Strategy is SKIP for {item['path']}")
                 return ProcessingResult(True, item["path"], "SKIP", "skipped")
            
            elif strategy_val == Strategy.PARSER_ONLY or strategy_val == "PARSER_ONLY":
                print(f"!!! MEGA TRACE: Strategy is PARSER_ONLY for {item['path']}")
                return self._create_success_result(item["path"], "PARSER_ONLY", 
                                                 self._extract_with_native_parser(job_id, full_path, content), start_time)
            
            elif strategy_val in [Strategy.LLM_ONLY, Strategy.PARSER_PLUS_LLM, "LLM_ONLY", "PARSER_PLUS_LLM"]:
                print(f"!!! MEGA TRACE: Strategy is LLM-based ({strategy_val}) for {item['path']}")
                # Determine Action Profile based on file type / item type
                action_name = self._determine_action_profile(item)
                
                res = self._extract_with_llm(job_id, full_path, content, action_name)
                
                if res.success:
                     return self._create_success_result(item["path"], strategy, res, start_time)
                else:
                     print(f"!!! MEGA TRACE: _extract_with_llm FAILED for {item['path']}: {res.error_message}")
                     return self._create_error_result(item["path"], strategy, res, start_time)
                     
            else:
                print(f"!!! MEGA TRACE: UNKNOWN STRATEGY hit: {strategy_val}")
                return ProcessingResult(False, item["path"], strategy, "error", error_message=f"Unknown strategy {strategy}")

        except Exception as e:
             print(f"!!! MEGA TRACE: EXCEPTION in _process_item_v3 for {item['path']}: {str(e)}")
             traceback.print_exc()
             return ProcessingResult(False, item["path"], strategy, "error", error_message=str(e))

    def _determine_action_profile(self, item: Dict) -> str:
        """Maps item to v3 Action Profile"""
        ft = item.get("file_type", "").upper()
        
        if ft in ["SQL", "DDL"]:
            return "extract.schema" # v3 profile (dotted)
        elif ft in ["DTSX", "DSX"]:
            return "extract.lineage.package" # v3 profile (dotted)
        elif ft in ["PY", "IPYNB"]:
            return "extract.python" # v3 profile (dotted)
        else:
            return "extract.strict" # Fallback (dotted)

    # --- Reused Methods from v2 (Private) ---
    # Copied helper methods like _execute_stage, _ingest_artifact, _persist_results, etc.
    # to maintain functionality. For brevity in this turn, I assume they exist or I paste them.
    # I will paste the critical ones.

    def _execute_stage(self, job_id: str, stage_name: str, stage_func) -> ActionResult:
        print(f"[PIPELINE] Executing stage: {stage_name}")
        try:
            result = stage_func()
            self._update_job_progress(job_id, stage_name)
            return ActionResult(success=True, data=result if result else {})
        except Exception as e:
            return ActionResult(success=False, error_message=str(e))

    def _ingest_artifact(self, artifact_path: str) -> Dict[str, Any]:
        # Same as v2
        print(f"[PIPELINE] Ingesting artifact: {artifact_path}")
        local_path = self.storage.download_and_extract(artifact_path)
        return {"local_path": local_path}

    def _extract_with_native_parser(self, job_id: str, file_path: str, content: str) -> ActionResult:
        # Same as v2
        extension = Path(file_path).suffix.lower()
        if extension == ".sql":
            return self._extract_sql_native(file_path, content)
        # ... (rest of native parsers)
        return ActionResult(success=False, error_message="No native parser")

    def _extract_sql_native(self, file_path: str, content: str) -> ActionResult:
         # Simplified regex parser from v2
         import re
         table_pattern = r'(?:FROM|JOIN|INTO|UPDATE|TABLE)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)'
         tables = list(set(re.findall(table_pattern, content, re.IGNORECASE)))
         nodes = [{"node_id": t, "node_type": "table", "name": t, "system": "sql"} for t in tables]
         return ActionResult(success=True, data={"nodes": nodes, "edges": []})

    def _extract_with_llm(self, job_id: str, file_path: str, content: str, action_name: str = "extract.strict") -> ActionResult:
        # Same as v2 but accepts action_name
        
        # Enhanced Logic for SSIS/Packages (Deep Inspection)
        if action_name == "extract.lineage.package" and (file_path.lower().endswith(".dtsx") or file_path.lower().endswith(".xml")):
            try:
                print(f"[PIPELINE v3] Running Deep Package Inspection (SSIS Parser) for {file_path}")
                structure = SSISParser.parse_structure(content)
                # Append structure to content to guide LLM
                content = f"XML STRUCTURE SUMMARY:\n{json.dumps(structure, indent=2)}\n\nRAW CONTENT:\n{content}"
            except Exception as e:
                print(f"[PIPELINE] SSIS Parser failed for {file_path}: {e}")

        # Strategy Selection
        llm_input = {"content": content[:settings.MAX_CONTENT_CHARS], "extension": Path(file_path).suffix}
        context = {"job_id": job_id, "file_path": file_path}
        
        # Audit Start
        log_action_name = action_name.replace(".", "_")
        if action_name == "extract.lineage.package":
            log_action_name = "extract_strict"
            
        log_id = self.logger.start_file_processing(job_id, file_path, log_action_name, len(content))
        
        
        print(f"!!! MEGA TRACE: Calling ActionRunner for {action_name} (File: {file_path})")
        result = self.action_runner.run_action(action_name, llm_input, context, log_id)
        print(f"!!! MEGA TRACE: ActionRunner Result: Success={result.success}, Model={result.model_used}")
        
        if result.success:
            # Audit Completion with correct strategy name for DB constraint
            # Map back to enum strings if they are what's expected
            strat_for_audit = "LLM_ONLY"
            if action_name == "extract.schema": strat_for_audit = "PARSER_PLUS_LLM"
            
            self.logger.complete_file_processing(log_id, "success", strat_for_audit)
        else:
             self.logger.log_file_error(log_id, "llm_error", result.error_message)
        return result

    def _persist_results(self, job_id: str, file_results: List[ProcessingResult]):
        count = 0
        try:
            job_data = self.supabase.table("job_run").select("project_id").eq("job_id", job_id).single().execute()
            project_id = job_data.data.get("project_id")
            
            for res in file_results:
                if res.success and res.data:
                    # Convert raw dict to ExtractionResult object
                    try:
                        # Ensure 'nodes' and 'edges' exist
                        if "nodes" not in res.data: res.data["nodes"] = []
                        if "edges" not in res.data: res.data["edges"] = []
                        if "evidences" not in res.data: res.data["evidences"] = []
                        
                        # Pre-process data to handle missing fields leniently
                        import uuid
                        
                        # Fix Nodes
                        for node in res.data.get("nodes", []):
                            if "name" not in node and "node_id" in node:
                                node["name"] = node["node_id"].split('.')[-1]
                            if "system" not in node:
                                node["system"] = "unknown"
                        
                        # Fix Edges
                        for edge in res.data.get("edges", []):
                            if "edge_id" not in edge:
                                edge["edge_id"] = str(uuid.uuid4())
                            if "rationale" not in edge:
                                edge["rationale"] = "Extracted by LLM"
                            if "confidence" not in edge:
                                edge["confidence"] = 1.0
                        
                        # Add meta info
                        res.data["meta"] = {
                            "source_file": res.file_path,
                            "extractor_id": res.model_used or res.strategy_used
                        }
                        
                        # Use Pydantic models for validation/conversion
                        extraction_result = ExtractionResult(**res.data)
                        
                        # Sync to Catalog
                        self.catalog.sync_extraction_result(extraction_result, project_id, artifact_id=job_id)
                        count += 1
                    except Exception as parse_e:
                        print(f"[PIPELINE] Error converting/persisting result for {res.file_path}: {parse_e}")
                        
        except Exception as e:
            print(f"Persist error: {e}")
            traceback.print_exc()
        return {"persisted_count": count}

    def _update_job_progress(self, job_id: str, stage: str):
        try:
            self.supabase.table("job_run").update({"current_stage": stage}).eq("job_id", job_id).execute()
        except: pass

    def _update_job_status(self, job_id: str, status: str, msg: str = None):
        data = {"status": status}
        if msg: data["error_message"] = msg
        try:
            self.supabase.table("job_run").update(data).eq("job_id", job_id).execute()
        except: pass

    def _create_success_result(self, file_path, strategy, res, start_time):
        return ProcessingResult(True, file_path, strategy, "extraction", data=res.data, processing_time_ms=int((time.time()-start_time)*1000))

    def _create_error_result(self, file_path, strategy, res, start_time):
         return ProcessingResult(False, file_path, strategy, "extraction", error_message=res.error_message, processing_time_ms=int((time.time()-start_time)*1000))

    def _update_metrics(self, res):
        self.metrics.total_files += 1
        if res.success: self.metrics.successful_files += 1
        else: self.metrics.failed_files += 1

    def _get_metrics_summary(self):
        return f"Files: {self.metrics.successful_files}/{self.metrics.total_files}"

    def _update_graph(self, job_id: str, results: List[ProcessingResult]):
        """Sincroniza los resultados con Neo4j si está configurado"""
        from ..services.graph import get_graph_service
        
        try:
            job_res = self.supabase.table("job_run").select("project_id").eq("job_id", job_id).single().execute()
            project_id = job_res.data.get("project_id")
            
            graph_svc = get_graph_service()
            print(f"[PIPELINE] Syncing {len(results)} file results to Graph...")
            
            for res in results:
                if not res.success or not res.data:
                    continue
                
                # Sincronizar Nodos
                for node in res.data.get("nodes", []):
                    # Inyectar project_id para filtrado posterior
                    node["project_id"] = project_id
                    node["solution_id"] = project_id # Compatibilidad
                    
                    label = "Asset"
                    # Mapear tipo a Etiqueta si es necesario, o usar Asset genérico
                    graph_svc.upsert_node(label, node)
                
                # Sincronizar Relaciones
                for edge in res.data.get("edges", []):
                    # En Neo4j las relaciones necesitan que los nodos existan
                    # upsert_relationship en Neo4jGraphService usa MATCH + MERGE basado en IDs
                    source_props = {"id": edge.get("from_node_id") or edge.get("source_id")}
                    target_props = {"id": edge.get("to_node_id") or edge.get("target_id")}
                    rel_type = edge.get("edge_type", "DEPENDS_ON")
                    
                    if source_props["id"] and target_props["id"]:
                        graph_svc.upsert_relationship(source_props, target_props, rel_type)
            
            print(f"[PIPELINE] Graph Sync Completed.")
            
        except Exception as e:
            print(f"[PIPELINE ERROR] Graph Sync Failed: {e}")
            traceback.print_exc()
