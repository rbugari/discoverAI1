import os
import requests
import uuid
import time
from supabase import create_client
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API_URL = "http://localhost:8001"

print(f"Connecting to Supabase at: {SUPABASE_URL}")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. Verification of the 'solutions' table
try:
    print("Verifying 'solutions' table...")
    test_res = supabase.from_("solutions").select("id").limit(1).execute()
    print(f"Connection OK. Tables visible.")
except Exception as e:
    print(f"Critical Error: Cannot access 'solutions' table: {e}")
    exit(1)

# 2. Prepare Data
solution_id = str(uuid.uuid4())
# Ensure this path is correct for your system
local_path = r"c:\proyectos_dev\discoverIA - gravity\datosprueba\build-etl-using-ssis-main.zip"

sol_data = {
    "id": solution_id,
    "org_id": "6983a04b-45c2-4213-9d0a-2f6aa9ed85c8",
    "name": "V4 Test - SSIS Deep Dive",
    "status": "PROCESSING",
    "storage_path": f"local://{local_path}"
}

print(f"Creating test solution: {solution_id}")

# 3. Insert using .table() (Standard)
try:
    res = supabase.table("solutions").insert(sol_data).execute()
    if res.data:
        print("✅ Solution created successfully.")
    else:
        print(f"❌ Error: No data returned. Response: {res}")
        exit(1)
except Exception as e:
    print(f"❌ Error inserting solution: {e}")
    print("Trying alternative method...")
    try:
        # Some versions/proxies prefer directly adding solution_id if 'id' is pk
        res = supabase.from_("solutions").insert(sol_data).execute()
        print("✅ Insert successful with alternative method.")
    except Exception as e2:
        print(f"❌ All insert attempts failed: {e2}")
        exit(1)

# 4. Trigger Analysis via API
print(f"Triggering analysis for solution {solution_id}...")
# Wait a bit for Supabase to persist
time.sleep(1)

try:
    resp = requests.post(f"{API_URL}/solutions/{solution_id}/analyze", json={"mode": "full"})
    if resp.status_code == 200:
        print(f"✅ API Response: {resp.json()}")
        print(f"\nSUCCESS! Viewing results at: http://localhost:3000/solutions/{solution_id}")
    else:
        print(f"⚠️ Warning: API returned {resp.status_code}: {resp.text}")
except Exception as e:
    print(f"❌ Error calling API: {e}")
    print("Make sure the backend is running with: python -m uvicorn app.main:app")
