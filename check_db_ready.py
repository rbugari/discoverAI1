import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("❌ Missing Supabase credentials")
    exit(1)

supabase = create_client(url, key)

try:
    # Try to select from job_queue
    print("Checking 'job_queue' table...")
    supabase.table("job_queue").select("count", count="exact").execute()
    print("✅ 'job_queue' table exists.")
    
    print("Checking 'asset' table...")
    supabase.table("asset").select("count", count="exact").execute()
    print("✅ 'asset' table exists.")
    
    print("🎉 Database seems ready!")
except Exception as e:
    print(f"❌ Database check failed: {e}")
    print("⚠️ Please run the migration 'migrations/01_init_schema.sql' in Supabase SQL Editor.")
