import asyncio
import traceback
import sys
import os

import asyncio
import traceback
import sys
import os

# Ensure the path includes the apps/api directory for relative imports if executed as a script
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
    
    # Supabase Client
    key_to_use = settings.SUPABASE_SERVICE_ROLE_KEY if settings.SUPABASE_SERVICE_ROLE_KEY else settings.SUPABASE_KEY
    supabase = create_client(settings.SUPABASE_URL, key_to_use)
    
    print(f"[WORKER] Processing Job {job_id}", flush=True)
    
    try:
        # 1. Fetch Job Details
        job_res = supabase.table("job_run").select("*").eq("job_id", job_id).single().execute()
        if not job_res.data:
            raise Exception(f"Job Run {job_id} not found")
        job_run = job_res.data
        project_id = job_run["project_id"]
        
        # Update status to Running
        supabase.table("job_run").update({"status": "running", "started_at": "now()"}).eq("job_id", job_id).execute()
        supabase.table("solutions").update({"status": "PROCESSING"}).eq("id", project_id).execute()
        
        # 2. Get Storage Path
        sol_res = supabase.table("solutions").select("storage_path").eq("id", project_id).single().execute()
        if not sol_res.data:
             raise Exception(f"Solution {project_id} not found")
             
        file_path = sol_res.data["storage_path"].strip()
        
        # 3. Execute Pipeline
        print(f"[WORKER] Starting Pipeline for {file_path}...", flush=True)
        
        # Instantiate orchestrator with supabase client
        orchestrator = PipelineOrchestrator(supabase)
        
        # Execute pipeline validation (sync method blocked the async loop, causing issues with internal asyncio.run calls)
        # Fix: Run in a separate thread so it has its own event loop context if needed, or at least doesn't conflict.
        loop = asyncio.get_running_loop()
        success = await loop.run_in_executor(None, orchestrator.execute_pipeline, job_id, file_path)
        
        if success:
            # Check current status to ensure we don't overwrite 'planning_ready'
            job_check = supabase.table("job_run").select("status").eq("job_id", job_id).single().execute()
            current_status = job_check.data["status"]
            
            if current_status == "planning_ready":
                print(f"[WORKER] Job {job_id} paused for planning approval.", flush=True)
                # We complete the queue item because this 'run' is done. 
                # The approval process must re-enqueue the job.
                queue.complete_job(job_queue_item["id"])
            else:
                # Complete Job
                supabase.table("job_run").update({
                    "status": "completed", 
                    "finished_at": "now()", 
                    "progress_pct": 100
                }).eq("job_id", job_id).execute()
                
                queue.complete_job(job_queue_item["id"])
                
                # Update solution status
                supabase.table("solutions").update({"status": "READY"}).eq("id", project_id).execute()
                print(f"[WORKER] Job {job_id} Completed Successfully", flush=True)
            
        else:
            raise Exception("Pipeline execution failed (check logs)")
        
    except Exception as e:
        error_msg = str(e)
        detailed_error = traceback.format_exc()
        print(f"\n[WORKER] !!! CRITICAL FAILURE IN JOB {job_id} !!!", flush=True)
        print(f"[WORKER] Error: {error_msg}", flush=True)
        print(detailed_error, flush=True)
        
        # 4. Defensive Check: Has the orchestrator already logged a better error?
        try:
            current_job = supabase.table("job_run").select("error_message, error_details").eq("job_id", job_id).single().execute()
            if current_job.data:
                db_msg = current_job.data.get("error_message")
                db_dtl = current_job.data.get("error_details")
                # If DB already has a specific error (not just 'Pipeline execution failed'), use it
                if db_msg and "Pipeline execution failed" not in db_msg:
                    error_msg = db_msg
                    if db_dtl: detailed_error = db_dtl
        except:
            pass

        # Log error with full details
        supabase.table("job_run").update({
            "status": "failed", 
            "error_message": error_msg,
            "error_details": detailed_error,
            "finished_at": "now()"
        }).eq("job_id", job_id).execute()
        
        supabase.table("solutions").update({"status": "ERROR"}).eq("id", project_id).execute()
        queue.fail_job(job_queue_item["id"], error_msg)

async def worker_loop():
    queue = SQLJobQueue()
    print("[WORKER] Started polling (New Pipeline Enabled)...", flush=True)
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