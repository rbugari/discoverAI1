import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

solution_id = '7021ac4b-921d-402f-bc21-1c63701b8180'

print("--- JOB QUEUE ---")
q_res = supabase.table("job_queue").select("*").execute()
print(f"Total entries: {len(q_res.data)}")
for q in q_res.data:
    print(f"ID: {q['id']} | Job: {q['job_id']} | Status: {q['status']} | Created: {q['created_at']}")

print("\n--- JOB RUN (Latest 5 for this solution) ---")
j_res = supabase.table("job_run").select("*").eq("project_id", solution_id).order("created_at", desc=True).limit(5).execute()
for j in j_res.data:
    print(f"ID: {j['job_id']} | Status: {j['status']} | Stage: {j['current_stage']} | ERR: {j['error_details']}")
    
    # If failed in planning, check per-file logs? (Planning doesn't usually have per-file logs in file_processing_log yet)
    # Check reasoning_log for this job
    r_res = supabase.table("reasoning_log").select("*").eq("job_id", j['job_id']).limit(1).execute()
    if r_res.data:
        print(f"  Reasoning Logic found: {r_res.data[0]['step_name']}")
