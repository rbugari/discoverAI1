import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")

supabase = create_client(url, key)

res = supabase.table("asset").select("asset_type").limit(10).execute()
print(res.data)
