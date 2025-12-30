import os
import sys
from pathlib import Path
from supabase import create_client, Client
from neo4j import GraphDatabase

# Add app to path
sys.path.append(str(Path(__file__).parent.parent))
from app.config import settings

def reset_neo4j():
    print("🧹 Cleaning Neo4j Graph...")
    try:
        driver = GraphDatabase.driver(
            settings.NEO4J_URI, 
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        driver.close()
        print("✅ Neo4j Cleaned.")
    except Exception as e:
        print(f"❌ Neo4j Clean Failed: {e}")

def reset_supabase():
    print("🧹 Cleaning Supabase Tables...")
    try:
        # Initialize Client
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        # Map tables to their Primary Keys for safe deletion
        table_pks = {
            "code_embeddings": "id",
            "column_lineage": "lineage_id",
            "transformation_ir": "ir_id",
            "package_component": "component_id",
            "package": "package_id",
            "file_processing_log": "id",
            "job_plan_item": "item_id",
            "job_plan_area": "area_id",
            "job_plan": "plan_id",
            "edge_evidence": "edge_id",
            "edge_index": "edge_id",
            "asset_version": "asset_version_id",
            "asset": "asset_id",
            "job_stage_run": "id",
            "job_queue": "id",
            "job_run": "job_id",
            "evidence": "evidence_id",
            "solutions": "id"
        }
        
        # Deletion order (child tables first)
        tables = [
            "code_embeddings",
            "column_lineage",
            "transformation_ir",
            "package_component",
            "package",
            "file_processing_log",
            "job_plan_item",
            "job_plan_area",
            "job_plan",
            "edge_evidence",
            "edge_index",
            "asset_version",
            "asset",
            "job_stage_run",
            "job_queue",
            "job_run",
            "evidence",
            "solutions"
        ]
        
        for table in tables:
            print(f"   Deleting {table}...")
            pk = table_pks.get(table, "id")
            try:
                # neq 0 uuid is a common way to select all. 
                # If PK is int, we might need neq 0. 
                # Using a dummy UUID for UUID columns.
                dummy_val = "00000000-0000-0000-0000-000000000000"
                if table == "jobs": # Legacy might be int? Let's assume UUID as per migration usually
                     pass 
                
                supabase.table(table).delete().neq(pk, dummy_val).execute()
            except Exception as e:
                print(f"⚠️ Failed to delete {table} (PK: {pk}): {e}")

        print("✅ Supabase Cleaned.")
    except Exception as e:
        print(f"❌ Supabase Clean Failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting System Reset...")
    reset_neo4j()
    reset_supabase()
    print("✨ System Reset Complete.")
