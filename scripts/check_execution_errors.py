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

def check_latest_errors():
    # 1. Get latest job
    jobs = supabase.table("job_run").select("job_id, status").order("created_at", desc=True).limit(1).execute()
    if not jobs.data:
        print("No jobs found.")
        return
    
    job_id = jobs.data[0]['job_id']
    print(f"Checking errors for Job ID: {job_id}")

    # 2. Check file logs
    logs = supabase.table("file_processing_log")\
        .select("file_path, status, error_type, error_message")\
        .eq("job_id", job_id)\
        .execute()
    
    print(f"Found {len(logs.data)} log entries.")
    
    failed = [l for l in logs.data if l['status'] == 'failed']
    print(f"Failed count: {len(failed)}")
    
    if failed:
        print("\nSAMPLE ERRORS:")
        for f in failed[:5]:
            print(f"File: {f['file_path']}")
            print(f"  Error: {f['error_type']} - {f['error_message']}")
            print("-" * 20)

if __name__ == "__main__":
    check_latest_errors()
