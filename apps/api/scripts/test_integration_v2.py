#!/usr/bin/env python3
"""
Test de Integración V2 - Verificación de Persistencia de Grafo
"""
import uuid
import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Añadir el directorio padre al path
sys.path.append(str(Path(__file__).parent.parent))

from app.config import settings
from app.services.queue import SQLJobQueue
from supabase import create_client

def run_test_v2():
    print("Iniciando Test V2 (Persistencia de Grafo)...")
    
    # Ruta de prueba (usando solo los SQLs para ir más rápido)
    test_data_path = r"c:\proyectos_dev\discoverIA\temp_test_extract\build-etl-using-ssis-main\Scripts"
    
    key_to_use = settings.SUPABASE_SERVICE_ROLE_KEY if settings.SUPABASE_SERVICE_ROLE_KEY else settings.SUPABASE_KEY
    supabase = create_client(settings.SUPABASE_URL, key_to_use)
    
    try:
        # 0. Crear Org
        org_id = str(uuid.uuid4())
        try:
            supabase.table("organizations").insert({
                "id": org_id,
                "name": "Test Org V2",
                "created_at": datetime.utcnow().isoformat()
            }).execute()
        except:
            pass # Asumimos que puede fallar si ya existe o lo que sea, no es crítico si podemos crear solution
            
        # 1. Crear Solution
        solution_id = str(uuid.uuid4())
        print(f"Solution ID: {solution_id}")
        
        supabase.table("solutions").insert({
            "id": solution_id,
            "org_id": org_id,
            "name": "Test Graph Persistence",
            "storage_path": test_data_path,
            "status": "PENDING",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).execute()
        
        # 2. Crear Job
        job_id = str(uuid.uuid4())
        print(f"Job ID: {job_id}")
        
        supabase.table("job_run").insert({
            "job_id": job_id,
            "project_id": solution_id,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        
        # 3. Encolar
        queue = SQLJobQueue()
        queue.enqueue_job(job_id)
        print("Job encolado. Esperando...")
        
        # 4. Polling
        for i in range(120): # 10 minutos max
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
            
        print("Timeout.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test_v2()