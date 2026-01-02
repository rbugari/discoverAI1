import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "apps", "api"))
load_dotenv()

from app.config import settings
from supabase import create_client

def debug_ids():
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    project_id = "7021ac4b-921d-402f-bc21-1c63701b8180"
    
    # Fetch 5 Assets
    assets = supabase.table("asset").select("asset_id, name_display").eq("project_id", project_id).limit(5).execute().data
    print("\nSample Assets:")
    asset_ids = set()
    for a in assets:
        print(f"- {a['name_display']}: {a['asset_id']}")
        asset_ids.add(a['asset_id'])

    # Fetch 5 Column Lineages
    lineage = supabase.table("column_lineage").select("lineage_id, source_asset_id, target_asset_id").eq("project_id", project_id).limit(5).execute().data
    print("\nSample Lineage:")
    for l in lineage:
        print(f"- Lineage {l['lineage_id']}: Source={l['source_asset_id']}, Target={l['target_asset_id']}")
        if l['source_asset_id'] in asset_ids:
            print("  [MATCH] Source ID found in Assets!")
        if l['target_asset_id'] in asset_ids:
            print("  [MATCH] Target ID found in Assets!")

    # Fetch 5 Edges
    edges = supabase.table("edge_index").select("edge_id, from_asset_id, to_asset_id").eq("project_id", project_id).limit(5).execute().data
    print("\nSample Edges:")
    for e in edges:
        print(f"- Edge {e['edge_id']}: From={e['from_asset_id']}, To={e['to_asset_id']}")

if __name__ == "__main__":
    debug_ids()
