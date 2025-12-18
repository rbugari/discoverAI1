#!/usr/bin/env python3
"""
Verifica los resultados de auditoría para el último job ejecutado
"""
import sys
import os
from pathlib import Path
from tabulate import tabulate

# Añadir el directorio padre al path
sys.path.append(str(Path(__file__).parent.parent))

from app.config import settings
from supabase import create_client

def check_audit():
    print("📊 Consultando resultados de auditoría...")
    
    key_to_use = settings.SUPABASE_SERVICE_ROLE_KEY if settings.SUPABASE_SERVICE_ROLE_KEY else settings.SUPABASE_KEY
    supabase = create_client(settings.SUPABASE_URL, key_to_use)
    
    # Obtener el último job run
    try:
        jobs = supabase.table("job_run").select("*").order("created_at", desc=True).limit(1).execute()
        
        if not jobs.data:
            print("❌ No se encontraron jobs.")
            return
            
        last_job = jobs.data[0]
        job_id = last_job['job_id']
        status = last_job['status']
        
        print(f"🆔 Job ID: {job_id}")
        print(f"📈 Estado: {status}")
        
        # Obtener logs de auditoría
        audit_logs = supabase.table("file_processing_log").select("*").eq("job_id", job_id).execute()
        
        if not audit_logs.data:
            print("⚠️  No hay logs de auditoría para este job.")
            return
            
        print(f"\n📑 Archivos procesados: {len(audit_logs.data)}")
        
        # Preparar tabla
        table_data = []
        total_tokens = 0
        total_cost = 0.0
        
        for log in audit_logs.data:
            file_name = Path(log['file_path']).name
            model = log.get('model_used', 'N/A')
            status = log.get('status', 'N/A')
            tokens = log.get('total_tokens', 0) or 0
            cost = log.get('cost_estimate', 0.0) or 0.0
            action = log.get('action_name', 'N/A')
            
            total_tokens += tokens
            total_cost += cost
            
            table_data.append([
                file_name[:30], 
                action,
                model.split('/')[-1] if model else 'N/A', 
                status, 
                tokens, 
                f"${cost:.6f}"
            ])
            
        headers = ["Archivo", "Acción", "Modelo", "Estado", "Tokens", "Costo"]
        print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
        
        print(f"\n💰 Total Tokens: {total_tokens}")
        print(f"💵 Costo Total Estimado: ${total_cost:.6f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_audit()