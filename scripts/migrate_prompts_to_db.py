import os
import uuid
import yaml
from dotenv import load_dotenv
from supabase import create_client

# Cargar variables de entorno (asumiendo que estamos en la raíz o similar)
# En una ejecución real, esto leería del .env
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_KEY must be set.")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

PROMPT_DIR = "apps/api/app/prompts"

def migrate():
    print(f"Migrating prompts from {PROMPT_DIR} to Supabase...")
    
    # Scan prompts directory
    for root, dirs, files in os.walk(PROMPT_DIR):
        for filename in files:
            if filename.endswith('.md') or filename.endswith('.txt'):
                file_path = os.path.join(root, filename)
                
                # Action name: subfolders/file.md -> subfolders.file
                rel_path = os.path.relpath(file_path, PROMPT_DIR)
                action_name = rel_path.replace('\\', '.').replace('/', '.')
                action_name = action_name.replace('.md', '').replace('.txt', '').replace('_', '.')
                
                # Clean "v3." or "v4." prefixes if they match the models.yml expectations or just keep them
                # models.yml uses "extract_lineage_package" but with prompt_file "prompts/v3/extract_lineage_package.txt"
                # Actually, let's keep the name as dot-separated relative path
                
                print(f"Migrating {rel_path} as {action_name}...")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 1. Upsert Prompt Layer
                supabase.table("prompt_layer").upsert({
                    "name": action_name,
                    "layer_type": "BASE", # Changed from "type" to "layer_type" to match schema
                    "content": content
                }, on_conflict="name").execute()
                
                # 2. Get the layer ID (if we didn't get it from upsert)
                l_res = supabase.table("prompt_layer").select("id").eq("name", action_name).single().execute()
                db_layer_id = l_res.data["id"]
                
                # 3. Upsert Action Config
                supabase.table("action_prompt_config").upsert({
                    "action_name": action_name,
                    "base_layer_id": db_layer_id
                }, on_conflict="action_name").execute()

    print("Migration complete.")

if __name__ == "__main__":
    migrate()
