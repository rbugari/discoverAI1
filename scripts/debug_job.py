import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Latest Solution
sol_res = supabase.table("solutions").select("id, name").order("created_at", desc=True).limit(1).execute()
sol_id = sol_res.data[0]["id"]
print(f"Solution: {sol_id}")

job_res = supabase.table("job_run").select("*").eq("project_id", sol_id).order("created_at", desc=True).limit(1).execute()
job_id = job_res.data[0]["job_id"]
plan_id = job_res.data[0]["plan_id"]
print(f"Job: {job_id} | Plan: {plan_id}")

# Items by index
items = supabase.table("job_plan_item").select("item_id, path, status, strategy").eq("plan_id", plan_id).execute().data
# Sort them by their original order if possible, but they usually come in order
# Let's just find the first pending

first_pending_idx = -1
for i, item in enumerate(items):
    if item['status'] == 'pending':
        first_pending_idx = i
        break

if first_pending_idx != -1:
    print(f"\nFailure Edge at Index {first_pending_idx}:")
    start = max(0, first_pending_idx - 3)
    end = min(len(items), first_pending_idx + 3)
    for j in range(start, end):
        it = items[j]
        print(f"[{j}] {it['path']} | Status: {it['status']} | Strategy: {it['strategy']}")
else:
    print("No pending items found.")
