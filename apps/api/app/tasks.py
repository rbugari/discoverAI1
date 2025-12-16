import asyncio
import os
from .config import settings
from .services.graph import get_graph_service
from .services.storage import StorageService
from .services.llm import LLMService
from supabase import create_client

async def analyze_solution_task(job_id: str, file_path: str):
    print(f"Starting analysis for Job {job_id}. Source: {file_path}")
    
    # Update Job Status to RUNNING
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    solution_id = job_id 
    
    try:
        supabase.from_("solutions").update({"status": "PROCESSING"}).eq("id", solution_id).execute()
        
        # 1. Services Init
        graph_service = get_graph_service()
        storage_service = StorageService()
        llm_service = LLMService()
        
        # 2. Prepare Source Code
        # Detect if it's a Git URL or a Storage Path
        extract_dir = ""
        if file_path.startswith("http://") or file_path.startswith("https://"):
            # It's a Git URL
            extract_dir = storage_service.clone_repo(file_path)
        else:
            # It's a Storage Path (ZIP)
            extract_dir = storage_service.download_and_extract(file_path)
        
        # 3. Walk & Analyze
        for current_file_path, content, ext in storage_service.walk_files(extract_dir):
            # Analyze with LLM
            analysis = llm_service.analyze_code(current_file_path, content, ext)
            
            # Persist to Graph
            # Determine Node Type
            node_type = "FILE"
            if ext == ".dtsx":
                node_type = "PIPELINE"
            elif ext == ".sql":
                node_type = "SCRIPT"
            elif ext == ".py":
                node_type = "SCRIPT"

            # Node: Script/Pipeline
            script_node = {
                "id": analysis.file_path, 
                "name": os.path.basename(analysis.file_path), 
                "type": node_type,
                "summary": analysis.summary,
                "solution_id": solution_id # Tag with solution_id
            }
            graph_service.upsert_node("Asset", script_node)
            
            # Inputs
            for inp in analysis.inputs:
                # Normalize type for Tables
                input_type = inp.type
                if not input_type or input_type.lower() in ["table", "view"]:
                    input_type = "TABLE"
                elif input_type.lower() in ["database", "schema"]:
                    input_type = "DATABASE"

                input_node = {
                    "id": inp.name, 
                    "name": inp.name, 
                    "type": input_type, 
                    "schema_name": inp.schema_name, 
                    "columns": inp.columns or [],
                    "solution_id": solution_id # Tag with solution_id
                }
                graph_service.upsert_node("Asset", input_node)
                graph_service.upsert_relationship(input_node, script_node, "INPUT_OF")
                
            # Outputs
            for out in analysis.outputs:
                # Normalize type for Tables
                output_type = out.type
                if not output_type or output_type.lower() in ["table", "view"]:
                    output_type = "TABLE"
                elif output_type.lower() in ["database", "schema"]:
                    output_type = "DATABASE"

                output_node = {
                    "id": out.name, 
                    "name": out.name, 
                    "type": output_type, 
                    "schema_name": out.schema_name,
                    "columns": out.columns or [],
                    "solution_id": solution_id # Tag with solution_id
                }
                graph_service.upsert_node("Asset", output_node)
                graph_service.upsert_relationship(script_node, output_node, "OUTPUT_TO")
        
        # 4. Cleanup & Finish
        supabase.from_("solutions").update({"status": "READY"}).eq("id", solution_id).execute()
        print(f"Job {solution_id} Completed Successfully.")
        
    except Exception as e:
        print(f"Job {solution_id} Failed: {e}")
        supabase.from_("solutions").update({"status": "ERROR"}).eq("id", solution_id).execute()
    
    return {"status": "completed", "job_id": solution_id}