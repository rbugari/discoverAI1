import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

solution_id = '7021ac4b-921d-402f-bc21-1c63701b8180'
res = supabase.table("job_run").select("*").eq("project_id", solution_id).order("created_at", desc=True).limit(1).execute()

if res.data:
    job = res.data[0]
    print(f"JOB_ID: {job['job_id']}")
    print(f"JOB_STATUS: {job['status']}")
    print(f"STAGE: {job['current_stage']}")
    print(f"ERROR_DETAILS: {job['error_details']}")
    
    # Also check the plan for this job
    plan_res = supabase.table("job_plan").select("*").eq("job_id", job['job_id']).execute()
    if plan_res.data:
        print(f"PLAN_STATUS: {plan_res.data[0]['status']}")

# Check solution status
sol_res = supabase.table("solutions").select("status").eq("id", solution_id).single().execute()
if sol_res.data:
    print(f"SOLUTION_STATUS: {sol_res.data['status']}")
else:
    print("Solution not found")
