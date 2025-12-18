#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Añadir el directorio padre al path
sys.path.append(str(Path(__file__).parent.parent))

from app.config import settings
from supabase import create_client

def check_assets(solution_id):
    print(f"Verificando Assets para Solución: {solution_id}")
    key_to_use = settings.SUPABASE_SERVICE_ROLE_KEY if settings.SUPABASE_SERVICE_ROLE_KEY else settings.SUPABASE_KEY
    supabase = create_client(settings.SUPABASE_URL, key_to_use)
    
    assets = supabase.table("asset").select("*").eq("project_id", solution_id).execute()
    print(f"Total Assets: {len(assets.data)}")
    
    for a in assets.data:
        tags = a.get('tags') or {}
        cols = tags.get('columns')
        if cols:
            print(f"✅ {a['name_display']} ({a['asset_type']}) tiene {len(cols)} columnas: {cols[:3]}")
        else:
            print(f"❌ {a['name_display']} ({a['asset_type']}) NO tiene columnas. Tags: {tags.keys()}")

if __name__ == "__main__":
    check_assets("42439ba0-28dc-47d2-8027-90adbb7f0ff9") # ID de la solución del test v3
