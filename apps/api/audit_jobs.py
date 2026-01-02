import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

solution_id = '7021ac4b-921d-402f-bc21-1c63701b8180'

res = supabase.table("job_run")\
    .select("job_id, status, error_details, current_stage, created_at")\
    .eq("project_id", solution_id)\
    .order("created_at", desc=True)\
    .limit(10)\
    .execute()

print(f"{'CREATED_AT':<25} | {'JOB_ID':<40} | {'STATUS':<15} | {'STAGE':<20}")
print("-" * 110)
for job in res.data:
    print(f"{job['created_at']:<25} | {job['job_id']:<40} | {job['status']:<15} | {job['current_stage']:<20}")
    if job['error_details']:
        print(f"  ERROR: {job['error_details']}")
