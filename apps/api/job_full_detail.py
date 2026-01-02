import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

job_id = 'b0925608-45b8-41cc-bf7d-3deec42180ba'
print(f"=== DETAILED REPORT FOR JOB {job_id} ===")

res = supabase.table("job_run").select("*").eq("job_id", job_id).single().execute()
if res.data:
    j = res.data
    for k, v in j.items():
        print(f"{k}: {v}")
    
    # Check logs
    logs = supabase.table("file_processing_log").select("*").eq("job_id", job_id).execute()
    print(f"\nLOG ENTRIES: {len(logs.data)}")
    for l in logs.data:
        print(f"  [{l['status']}] {l['file_path']} | {l['error_message']}")
else:
    print("Job not found.")
