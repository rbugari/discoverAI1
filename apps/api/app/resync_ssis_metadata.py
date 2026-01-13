import os
import uuid
import json
from datetime import datetime
from app.services.extractors.ssis_deep import SSISDeepExtractor
from app.services.catalog import CatalogService
from app.config import get_settings

def resync():
    settings = get_settings()
    catalog = CatalogService()
    extractor = SSISDeepExtractor()
    
    project_id = "7021ac4b-921d-402f-bc21-1c63701b8180"
    storage_path = rf"c:\proyectos_dev\discoverIA - gravity\storage\{project_id}"
    
    if not os.path.exists(storage_path):
        print(f"Path not found: {storage_path}")
        return

    for root, dirs, files in os.walk(storage_path):
        for file in files:
            if file.endswith(".dtsx"):
                file_path = os.path.join(root, file)
                print(f"Reprocessing {file}...")
                
                # Extract
                result = extractor.extract_deep(file_path)
                if result:
                    # Sync using bridge logic
                    print(f"Syncing {len(result.components)} components for {file}...")
                    catalog.sync_deep_dive_result(uuid.UUID(project_id), result)

if __name__ == "__main__":
    resync()
