import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

project_id = '7021ac4b-921d-402f-bc21-1c63701b8180'
print(f"=== PATH VALIDATOR FOR SOLUTION {project_id} ===")

# 1. Fetch Solution Info
sol_res = supabase.table("solutions").select("*").eq("id", project_id).single().execute()
if sol_res.data:
    sol = sol_res.data
    path = sol.get("storage_path", "").strip()
    print(f"DB STORAGE PATH: '{path}'")
    
    if not path:
        print("ERROR: Storage path is EMPTY in DB")
    else:
        # Check if absolute
        if os.path.isabs(path):
            print(f"Path is ABSOLUTE. Checking existence...")
        else:
            print(f"Path is RELATIVE. This might be a problem if local worker is expected to find it.")
        
        if os.path.exists(path):
            print(f"✅ PATH EXISTS on this machine.")
            if os.path.isdir(path):
                print(f"✅ It is a DIRECTORY.")
                files = os.listdir(path)
                print(f"FOUND {len(files)} items in directory.")
                for f in files[:5]:
                    print(f"  - {f}")
            else:
                print(f"⚠️ It is a FILE, not a directory.")
        else:
            print(f"❌ PATH DOES NOT EXIST on this machine: {path}")

# 2. Check Latest Job Failure details again
job_res = supabase.table("job_run").select("*").eq("project_id", project_id).order("created_at", desc=True).limit(1).execute()
if job_res.data:
    j = job_res.data[0]
    print(f"\nLATEST JOB: {j['job_id']}")
    print(f"STATUS: {j['status']} | STAGE: {j['current_stage']}")
    print(f"ERR_MSG: {j['error_message']}")
    print(f"ERR_DTL: {j['error_details']}")
