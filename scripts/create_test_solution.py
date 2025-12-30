import os
from supabase import create_client
from dotenv import load_dotenv
import uuid

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
s = create_client(url, key)

sol_id = str(uuid.uuid4())
org_id = "6983a04b-45c2-4213-9d0a-2f6aa9ed85c8" # ID from existing solution
try:
    res = s.table("solutions").insert({
        "id": sol_id,
        "org_id": org_id,
        "name": "SSIS v4 Test Final",
        "status": "READY",
        "storage_path": "c:/proyectos_dev/discoverIA - gravity/datosprueba/ssis_test/build-etl-using-ssis-main"
    }).execute()
    print(f"SUCCESS:{sol_id}")
except Exception as e:
     print(f"ERROR:{e}")
