#!/usr/bin/env python3
"""
Test V4 - Single File (README.md) con Groq
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

def run_test_v4():
    print("🚀 Iniciando Test V4 (Single File)...")
    
    # Ruta COMPLETA al repo de prueba (usamos README para que sea rápido y pequeño)
    # Nota: El pipeline escanea recursivamente. Para probar solo uno, tendría que aislarlo.
    # Pero si el problema es tamaño, el README pasará y los dtsx fallarán.
    test_data_path = r"c:\proyectos_dev\discoverIA\temp_test_extract\build-etl-using-ssis-main"
    
    key_to_use = settings.SUPABASE_SERVICE_ROLE_KEY if settings.SUPABASE_SERVICE_ROLE_KEY else settings.SUPABASE_KEY
    supabase = create_client(settings.SUPABASE_URL, key_to_use)
    
    try:
        # 1. Crear Solution
        solution_id = str(uuid.uuid4())
        solution_name = f"Test Groq Single {datetime.now().strftime('%H:%M')}"
        print(f"📝 Solución: {solution_name} ({solution_id})")
        
        # Org Dummy
        orgs = supabase.table("organizations").select("id").limit(1).execute()
        org_id = orgs.data[0]['id'] if orgs.data else str(uuid.uuid4())
        
        supabase.table("solutions").insert({
            "id": solution_id,
            "org_id": org_id,
            "name": solution_name,
            "storage_path": test_data_path,
            "status": "PENDING",
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        
        # 2. Crear Job
        job_id = str(uuid.uuid4())
        print(f"⚙️  Job ID: {job_id}")
        
        supabase.table("job_run").insert({
            "job_id": job_id,
            "project_id": solution_id,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        
        # 3. Encolar
        queue = SQLJobQueue()
        queue.enqueue_job(job_id)
        print("📥 Job encolado.")
        
        # 4. Polling
        start_time = time.time()
        while (time.time() - start_time) < 120:
            job = supabase.table("job_run").select("status").eq("job_id", job_id).single().execute()
            status = job.data["status"]
            sys.stdout.write(f"\rEstado: {status}")
            sys.stdout.flush()
            
            if status == "completed":
                print("\n✅ Completado!")
                break
            time.sleep(2)
            
        # 5. Verificar si hay al menos 1 asset (el README)
        assets = supabase.table("asset").select("*").eq("project_id", solution_id).execute()
        print(f"\nAssets encontrados: {len(assets.data)}")
        for a in assets.data:
            print(f"- {a['name_display']} ({a['asset_type']})")

    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    run_test_v4()