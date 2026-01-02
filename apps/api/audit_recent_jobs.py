import os
import json
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

project_id = '7021ac4b-921d-402f-bc21-1c63701b8180'

# Check for jobs in the last hour across ALL projects
now = datetime.utcnow()
one_hour_ago = (now - timedelta(hours=1)).isoformat()

print(f"--- ABSOLUTE LATEST 10 JOBS IN THE SYSTEM ---")
res = supabase.table("job_run").select("*").order("created_at", desc=True).limit(10).execute()

for j in res.data:
    is_target = j['project_id'] == project_id
    marker = ">>>" if is_target else "   "
    print(f"{marker} ID: {j['job_id']} | PROJECT: {j['project_id']} | STATUS: {j['status']} | STAGE: {j['current_stage']} | CREATED: {j['created_at']}")
    if (j['error_message'] or j['error_details']) and is_target:
        print(f"      ERR: {j['error_message']}")
        print(f"      DTL: {str(j['error_details'])[:200]}...")

if not res.data:
    print("No jobs found in the system.")
