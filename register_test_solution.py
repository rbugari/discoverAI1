import asyncio
import uuid
from supabase import create_client
from apps.api.app.config import settings

async def register_test_solution():
    print("📝 Registering Test Solution in Supabase...")
    
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    # 0. Cleanup (Optional)
    # print("Cleaning old test solutions...")
    # supabase.from_('solutions').delete().ilike('name', '%Test Run%').execute()

    # 1. Get or Create Organization
    org_id = ''
    orgs = supabase.from_('organizations').select('id').limit(1).execute()
    if orgs.data:
        org_id = orgs.data[0]['id']
    else:
        new_org = supabase.from_('organizations').insert({'name': 'Test Org'}).execute()
        org_id = new_org.data[0]['id']
        
    # 2. Create Solution Record
    solution_id = str(uuid.uuid4())
    
    # Absolute path to the test zip
    zip_path = r"c:\proyectos_dev\discoverIA\datosprueba\build-etl-using-ssis-main.zip"
    
    data = {
        "id": solution_id,
        "name": "SQLGlot Test Run (SSIS)",
        "org_id": org_id,
        "status": "QUEUED", # Set to QUEUED so the Worker picks it up
        "storage_path": f"local://{zip_path}"
    }
    
    res = supabase.from_('solutions').insert(data).execute()
    
    # 3. Create Job Run to trigger worker
    job_data = {
        "project_id": solution_id,
        "status": "queued",
        "current_stage": "ingest"
    }
    job_res = supabase.table("job_run").insert(job_data).execute()
    new_job_id = job_res.data[0]["job_id"]
    
    # 4. Enqueue in SQL Queue
    from apps.api.app.services.queue import SQLJobQueue
    queue = SQLJobQueue()
    queue.enqueue_job(new_job_id)
    
    print(f"✅ Created Solution: {data['name']}")
    print(f"🆔 ID: {solution_id}")
    print(f"👷 Job Queued: {new_job_id}")
    print(f"🔗 View Graph at: http://localhost:3000/solutions/{solution_id}")

if __name__ == "__main__":
    asyncio.run(register_test_solution())