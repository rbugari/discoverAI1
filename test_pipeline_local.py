import os
import asyncio
import shutil
import zipfile
from apps.api.app.services.llm import LLMService
from apps.api.app.services.graph import get_graph_service
from apps.api.app.config import settings

# Override settings to ensure we are in NEO4J mode if configured
# settings.GRAPH_MODE = "NEO4J" 

async def run_local_test(zip_path: str):
    print(f"🚀 Starting Local Test with ZIP: {zip_path}")
    
    # 1. Simulate Extraction
    extract_dir = "temp_test_extract"
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir)
    
    print(f"📂 Extracting to {extract_dir}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
        
    # 2. Initialize Services
    graph_service = get_graph_service()
    llm_service = LLMService()
    
    # 3. Walk and Analyze
    valid_extensions = {'.sql', '.dtsx'} # Focusing on SQL and SSIS for this test
    
    files_to_process = []
    for dirpath, _, filenames in os.walk(extract_dir):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext in valid_extensions:
                files_to_process.append(os.path.join(dirpath, filename))
    
    print(f"Found {len(files_to_process)} valid files to analyze.")
    
    for file_path in files_to_process:
        print(f"\n--- Analyzing {os.path.basename(file_path)} ---")
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Analyze
            ext = os.path.splitext(file_path)[1].lower()
            analysis = llm_service.analyze_code(file_path, content, ext)
            
            print(f"✅ Summary: {analysis.summary}")
            print(f"   Inputs: {[i.name for i in analysis.inputs]}")
            print(f"   Outputs: {[o.name for o in analysis.outputs]}")
            
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
                "summary": analysis.summary
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

                input_node = {"id": inp.name, "name": inp.name, "type": input_type, "schema": inp.schema_name}
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

                output_node = {"id": out.name, "name": out.name, "type": output_type, "schema": out.schema_name}
                graph_service.upsert_node("Asset", output_node)
                graph_service.upsert_relationship(script_node, output_node, "OUTPUT_TO")
                
        except Exception as e:
            print(f"❌ Error analyzing {file_path}: {e}")

    print("\n🎉 Test Completed. Check Neo4j for results.")

if __name__ == "__main__":
    zip_file = r"c:\proyectos_dev\discoverIA\datosprueba\build-etl-using-ssis-main.zip"
    asyncio.run(run_local_test(zip_file))