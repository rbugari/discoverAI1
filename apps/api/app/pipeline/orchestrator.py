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
from ..models.deep_dive import DeepDiveResult, Package, PackageComponent, TransformationIR, ColumnLineage
from ..models.planning import JobPlanStatus, RecommendedAction, Strategy
from ..router import get_model_router
from ..audit import FileProcessingLogger
from ..actions import ActionRunner, ActionResult
from ..services.storage import StorageService
from ..services.catalog import CatalogService
from ..services.planner import PlannerService
from ..services.extractors.ssis import SSISParser
from ..services.extractors.datastage import DataStageParser
from ..services.extractors.registry import ExtractorRegistry
from ..services.auditor import DiscoveryAuditor
from ..services.refiner import DiscoveryRefiner
from ..services.prompt_service import PromptService
from ..services.reasoning_service import ReasoningService
from ..services.report_service import ReportService
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
        self.auditor = DiscoveryAuditor(self.supabase)
        self.refiner = DiscoveryRefiner(self.auditor, self.action_runner)
        self.prompt_service = PromptService(self.supabase)
        self.reasoning = ReasoningService(self.supabase, self.catalog, self.prompt_service)
        self.reports = ReportService(self.supabase)
        
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
        print(f"[PIPELINE v3] Starting pipeline for job {job_id}", flush=True)
        
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
                requires_approval = False # Changed from True to skip confirmation by default
            
            # Case A: No Plan -> Create Plan
            if not current_plan_id:
                try:
                    print(f"[PIPELINE v3] Starting Case A: New Solution. Needs Planning.", flush=True)
                    self._update_job_progress(job_id, "planning")
                    
                    plan_id = self.planner.create_plan(job_id, local_artifact_path)
                    print(f"[PIPELINE v3] Plan created: {plan_id}. Waiting for approval.", flush=True)
                    
                    # If legacy mode (requires_approval=False), auto-approve immediately
                    if not requires_approval:
                         print(f"[PIPELINE v3] Auto-approving plan (Legacy Mode)", flush=True)
                         self.supabase.table("job_plan").update({"status": JobPlanStatus.APPROVED}).eq("plan_id", plan_id).execute()
                         self.supabase.table("job_run").update({"requires_approval": False}).eq("job_id", job_id).execute()
                         current_plan_id = plan_id
                    else:
                        # Update status to planning_ready for UI feedback
                        self._update_job_status(job_id, "planning_ready")
                        return True # Stop here, wait for UI
                except Exception as plan_e:
                    error_msg = f"Planning stage failed: {str(plan_e)}"
                    detailed_error = traceback.format_exc()
                    print(f"\n[PIPELINE] ❌ {error_msg}", flush=True)
                    print(detailed_error, flush=True)
                    self._update_job_status(job_id, "ERROR", error_msg, detailed_error)
                    return False
            
            # Case B: Plan Exists. Check Status.
            plan_res = self.supabase.table("job_plan").select("status").eq("plan_id", current_plan_id).single().execute()
            plan_status = plan_res.data.get("status")
            
            if plan_status != JobPlanStatus.APPROVED:
                print(f"[PIPELINE v3] Plan {current_plan_id} is {plan_status}. Waiting for approval.", flush=True)
                return True # Stop here
                
            # Case C: Plan Approved -> Execute
            print(f"[PIPELINE v3] Plan Approved. Starting Execution Phase.")
            self._update_job_progress(job_id, "execution")
            
            return self._execute_plan(job_id, current_plan_id, local_artifact_path)
            
        except Exception as e:
            error_msg = f"Pipeline failed for job {job_id}: {str(e)}"
            detailed_error = traceback.format_exc()
            print(detailed_error, flush=True)
            
            # --- DEBUG: WRITE CRASH TO FILE ---
            try:
                with open("CRASH_LOG.txt", "w", encoding="utf-8") as f:
                    f.write(detailed_error)
            except: pass
            # ----------------------------------
            
            self._update_job_status(job_id, "ERROR", error_msg, detailed_error)
            return False

    def _execute_plan(self, job_id: str, plan_id: str, root_path: str) -> bool:
        """Executes the approved items in the plan"""
        
        # Fetch project_id for later use (Reasoning/Artifacts)
        job_res = self.supabase.table("job_run").select("project_id").eq("job_id", job_id).single().execute()
        project_id = job_res.data.get("project_id")
        
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
            print(f"[PIPELINE v3] DEBUG MODE: Limiting execution to top {settings.DEBUG_MAX_ITEMS} items.", flush=True)
            items = items[:settings.DEBUG_MAX_ITEMS]
            
        total_items = len(items)
        print(f"[PIPELINE v3] Executing {total_items} items from plan.", flush=True)
        
        file_results = []
        
        for i, item in enumerate(items):
            progress = int(((i) / total_items) * 100)
            print(f"!!! LOOP TRACE: Processing {i+1}/{total_items} ({progress}%): {item['path']}", flush=True)
            
            # Update Job Progress (Current Item)
            self._update_job_progress(job_id, f"processing: {os.path.basename(item['path'])}", progress)
            
            # Check for Cancellation
            try:
                job_check = self.supabase.table("job_run").select("status").eq("job_id", job_id).single().execute()
                if job_check.data and job_check.data.get("status") == "cancelled":
                    print(f"[PIPELINE v3] Job {job_id} cancelled by user. Aborting...", flush=True)
                    return False
            except Exception as cancel_e:
                print(f"[PIPELINE v3] Error checking cancellation status: {cancel_e}")
            
            # Read Content
            full_path = os.path.join(root_path, item["path"])
            print(f"!!! LOOP TRACE: Attempting to read: {full_path}")
            try:
                if not os.path.exists(full_path):
                    raise FileNotFoundError(f"File not found: {full_path}")
                
                strategy_val = item.get("strategy")
                if hasattr(strategy_val, 'value'): strategy_val = strategy_val.value
                
                # Check if we need binary reading (VLM)
                is_binary = strategy_val == "VLM_EXTRACT"
                
                if is_binary:
                    import base64
                    with open(full_path, 'rb') as f:
                        binary_data = f.read()
                        # Base64 encode for LLM consumption
                        content = base64.b64encode(binary_data).decode('utf-8')
                else:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
            except Exception as e:
                print(f"Error reading file {full_path}: {e}")
                self.supabase.table("job_plan_item").update({"status": "failed"}).eq("item_id", item["item_id"]).execute()
                continue

            # Execute based on Strategy
            res = self._process_item_v3(job_id, item, content, full_path)
            self._update_metrics(res)
            
            # --- v3/v4 PERSISTENCE & DEEP DIVE ---
            node_id_map = {}
            if res.success:
                # 1. Persist Macro Results immediately to get UUIDs
                persist_res = self._persist_single_result(job_id, res)
                node_id_map = persist_res.get("node_id_map", {})
                
                # Update Item Status
                self.supabase.table("job_plan_item").update({"status": "completed"}).eq("item_id", item["item_id"]).execute()
                
                # 2. Deep Dive (if applicable)
                if self._should_perform_deep_dive(item):
                    try:
                        print(f"[PIPELINE v4] Performing Deep Dive for {item['path']}")
                        self._perform_deep_dive(job_id, item, content, res, node_id_map)
                    except Exception as dd_e:
                        print(f"[PIPELINE v4] CRITICAL ERROR in Deep Dive for {item['path']}: {dd_e}")
                        traceback.print_exc()
            else:
                self.supabase.table("job_plan_item").update({"status": "failed"}).eq("item_id", item["item_id"]).execute()
            
            # Accumulate result for Graph Sync and Reporting
            file_results.append(res)

        # Finalize
        print(f"[PIPELINE v3] Finalizing execution...")
        
        # Update Graph
        if settings.NEO4J_URI:
             print(f"[PIPELINE v3] Syncing to Neo4j...")
             # self._execute_stage(job_id, "update_graph", lambda: self._update_graph(job_id, file_results))
             self._update_graph(job_id, file_results)
             
        # Complete Job
        self.supabase.table("job_run").update({
            "status": "completed",
            "progress_pct": 100,
            "current_item_id": None
        }).eq("job_id", job_id).execute()
        
        # --- v5.0 ACCURACY AUDIT ---
        print(f"[PIPELINE v5.0] Running Post-Processing Accuracy Audit...")
        self._run_post_processing_audit(job_id)

        # --- v6.2 REASONING SYNTHESIS ---
        print(f"[PIPELINE v6.2] Running Reasoning Synthesis...", flush=True)
        try:
            import asyncio
            # Since _execute_plan is sync, we use a controlled async run
            if project_id:
                asyncio.run(self.reasoning.synthesize_global_conclusion(job_id, project_id))
        except Exception as re_e:
            print(f"[PIPELINE v6.2] ERROR in Reasoning Synthesis: {re_e}", flush=True)
            traceback.print_exc()

        # --- v6.3 AUTOMATED ARTIFACT GENERATION ---
        print(f"[PIPELINE v6.3] Generating Automated Reports & Artifacts...", flush=True)
        try:
            import asyncio
            if project_id:
                asyncio.run(self.reports.generate_and_save_latest_artifacts(project_id))
        except Exception as art_e:
            print(f"[PIPELINE v6.3] ERROR in Artifact Generation: {art_e}", flush=True)
            traceback.print_exc()

        print(f"[PIPELINE v3] Execution Completed.", flush=True)
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
            
            elif strategy_val in [Strategy.LLM_ONLY, Strategy.PARSER_PLUS_LLM, Strategy.VLM_EXTRACT, "LLM_ONLY", "PARSER_PLUS_LLM", "VLM_EXTRACT"]:
                print(f"!!! MEGA TRACE: Strategy is LLM-based ({strategy_val}) for {item['path']}")
                # Determine Action Profile based on file type / item type
                action_name = self._determine_action_profile(item)
                
                res = self._extract_with_llm(job_id, full_path, content, action_name)
                
                if res.success:
                     return self._create_success_result(item["path"], strategy_val, res, start_time)
                else:
                     print(f"!!! MEGA TRACE: _extract_with_llm FAILED for {item['path']}: {res.error_message}")
                     return self._create_error_result(item["path"], strategy_val, res, start_time)
                     
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
        elif ft in ["JPG", "JPEG", "PNG"]: # SVG excluded from VLM
            return "extract.diagram" # [NEW] Vision profile
        else:
            return "extract.strict" # Fallback (dotted)

    def _should_perform_deep_dive(self, item: Dict) -> bool:
        """Determines if the item qualifies for v4.0 Deep Dive"""
        ft = item.get("file_type", "").upper()
        strategy = item.get("strategy")
        strategy_val = strategy.value if hasattr(strategy, 'value') else strategy
        
        # Packages always get deep dive. Complex SQL with PARSER_PLUS_LLM too.
        if ft in ["DTSX", "DSX"]:
            return True
        if ft in ["SQL", "DDL"] and strategy_val == "PARSER_PLUS_LLM":
            return True
        return False

    def _perform_deep_dive(self, job_id: str, item: Dict, content: str, extraction_res: ProcessingResult, node_id_map: Dict[str, str] = None):
        """
        v4.0 Deep Dive: Extracts internal package components and column-level lineage.
        """
        node_id_map = node_id_map or {}
        try:
            # 1. Prepare Input & Resolve Asset Names
            # We pass the content and the 'macro' extraction results to give context to the LLM
            macro_nodes = []
            name_map = {} # name -> UUID
            id_name_map = {} # node_id -> UUID
            
            if extraction_res.data and "nodes" in extraction_res.data:
                for n in extraction_res.data["nodes"]:
                    node_dict = {}
                    if hasattr(n, "model_dump"):
                        node_dict = n.model_dump()
                    elif isinstance(n, dict):
                        node_dict = n
                    
                    macro_nodes.append(node_dict)
                    
                    # Populate resolution maps
                    u_id = node_id_map.get(node_dict.get("node_id"))
                    if u_id:
                        if node_dict.get("name"): name_map[node_dict["name"]] = u_id
                        if node_dict.get("node_id"): id_name_map[node_dict["node_id"]] = u_id
            
            llm_input = {
                "content": content[:settings.MAX_CONTENT_CHARS],
                "file_path": item["path"],
                "file_type": item["file_type"],
                "macro_nodes": macro_nodes
            }
            
            context = {"job_id": job_id, "file_path": item["path"]}

            # --- v4.1 DETERMINISTIC EXTRACTOR SHORTCUT ---
            # If we have a dedicated python extractor (like for SSIS), use it instead of LLM
            ext = os.path.splitext(item["path"])[1].lower()
            if ext == ".dtsx":
                print(f"[PIPELINE v4] Using Deterministic SSIS Deep Extractor for {item['path']}")
                try:
                    # Capture raw content (it might be encoded/summarized in 'content' arg)
                    # For deep dive, we usually trust 'content' passed to this method unless it was mutated upstream.
                    # Wait, 'content' passed to 'execute_pipeline' loop is fresh read.
                    # BUT 'content' passed to '_process_item_v3' (which mutated it) is NOT passed here.
                    # This method '_perform_deep_dive' receives 'content' from '_execute_plan' loop.
                    # In '_execute_plan', 'content' is read from file.
                    # Wait, let's check call site.
                    # Line 272 calls self._perform_deep_dive(job_id, item, content, res, node_id_map)
                    # In _execute_plan, 'content' is read from file. It is NOT mutated.
                    # So 'content' here IS raw. The mutation happens inside _extract_with_llm which is called by _process_item_v3.
                    # Ah, _process_item_v3 is called with 'content'.
                    # It mutates 'content' locally inside _extract_with_llm? No.
                    # _extract_with_llm receives 'content'. Python strings are immutable, but the variable 'content' inside that function changes.
                    # However, '_execute_plan' holds the original string.
                    # So 'content' passed to this method IS SAFE.
                    # BUT wait, the previous fix to _extract_with_llm was needed because THAT was where macro ran.
                    # Here for Deep Dive, we are fine.
                    
                    registry = ExtractorRegistry()
                    deep_result = registry.get_extractor(item["path"]).extract_deep(item["path"], content)
                    
                    if deep_result:
                        print(f"[PIPELINE v4] Deterministic Extraction Successful!")
                        # Sync and return immediately
                        # Fetch project_id (needed for sync validation inside catalog or explicit pass)
                        job_res = self.supabase.table("job_run").select("project_id").eq("job_id", job_id).single().execute()
                        project_id_val = job_res.data.get("project_id")
                        
                        # Fix UUIDs: The extractor generates random project_id. We must overwrite it.
                        real_pid = str(project_id_val)
                        
                        deep_result.package.project_id = real_pid
                        for comp in deep_result.components:
                            # Component doesn't usually have project_id but check model
                             if hasattr(comp, 'project_id'): comp.project_id = real_pid
                        for trans in deep_result.transformations:
                            trans.project_id = real_pid
                        for lin in deep_result.lineage:
                            lin.project_id = real_pid
                        
                        # Perform sync
                        self.catalog.sync_deep_dive_result(deep_result, real_pid)
                        print(f"[PIPELINE v4] Deep Dive Persisted (Deterministic).")
                        return
                    else:
                         print("[PIPELINE v4] Deterministic extraction returned None. Falling back to LLM.")
                except Exception as det_e:
                    print(f"[PIPELINE v4] Deterministic Extraction Failed: {det_e}")
                    traceback.print_exc()
                    # Fallback to LLM execution below
            
            # 2. Run Deep Dive Action (LLM Fallback/Default)
            action_name = "extract.deep_dive"
            print(f"[PIPELINE v4] Calling ActionRunner for {action_name}")
            result = self.action_runner.run_action(action_name, llm_input, context)
            
            if not result.success:
                print(f"[PIPELINE v4] Deep Dive failed for {item['path']}: {result.error_message}")
                return

            # 3. Process & Persist Deep Dive Results
            # We expect a JSON that fits DeepDiveResult (Package, Components, Transformations, Lineage)
            data = result.data or {}
            
            # AUTO-FIX: If LLM returned a list (common with some models), try to find the dict inside or default
            if isinstance(data, list):
                if len(data) > 0 and isinstance(data[0], dict):
                    data = data[0]
                else:
                    data = {}
            
            # Fetch project_id
            job_res = self.supabase.table("job_run").select("project_id").eq("job_id", job_id).single().execute()
            project_id = job_res.data.get("project_id")
            
            # Enrich data with IDs and dates
            now = datetime.now().isoformat()
            
            # Package enrichment
            pkg_data = data.get("package", {})
            pkg_data["project_id"] = project_id
            pkg_data["created_at"] = now
            pkg_data["updated_at"] = now
            if not pkg_data.get("package_id"): pkg_data["package_id"] = str(uuid.uuid4())
            # Try to link to asset if it was created in macro extraction
            if macro_nodes:
                # Heuristic: the first node of type PACKAGE or FILE might be our parent asset
                assets = [n for n in macro_nodes if n["node_type"] in ["PACKAGE", "FILE"]]
                if assets:
                    # Note: sync_extraction_result might have assigned a different UUID in DB
                    # This link is best-effort unless we return the id_map from catalog
                    pass 

            package = Package(**pkg_data)
            
            # Components enrichment
            components = []
            comp_id_map = {} # LLM might use temporary IDs, we fix them
            for c in data.get("components", []):
                llm_cid = c.get("component_id", str(uuid.uuid4()))
                
                # Sanitize component_id: must be valid UUID
                try:
                    uuid.UUID(str(llm_cid))
                    real_cid = str(llm_cid)
                except ValueError:
                    real_cid = str(uuid.uuid4())
                
                comp_id_map[llm_cid] = real_cid
                
                c["component_id"] = real_cid
                c["package_id"] = package.package_id
                c["created_at"] = now
                components.append(PackageComponent(**c))
                
            # Transformations enrichment
            transformations = []
            for t in data.get("transformations", []):
                t["project_id"] = project_id
                t["created_at"] = now
                
                # Sanitize ir_id
                ir_id = t.get("ir_id")
                try:
                    if ir_id: uuid.UUID(str(ir_id))
                    else: t["ir_id"] = str(uuid.uuid4())
                except ValueError:
                    t["ir_id"] = str(uuid.uuid4())
                
                # Remap component ID
                old_cid = t.get("source_component_id")
                if old_cid in comp_id_map:
                    t["source_component_id"] = comp_id_map[old_cid]
                else:
                    # Ensure it's a UUID or None
                    try:
                        if old_cid: uuid.UUID(str(old_cid))
                    except ValueError:
                        t["source_component_id"] = None
                        
                transformations.append(TransformationIR(**t))
                
            # Lineage enrichment
            lineage = []
            for l in data.get("lineage", []):
                l["project_id"] = project_id
                l["package_id"] = package.package_id
                l["created_at"] = now
                if not l.get("lineage_id"): l["lineage_id"] = str(uuid.uuid4())
                
                # --- ASSET RESOLUTION ---
                # Resolve names into UUIDs from the macro extraction
                src_search = l.get("source_asset_id") or l.get("source_asset_name")
                tgt_search = l.get("target_asset_id") or l.get("target_asset_name")
                
                # Heuristic: If name is missing but column has dot notation, try to parse table name
                if not src_search and l.get("source_column") and "." in l.get("source_column"):
                    src_search = l.get("source_column").split(".")[0]
                if not tgt_search and l.get("target_column") and "." in l.get("target_column"):
                    tgt_search = l.get("target_column").split(".")[0]
                
                # Resolution logic: Check ID map then Name map
                resolved_src = id_name_map.get(src_search) or name_map.get(src_search)
                resolved_tgt = id_name_map.get(tgt_search) or name_map.get(tgt_search)
                
                # Update with UUIDs or set to None (Pydantic expects UUID or None)
                try:
                    if resolved_src: uuid.UUID(str(resolved_src))
                    l["source_asset_id"] = resolved_src
                except ValueError:
                    l["source_asset_id"] = None
                    
                try:
                    if resolved_tgt: uuid.UUID(str(resolved_tgt))
                    l["target_asset_id"] = resolved_tgt
                except ValueError:
                    l["target_asset_id"] = None
                
                lineage.append(ColumnLineage(**l))
                
            deep_res = DeepDiveResult(
                package=package,
                components=components,
                transformations=transformations,
                lineage=lineage
            )
            
            self.catalog.sync_deep_dive_result(deep_res, project_id)
            print(f"[PIPELINE v4] Deep Dive Persisted for {item['path']}")

        except Exception as e:
            print(f"[PIPELINE v4] Error in _perform_deep_dive for {item['path']}: {e}")
            traceback.print_exc()

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
        is_ssis = file_path.lower().endswith(".dtsx") or file_path.lower().endswith(".xml")
        is_dsx = file_path.lower().endswith(".dsx")
        
        # Capture raw content for deterministic extractors before it potentially gets summarized for LLM
        raw_content = content 

        if is_ssis:
            try:
                print(f"[PIPELINE v3] Running Deep Package Inspection (SSIS Parser) for {file_path}")
                structure = SSISParser.parse_structure(content)
                
                # To avoid token limits with Flash models, we prioritize the structure summary
                # and only include raw content if it's reasonably sized.
                struct_json = json.dumps(structure, indent=2)
                if len(content) > 20000:
                    content = f"XML STRUCTURE SUMMARY:\n{struct_json}\n\nRAW CONTENT (Truncated):\n{content[:5000]}... [REST TRUNCATED]"
                else:
                    content = f"XML STRUCTURE SUMMARY:\n{struct_json}\n\nRAW CONTENT:\n{content}"
            except Exception as e:
                print(f"[PIPELINE] SSIS Parser failed for {file_path}: {e}")
                
            # --- v4.2 Deterministic Macro Extraction ---
            # Using the new extract_macro from SSISDeepExtractor
            try:
                print(f"[PIPELINE v4] Using Deterministic Macro Extraction for {file_path}")
                registry = ExtractorRegistry()
                # Use raw_content to ensure valid XML parsing
                macro_result = registry.extract(file_path, raw_content)
                
                if macro_result:
                     return ActionResult(
                        success=True,
                        data=macro_result.model_dump(), # Pydantic to dict
                        model_used="SSISDeepExtractor",
                        latency_ms=0
                     )
            except Exception as e:
                print(f"[PIPELINE v4] Deterministic Macro Failed: {e}")
                traceback.print_exc()
                # Fallback to LLM if needed, or fail safe

        
        elif is_dsx:
            try:
                print(f"[PIPELINE v4] Running DataStage Structural Parser for {file_path}")
                structure = DataStageParser.parse_structure(content)
                content = f"DATASTAGE STRUCTURE SUMMARY:\n{json.dumps(structure, indent=2)}\n\nRAW CONTENT:\n{content}"
            except Exception as e:
                print(f"[PIPELINE] DataStage Parser failed for {file_path}: {e}")

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

    def _persist_single_result(self, job_id: str, res: ProcessingResult) -> Dict[str, Any]:
        """Persiste el resultado de un solo archivo y retorna el mapa de IDs"""
        try:
            job_data = self.supabase.table("job_run").select("project_id").eq("job_id", job_id).single().execute()
            project_id = job_data.data.get("project_id")
            
            if not res.data:
                return {"node_id_map": {}}

            # Ensure 'nodes' and 'edges' exist
            if "nodes" not in res.data: res.data["nodes"] = []
            if "edges" not in res.data: res.data["edges"] = []
            if "evidences" not in res.data: res.data["evidences"] = []
            
            # Fix Nodes & Edges names/ids
            # Fix Nodes & Edges names/ids (Double Safety Check)
            filtered_nodes = []
            for i, node in enumerate(res.data.get("nodes", [])):
                if not isinstance(node, dict): continue
                
                # Critical Pydantic Fix: Ensure fields are NEVER None
                if not node.get("node_id"): node["node_id"] = f"unnamed_node_{i}_{job_id[:4]}"
                if not node.get("name"): node["name"] = node["node_id"].split('.')[-1]
                if not node.get("node_type"): node["node_type"] = "unknown"
                if not node.get("system"): node["system"] = "unknown"
                
                # Sanitize strings to avoid "None" string literal if that happened upstream
                if node["node_id"] is None: node["node_id"] = f"unnamed_node_{i}_{job_id[:4]}"
                if node["name"] is None: node["name"] = "unnamed"

                # V6.5 FIX: Attributes must be a dict, not a list
                if "attributes" in node:
                    if isinstance(node["attributes"], list):
                        # Convert list of KV pairs to dict if needed (common VLM hallucination)
                        new_attrs = {}
                        for item in node["attributes"]:
                            if isinstance(item, dict):
                                k = item.get("name") or item.get("attribute_name") or "unknown"
                                v = item.get("value") or item.get("attribute_value") or "unknown"
                                new_attrs[str(k)] = v
                        node["attributes"] = new_attrs
                    elif not isinstance(node["attributes"], dict):
                         node["attributes"] = {} # nuking invalid format

                filtered_nodes.append(node)
            res.data["nodes"] = filtered_nodes
            
            for edge in res.data.get("edges", []):
                if "edge_id" not in edge: edge["edge_id"] = str(uuid.uuid4())
                if "rationale" not in edge: edge["rationale"] = "Extracted by LLM"
                if "confidence" not in edge: edge["confidence"] = 1.0
            
            # Add meta info
            res.data["meta"] = {
                "source_file": res.file_path,
                "extractor_id": res.model_used or res.strategy_used
            }
            
            # Use Pydantic models for validation/conversion
            extraction_result = ExtractionResult(**res.data)
            
            # Sync to Catalog
            node_id_map = self.catalog.sync_extraction_result(extraction_result, project_id, artifact_id=job_id)
            return {"node_id_map": node_id_map}
                        
        except Exception as e:
            print(f"[PIPELINE] Persist error for {res.file_path}: {e}")
            traceback.print_exc()
            return {"node_id_map": {}}

    def _persist_results(self, job_id: str, file_results: List[ProcessingResult]):
        """Legacy compatibility or bulk persistence handler"""
        # Since we now persist per-item, this might be redundant but 
        # let's keep it if we need to sync graphs or something else at high level.
        pass

    def _update_job_progress(self, job_id: str, stage: str, pct: int = None):
        try:
            data = {"current_stage": stage}
            if pct is not None:
                data["progress_pct"] = pct
            self.supabase.table("job_run").update(data).eq("job_id", job_id).execute()
        except: pass

    def _update_job_status(self, job_id: str, status: str, msg: str = None, dtl: str = None):
        data = {"status": status}
        if msg: 
            data["error_message"] = msg
        if dtl:
            data["error_details"] = dtl
        elif msg:
            data["error_details"] = msg # Fallback if no specific dtl

        try:
            self.supabase.table("job_run").update(data).eq("job_id", job_id).execute()
        except Exception as e:
            print(f"[PIPELINE ERROR] Failed to update job status: {e}", flush=True)

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

    def _run_post_processing_audit(self, job_id: str):
        """
        Calculates accuracy metrics and generates improvement recommendations.
        """
        try:
            # 1. Fetch project_id
            job_res = self.supabase.table("job_run").select("project_id").eq("job_id", job_id).single().execute()
            project_id = job_res.data.get("project_id")
            
            # 2. Run Audit & Refinement
            report = self.refiner.generate_recommendations(project_id)
            
            # 3. Persist Audit Result to job_run and audit_snapshot table
            print(f"[AUDITOR] Audit completed for project {project_id}")
            print(f"  - Coverage: {report['audit']['metrics']['coverage_score']}%")
            print(f"  - AI Suggestions: {len(report['ai_suggestions'])} found.")
            
            # Save Persistent Snapshot
            self.auditor.save_snapshot(job_id, report['audit'])
            
        except Exception as e:
            print(f"[AUDITOR ERROR] Audit failed: {e}")
            traceback.print_exc()
