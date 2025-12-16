import asyncio
import uuid
from supabase import create_client
from apps.api.app.config import settings

async def register_test_solution():
    print("📝 Registering Test Solution in Supabase...")
    
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    # 1. Get or Create Organization
    org_id = ''
    orgs = supabase.from_('organizations').select('id').limit(1).execute()
    if orgs.data:
        org_id = orgs.data[0]['id']
    else:
        new_org = supabase.from_('organizations').insert({'name': 'Test Org'}).execute()
        org_id = new_org.data[0]['id']
        
    # 2. Create Solution Record
    # We use a real UUID
    solution_id = str(uuid.uuid4())
    
    data = {
        "id": solution_id,
        "name": "Local Test Run (SSIS)",
        "org_id": org_id,
        "status": "READY", # Mark as READY since we already ran the analysis manually
        "storage_path": "manual/local-test.zip"
    }
    
    res = supabase.from_('solutions').insert(data).execute()
    
    print(f"✅ Created Solution: {data['name']}")
    print(f"🆔 ID: {solution_id}")
    print(f"🔗 View Graph at: http://localhost:3000/solutions/{solution_id}")

if __name__ == "__main__":
    asyncio.run(register_test_solution())