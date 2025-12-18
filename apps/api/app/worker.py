import asyncio
import traceback
import sys
import os

# Asegurar que el path incluye el directorio apps/api para imports relativos si se ejecuta como script
if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "app"

from .services.queue import SQLJobQueue
from .pipeline import PipelineOrchestrator
from .config import settings
from supabase import create_client

async def process_job(job_queue_item):
    job_id = job_queue_item["job_id"]
    queue = SQLJobQueue()
    
    # Cliente Supabase
    key_to_use = settings.SUPABASE_SERVICE_ROLE_KEY if settings.SUPABASE_SERVICE_ROLE_KEY else settings.SUPABASE_KEY
    supabase = create_client(settings.SUPABASE_URL, key_to_use)
    
    print(f"[WORKER] Processing Job {job_id}")
    
    try:
        # 1. Obtener detalles del Job
        job_res = supabase.table("job_run").select("*").eq("job_id", job_id).single().execute()
        if not job_res.data:
            raise Exception(f"Job Run {job_id} not found")
        job_run = job_res.data
        project_id = job_run["project_id"]
        
        # Actualizar estado a Running
        supabase.table("job_run").update({"status": "running", "started_at": "now()"}).eq("job_id", job_id).execute()
        supabase.table("solutions").update({"status": "PROCESSING"}).eq("id", project_id).execute()
        
        # 2. Obtener ruta del archivo
        sol_res = supabase.table("solutions").select("storage_path").eq("id", project_id).single().execute()
        if not sol_res.data:
             raise Exception(f"Solution {project_id} not found")
             
        file_path = sol_res.data["storage_path"].strip()
        
        # 3. Ejecutar Pipeline
        print(f"[WORKER] Starting Pipeline for {file_path}...")
        
        # Instanciar orquestador pasando el cliente supabase
        orchestrator = PipelineOrchestrator(supabase)
        
        # Ejecutar pipeline (esto bloquea el worker por ahora, idealmente sería async)
        # Como el orchestrator usa llamadas síncronas a LLM, está bien en este worker
        success = orchestrator.execute_pipeline(job_id, file_path)
        
        if success:
            # Completar Job
            supabase.table("job_run").update({
                "status": "completed", 
                "finished_at": "now()", 
                "progress_pct": 100
            }).eq("job_id", job_id).execute()
            
            queue.complete_job(job_queue_item["id"])
            
            # Actualizar estado de solución
            supabase.table("solutions").update({"status": "READY"}).eq("id", project_id).execute()
            print(f"[WORKER] Job {job_id} Completed Successfully")
            
        else:
            raise Exception("Pipeline execution failed (check logs)")
        
    except Exception as e:
        print(f"[WORKER] Job {job_id} Failed: {e}")
        traceback.print_exc()
        
        # Registrar error
        supabase.table("job_run").update({
            "status": "failed", 
            "error_message": str(e),
            "finished_at": "now()"
        }).eq("job_id", job_id).execute()
        
        supabase.table("solutions").update({"status": "ERROR"}).eq("id", project_id).execute()
        queue.fail_job(job_queue_item["id"], str(e))

async def worker_loop():
    queue = SQLJobQueue()
    print("[WORKER] Started polling (New Pipeline Enabled)...")
    while True:
        try:
            job = queue.fetch_next_job()
            if job:
                await process_job(job)
            else:
                await asyncio.sleep(5) # Poll interval
        except Exception as e:
            print(f"[WORKER] Loop Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(worker_loop())