import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

# Fetch all jobs from the last hour
one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()

res = supabase.table("job_run")\
    .select("job_id, project_id, status, error_details, created_at")\
    .gte("created_at", one_hour_ago)\
    .order("created_at", desc=True)\
    .execute()

print(f"RECENT JOBS (Last 1h): {len(res.data)}")
print("-" * 120)
for job in res.data:
    print(f"{job['created_at']} | {job['job_id']} | Sol: {job['project_id'][:8]} | {job['status']:<10} | ERR: {job['error_details']}")
