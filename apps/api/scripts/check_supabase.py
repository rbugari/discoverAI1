import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

print(f"Connecting to Supabase at: {url}")

try:
    supabase: Client = create_client(url, key)
    # Try to select from a table that might exist or just check auth
    # Since we haven't run migration yet, tables might not exist.
    # We can check if we get a response, even an error is a sign of connection.
    response = supabase.table("organizations").select("*").limit(1).execute()
    print("Connection Successful!")
    print(f"Data: {response.data}")
except Exception as e:
    print(f"Connection attempted but encountered an error (this might be normal if tables aren't created yet): {e}")
