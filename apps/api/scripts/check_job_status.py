#!/usr/bin/env python3
import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Añadir el directorio padre al path
sys.path.append(str(Path(__file__).parent.parent))

from app.config import settings
from supabase import create_client

def check_job(job_id, solution_id):
    print(f"Verificando Job: {job_id}")
    key_to_use = settings.SUPABASE_SERVICE_ROLE_KEY if settings.SUPABASE_SERVICE_ROLE_KEY else settings.SUPABASE_KEY
    supabase = create_client(settings.SUPABASE_URL, key_to_use)
    
    for i in range(120): # Polling
        job = supabase.table("job_run").select("status").eq("job_id", job_id).single().execute()
        status = job.data["status"]
        print(f"Estado: {status}")
        
        if status == "completed":
            print("Job completado. Verificando persistencia...")
            
            # Verificar Assets
            assets = supabase.table("asset").select("*", count="exact").eq("project_id", solution_id).execute()
            print(f"Assets encontrados: {len(assets.data)}")
            
            # Verificar Edges
            edges = supabase.table("edge_index").select("*", count="exact").eq("project_id", solution_id).execute()
            print(f"Edges encontrados: {len(edges.data)}")
            
            if len(assets.data) > 0:
                print("SUCCESS: El grafo se ha persistido correctamente.")
                print(f"Muestra Asset: {assets.data[0]['name_display']} ({assets.data[0]['asset_type']})")
            else:
                print("FAILURE: No se encontraron assets en la DB.")
            
            return
        elif status == "failed":
            print("Job falló.")
            return
            
        time.sleep(5)

if __name__ == "__main__":
    check_job("d364b91e-ee89-4afb-8ff3-6122a81c0a00", "8cfb51c7-8a1f-43f1-9f10-e77d1fbab78d")