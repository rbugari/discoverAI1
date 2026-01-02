import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

job_id = 'e94e55b7-4632-4230-a667-6c2fc1bfe01a'

res = supabase.table("job_run").select("*").eq("job_id", job_id).single().execute()
if res.data:
    j = res.data
    print(f"JOB_ID: {j['job_id']}")
    print(f"STATUS: {j['status']}")
    print(f"STAGE: {j['current_stage']}")
    print(f"ERR_MSG: {j['error_message']}")
    print(f"ERR_DTL: {j['error_details']}")
    
    # Check if there are any worker logs in file_processing_log
    log_res = supabase.table("file_processing_log").select("*").eq("job_id", job_id).execute()
    print(f"FILE_LOGS: {len(log_res.data)}")
    for l in log_res.data[:5]:
        print(f" - {l['status']} | {l['file_path']} | {l['error_message']}")
else:
    print("Job not found")
