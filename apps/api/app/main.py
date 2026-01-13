import os
import traceback
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .tasks import analyze_solution_task
from pydantic import BaseModel
from .routers import planning, solutions, admin, governance

load_dotenv()

app = FastAPI(title="Nexus Discovery API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(planning.router)
app.include_router(solutions.router)
app.include_router(admin.router)
app.include_router(governance.router)

class JobRequest(BaseModel):
    solution_id: str
    file_path: str

@app.get("/")
def read_root():
    return {"message": "Nexus Discovery API is running (No Docker Mode)"}

@app.get("/health")
def health_check():
    return {"status": "ok", "file": __file__}

@app.post("/jobs")
def create_job(job: JobRequest):
    from .services.queue import SQLJobQueue
    from supabase import create_client
    from .config import settings
    
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    # 1. Create Job Run Record
    job_data = {
        "project_id": job.solution_id,
        "status": "queued",
        "current_stage": "ingest",
        "requires_approval": True
    }
    # Use job.solution_id as job_id for now? 
    # MD says job_id is UUID. solution_id is UUID.
    # But job_run.project_id is solution_id. job_run.job_id is new.
    # The frontend expects job_id. If I return a new UUID, frontend might get confused if it expects solution_id.
    # Existing code returned {"job_id": job.solution_id}.
    # I should check frontend code.
    # But sticking to requirements: "response: { job_id: ... }"
    
    # Insert into job_run
    res = supabase.table("job_run").insert(job_data).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create job record")
        
    new_job_id = res.data[0]["job_id"]
    
    # Update Solution Status to QUEUED
    supabase.table("solutions").update({"status": "QUEUED"}).eq("id", job.solution_id).execute()
    
    # 2. Enqueue
    queue = SQLJobQueue()
    queue.enqueue_job(new_job_id)
    
    # We also need to store the file_path somewhere so the worker knows what to process.
    # The `job_run` table has `artifact_id`. 
    # But `JobRequest` has `file_path`.
    # I should probably store `file_path` in `job_run` or look it up from `solutions` (if it's there).
    # The `solutions` table has `storage_path`.
    # The worker can look up `solutions` using `project_id` (which is solution_id).
    
    return {"job_id": new_job_id, "status": "queued"}

@app.get("/solutions/{solution_id}/graph")
def get_solution_graph(solution_id: str, mode: str = "GLOBAL", package_id: str = None):
    from .services.graph import get_graph_service
    # For now we return the whole graph as we are not filtering by subgraph yet in Neo4j service
    graph_service = get_graph_service()
    data = graph_service.get_graph_data(solution_id, mode=mode, package_id=package_id)
    return data

class ChatRequest(BaseModel):
    question: str

@app.post("/solutions/{solution_id}/chat")
def chat_solution(solution_id: str, request: ChatRequest):
    from .services.graph import get_graph_service
    from .services.llm import LLMService
    
    # 1. Fetch Graph Context
    graph_service = get_graph_service()
    graph_data = graph_service.get_graph_data(solution_id)
    
    # 2. Ask LLM
    llm_service = LLMService()
    answer = llm_service.chat_with_graph(graph_data, request.question)
    
    return {"answer": answer}

@app.post("/solutions/{solution_id}/optimize")
async def optimize_solution(solution_id: str):
    """
    AI-driven gap analysis and prompt refinement.
    Moved to main.py to ensure correct route priority.
    """
    from .services.auditor import DiscoveryAuditor
    from .services.refiner import DiscoveryRefiner
    from .actions import ActionRunner
    from .routers.solutions import get_supabase
    
    supabase = get_supabase()
    auditor = DiscoveryAuditor(supabase)
    runner = ActionRunner()
    refiner = DiscoveryRefiner(auditor, runner)
    
    # 1. Generate Recommendations
    print(f"[API] Running AI Optimization for solution {solution_id}...", flush=True)
    report = refiner.generate_recommendations(solution_id)
    
    # 2. Save snapshot (fetch latest job_id to avoid UUID type mismatch)
    job_res = supabase.table("job_run").select("job_id").eq("project_id", solution_id).order("created_at", desc=True).limit(1).execute()
    latest_job_id = job_res.data[0]["job_id"] if job_res.data else None
    
    snapshot_id = auditor.save_snapshot(latest_job_id, report["audit"])
    
    return {
        "status": "success",
        "snapshot_id": snapshot_id,
        "recommendations": report.get("ai_suggestions", []),
        "patch": report.get("suggested_solution_layer", ""),
        "next_action": report.get("next_best_action", "")
    }

@app.options("/solutions/{solution_id}/chat")
async def chat_solution_options(solution_id: str):
    return {}

@app.delete("/solutions/{solution_id}")
def delete_solution(solution_id: str):
    from .services.reset_service import NuclearResetService
    from .services.graph import get_graph_service
    from supabase import create_client
    from .config import settings
    
    key_to_use = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
    supabase = create_client(settings.SUPABASE_URL, key_to_use)
    reset_service = NuclearResetService(supabase)
    
    try:
        # 1. Nuclear Reset (Brain, Sandbox, Lineage)
        reset_service.reset_solution_data(solution_id)
        
        # 2. Neo4j cleanup
        try:
            graph_service = get_graph_service()
            graph_service.delete_solution_nodes(solution_id)
        except Exception as graph_e:
            print(f"Failed to delete graph nodes: {graph_e}")

        # 3. Final removal from 'solutions' table
        res = supabase.from_("solutions").delete().eq("id", solution_id).execute()
        
        return {"status": "deleted", "id": solution_id}
    except Exception as e:
        print(f"Delete Exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        # Return success even if failed, to allow UI to update? No, better return 500 so user knows.
        # But if it's partial failure (e.g. Neo4j down), we might want to return 200 with warning.
        raise HTTPException(status_code=500, detail=str(e))

class ReanalyzeRequest(BaseModel):
    mode: str = "update" # update | full

@app.post("/solutions/{solution_id}/analyze")
async def reanalyze_solution(solution_id: str, request: ReanalyzeRequest = ReanalyzeRequest(mode="update")):
    from .services.queue import SQLJobQueue
    from supabase import create_client
    from .config import settings
    
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    # Check if full cleanup requested
    if request.mode == "full":
        try:
            print(f"Cleaning previous data for solution {solution_id} (Full Reprocess)...", flush=True)
            
            # 1. Fetch all job_ids for this project to clean logs and plans
            jobs_res = supabase.table("job_run").select("job_id").eq("project_id", solution_id).execute()
            job_ids = [j["job_id"] for j in jobs_res.data]
            
            if job_ids:
                # Cleanup logs and plans
                supabase.table("file_processing_log").delete().in_("job_id", job_ids).execute()
                
                # Fetch plan_ids
                plans_res = supabase.table("job_plan").select("plan_id").in_("job_id", job_ids).execute()
                plan_ids = [p["plan_id"] for p in plans_res.data]
                
                if plan_ids:
                    # Cleanup Items -> Areas -> Plans
                    # CRITICAL: Nullify plan_id in job_run first to avoid FK violation
                    supabase.table("job_run").update({"plan_id": None}).in_("plan_id", plan_ids).execute()
                    
                    supabase.table("job_plan_item").delete().in_("plan_id", plan_ids).execute()
                    supabase.table("job_plan_area").delete().in_("plan_id", plan_ids).execute()
                    supabase.table("job_plan").delete().in_("plan_id", plan_ids).execute()

            # 2. Cleanup Catalog Data (Manual Cascade for Packages)
            supabase.table("column_lineage").delete().eq("project_id", solution_id).execute()
            supabase.table("transformation_ir").delete().eq("project_id", solution_id).execute()
            
            # Fetch package_ids to delete components
            pkg_res = supabase.table("package").select("package_id").eq("project_id", solution_id).execute()
            pkg_ids = [p["package_id"] for p in pkg_res.data]
            if pkg_ids:
                supabase.table("package_component").delete().in_("package_id", pkg_ids).execute()
            
            supabase.table("package").delete().eq("project_id", solution_id).execute()
            
            supabase.table("edge_index").delete().eq("project_id", solution_id).execute()
            supabase.table("asset").delete().eq("project_id", solution_id).execute()
            supabase.table("evidence").delete().eq("project_id", solution_id).execute()
            
            # 3. Cleanup Job Runs
            supabase.table("job_run").delete().eq("project_id", solution_id).execute()
            
            # 4. Cleanup Neo4j
            try:
                from .services.graph import get_graph_service
                graph_svc = get_graph_service()
                graph_svc.delete_solution_nodes(solution_id)
            except Exception as graph_e:
                print(f"Neo4j Cleanup Warning: {graph_e}")

        except Exception as e:
            print(f"Warning during cleanup: {e}")
            traceback.print_exc()

    # Fetch solution to get file_path
    try:
        response = supabase.from_("solutions").select("storage_path").eq("id", solution_id).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Solution not found")
            
        # Create Job Run
        job_data = {
            "project_id": solution_id,
            "status": "queued",
            "current_stage": "ingest",
            "requires_approval": False
        }
        res = supabase.table("job_run").insert(job_data).execute()
        new_job_id = res.data[0]["job_id"]
        
        # Update Solution Status to PROCESSING
        supabase.table("solutions").update({"status": "PROCESSING"}).eq("id", solution_id).execute()
        
        # Enqueue
        queue = SQLJobQueue()
        queue.enqueue_job(new_job_id)
        
        return {"status": "queued", "job_id": new_job_id, "mode": request.mode}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/solutions/{solution_id}/cancel")
async def cancel_solution_job(solution_id: str):
    from .routers.solutions import get_supabase
    supabase = get_supabase()
    
    # 1. Fetch active job
    job_res = supabase.table("job_run")\
        .select("job_id, status")\
        .eq("project_id", solution_id)\
        .in_("status", ["running", "queued"])\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()
        
    if not job_res.data:
         # Check if it's PLANNING READY (which is technically pause, but user might want to stop it)
         job_res_p = supabase.table("job_run")\
            .select("job_id, status")\
            .eq("project_id", solution_id)\
            .eq("status", "planning_ready")\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
            
         if not job_res_p.data:
            return {"status": "no_active_job"}
         job_id = job_res_p.data[0]["job_id"]
    else:
        job_id = job_res.data[0]["job_id"]
    
    print(f"[API] Cancelling job {job_id} for solution {solution_id}...")
    
    # 2. Update status to 'cancelled'
    supabase.table("job_run").update({"status": "cancelled", "finished_at": "now()"}).eq("job_id", job_id).execute()
    
    # 3. Update solution status back to READY
    supabase.table("solutions").update({"status": "READY"}).eq("id", solution_id).execute()
    
    # 4. Update queue if exists
    supabase.table("job_queue").update({"status": "failed", "last_error": "User Cancelled"}).eq("job_id", job_id).execute()
    
    return {"status": "cancelled", "job_id": job_id}

class SubgraphRequest(BaseModel):
    center_id: str
    depth: int = 1
    limit: int = 100

class PathRequest(BaseModel):
    from_id: str
    to_id: str
    max_hops: int = 5

@app.post("/graph/subgraph")
async def get_subgraph(req: SubgraphRequest):
    from .services.graph import get_graph_service
    graph = get_graph_service()
    return graph.get_subgraph(req.center_id, req.depth, req.limit)

@app.post("/graph/path")
async def find_paths(req: PathRequest):
    from .services.graph import get_graph_service
    graph = get_graph_service()
    return graph.find_paths(req.from_id, req.to_id, req.max_hops)

# Admin endpoints moved to routers/admin.py

@app.get("/solutions/{solution_id}/stats")
async def get_solution_stats(solution_id: str):
    from supabase import create_client
    from .config import settings
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    # Total Assets
    assets_count = supabase.table("asset").select("asset_id", count="exact").eq("project_id", solution_id).execute()
    
    # Assets by Type
    # Supabase doesn't support GROUP BY easily in simple client, use RPC or just raw fetch (inefficient for large data but ok for MVP)
    # Or multiple queries.
    
    # Let's count common types explicitly
    files_count = supabase.table("asset").select("asset_id", count="exact").eq("project_id", solution_id).eq("asset_type", "FILE").execute()
    tables_count = supabase.table("asset").select("asset_id", count="exact").eq("project_id", solution_id).eq("asset_type", "TABLE").execute()
    pipelines_count = supabase.table("asset").select("asset_id", count="exact").eq("project_id", solution_id).eq("asset_type", "PIPELINE").execute()
    
    # Total Edges (Relationships)
    edges_count = supabase.table("edge_index").select("edge_id", count="exact").eq("project_id", solution_id).execute()
    
    # Active Job Status (New)
    job_status = None
    # Check if there is a running or queued job
    # Ensure we are selecting 'job_id' explicitly as 'id' is not in the schema for job_run
    job_res = supabase.table("job_run")\
        .select("job_id, plan_id, status, progress_pct, error_details, created_at, current_stage")\
        .eq("project_id", solution_id)\
        .in_("status", ["queued", "running", "planning_ready"])\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()
        
    if job_res.data:
        job_status = job_res.data[0]
    else:
        # Check for completed jobs to ensure we don't miss status if just finished?
        # No, active job implies currently running/queued. 
        # But if we want to show "Planning Ready" even if it's not strictly "running" (it's paused),
        # we need to ensure 'planning_ready' is included (which I did).
        pass
    
    # DEBUG: Print status for troubleshooting
    if job_status:
        print(f"DEBUG: Active Job for {solution_id}: {job_status['status']} (Plan: {job_status.get('plan_id')})")
    else:
        print(f"DEBUG: No active job for {solution_id}")

    # Last Completed Job
    last_run = None
    last_run_res = supabase.table("job_run")\
        .select("finished_at")\
        .eq("project_id", solution_id)\
        .eq("status", "completed")\
        .order("finished_at", desc=True)\
        .limit(1)\
        .execute()
    
    if last_run_res.data:
        last_run = last_run_res.data[0]["finished_at"]

    # Latest Audit Report (v5.0 Integration)
    audit_report = None
    audit_res = supabase.table("audit_snapshot")\
        .select("*")\
        .eq("project_id", solution_id)\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()
    
    if audit_res.data:
        audit_report = audit_res.data[0]

    return {
        "total_assets": assets_count.count,
        "total_edges": edges_count.count,
        "files": files_count.count,
        "tables": tables_count.count,
        "pipelines": pipelines_count.count,
        "active_job": job_status,
        "last_run": last_run,
        "audit_report": audit_report,
        "metrics": audit_report["metrics"] if audit_report else None
    }

@app.get("/solutions/{solution_id}/assets")
async def get_solution_assets(
    solution_id: str, 
    type: str = None, 
    search: str = None, 
    limit: int = 50, 
    offset: int = 0
):
    from supabase import create_client
    from .config import settings
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    query = supabase.table("asset").select("*", count="exact").eq("project_id", solution_id)
    
    if type and type != "ALL":
        # Use ilike for case-insensitive exact match
        query = query.ilike("asset_type", type)
        
    if search:
        query = query.ilike("name_display", f"%{search}%")
        
    query = query.range(offset, offset + limit - 1).order("name_display")
        
    res = query.execute()
    return {"data": res.data, "count": res.count}

@app.get("/solutions/{solution_id}/asset-types")
async def get_solution_asset_types(solution_id: str):
    from supabase import create_client
    from .config import settings
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    # Fetch distinct asset types
    # Since Supabase simple client doesn't support distinct well without RPC, 
    # we fetch all types (selecting only asset_type) and do unique in memory 
    # as types are few per solution.
    res = supabase.table("asset").select("asset_type").eq("project_id", solution_id).execute()
    
    if not res.data:
        return {"types": []}
        
    types = sorted(list(set(item["asset_type"] for item in res.data if item.get("asset_type"))))
    return {"types": types}

@app.get("/assets/{asset_id}/details")
async def get_asset_details(asset_id: str):
    from supabase import create_client
    from .config import settings
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    # 1. Fetch Asset
    asset_res = supabase.table("asset").select("*").eq("asset_id", asset_id).single().execute()
    if not asset_res.data:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    asset = asset_res.data
    
    # 2. Fetch Relationships (Incoming and Outgoing)
    # Outgoing: from_asset_id = asset_id
    outgoing = supabase.table("edge_index")\
        .select("edge_id, edge_type, confidence, is_hypothesis, to_asset:to_asset_id(asset_id, name_display, asset_type)")\
        .eq("from_asset_id", asset_id)\
        .execute()
        
    # Incoming: to_asset_id = asset_id
    incoming = supabase.table("edge_index")\
        .select("edge_id, edge_type, confidence, is_hypothesis, from_asset:from_asset_id(asset_id, name_display, asset_type)")\
        .eq("to_asset_id", asset_id)\
        .execute()
        
    # 3. Fetch Evidences for this asset (via evidence table directly? or via edges?)
    # Evidence is linked to edges or artifact.
    # But an asset might have evidences directly if we linked them. 
    # Currently `evidence` table has `file_path` but no direct link to `asset_id` unless we infer from name or locator.
    # However, we can fetch evidences for the edges found above.
    
    # Let's collect all edge_ids
    edge_ids = [e["edge_id"] for e in (outgoing.data or [])] + [e["edge_id"] for e in (incoming.data or [])]
    
    evidences = []
    if edge_ids:
        # Fetch edge evidences
        ev_res = supabase.table("edge_evidence")\
            .select("edge_id, evidence:evidence_id(*)")\
            .in_("edge_id", edge_ids)\
            .execute()
        
        # Structure evidences by edge_id
        evidences = ev_res.data
        
    return {
        "asset": asset,
        "outgoing_edges": outgoing.data,
        "incoming_edges": incoming.data,
        "evidences": evidences
    }