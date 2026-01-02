import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

solution_id = '7021ac4b-921d-402f-bc21-1c63701b8180'

print("--- SOLUTION STATUS ---")
sol_res = supabase.table("solutions").select("*").eq("id", solution_id).single().execute()
if sol_res.data:
    print(f"ID: {sol_res.data['id']}")
    print(f"NAME: {sol_res.data['name']}")
    print(f"STATUS: {sol_res.data['status']}")
else:
    print("Solution not found")

print("\n--- RECENT JOBS (Last 30m) ---")
time_limit = (datetime.utcnow() - timedelta(minutes=30)).isoformat()
jobs_res = supabase.table("job_run")\
    .select("*")\
    .eq("project_id", solution_id)\
    .gte("created_at", time_limit)\
    .order("created_at", desc=True)\
    .execute()

for job in jobs_res.data:
    print(f"JOB: {job['job_id']} | STATUS: {job['status']} | STAGE: {job['current_stage']} | CREATED: {job['created_at']}")
    if job['error_details']:
        print(f"  ERROR: {job['error_details']}")

print("\n--- QUEUE STATUS ---")
# Check if there are any jobs in the queue table
try:
    queue_res = supabase.table("job_queue").select("*").execute()
    print(f"Total jobs in queue: {len(queue_res.data)}")
    for q in queue_res.data:
        print(f"  Queue ID: {q['id']} | Job ID: {q['job_id']} | Status: {q['status']}")
except Exception as e:
    print(f"Could not fetch queue: {e}")

print("\n--- DISCONNECT CHECK ---")
# Check if the latest job is NOT what the solution expects
if jobs_res.data:
    latest_job = jobs_res.data[0]
    if latest_job['status'] == 'completed' and sol_res.data['status'] == 'ERROR':
        print("ALERT: State disconnect detected! Solution is ERROR but latest job is COMPLETED.")
