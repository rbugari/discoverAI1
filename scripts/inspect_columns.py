import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    print("Fetching one row from 'solutions' to see columns...")
    res = supabase.from_("solutions").select("*").limit(1).execute()
    if res.data:
        print(f"Data found: {res.data[0]}")
    else:
        print("Table is empty. Trying to guess columns...")
        # PostgREST doesn't easily expose schema via client without data
        # Let's try to select specific common names
        for col in ["id", "name", "description", "status", "storage_path", "created_at", "project_id"]:
            try:
                supabase.from_("solutions").select(col).limit(1).execute()
                print(f"Column '{col}' EXISTS")
            except Exception as e:
                print(f"Column '{col}' NOT FOUND or error: {str(e)[:50]}...")
except Exception as e:
    print(f"Error: {e}")
