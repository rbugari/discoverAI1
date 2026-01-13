import sys
import os
import json
import logging

# Ensure app is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '../apps/api'))

from app.services.extractors.registry import ExtractorRegistry

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestSSIS")

def test_extraction():
    # Path to a sample file we found earlier
    sample_file = r"c:\proyectos_dev\discoverIA - gravity\dump_sample_ssis.dtsx"
    
    # Check if a sample exists, if not we might need to point to one of the temp_uploads
    # Found: discoverIA - back 1\temp_inspect\build-etl-using-ssis-main\Package-SSIS\ETL_nexttime.dtsx
    # Let's use a robust path or search
    
    candidates = [
        r"c:\proyectos_dev\discoverIA - gravity\apps\api\temp_uploads\1765870044878_build-etl-using-ssis-main\build-etl-using-ssis-main\Package-SSIS\ETL_nexttime.dtsx"
    ]
    
    target_file = None
    for c in candidates:
        if os.path.exists(c):
            target_file = c
            break
            
    if not target_file:
        logger.error("No sample file found to test!")
        # Fallback to creating a dummy one if needed, but better to use existing
        return

    logger.info(f"Testing extraction on: {target_file}")
    
    registry = ExtractorRegistry()
    
    with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        
    result = registry.extract(target_file, content)
    
    if result:
        logger.info("Extraction Successful!")
        logger.info(f"Package Name: {result.package.name}")
        logger.info(f"Component Count: {len(result.components)}")
        logger.info(f"Transformation Count: {len(result.transformations)}")
        
        # Print first few components
        for i, comp in enumerate(result.components[:5]):
            logger.info(f"[{i}] {comp.name} ({comp.type})")
            
        print(json.dumps(result.dict(exclude_none=True), indent=2, default=str))
    else:
        logger.error("Extraction returned None")

if __name__ == "__main__":
    test_extraction()
