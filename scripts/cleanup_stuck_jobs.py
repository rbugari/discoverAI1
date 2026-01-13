import os
from supabase import create_client
from dotenv import load_dotenv

# Load ENV from root directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
    exit(1)

supabase = create_client(url, key)

def cleanup():
    print("--- Starting Cleanup of Stuck Jobs ---")
    
    # 1. Update stuck job_runs
    print("Cleaning job_run...")
    res1 = supabase.table("job_run").update({
        "status": "failed", 
        "error_message": "Worker interrupted (console closed)",
        "finished_at": "now()"
    }).in_("status", ["running", "queued"]).execute()
    print(f"Updated {len(res1.data)} jobs.")

    # 2. Update stuck job_queue items
    print("Cleaning job_queue...")
    res2 = supabase.table("job_queue").update({
        "status": "failed",
        "last_error": "Worker interrupted"
    }).in_("status", ["processing", "pending"]).execute()
    print(f"Updated {len(res2.data)} queue items.")

    # 3. Update solutions status
    print("Cleaning solutions...")
    res3 = supabase.table("solutions").update({
        "status": "ERROR"
    }).eq("status", "PROCESSING").execute()
    print(f"Updated {len(res3.data)} solutions.")

    # 4. Update stuck plan items
    print("Cleaning job_plan_item...")
    res4 = supabase.table("job_plan_item").update({
        "status": "failed"
    }).eq("status", "running").execute()
    print(f"Updated {len(res4.data)} plan items.")

    print("--- Cleanup Finished ---")

if __name__ == "__main__":
    cleanup()
