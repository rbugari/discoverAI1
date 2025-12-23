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

def check_errors(job_id):
    print(f"--- ERRORS FOR JOB {job_id} ---")
    logs = supabase.table("file_processing_log")\
        .select("file_path, error_type, error_message, status")\
        .eq("job_id", job_id)\
        .eq("status", "failed")\
        .limit(10).execute()
        
    if not logs.data:
        print("No error logs found for this job ID in file_processing_log.")
        return

    for l in logs.data:
        print(f"File: {l['file_path']}")
        print(f"  Error Type: {l['error_type']}")
        print(f"  Error Msg: {l['error_message']}")
        print("-" * 20)

if __name__ == "__main__":
    job_id = "3d93f6a2-4035-4857-a7b9-27d28a8649a9" # Latest failed job
    check_errors(job_id)
