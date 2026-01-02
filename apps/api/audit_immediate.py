import os
import json
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

now = datetime.utcnow()
ten_mins_ago = (now - timedelta(minutes=10)).isoformat()

print(f"--- JOBS CREATED SINCE {ten_mins_ago} ---")
res = supabase.table("job_run").select("*").gte("created_at", ten_mins_ago).order("created_at", desc=True).execute()

for j in res.data:
    print(f"ID: {j['job_id']} | STATUS: {j['status']} | STAGE: {j['current_stage']} | CREATED: {j['created_at']}")

if not res.data:
    print("Zero jobs created in the last 10 minutes.")
