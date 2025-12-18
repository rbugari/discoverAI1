"""
Pipeline Orchestrator - Coordina el procesamiento completo de archivos
con routing de modelos y auditoría detallada
"""
import os
import time
import hashlib
import json
import traceback
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from supabase import create_client

from ..models.extraction import ExtractionResult, ExtractedNode, ExtractedEdge, Evidence, Locator
from ..router import get_model_router
from ..audit import FileProcessingLogger
from ..actions import ActionRunner, ActionResult
from ..services.storage import StorageService
from ..services.catalog import CatalogService
from ..config import settings

@dataclass
class ProcessingResult:
    """Resultado del procesamiento de un archivo"""
    success: bool
    file_path: str
    strategy_used: str
    action_taken: str
    
    data: Optional[Dict[str, Any]] = None # Datos extraídos (nodos, edges, etc)
    
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
    """Métricas globales del pipeline"""
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
    Orquesta el procesamiento completo de archivos con:
    - Detección de tipos
    - Routing de estrategias
    - Ejecución de acciones
    - Auditoría detallada
    """
    
    def __init__(self, supabase_client=None):
        self.router = get_model_router()
        self.logger = FileProcessingLogger(supabase_client)
        self.action_runner = ActionRunner(self.logger)
        self.storage = StorageService()
        
        # Inicializar cliente supabase si no se proporciona
        if supabase_client:
            self.supabase = supabase_client
        else:
            self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            
        self.catalog = CatalogService(self.supabase)
        
        # Métricas del pipeline
        self.metrics = PipelineMetrics()
        self.metrics.strategy_counts = {}
        self.metrics.model_usage = {}
        self.metrics.error_counts = {}
    
    def execute_pipeline(self, job_id: str, artifact_path: str) -> bool:
        """
        Ejecuta el pipeline completo de procesamiento
        
        Args:
            job_id: ID del job
            artifact_path: Path al artefacto (ZIP/repo)
            
        Returns:
            True si el pipeline completó exitosamente
        """
        print(f"[PIPELINE] Starting pipeline for job {job_id}")
        
        try:
            # Etapa 1: Ingesta (Descarga/Clonado)
            ingest_result = self._execute_stage(job_id, "ingest", lambda: self._ingest_artifact(artifact_path))
            
            if not ingest_result.success:
                raise Exception(f"Ingest failed: {ingest_result.error_message}")
                
            # Obtener ruta local descomprimida/clonada
            local_artifact_path = ingest_result.data.get("local_path")
            if not local_artifact_path:
                raise Exception("Ingest stage did not return 'local_path'")
            
            print(f"[PIPELINE] Artifact ingested to: {local_artifact_path}")
            
            # Etapa 2: Enumerar archivos (Usando ruta local)
            files_result = self._execute_stage(job_id, "enumerate_files", lambda: self._enumerate_files(local_artifact_path))
            
            if not files_result.success:
                raise Exception(f"Failed to enumerate files: {files_result.error_message}")
            
            files = files_result.data.get("files", [])
            print(f"[PIPELINE] Found {len(files)} files to process")
            
            # Procesar cada archivo
            file_results = []
            for i, file_info in enumerate(files):
                print(f"[PIPELINE] Processing file {i+1}/{len(files)}: {file_info['path']}")
                
                file_result = self._process_file(
                    job_id, 
                    file_info['path'], 
                    file_info['content'],
                    file_info.get('size', 0)
                )
                
                file_results.append(file_result)
                self._update_metrics(file_result)
            
            # Etapa 3: Persistir resultados
            self._execute_stage(job_id, "persist_results", lambda: self._persist_results(job_id, file_results))
            
            # Etapa 4: Actualizar grafo (opcional)
            if settings.NEO4J_URI:
                self._execute_stage(job_id, "update_graph", lambda: self._update_graph(job_id, file_results))
            
            print(f"[PIPELINE] Pipeline completed successfully for job {job_id}")
            print(f"[PIPELINE] Metrics: {self._get_metrics_summary()}")
            
            return True
            
        except Exception as e:
            error_msg = f"Pipeline failed for job {job_id}: {str(e)}"
            print(f"[PIPELINE] {error_msg}")
            print(f"[PIPELINE] Traceback: {traceback.format_exc()}")
            
            # Registrar error en el job
            self._update_job_status(job_id, "ERROR", error_msg)
            
            return False
    
    def _execute_stage(self, job_id: str, stage_name: str, stage_func) -> ActionResult:
        """Ejecuta una etapa del pipeline con logging"""
        print(f"[PIPELINE] Executing stage: {stage_name}")
        
        start_time = time.time()
        
        try:
            result = stage_func()
            
            # Actualizar progreso del job
            self._update_job_progress(job_id, stage_name)
            
            return ActionResult(success=True, data=result if result else {})
            
        except Exception as e:
            error_msg = f"Stage {stage_name} failed: {str(e)}"
            print(f"[PIPELINE] {error_msg}")
            
            return ActionResult(
                success=False,
                error_message=error_msg,
                error_type="stage_execution_error"
            )
    
    def _process_file(self, job_id: str, file_path: str, content: str, file_size: int) -> ProcessingResult:
        """
        Procesa un archivo individual con estrategia de routing
        """
        start_time = time.time()
        
        try:
            # Calcular hash del archivo
            file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
            
            # Etapa 1: Triage rápido
            triage_result = self._triage_file(job_id, file_path, content, file_size, file_hash)
            
            if not triage_result.success:
                return ProcessingResult(
                    success=False,
                    file_path=file_path,
                    strategy_used="triage_failed",
                    action_taken="triage",
                    error_message=triage_result.error_message,
                    error_type=triage_result.error_type,
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
            
            # Determinar estrategia basada en triage
            strategy = self._determine_strategy(triage_result.data)
            
            # Ejecutar estrategia
            if strategy == "native_parser":
                extraction_result = self._extract_with_native_parser(job_id, file_path, content)
            elif strategy == "structural":
                extraction_result = self._extract_with_structural(job_id, file_path, content)
            elif strategy == "llm_heavy":
                extraction_result = self._extract_with_llm(job_id, file_path, content)
            else:
                extraction_result = ActionResult(
                    success=False,
                    error_message=f"Unknown strategy: {strategy}",
                    error_type="strategy_error"
                )
            
            # Procesar resultado de extracción
            if extraction_result.success:
                return self._create_success_result(
                    file_path, strategy, extraction_result, start_time
                )
            else:
                return self._create_error_result(
                    file_path, strategy, extraction_result, start_time
                )
                
        except Exception as e:
            error_msg = f"Unexpected error processing file {file_path}: {str(e)}"
            print(f"[PIPELINE] {error_msg}")
            
            return ProcessingResult(
                success=False,
                file_path=file_path,
                strategy_used="unknown",
                action_taken="processing",
                error_message=error_msg,
                error_type="unexpected_error",
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
    
    def _triage_file(self, job_id: str, file_path: str, content: str, file_size: int, file_hash: str) -> ActionResult:
        """Ejecuta triage rápido para clasificar el archivo"""
        
        # Preparar datos para triage
        triage_input = {
            "file_path": file_path,
            "file_size": file_size,
            "file_hash": file_hash,
            "content_preview": content[:1000],  # Primeros 1000 chars
            "extension": Path(file_path).suffix.lower()
        }
        
        context = {
            "job_id": job_id,
            "file_path": file_path,
            "stage": "triage"
        }
        
        # Iniciar log de auditoría
        log_id = self.logger.start_file_processing(
            job_id, file_path, "triage_fast", file_size, file_hash
        )
        
        # Ejecutar acción de triage
        result = self.action_runner.run_action(
            "triage_fast", triage_input, context, log_id
        )
        
        # Completar log
        if result.success:
            self.logger.complete_file_processing(log_id, "success", "triage")
        else:
            self.logger.log_file_error(
                log_id, result.error_type or "triage_error", result.error_message
            )
        
        return result
    
    def _determine_strategy(self, triage_data: Dict[str, Any]) -> str:
        """Determina estrategia de procesamiento basada en triage"""
        
        recommended = triage_data.get("recommended_strategy", "llm_heavy")
        
        # Mapeo de recomendaciones a estrategias implementadas
        strategy_map = {
            "native_parser": "native_parser",
            "structural": "structural", 
            "llm_heavy": "llm_heavy"
        }
        
        return strategy_map.get(recommended, "llm_heavy")
    
    def _extract_with_native_parser(self, job_id: str, file_path: str, content: str) -> ActionResult:
        """Extracción usando parsers nativos (sin LLM)"""
        
        extension = Path(file_path).suffix.lower()
        
        if extension == ".sql":
            return self._extract_sql_native(file_path, content)
        elif extension == ".py":
            return self._extract_python_native(file_path, content)
        elif extension in [".json", ".xml"]:
            return self._extract_structural_native(file_path, content)
        else:
            return ActionResult(
                success=False,
                error_message=f"No native parser for extension {extension}",
                error_type="no_native_parser"
            )
    
    def _extract_sql_native(self, file_path: str, content: str) -> ActionResult:
        """Extracción nativa de SQL"""
        try:
            # Parser SQL simple usando regex
            import re
            
            # Buscar tablas en FROM, JOIN, INSERT, UPDATE
            table_pattern = r'(?:FROM|JOIN|INTO|UPDATE|TABLE)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)'
            tables = re.findall(table_pattern, content, re.IGNORECASE)
            
            # Normalizar nombres de tablas
            unique_tables = list(set(tables))
            
            # Crear nodos y edges
            nodes = []
            edges = []
            
            for table in unique_tables:
                node_id = f"table_{table.replace('.', '_')}"
                nodes.append({
                    "node_id": node_id,
                    "node_type": "table",
                    "name": table,
                    "system": "sqlserver",  # Asumir por ahora
                    "attributes": {
                        "extracted_by": "native_parser",
                        "confidence": 0.8
                    }
                })
            
            return ActionResult(
                success=True,
                data={
                    "nodes": nodes,
                    "edges": edges,
                    "extraction_method": "native_sql_parser"
                }
            )
            
        except Exception as e:
            return ActionResult(
                success=False,
                error_message=f"SQL native extraction failed: {str(e)}",
                error_type="native_parser_error"
            )
    
    def _extract_with_structural(self, job_id: str, file_path: str, content: str) -> ActionResult:
        """Extracción estructural usando regex y parsing simple"""
        
        # Para archivos JSON/XML, hacer parsing simple
        extension = Path(file_path).suffix.lower()
        
        if extension == ".json":
            # TODO: Implementar parser JSON
            return ActionResult(success=False, error_message="JSON parser not implemented", error_type="not_implemented")
        elif extension == ".xml":
            # TODO: Implementar parser XML
            return ActionResult(success=False, error_message="XML parser not implemented", error_type="not_implemented")
        else:
            # Para otros formatos, usar regex patterns
            return ActionResult(success=False, error_message="Regex parser not implemented", error_type="not_implemented")
    
    def _extract_with_llm(self, job_id: str, file_path: str, content: str) -> ActionResult:
        """Extracción usando LLM pesado"""
        
        # Determinar qué tipo de extracción LLM usar
        extension = Path(file_path).suffix.lower()
        
        if extension == ".sql":
            action_name = "extract_sql"
        elif extension == ".py":
            action_name = "extract_python"
        elif extension == ".dtsx":
            action_name = "extract_strict"  # SSIS requiere extracción estricta
        else:
            action_name = "extract_strict"  # Default
        
        # Preparar input para LLM
        llm_input = {
            "file_path": file_path,
            "content": content,
            "file_extension": extension,
            "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16]
        }
        
        context = {
            "job_id": job_id,
            "file_path": file_path,
            "stage": "extraction",
            "strategy": "llm_heavy"
        }
        
        # Iniciar log de auditoría
        log_id = self.logger.start_file_processing(
            job_id, file_path, action_name, len(content.encode('utf-8'))
        )
        
        # Ejecutar extracción con LLM
        result = self.action_runner.run_action(
            action_name, llm_input, context, log_id
        )
        
        # Procesar resultado
        if result.success and result.data:
            # Extraer conteos de nodos/edges
            nodes_count = len(result.data.get("nodes", []))
            edges_count = len(result.data.get("edges", []))
            evidences_count = len(result.data.get("evidences", []))
            
            # Actualizar log con resultados
            self.logger.update_processing_results(
                log_id, nodes_count, edges_count, evidences_count, result.data
            )
            
            self.logger.complete_file_processing(log_id, "success", "llm_heavy")
            
        else:
            self.logger.log_file_error(
                log_id, result.error_type or "extraction_error", result.error_message
            )
        
        return result
    
    def _create_success_result(self, file_path: str, strategy: str, extraction_result: ActionResult, start_time: float) -> ProcessingResult:
        """Crea resultado exitoso del procesamiento"""
        
        data = extraction_result.data or {}
        nodes = len(data.get("nodes", []))
        edges = len(data.get("edges", []))
        evidences = len(data.get("evidences", []))
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return ProcessingResult(
            success=True,
            file_path=file_path,
            strategy_used=strategy,
            action_taken="extraction",
            data=data,
            nodes_extracted=nodes,
            edges_extracted=edges,
            evidences_extracted=evidences,
            model_used=extraction_result.model_used,
            fallback_used=extraction_result.fallback_used,
            processing_time_ms=processing_time,
            tokens_used=extraction_result.total_tokens or 0,
            cost_estimate=extraction_result.cost_estimate_usd or 0.0
        )
    
    def _create_error_result(self, file_path: str, strategy: str, extraction_result: ActionResult, start_time: float) -> ProcessingResult:
        """Crea resultado con error del procesamiento"""
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return ProcessingResult(
            success=False,
            file_path=file_path,
            strategy_used=strategy,
            action_taken="extraction",
            error_message=extraction_result.error_message,
            error_type=extraction_result.error_type,
            model_used=extraction_result.model_used,
            fallback_used=extraction_result.fallback_used,
            processing_time_ms=processing_time,
            tokens_used=extraction_result.total_tokens or 0,
            cost_estimate=extraction_result.cost_estimate_usd or 0.0
        )
    
    def _update_metrics(self, result: ProcessingResult):
        """Actualiza métricas globales"""
        self.metrics.total_files += 1
        
        if result.success:
            self.metrics.successful_files += 1
            self.metrics.total_nodes += result.nodes_extracted
            self.metrics.total_edges += result.edges_extracted
            self.metrics.total_evidences += result.evidences_extracted
        else:
            self.metrics.failed_files += 1
            
            # Contar errores por tipo
            if result.error_type:
                self.metrics.error_counts[result.error_type] = self.metrics.error_counts.get(result.error_type, 0) + 1
        
        # Contar estrategias
        strategy = result.strategy_used
        self.metrics.strategy_counts[strategy] = self.metrics.strategy_counts.get(strategy, 0) + 1
        
        # Contar modelos usados
        if result.model_used:
            self.metrics.model_usage[result.model_used] = self.metrics.model_usage.get(result.model_used, 0) + 1
        
        # Acumular tokens y costos
        self.metrics.total_tokens += result.tokens_used
        self.metrics.total_cost += result.cost_estimate
        self.metrics.total_processing_time_ms += result.processing_time_ms
    
    def _get_metrics_summary(self) -> str:
        """Obtiene resumen de métricas"""
        return f"""
        Files: {self.metrics.successful_files}/{self.metrics.total_files} successful
        Nodes: {self.metrics.total_nodes}, Edges: {self.metrics.total_edges}, Evidences: {self.metrics.total_evidences}
        Tokens: {self.metrics.total_tokens}, Cost: ${self.metrics.total_cost:.4f}
        Time: {self.metrics.total_processing_time_ms/1000:.1f}s
        Strategies: {self.metrics.strategy_counts}
        Models: {self.metrics.model_usage}
        """.strip()
    
    def _update_job_progress(self, job_id: str, current_stage: str):
        """Actualiza progreso del job"""
        try:
            self.supabase.table("job_run").update({
                "current_stage": current_stage,
                # "updated_at": datetime.utcnow().isoformat()  # Columna no existe en schema actual
            }).eq("job_id", job_id).execute()
        except Exception as e:
            print(f"[PIPELINE] Error updating job progress: {e}")
    
    def _update_job_status(self, job_id: str, status: str, error_message: Optional[str] = None):
        """Actualiza estado del job"""
        try:
            # data = {"status": status, "updated_at": datetime.utcnow().isoformat()} # updated_at no existe
            data = {"status": status}
            if error_message:
                data["error_message"] = error_message
                
            self.supabase.table("job_run").update(data).eq("job_id", job_id).execute()
        except Exception as e:
            print(f"[PIPELINE] Error updating job status: {e}")
    
    def _persist_results(self, job_id: str, file_results: List[ProcessingResult]):
        """Persiste resultados en la base de datos"""
        print(f"[PIPELINE] Persisting {len(file_results)} results for job {job_id}")
        
        successful_results = [r for r in file_results if r.success]
        
        # Obtener project_id del job
        try:
            job_data = self.supabase.table("job_run").select("project_id").eq("job_id", job_id).single().execute()
            project_id = job_data.data.get("project_id") if job_data.data else None
            
            if not project_id:
                print(f"[PIPELINE] Project ID not found for job {job_id}")
                return {"persisted_count": 0}
                
        except Exception as e:
            print(f"[PIPELINE] Error getting project_id: {e}")
            return {"persisted_count": 0}
        
        count = 0
        for result in successful_results:
            try:
                if not result.data:
                    continue
                    
                # Mapear diccionario a modelos Pydantic
                raw_data = result.data
                
                # Nodos
                nodes = []
                for n in raw_data.get("nodes", []):
                    nodes.append(ExtractedNode(
                        node_id=n.get("node_id"),
                        node_type=n.get("node_type"),
                        name=n.get("name"),
                        system=n.get("system", "unknown"),
                        attributes=n.get("attributes", {})
                    ))
                
                # Edges
                edges = []
                for e in raw_data.get("edges", []):
                    edges.append(ExtractedEdge(
                        edge_id=e.get("edge_id"),
                        edge_type=e.get("edge_type"),
                        from_node_id=e.get("from_node_id"),
                        to_node_id=e.get("to_node_id"),
                        confidence=e.get("confidence", 1.0),
                        rationale=e.get("rationale", ""),
                        evidence_refs=e.get("evidence_refs", []),
                        is_hypothesis=e.get("is_hypothesis", False)
                    ))
                
                # Evidencias
                evidences = []
                # TODO: Mapear evidencias si vienen en el output del LLM
                # Por ahora el prompt no siempre devuelve evidencias estructuradas completas
                
                extraction_result = ExtractionResult(
                    meta={"source_file": result.file_path, "extractor_id": result.strategy_used},
                    nodes=nodes,
                    edges=edges,
                    evidences=evidences
                )
                
                # Persistir usando CatalogService
                self.catalog.sync_extraction_result(extraction_result, project_id)
                count += 1
                
            except Exception as e:
                print(f"[PIPELINE] Error persisting result for {result.file_path}: {e}")
                traceback.print_exc()
            
        print(f"[PIPELINE] Persisted {count} successful extractions")
        return {"persisted_count": count}
    
    def _update_graph(self, job_id: str, file_results: List[ProcessingResult]):
        """Actualiza grafo Neo4j"""
        print(f"[PIPELINE] Graph update logic placeholder")
        return {"graph_updated": 0}
    
    def _ingest_artifact(self, artifact_path: str) -> Dict[str, Any]:
        """Ingesta el artefacto (ZIP/repo)"""
        print(f"[PIPELINE] Ingesting artifact: {artifact_path}")
        
        # Descargar/Clonar usando StorageService
        try:
            local_path = self.storage.download_and_extract(artifact_path)
        except Exception as e:
            print(f"[PIPELINE] Error downloading/extracting artifact: {e}")
            raise e
        
        # Calcular hash del directorio (opcional, o usar el original)
        artifact_hash = hashlib.sha256(artifact_path.encode()).hexdigest()
        
        return {
            "artifact_path": artifact_path, # Ruta original
            "local_path": local_path,       # Ruta local procesable
            "artifact_hash": artifact_hash,
            "ingested_at": datetime.utcnow().isoformat()
        }
    
    def _enumerate_files(self, artifact_path: str) -> Dict[str, Any]:
        """Enumera todos los archivos procesables en el artefacto"""
        print(f"[PIPELINE] Enumerating files in: {artifact_path}")
        
        files = []
        
        # Si es un directorio, recorrerlo
        if os.path.isdir(artifact_path):
            for file_path, content, ext in self.storage.walk_files(artifact_path):
                files.append({
                    "path": file_path,
                    "content": content,
                    "extension": ext,
                    "size": len(content.encode('utf-8'))
                })
        
        # Si es un archivo, procesarlo directamente
        elif os.path.isfile(artifact_path):
            with open(artifact_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            files.append({
                "path": artifact_path,
                "content": content,
                "extension": Path(artifact_path).suffix.lower(),
                "size": len(content.encode('utf-8'))
            })
        
        print(f"[PIPELINE] Found {len(files)} files to process")
        
        return {"files": files, "total_files": len(files)}