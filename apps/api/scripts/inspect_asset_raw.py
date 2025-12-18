#!/usr/bin/env python3
import sys
import os
from pathlib import Path
import json

sys.path.append(str(Path(__file__).parent.parent))
from app.config import settings
from supabase import create_client

def inspect():
    key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
    supabase = create_client(settings.SUPABASE_URL, key)
    
    # Buscar un asset tipo TABLE
    res = supabase.table("asset").select("*").eq("asset_type", "TABLE").limit(1).execute()
    
    if res.data:
        asset = res.data[0]
        print(f"Asset: {asset['name_display']}")
        print(f"Tags: {json.dumps(asset.get('tags'), indent=2)}")
    else:
        print("No se encontraron tablas.")

if __name__ == "__main__":
    inspect()