#!/usr/bin/env python3
import sys
import os
from pathlib import Path
import json

sys.path.append(str(Path(__file__).parent.parent))
from app.config import settings
from supabase import create_client

def inspect_latest_log():
    key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
    supabase = create_client(settings.SUPABASE_URL, key)
    
    # Obtener último log completado
    res = supabase.table("file_processing_log")\
        .select("*")\
        .eq("status", "success")\
        .order("completed_at", desc=True)\
        .limit(1)\
        .execute()
    
    if res.data:
        log = res.data[0]
        print(f"File: {log['file_path']}")
        print(f"Action: {log['action_name']}")
        print(f"Model: {log.get('model_used')}")
        
        # El resultado suele guardarse en una columna JSONB si la tabla lo soporta, 
        # pero en el esquema actual parece que solo guardamos contadores (nodes_count, etc)
        # o quizas en 'error_details' si falló.
        # Vamos a ver qué columnas tiene.
        print(f"Nodes Extracted: {log.get('nodes_count')}")
        
        # Si queremos ver el contenido, tendríamos que haberlo guardado. 
        # FileProcessingLogger.update_processing_results guarda 'processing_result' si existe la columna.
        # Vamos a ver si 'processing_result' está en el log.
        if 'processing_result' in log:
             print("Result Preview:")
             print(json.dumps(log['processing_result'], indent=2)[:500] + "...")
        else:
             print("No 'processing_result' column found.")

if __name__ == "__main__":
    inspect_latest_log()