import os
import json
import traceback
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

project_id = '7021ac4b-921d-402f-bc21-1c63701b8180'
print(f"=== ABSOLUTE DEBUGGER FOR PROJECT {project_id} ===")

# 1. Fetch THE LATEST job regardless of status
res = supabase.table("job_run")\
    .select("*")\
    .eq("project_id", project_id)\
    .order("created_at", desc=True)\
    .limit(1)\
    .execute()

if not res.data:
    print("No jobs found for this project.")
else:
    j = res.data[0]
    print(f"\nLATEST JOB: {j['job_id']}")
    print(f"CREATED: {j['created_at']}")
    print(f"STARTED: {j['started_at']}")
    print(f"STATUS:  {j['status']}")
    print(f"STAGE:   {j['current_stage']}")
    print(f"ERROR:   {j['error_message']}")
    print(f"DETAILS: {j['error_details']}")
    print("-" * 40)
    
    # Check if there are any specific logs in file_processing_log for this job
    log_res = supabase.table("file_processing_log").select("*").eq("job_id", j['job_id']).execute()
    print(f"FILE LOGS: {len(log_res.data)}")
    for log in log_res.data:
        print(f"  [{log['status']}] {log['file_path']} | {log['error_message']}")

# 2. Check Solution state
sol = supabase.table("solutions").select("*").eq("id", project_id).single().execute()
print(f"\nSOLUTION STATE: {sol.data['status']}")
print(f"STORAGE PATH:   {sol.data['storage_path']}")

# 3. Check Queue for ANY job belonging to this project
q_res = supabase.table("job_queue").select("*").order("created_at", desc=True).limit(5).execute()
print(f"\nRECENT QUEUE ITEMS:")
for q in q_res.data:
    print(f"  Q_ID: {q['id']} | JOB_ID: {q['job_id']} | STATUS: {q['status']}")
