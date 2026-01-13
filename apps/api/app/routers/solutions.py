from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from supabase import create_client, Client
from ..config import settings
from ..services.report_service import ReportService
from ..services.catalog import CatalogService
from ..services.reset_service import NuclearResetService
from ..services.queue import SQLJobQueue

router = APIRouter(prefix="/solutions", tags=["solutions"])

def get_supabase():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def _clear_stuck_jobs(supabase: Client, solution_id: str):
    """Marks any 'queued', 'running', or 'planning_ready' jobs as 'failed' for this solution."""
    supabase.table("job_run")\
        .update({"status": "failed", "error_message": "Job cancelled by new request (Clean/Analyze)"})\
        .eq("project_id", solution_id)\
        .in_("status", ["queued", "running", "planning_ready"])\
        .execute()

@router.get("")
def list_solutions(supabase: Client = Depends(get_supabase)):
    """Returns a list of all projects/solutions."""
    res = supabase.table("solutions").select("id, name").execute()
    return res.data

@router.get("/{solution_id}")
def get_solution(solution_id: str, supabase: Client = Depends(get_supabase)):
    """Fetches details for a single solution."""
    res = supabase.table("solutions").select("*").eq("id", solution_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Solution not found")
    return res.data

@router.get("/{solution_id}/report/pdf")
async def get_solution_report_pdf(solution_id: str, supabase: Client = Depends(get_supabase)):
    report_service = ReportService(supabase)
    try:
        data = await report_service.get_solution_summary(solution_id)
        buffer = report_service.generate_pdf_buffer(data)
        
        # En una versión real usaríamos StreamingResponse con media_type="application/pdf"
        from fastapi.responses import Response
        return Response(content=buffer, media_type="application/pdf", headers={
            "Content-Disposition": f"attachment; filename=report_{solution_id}.pdf"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{solution_id}/integrations/status")
def get_integrations_status(solution_id: str, supabase: Client = Depends(get_supabase)):
    # Placeholder para el GovernanceService
    return {
        "dbt": {"status": "not_configured"},
        "unity_catalog": {"status": "not_configured"},
        "purview": {"status": "not_configured"}
    }

@router.get("/{solution_id}/audit/history")
def get_audit_history(solution_id: str, supabase: Client = Depends(get_supabase)):
    res = supabase.table("audit_snapshot")\
        .select("*")\
        .eq("project_id", solution_id)\
        .order("created_at", desc=True)\
        .limit(10)\
        .execute()
    
    
    return res.data or []

@router.post("/{solution_id}/process")
def process_solution(solution_id: str, full_reset: bool = False, supabase: Client = Depends(get_supabase)):
    """
    Unified entry point for solution discovery.
    - if full_reset=True: Performs a complete wipe before starting.
    - if full_reset=False: Performs a smart/incremental update.
    """
    queue = SQLJobQueue()
    _clear_stuck_jobs(supabase, solution_id)

    if full_reset:
        print(f"[API] Performing FULL RESET for solution {solution_id}", flush=True)
        reset_service = NuclearResetService(supabase)
        reset_service.reset_solution_data(solution_id)
    
    # Ensure status is PROCESSING
    supabase.table("solutions").update({"status": "PROCESSING"}).eq("id", solution_id).execute()

    job_data = {
        "project_id": solution_id,
        "status": "queued",
        "current_stage": "ingest",
        "requires_approval": True 
    }
    
    try:
        res = supabase.table("job_run").insert(job_data).execute()
        new_job_id = res.data[0]["job_id"]
        queue.enqueue_job(new_job_id)
        return {
            "status": "queued", 
            "job_id": new_job_id, 
            "mode": "full" if full_reset else "incremental"
        }
    except Exception as e:
        # Revert status if queueing fails
        supabase.table("solutions").update({"status": "ERROR"}).eq("id", solution_id).execute()
        raise HTTPException(status_code=500, detail=f"Failed to queue job: {str(e)}")

@router.post("/{solution_id}/reprocess")
def reprocess_solution_legacy(solution_id: str, supabase: Client = Depends(get_supabase)):
    """Legacy endpoint, redirected to /process (full)."""
    return process_solution(solution_id, full_reset=True, supabase=supabase)

@router.post("/{solution_id}/clean")
def clean_solution(solution_id: str, supabase: Client = Depends(get_supabase)):
    """Wipes existing discovery data and leaves the solution blank."""
    reset_service = NuclearResetService(supabase)
    
    # 0. Clear stuck jobs
    _clear_stuck_jobs(supabase, solution_id)

    success = reset_service.reset_solution_data(solution_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clean solution data")
        

        
    return {"status": "success", "message": "Solution data wiped successfully"}

@router.post("/{solution_id}/analyze")
def analyze_solution_legacy(solution_id: str, supabase: Client = Depends(get_supabase)):
    """Legacy endpoint, redirected to /process (incremental)."""
    return process_solution(solution_id, full_reset=False, supabase=supabase)

@router.get("/jobs/{job_id}/logs")
def get_job_logs(job_id: str, supabase: Client = Depends(get_supabase)):
    """Fetches high-level processing logs for the UI terminal."""
    try:
        # Fetch using the actual DB column names
        res = supabase.table("file_processing_log")\
            .select("created_at, action_name, file_path, strategy_used, status, model_used")\
            .eq("job_id", job_id)\
            .order("created_at", desc=False)\
            .execute()
        
        logs = []
        for row in res.data or []:
            # Map DB columns to Frontend Interface
            logs.append({
                "created_at": row.get("created_at"),
                "action_taken": row.get("action_name"),  # Map action_name -> action_taken
                "file_path": row.get("file_path"),
                "strategy_used": row.get("strategy_used"),
                "success": row.get("status") == "success", # Map status -> success boolean
                "model_used": row.get("model_used")
            })
            
        return logs
    except Exception as e:
        print(f"[ERROR] Failed to fetch logs for {job_id}: {e}", flush=True)
        return []
from ..services.lineage_service import LineageService

# ... (existing imports/setup)

@router.get("/{solution_id}/lineage/trace")
def trace_column(
    solution_id: str, 
    asset_id: str, 
    column_name: str, 
    max_depth: int = 5, 
    supabase: Client = Depends(get_supabase)
):
    service = LineageService(supabase)
    return service.trace_column_upstream(solution_id, asset_id, column_name, max_depth)
