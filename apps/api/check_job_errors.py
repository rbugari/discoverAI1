import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

solution_id = '7021ac4b-921d-402f-bc21-1c63701b8180'

res = supabase.table("job_run")\
    .select("job_id, status, error_details, current_stage")\
    .eq("project_id", solution_id)\
    .order("created_at", desc=True)\
    .limit(1)\
    .execute()

if res.data:
    job = res.data[0]
    print(f"\n=== LATEST JOB: {job['job_id']} | Status: {job['status']} | Stage: {job['current_stage']} ===")
    if job['error_details']:
        print(f"ERROR DETAILS: {job['error_details']}")
    
    # Check processing logs for this job
    logs = supabase.table("file_processing_log")\
        .select("file_path, action_name, status, error_message")\
        .eq("job_id", job['job_id'])\
        .execute()
    
    print(f"\nFile Processing Logs ({len(logs.data)} items):")
    for l in logs.data:
        print(f" - [{l['status']}] {l['file_path']} ({l['action_name']})")
        if l['status'] == 'failed':
            print(f"   ERR: {l.get('error_message')}")
else:
    print("No jobs found for this solution.")
