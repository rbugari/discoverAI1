#!/usr/bin/env python3
import sys
import os
from pathlib import Path
import json

sys.path.append(str(Path(__file__).parent.parent))
from app.config import settings
from supabase import create_client

def inspect(project_id):
    key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
    supabase = create_client(settings.SUPABASE_URL, key)
    
    # Buscar un asset tipo TABLE o FILE
    res = supabase.table("asset").select("*").eq("project_id", project_id).limit(5).execute()
    
    for asset in res.data:
        print(f"Asset: {asset['name_display']} ({asset['asset_type']})")
        print(f"Tags: {json.dumps(asset.get('tags'), indent=2)}")
        print("-" * 20)

if __name__ == "__main__":
    inspect("ccfe6520-0391-476f-85dd-ad0c2d6bd7fb")