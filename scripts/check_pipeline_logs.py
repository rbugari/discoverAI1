import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
s = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
job_id = "54244643-f7a6-4685-831f-8222b0900b83"

res = s.table("file_processing_log").select("file_path, status, error_message").eq("job_id", job_id).execute()
for l in res.data:
    print(f"[{l['status'].upper()}] {l['file_path']}")
    if l['error_message']:
        print(f"  Error: {l['error_message']}")
