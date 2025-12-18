#!/usr/bin/env python3
"""
Test de Integración V3 - Procesamiento Completo (SSIS + SQL)
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

def run_test_v3():
    print("🚀 Iniciando Test V3 (Full Repo)...")
    
    # Ruta COMPLETA al repo de prueba
    test_data_path = r"c:\proyectos_dev\discoverIA\temp_test_extract\build-etl-using-ssis-main"
    
    key_to_use = settings.SUPABASE_SERVICE_ROLE_KEY if settings.SUPABASE_SERVICE_ROLE_KEY else settings.SUPABASE_KEY
    supabase = create_client(settings.SUPABASE_URL, key_to_use)
    
    try:
        # 1. Crear Solution
        solution_id = str(uuid.uuid4())
        solution_name = f"Test Full SSIS {datetime.now().strftime('%H:%M')}"
        print(f"📝 Solución: {solution_name} ({solution_id})")
        
        # Org Dummy si es necesario (ya debería existir del test anterior, reusamos o creamos nueva si falla FK)
        # Asumimos que podemos insertar sin org_id o con uno válido si la tabla lo permite.
        # Mejor buscamos una org existente.
        orgs = supabase.table("organizations").select("id").limit(1).execute()
        org_id = orgs.data[0]['id'] if orgs.data else str(uuid.uuid4())
        
        if not orgs.data:
             try:
                supabase.table("organizations").insert({"id": org_id, "name": "Auto Org"}).execute()
             except: pass

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
        print("📥 Job encolado. Esperando worker...")
        
        # 4. Polling con barra de progreso
        start_time = time.time()
        max_wait = 600 # 10 min
        
        while (time.time() - start_time) < max_wait:
            job = supabase.table("job_run").select("status, current_stage").eq("job_id", job_id).single().execute()
            status = job.data["status"]
            stage = job.data.get("current_stage", "unknown")
            
            # Auditoría progresiva
            audit = supabase.table("file_processing_log").select("id", count="exact").eq("job_id", job_id).execute()
            processed = audit.count or 0
            
            sys.stdout.write(f"\r⏳ [{int(time.time()-start_time)}s] Estado: {status} | Etapa: {stage} | Archivos: {processed}")
            sys.stdout.flush()
            
            if status == "completed":
                print("\n\n✅ Job completado!")
                break
            elif status == "failed":
                print(f"\n\n❌ Job falló: {job.data.get('error_message')}")
                return
                
            time.sleep(5)
            
        # 5. Verificación de Resultados
        print("\n🔍 Verificando resultados...")
        
        assets = supabase.table("asset").select("*").eq("project_id", solution_id).execute()
        print(f"   - Total Assets: {len(assets.data)}")
        
        # Verificar tipos
        types = {}
        columns_found = 0
        for a in assets.data:
            t = a['asset_type']
            types[t] = types.get(t, 0) + 1
            
            # Chequear columnas en tags
            tags = a.get('tags') or {}
            cols = tags.get('columns')
            if cols:
                columns_found += 1
                if columns_found == 1:
                    print(f"   - Ejemplo columnas en {a['name_display']}: {cols[:3]}...")

        print(f"   - Tipos encontrados: {types}")
        print(f"   - Assets con columnas detectadas: {columns_found}")
        
        if columns_found == 0:
            print("⚠️  ADVERTENCIA: No se detectaron columnas. Revisar prompt del LLM o parser.")
        else:
            print("✅ Columnas detectadas correctamente.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test_v3()