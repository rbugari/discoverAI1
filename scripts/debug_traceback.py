import asyncio
import os
import sys
import traceback
from dotenv import load_dotenv

# Path setup
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))
os.chdir(os.path.join(os.getcwd(), "apps", "api"))

from app.worker import process_job

async def main():
    job_id = "54244643-f7a6-4685-831f-8222b0900b83"
    print(f"DEBUG: Manually triggering job {job_id}")
    job_item = {"id": "f21464af-2e39-40c9-80b0-0fa3361d221e", "job_id": job_id}
    
    try:
        await process_job(job_item)
        print("DEBUG: Processing completed (or Paused)")
    except Exception:
        print("DEBUG: Caught Exception in main!")
        traceback.print_exc()

if __name__ == "__main__":
    load_dotenv("../../.env")
    asyncio.run(main())
