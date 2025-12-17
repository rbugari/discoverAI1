import asyncio
import time
import traceback
from .services.queue import SQLJobQueue
from .services.storage import StorageService
from .services.extractors.registry import ExtractorRegistry
from .services.catalog import CatalogService
from .config import settings
from supabase import create_client

async def process_job(job_queue_item):
    job_id = job_queue_item["job_id"]
    queue = SQLJobQueue()
    
    # Use Service Role Key for robust operations
    key_to_use = settings.SUPABASE_SERVICE_ROLE_KEY if settings.SUPABASE_SERVICE_ROLE_KEY else settings.SUPABASE_KEY
    supabase = create_client(settings.SUPABASE_URL, key_to_use)
    
    print(f"[WORKER] Processing Job {job_id}")
    
    try:
        # 1. Fetch Job Details
        job_res = supabase.table("job_run").select("*").eq("job_id", job_id).single().execute()
        if not job_res.data:
            raise Exception(f"Job Run {job_id} not found")
        job_run = job_res.data
        project_id = job_run["project_id"]
        
        # Update Status to Running
        supabase.table("job_run").update({"status": "running", "started_at": "now()"}).eq("job_id", job_id).execute()
        
        # Update Solution Status to PROCESSING
        supabase.table("solutions").update({"status": "PROCESSING"}).eq("id", project_id).execute()
        
        # 2. Get File Path from Solutions (Legacy) or Job Run
        # Assuming project_id is solution_id
        sol_res = supabase.table("solutions").select("storage_path").eq("id", project_id).single().execute()
        if not sol_res.data:
             raise Exception(f"Solution {project_id} not found")
             
        file_path = sol_res.data["storage_path"]
        
        # 3. Pipeline
        # Init Services
        storage = StorageService()
        registry = ExtractorRegistry()
        catalog = CatalogService(supabase)
        
        # Unpack
        extract_dir = ""
        print(f"[WORKER] Extracting {file_path}...")
        if file_path.startswith("http"):
            extract_dir = storage.clone_repo(file_path)
        else:
            extract_dir = storage.download_and_extract(file_path)
            
        # Walk
        files = list(storage.walk_files(extract_dir))
        
        # Filter relevant files upfront for accurate counting
        relevant_extensions = ['.sql', '.py', '.xml', '.dtsx', '.json', '.md']
        files_to_process = [f for f in files if f[2] in relevant_extensions]
        
        total_files = len(files_to_process)
        processed_files = 0
        
        print(f"[WORKER] Found {len(files)} total files. {total_files} relevant to process.")
        
        # Initial Progress Update
        supabase.table("job_run").update({
            "status": "running", 
            "progress_pct": 0,
            "error_details": {"total_files": total_files, "processed_files": 0, "current_file": "Starting..."}
        }).eq("job_id", job_id).execute()
        
        for fpath, content, ext in files_to_process:
            filename = fpath.split('/')[-1] if '/' in fpath else fpath.split('\\')[-1]
            
            # Update Current File Status (Throttle: every file or every 5? Let's do every file for real-time feel if not too fast)
            # Storing extra details in error_details JSONB for now to avoid schema migration, 
            # or we could assume the frontend reads progress_pct.
            # Ideally we'd add columns to job_run, but JSONB is flexible.
            supabase.table("job_run").update({
                 "error_details": {
                     "total_files": total_files, 
                     "processed_files": processed_files, 
                     "current_file": filename
                 }
            }).eq("job_id", job_id).execute()

            # Extract
            try:
                result = registry.extract(fpath, content)
                
                # Write to SQL Catalog
                node_id_map = catalog.sync_extraction_result(result, project_id)
                
                # Write to Neo4j
                from .services.graph import get_graph_service
                graph = get_graph_service()
                
                # 1. Upsert Nodes
                for node in result.nodes:
                    asset_id = node_id_map.get(node.node_id)
                    if not asset_id: continue
                    
                    props = {
                        "id": asset_id,
                        "name": node.name,
                        "type": node.node_type,
                        "project_id": project_id,
                        "solution_id": project_id, # For compatibility
                        "schema_name": node.attributes.get("schema", ""),
                        "system": node.system
                    }
                    graph.upsert_node("Asset", props)
                    # Add specific label? E.g. Table, File?
                    # graph.upsert_node(node.node_type, {"id": asset_id}) # Optional
                
                # 2. Upsert Edges
                for edge in result.edges:
                    from_uuid = node_id_map.get(edge.from_node_id)
                    to_uuid = node_id_map.get(edge.to_node_id)
                    
                    if from_uuid and to_uuid:
                        graph.upsert_relationship(
                            source_props={"id": from_uuid},
                            target_props={"id": to_uuid},
                            rel_type=edge.edge_type
                        )
                
            except Exception as e:
                print(f"Error processing file {fpath}: {e}")
            
            processed_files += 1
            # Update Progress (Throttle updates?)
            if processed_files % 5 == 0 or processed_files == total_files:
                progress = int((processed_files / total_files) * 100)
                supabase.table("job_run").update({"progress_pct": progress}).eq("job_id", job_id).execute()
            
        # Finish
        supabase.table("job_run").update({"status": "completed", "finished_at": "now()", "progress_pct": 100}).eq("job_id", job_id).execute()
        queue.complete_job(job_queue_item["id"])
        
        # Update Solution Status as well (Legacy support)
        supabase.table("solutions").update({"status": "READY"}).eq("id", project_id).execute()
        
        print(f"[WORKER] Job {job_id} Completed")
        
    except Exception as e:
        print(f"[WORKER] Job {job_id} Failed: {e}")
        traceback.print_exc()
        supabase.table("job_run").update({
            "status": "failed", 
            "error_message": str(e),
            "finished_at": "now()"
        }).eq("job_id", job_id).execute()
        
        supabase.table("solutions").update({"status": "ERROR"}).eq("id", project_id).execute()
        queue.fail_job(job_queue_item["id"], str(e))

async def worker_loop():
    queue = SQLJobQueue()
    print("[WORKER] Started polling...")
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
