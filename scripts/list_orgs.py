import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    print("Listing organizations...")
    res = supabase.from_("organizations").select("id, name").execute()
    print(f"Orgs found: {res.data}")
except Exception as e:
    print(f"Error: {e}")
