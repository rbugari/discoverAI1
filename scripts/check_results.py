import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. Get Latest Solution
sol_res = supabase.table("solutions").select("id, name, status").order("created_at", desc=True).limit(1).execute()
if not sol_res.data:
    print("No solutions found.")
    exit(0)

sol = sol_res.data[0]
print(f"Latest Solution: {sol['name']} ({sol['id']}) - Status: {sol['status']}")

# 2. Get Latest Job for this solution
job_res = supabase.table("job_run").select("job_id, status, current_stage, progress_pct").eq("project_id", sol["id"]).order("created_at", desc=True).limit(1).execute()
if job_res.data:
    job = job_res.data[0]
    print(f"Job: {job['job_id']} - Status: {job['status']} - Stage: {job['current_stage']} - Progress: {job['progress_pct']}%")
else:
    print("No jobs found for this solution.")

# 3. Check v4.0 Data for this solution
pkg_res = supabase.table("package").select("name, business_intent").eq("project_id", sol["id"]).execute()
print(f"Packages Found: {len(pkg_res.data)}")
for p in pkg_res.data:
    print(f"- {p['name']}: {p['business_intent']}")

lin_res = supabase.table("column_lineage").select("lineage_id").eq("project_id", sol["id"]).execute()
print(f"Lineage Rows: {len(lin_res.data)}")
