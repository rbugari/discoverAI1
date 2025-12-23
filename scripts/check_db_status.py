import os
import sys
from supabase import create_client
from pathlib import Path
from dotenv import load_dotenv

# Load env from root
root = Path(r"c:\proyectos_dev\discoverIA - gravity")
load_dotenv(root / ".env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

def check():
    # 1. Latest Jobs
    print("--- LATEST JOBS ---")
    jobs = supabase.table("job_run").select("*").order("created_at", desc=True).limit(5).execute()
    for j in jobs.data:
        print(f"Job ID: {j['job_id']}")
        print(f"  Project ID: {j['project_id']}")
        print(f"  Status: {j['status']}")
        print(f"  Stage: {j['current_stage']}")
        print(f"  Plan ID: {j['plan_id']}")
        print(f"  Progress: {j['progress_pct']}%")
        print(f"  Error: {j['error_message']}")
        print("-" * 20)

    # 2. Queue Status
    print("\n--- QUEUE STATUS ---")
    queue = supabase.table("job_queue").select("*").order("created_at", desc=True).limit(5).execute()
    for q in queue.data:
        print(f"Queue ID: {q['id']}")
        print(f"  Job ID: {q['job_id']}")
        print(f"  Status: {q['status']}")
        print(f"  Attempts: {q['attempts']}")
        print(f"  Error: {q['last_error']}")
        print("-" * 20)

    # 3. Plan Status
    if jobs.data:
        plan_id = jobs.data[0].get('plan_id')
        if plan_id:
            print(f"\n--- PLAN STATUS ({plan_id}) ---")
            plan = supabase.table("job_plan").select("*").eq("plan_id", plan_id).single().execute()
            if plan.data:
                print(f"Status: {plan.data['status']}")
                
            items = supabase.table("job_plan_item").select("item_id, status, enabled, path").eq("plan_id", plan_id).execute()
            enabled_count = len([i for i in items.data if i['enabled']])
            completed_count = len([i for i in items.data if i['status'] == 'completed'])
            print(f"Items: {len(items.data)}")
            print(f"Enabled: {enabled_count}")
            print(f"Completed: {completed_count}")
            if items.data:
                print("First 3 items:")
                for i in items.data[:3]:
                    print(f"  {i['path']} -> {i['status']} (Enabled: {i['enabled']})")

if __name__ == "__main__":
    check()
