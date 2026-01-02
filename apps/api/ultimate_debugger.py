import os
import json
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

project_id = '7021ac4b-921d-402f-bc21-1c63701b8180'
print(f"=== THOROUGH DEBUGGER FOR PROJECT {project_id} ===")

# 1. Get Project Status
sol = supabase.table("solutions").select("*").eq("id", project_id).single().execute()
if sol.data:
    print(f"SOLUTION STATUS: {sol.data['status']}")
    print(f"STORAGE PATH: {sol.data['storage_path']}")

# 2. Get Last 5 Jobs specifically for this project
jobs = supabase.table("job_run").select("*").eq("project_id", project_id).order("created_at", desc=True).limit(5).execute()
for j in jobs.data:
    print(f"\n" + "#"*60)
    print(f"JOB ID: {j['job_id']}")
    print(f"CREATED: {j['created_at']}")
    print(f"STATUS:  {j['status']}")
    print(f"STAGE:   {j['current_stage']}")
    print(f"PLAN ID: {j['plan_id']}")
    print(f"ERROR:   {j['error_message']}")
    print("-" * 20)
    print("DETAILS (TRUNCATED TO 2000 CHARS):")
    print(str(j['error_details'])[:2000])
    print("#"*60)
    
    # Check if there are any specific errors in file_processing_log
    logs = supabase.table("file_processing_log").select("*").eq("job_id", j['job_id']).execute()
    if logs.data:
        print(f"LOGS ({len(logs.data)}):")
        # Find failed logs specifically
        failed_logs = [l for l in logs.data if l['status'] == 'error']
        if failed_logs:
             print(f"FAILED LOGS ({len(failed_logs)}):")
             for l in failed_logs[:5]:
                 print(f"  - {l['file_path']} | {l['error_message']}")
        else:
             print("All log entries are successful.")

# 3. Check Queue for this specific project
# We have to fetch all queue items and filter by job_id in memory if needed, 
# or just join if supabase allowed it easily.
queue = supabase.table("job_queue").select("*").order("created_at", desc=True).limit(20).execute()
print("\n--- RECENT QUEUE ITEMS ---")
for q in queue.data:
    # Check if this job_id belongs to our project
    match = next((j for j in jobs.data if j['job_id'] == q['job_id']), None)
    if match or project_id in str(q): # broad check
        print(f"Q_ID: {q['id']} [MATCH] | JOB_ID: {q['job_id']} | STATUS: {q['status']} | CREATED: {q['created_at']}")
    else:
        print(f"Q_ID: {q['id']} | JOB_ID: {q['job_id']} | STATUS: {q['status']}")

# 4. Check Plan Statuses
if jobs.data:
    plan_ids = list(set([j['plan_id'] for j in jobs.data if j['plan_id']]))
    if plan_ids:
        plans = supabase.table("job_plan").select("*").in_("plan_id", plan_ids).execute()
        print("\n--- ASSOCIATED PLANS ---")
        for p in plans.data:
            print(f"PLAN: {p['plan_id']} | STATUS: {p['status']} | CREATED: {p['created_at']}")
