#!/usr/bin/env python3
import sys
import os
import time
from pathlib import Path

# Añadir el directorio padre al path
sys.path.append(str(Path(__file__).parent.parent))

from app.config import settings
from supabase import create_client

def check_job_v3(job_id, solution_id):
    print(f"Verificando Job: {job_id}")
    key_to_use = settings.SUPABASE_SERVICE_ROLE_KEY if settings.SUPABASE_SERVICE_ROLE_KEY else settings.SUPABASE_KEY
    supabase = create_client(settings.SUPABASE_URL, key_to_use)
    
    start_time = time.time()
    
    while True: # Polling infinito hasta que termine
        try:
            job = supabase.table("job_run").select("status, current_stage").eq("job_id", job_id).single().execute()
            status = job.data["status"]
            stage = job.data.get("current_stage", "unknown")
            
            # Auditoría progresiva
            audit = supabase.table("file_processing_log").select("id", count="exact").eq("job_id", job_id).execute()
            processed = audit.count or 0
            
            elapsed = int(time.time() - start_time)
            sys.stdout.write(f"\r[{elapsed}s] Estado: {status} | Etapa: {stage} | Archivos procesados (audit): {processed}")
            sys.stdout.flush()
            
            if status == "completed":
                print("\n\n✅ Job completado!")
                
                # Verificar Assets
                assets = supabase.table("asset").select("*", count="exact").eq("project_id", solution_id).execute()
                print(f"Assets encontrados: {len(assets.data)}")
                
                # Chequear columnas
                columns_found = 0
                for a in assets.data:
                    tags = a.get('tags') or {}
                    cols = tags.get('columns')
                    if cols:
                        columns_found += 1
                        if columns_found <= 3:
                            print(f"   - {a['name_display']}: {len(cols)} columnas")
                
                print(f"Assets con columnas: {columns_found}")
                return
                
            elif status == "failed":
                print(f"\n\n❌ Job falló: {job.data.get('error_message')}")
                return
                
            time.sleep(10)
            
        except Exception as e:
            print(f"\nError polling: {e}")
            time.sleep(10)

if __name__ == "__main__":
    check_job_v3("ec784745-d485-43f8-a3a5-bec47111a24f", "73491f2d-4dd3-4b48-94f2-7f94b3845fbe")