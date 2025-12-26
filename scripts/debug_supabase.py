import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print(f"URL: {SUPABASE_URL}")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    print("Checking 'solutions' table...")
    res = supabase.table("solutions").select("id").limit(1).execute()
    print(f"Solutions: {len(res.data)} found.")
except Exception as e:
    print(f"Error checking solutions: {e}")

try:
    print("Checking 'package' table...")
    res = supabase.table("package").select("package_id").limit(1).execute()
    print(f"Package table found. Data: {res.data}")
except Exception as e:
    print(f"Error checking package: {e}")

try:
    print("Checking 'column_lineage' table...")
    res = supabase.table("column_lineage").select("lineage_id").limit(1).execute()
    print(f"Column Lineage table found. Data: {res.data}")
except Exception as e:
    print(f"Error checking column_lineage: {e}")
