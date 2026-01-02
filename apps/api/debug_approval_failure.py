import os
import json
import traceback
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print(f"--- EXHAUSTIVE JOB ANALYSIS ---")

# Fetch last 5 jobs for project 7021ac4b-921d-402f-bc21-1c63701b8180
res = supabase.table("job_run")\
    .select("*")\
    .eq("project_id", "7021ac4b-921d-402f-bc21-1c63701b8180")\
    .order("created_at", desc=True)\
    .limit(5)\
    .execute()

if not res.data:
    print("No jobs found for this project.")
else:
    for j in res.data:
        print(f"\n" + "="*50)
        print(f"JOB ID: {j['job_id']}")
        print(f"STATUS: {j['status']}")
        print(f"STAGE:  {j['current_stage']}")
        print(f"PLAN ID: {j['plan_id']}")
        print(f"CREATED: {j['created_at']}")
        print(f"ERROR MSG: {j['error_message']}")
        print("-" * 20)
        print("ERROR DETAILS:")
        print(j['error_details'])
        print("-" * 20)
        
        # Check if plan exists and its status
        if j['plan_id']:
            p_res = supabase.table("job_plan").select("status").eq("plan_id", j['plan_id']).execute()
            if p_res.data:
                print(f"PLAN STATUS: {p_res.data[0]['status']}")
            else:
                print(f"PLAN STATUS: NOT FOUND in job_plan table")
        
        # Check file logs
        log_res = supabase.table("file_processing_log").select("*").eq("job_id", j['job_id']).execute()
        print(f"TOTAL LOG ENTRIES: {len(log_res.data)}")
        for l in log_res.data[:5]:
             print(f"  [{l['status']}] {l['file_path']} - {l['error_message']}")
