import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "apps", "api"))
load_dotenv()

from app.config import settings
from supabase import create_client

def inspect():
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    project_id = "7021ac4b-921d-402f-bc21-1c63701b8180" # SSIS v4 Test Final
    
    # Check Assets
    res = supabase.table("asset").select("asset_type").eq("project_id", project_id).execute()
    counts = {}
    for r in res.data:
        t = r['asset_type']
        counts[t] = counts.get(t, 0) + 1
    print(counts)

    # Check Edges
    edges = supabase.table("edge_index").select("edge_type").eq("project_id", project_id).execute()
    e_counts = {}
    for r in edges.data:
        t = r['edge_type']
        e_counts[t] = e_counts.get(t, 0) + 1
    print(f"\nEdges for {project_id}:")
    print(e_counts)

if __name__ == "__main__":
    inspect()
