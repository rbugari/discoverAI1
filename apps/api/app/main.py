from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .tasks import analyze_solution_task
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Nexus Discovery API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobRequest(BaseModel):
    solution_id: str
    file_path: str

@app.get("/")
def read_root():
    return {"message": "Nexus Discovery API is running (No Docker Mode)"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/jobs")
async def create_job(job: JobRequest, background_tasks: BackgroundTasks):
    # In a real app, we would insert into DB here (Supabase).
    # For MVP, we trigger the background task directly.
    background_tasks.add_task(analyze_solution_task, job.solution_id, job.file_path)
    return {"job_id": job.solution_id, "status": "queued"}

@app.get("/solutions/{solution_id}/graph")
def get_solution_graph(solution_id: str):
    from .services.graph import get_graph_service
    # For now we return the whole graph as we are not filtering by subgraph yet in Neo4j service
    graph_service = get_graph_service()
    data = graph_service.get_graph_data(solution_id)
    return data

class ChatRequest(BaseModel):
    question: str

@app.post("/solutions/{solution_id}/chat")
async def chat_solution(solution_id: str, request: ChatRequest):
    from .services.graph import get_graph_service
    from .services.llm import LLMService
    
    # 1. Fetch Graph Context
    graph_service = get_graph_service()
    graph_data = graph_service.get_graph_data(solution_id)
    
    # 2. Ask LLM
    llm_service = LLMService()
    answer = llm_service.chat_with_graph(graph_data, request.question)
    
    return {"answer": answer}

@app.options("/solutions/{solution_id}/chat")
async def chat_solution_options(solution_id: str):
    return {}

@app.delete("/solutions/{solution_id}")
async def delete_solution(solution_id: str):
    from supabase import create_client
    from .config import settings
    from .services.graph import get_graph_service
    
    # Use Service Role Key if available to bypass RLS, otherwise fallback to Anon Key
    key_to_use = settings.SUPABASE_SERVICE_ROLE_KEY if settings.SUPABASE_SERVICE_ROLE_KEY else settings.SUPABASE_KEY
    supabase = create_client(settings.SUPABASE_URL, key_to_use)
    
    try:
        # Delete from Supabase
        print(f"Attempting to delete solution {solution_id} from Supabase...")
        res = supabase.from_("solutions").delete().eq("id", solution_id).execute()
        print(f"Supabase Delete Result: {res}")
        
        # Check if anything was actually deleted
        if not res.data:
            print(f"WARNING: Solution {solution_id} was NOT deleted (RLS or ID not found).")
            # We might want to return 404 or 403 here, but for now let's just log it.
        
        # Delete from Neo4j
        try:
            graph_service = get_graph_service()
            graph_service.delete_solution_nodes(solution_id)
        except Exception as graph_e:
            print(f"Failed to delete graph nodes: {graph_e}")
        
        # Optionally: Delete from Storage
        
        return {"status": "deleted", "id": solution_id, "details": res.data}
    except Exception as e:
        print(f"Delete Exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/solutions/{solution_id}/analyze")
async def reanalyze_solution(solution_id: str, background_tasks: BackgroundTasks):
    from supabase import create_client
    from .config import settings
    
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    # Fetch solution to get file_path
    try:
        response = supabase.from_("solutions").select("storage_path").eq("id", solution_id).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Solution not found")
            
        file_path = response.data["storage_path"]
        
        # Trigger task
        background_tasks.add_task(analyze_solution_task, solution_id, file_path)
        return {"status": "queued", "id": solution_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))