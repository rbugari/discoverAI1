import sys
import os
from dotenv import load_dotenv

# Add parent dir to path to import app modules
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))

# Load .env
load_dotenv()

from app.config import settings
from supabase import create_client

def verify():
    print(f"Supabase URL: {settings.SUPABASE_URL}")
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        print("Error: SUPABASE_URL or SUPABASE_KEY not set.")
        return

    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    try:
        res = supabase.table("solutions").select("id, name, status").execute()
        print("\nAvailable Solutions for testing:")
        for row in res.data:
            print(f"- {row['name']} (ID: {row['id']}, Status: {row['status']})")
    except Exception as e:
        print(f"Error querying solutions: {e}")

if __name__ == "__main__":
    verify()
