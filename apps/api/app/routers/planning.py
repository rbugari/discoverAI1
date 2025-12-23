from fastapi import APIRouter, HTTPException, Depends
from supabase import Client, create_client
from ..config import settings
from ..services.planner import PlannerService
from ..models.planning import (
    JobPlan, JobPlanStatus, CreatePlanRequest, UpdatePlanItemRequest
)
from ..services.queue import SQLJobQueue

router = APIRouter()

def get_supabase() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

@router.post("/solutions/{solution_id}/plans")
async def create_plan(solution_id: str, request: CreatePlanRequest, supabase: Client = Depends(get_supabase)):
    """
    Triggers the creation of a new plan for the given solution/job.
    """
    # 1. Verify Job/Solution
    # Assuming request.job_id is passed, or we infer the latest job.
    # The spec says "Crea plan para la última carga".
    
    # Check if job exists
    job_res = supabase.table("job_run").select("*").eq("job_id", request.job_id).single().execute()
    if not job_res.data:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Get file path from solution
    sol_res = supabase.table("solutions").select("storage_path").eq("id", solution_id).single().execute()
    if not sol_res.data:
        raise HTTPException(status_code=404, detail="Solution not found")
        
    file_path = sol_res.data["storage_path"]
    
    planner = PlannerService(supabase)
    try:
        plan_id = planner.create_plan(request.job_id, file_path, request.mode)
        return {"plan_id": plan_id, "status": "planning_ready"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plans/{plan_id}")
async def get_plan(plan_id: str, supabase: Client = Depends(get_supabase)):
    """
    Returns the full plan hierarchy.
    """
    # Fetch Plan
    plan_res = supabase.table("job_plan").select("*").eq("plan_id", plan_id).single().execute()
    if not plan_res.data:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    plan = plan_res.data
    
    # Fetch Areas
    areas_res = supabase.table("job_plan_area").select("*").eq("plan_id", plan_id).order("order_index").execute()
    areas = areas_res.data
    
    # Fetch Items
    # Optimization: Fetch all items for the plan and map in memory
    items_res = supabase.table("job_plan_item").select("*").eq("plan_id", plan_id).order("order_index").execute()
    items = items_res.data
    
    # Build Hierarchy
    area_map = {a["area_id"]: {**a, "items": []} for a in areas}
    
    for item in items:
        if item["area_id"] in area_map:
            area_map[item["area_id"]]["items"].append(item)
            
    plan["areas"] = list(area_map.values())
    
    return plan

@router.patch("/plans/{plan_id}/items/{item_id}")
async def update_plan_item(plan_id: str, item_id: str, update: UpdatePlanItemRequest, supabase: Client = Depends(get_supabase)):
    """
    Update item status (enabled/disabled), order, or area.
    """
    data = {}
    if update.enabled is not None:
        data["enabled"] = update.enabled
    if update.order_index is not None:
        data["order_index"] = update.order_index
    if update.area_id is not None:
        data["area_id"] = update.area_id
        
    if not data:
        return {"status": "no_change"}
        
    res = supabase.table("job_plan_item").update(data).eq("item_id", item_id).execute()
    return res.data

@router.post("/plans/{plan_id}/approve")
async def approve_plan(plan_id: str, supabase: Client = Depends(get_supabase)):
    """
    Approves the plan and triggers execution.
    """
    # 1. Update Plan Status
    res = supabase.table("job_plan").update({"status": JobPlanStatus.APPROVED}).eq("plan_id", plan_id).execute()
    
    # 2. Update Job Status to 'queued' (or 'ready_to_run' if worker picks it up)
    # Get Job ID
    plan_res = supabase.table("job_plan").select("job_id").eq("plan_id", plan_id).single().execute()
    job_id = plan_res.data["job_id"]
    
    # Update Job
    supabase.table("job_run").update({
        "status": "queued", 
        "requires_approval": False # Flag handled
    }).eq("job_id", job_id).execute()
    
    # 3. Enqueue for Worker
    queue = SQLJobQueue()
    queue.enqueue_job(job_id)
    
    return {"status": "approved", "job_id": job_id}
@router.get("/solutions/{solution_id}/active-plan")
async def get_active_plan(solution_id: str, supabase: Client = Depends(get_supabase)):
    """
    Optimized endpoint that returns the active job and its full plan in one call.
    """
    # 1. Fetch Active Job
    job_res = supabase.table("job_run")\
        .select("job_id, plan_id, status, progress_pct, current_stage")\
        .eq("project_id", solution_id)\
        .in_("status", ["queued", "running", "planning_ready"])\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()
    
    if not job_res.data:
        return {"job": None, "plan": None}
    
    job = job_res.data[0]
    plan_id = job.get("plan_id")
    
    if not plan_id:
        return {"job": job, "plan": None}
    
    # 2. Fetch Plan, Areas, and Items in Parallel (as much as supabase-client allows)
    # Actually we just fetch them sequentially but it's much faster than separate HTTP calls from frontend
    plan_res = supabase.table("job_plan").select("*").eq("plan_id", plan_id).single().execute()
    areas_res = supabase.table("job_plan_area").select("*").eq("plan_id", plan_id).order("order_index").execute()
    items_res = supabase.table("job_plan_item").select("*").eq("plan_id", plan_id).order("order_index").execute()
    
    plan_data = plan_res.data
    areas = areas_res.data
    items = items_res.data
    
    # Build Hierarchy
    area_map = {a["area_id"]: {**a, "items": []} for a in areas}
    for item in items:
        if item["area_id"] in area_map:
            area_map[item["area_id"]]["items"].append(item)
            
    plan_data["areas"] = list(area_map.values())
    
    return {
        "job": job,
        "plan": plan_data
    }
