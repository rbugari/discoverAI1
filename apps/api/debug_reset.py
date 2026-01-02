import os
from supabase import create_client
from dotenv import load_dotenv
from app.services.reset_service import NuclearResetService
import traceback

load_dotenv()

supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
reset_service = NuclearResetService(supabase)

solution_id = "7021ac4b-921d-402f-bc21-1c63701b8180"

print(f"Attempting manual reset for {solution_id}...")
try:
    success = reset_service.reset_solution_data(solution_id)
    print(f"Reset Success: {success}")
except Exception as e:
    print("Reset Failed with Exception:")
    traceback.print_exc()
