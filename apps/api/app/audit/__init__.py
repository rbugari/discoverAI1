"""
Sistema de Auditoría de Procesamiento de Archivos
Registra qué pasó con cada archivo: modelos usados, tokens, errores, etc.
"""
import uuid
import time
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from supabase import create_client, Client

from ..config import settings

@dataclass
class FileProcessingLog:
    """Datos de auditoría para procesamiento de archivo"""
    job_id: str
    file_path: str
    file_size_bytes: Optional[int] = None
    file_hash: Optional[str] = None
    
    action_name: str = ""
    strategy_used: Optional[str] = None
    
    model_provider: Optional[str] = None
    model_used: Optional[str] = None
    fallback_used: bool = False
    fallback_chain: Optional[List[str]] = None
    
    status: str = "pending"  # success, failed, fallback_exhausted
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    cost_estimate_usd: Optional[float] = None
    
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    nodes_extracted: int = 0
    edges_extracted: int = 0
    evidences_extracted: int = 0
    result_hash: Optional[str] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class FileProcessingLogger:
    """
    Logger especializado para registrar el procesamiento de archivos
    con detalle de modelos usados, tokens, errores, etc.
    """
    
    def __init__(self, supabase_client: Optional[Client] = None):
        self.supabase = supabase_client or create_client(
            settings.SUPABASE_URL, 
            settings.SUPABASE_KEY
        )
        self._current_logs: Dict[str, FileProcessingLog] = {}
    
    def start_file_processing(
        self, 
        job_id: str, 
        file_path: str, 
        action_name: str,
        file_size: Optional[int] = None,
        file_hash: Optional[str] = None
    ) -> str:
        """
        Inicia el registro de procesamiento de un archivo
        
        Returns:
            log_id para usar en updates posteriores
        """
        log_id = str(uuid.uuid4())
        
        log_entry = FileProcessingLog(
            job_id=job_id,
            file_path=file_path,
            file_size_bytes=file_size,
            file_hash=file_hash,
            action_name=action_name,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self._current_logs[log_id] = log_entry
        
        # Insertar en DB
        try:
            log_data = asdict(log_entry)
            log_data['id'] = log_id # Fix: Assign the generated ID to the 'id' column
            # Convertir datetime a string ISO
            if log_data['created_at']:
                log_data['created_at'] = log_data['created_at'].isoformat()
            if log_data['updated_at']:
                log_data['updated_at'] = log_data['updated_at'].isoformat()
            
            # Convertir lista a JSON para PostgreSQL
            if log_data['fallback_chain']:
                log_data['fallback_chain'] = json.dumps(log_data['fallback_chain'])
            
            result = self.supabase.table('file_processing_log').insert(log_data).execute()
            
        except Exception as e:
            print(f"[AUDIT] Error al iniciar log de archivo {file_path}: {e}")
            # No fallamos el procesamiento por error de auditoría
        
        return log_id
    
    def update_model_usage(
        self, 
        log_id: str, 
        model_provider: str, 
        model_used: str,
        fallback_used: bool = False,
        fallback_chain: Optional[List[str]] = None
    ):
        """Actualiza información del modelo usado"""
        if log_id not in self._current_logs:
            return
        
        log_entry = self._current_logs[log_id]
        log_entry.model_provider = model_provider
        log_entry.model_used = model_used
        log_entry.fallback_used = fallback_used
        log_entry.fallback_chain = fallback_chain or []
        log_entry.updated_at = datetime.utcnow()
    
    def update_tokens_and_cost(
        self,
        log_id: str,
        input_tokens: int,
        output_tokens: int,
        cost_estimate: Optional[float] = None,
        latency_ms: Optional[int] = None
    ):
        """Actualiza métricas de tokens y costos"""
        if log_id not in self._current_logs:
            return
        
        log_entry = self._current_logs[log_id]
        log_entry.input_tokens = input_tokens
        log_entry.output_tokens = output_tokens
        log_entry.total_tokens = input_tokens + output_tokens
        log_entry.cost_estimate_usd = cost_estimate
        log_entry.latency_ms = latency_ms
        log_entry.updated_at = datetime.utcnow()
    
    def update_processing_results(
        self,
        log_id: str,
        nodes_extracted: int = 0,
        edges_extracted: int = 0,
        evidences_extracted: int = 0,
        result_data: Optional[dict] = None
    ):
        """Actualiza resultados del procesamiento"""
        if log_id not in self._current_logs:
            return
        
        log_entry = self._current_logs[log_id]
        log_entry.nodes_extracted = nodes_extracted
        log_entry.edges_extracted = edges_extracted
        log_entry.evidences_extracted = evidences_extracted
        
        # Generar hash del resultado para deduplicación
        if result_data:
            result_json = json.dumps(result_data, sort_keys=True)
            log_entry.result_hash = hashlib.sha256(result_json.encode()).hexdigest()[:16]
        
        log_entry.updated_at = datetime.utcnow()
    
    def complete_file_processing(
        self, 
        log_id: str, 
        status: str = "success",
        strategy_used: Optional[str] = None
    ):
        """Completa el procesamiento del archivo"""
        if log_id not in self._current_logs:
            return
        
        log_entry = self._current_logs[log_id]
        log_entry.status = status
        log_entry.strategy_used = strategy_used
        log_entry.updated_at = datetime.utcnow()
        
        # Actualizar en DB
        try:
            log_data = asdict(log_entry)
            
            # Convertir tipos para PostgreSQL
            log_data['updated_at'] = log_data['updated_at'].isoformat()
            if log_data['created_at']:
                log_data['created_at'] = log_data['created_at'].isoformat()
            
            if log_data['fallback_chain']:
                log_data['fallback_chain'] = json.dumps(log_data['fallback_chain'])
            
            result = self.supabase.table('file_processing_log').update(log_data).eq('id', log_id).execute()
            
            # Limpiar de memoria
            del self._current_logs[log_id]
            
        except Exception as e:
            print(f"[AUDIT] Error al completar log {log_id}: {e}")
    
    def log_file_error(
        self,
        log_id: str,
        error_type: str,
        error_message: str,
        retry_count: int = 0
    ):
        """Registra error en procesamiento de archivo"""
        if log_id not in self._current_logs:
            return
        
        log_entry = self._current_logs[log_id]
        log_entry.error_type = error_type
        log_entry.error_message = error_message
        log_entry.retry_count = retry_count
        log_entry.status = "failed"
        log_entry.updated_at = datetime.utcnow()
        
        # Actualizar en DB
        try:
            log_data = {
                'error_type': error_type,
                'error_message': error_message,
                'retry_count': retry_count,
                'status': 'failed',
                'updated_at': datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table('file_processing_log').update(log_data).eq('id', log_id).execute()
            
        except Exception as e:
            print(f"[AUDIT] Error al registrar error de archivo {log_id}: {e}")
    
    def get_file_history(self, job_id: str, file_path: str) -> List[Dict[str, Any]]:
        """Obtiene historial de procesamiento de un archivo"""
        try:
            result = self.supabase.table('file_processing_log').select('*').eq('job_id', job_id).eq('file_path', file_path).order('created_at', desc=True).execute()
            return result.data or []
        except Exception as e:
            print(f"[AUDIT] Error al obtener historial de archivo {file_path}: {e}")
            return []
    
    def get_job_files_summary(self, job_id: str) -> Dict[str, Any]:
        """Obtiene resumen de archivos procesados en un job"""
        try:
            # Total de archivos
            total_result = self.supabase.table('file_processing_log').select('*', count='exact').eq('job_id', job_id).execute()
            
            # Por estado
            success_result = self.supabase.table('file_processing_log').select('*', count='exact').eq('job_id', job_id).eq('status', 'success').execute()
            failed_result = self.supabase.table('file_processing_log').select('*', count='exact').eq('job_id', job_id).eq('status', 'failed').execute()
            
            # Con fallbacks
            fallback_result = self.supabase.table('file_processing_log').select('*', count='exact').eq('job_id', job_id).eq('fallback_used', True).execute()
            
            # Tokens y costos
            stats_result = self.supabase.rpc('get_file_processing_stats', {'job_id_param': job_id}).execute()
            
            return {
                'total_files': total_result.count or 0,
                'successful_files': success_result.count or 0,
                'failed_files': failed_result.count or 0,
                'fallback_files': fallback_result.count or 0,
                'stats': stats_result.data[0] if stats_result.data else {}
            }
            
        except Exception as e:
            print(f"[AUDIT] Error al obtener resumen de job {job_id}: {e}")
            return {
                'total_files': 0,
                'successful_files': 0,
                'failed_files': 0,
                'fallback_files': 0,
                'stats': {}
            }

# Función auxiliar para RPC de estadísticas
def create_file_processing_stats_rpc():
    """Crea función RPC para estadísticas agregadas"""
    return """
    CREATE OR REPLACE FUNCTION get_file_processing_stats(job_id_param UUID)
    RETURNS TABLE (
        total_tokens BIGINT,
        total_cost NUMERIC,
        avg_latency_ms NUMERIC,
        total_nodes BIGINT,
        total_edges BIGINT,
        total_evidences BIGINT
    ) AS $$
    BEGIN
        RETURN QUERY
        SELECT 
            COALESCE(SUM(total_tokens), 0)::BIGINT,
            COALESCE(SUM(cost_estimate_usd), 0.0)::NUMERIC,
            COALESCE(AVG(latency_ms), 0.0)::NUMERIC,
            COALESCE(SUM(nodes_extracted), 0)::BIGINT,
            COALESCE(SUM(edges_extracted), 0)::BIGINT,
            COALESCE(SUM(evidences_extracted), 0)::BIGINT
        FROM file_processing_log
        WHERE job_id = job_id_param;
    END;
    $$ LANGUAGE plpgsql;
    """