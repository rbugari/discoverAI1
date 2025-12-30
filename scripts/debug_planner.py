import asyncio
import os
import sys
import traceback
from dotenv import load_dotenv
from supabase import create_client

# Path setup
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))
os.chdir(os.path.join(os.getcwd(), "apps", "api"))

from app.services.planner import PlannerService
from app.config import settings

async def main():
    load_dotenv("../../.env")
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    planner = PlannerService(supabase)
    
    job_id = "54244643-f7a6-4685-831f-8222b0900b83"
    root_path = "c:/proyectos_dev/discoverIA - gravity/datosprueba/ssis_test/build-etl-using-ssis-main"
    
    print(f"DEBUG: Testing PlannerService.create_plan for job {job_id}")
    try:
        plan_id = planner.create_plan(job_id, root_path)
        print(f"DEBUG: Plan Created SUCCESS: {plan_id}")
    except Exception:
        print("DEBUG: Caught Exception in Planner!")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
