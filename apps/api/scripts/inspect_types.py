#!/usr/bin/env python3
import sys
import os
from pathlib import Path
import json
from collections import Counter

sys.path.append(str(Path(__file__).parent.parent))
from app.config import settings
from supabase import create_client

def inspect_types():
    key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
    supabase = create_client(settings.SUPABASE_URL, key)
    
    # Usar el project_id del último test para filtrar
    project_id = "7aa3e759-410b-4600-a413-566a821ab962"
    
    res = supabase.table("asset").select("asset_type, name_display").eq("project_id", project_id).execute()
    
    types = Counter([r['asset_type'] for r in res.data])
    print(f"Tipos de Assets: {types}")
    
    # Imprimir un ejemplo de cada tipo
    seen = set()
    for r in res.data:
        if r['asset_type'] not in seen:
            print(f"Ejemplo {r['asset_type']}: {r['name_display']}")
            
            # Fetch tags for this one
            full = supabase.table("asset").select("*").eq("project_id", project_id).eq("name_display", r['name_display']).execute()
            if full.data:
                print(f"Tags: {json.dumps(full.data[0].get('tags'), indent=2)}")
            seen.add(r['asset_type'])

if __name__ == "__main__":
    inspect_types()