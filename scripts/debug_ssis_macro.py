
import os
import sys

# Add the apps/api directory to sys.path so we can import 'app' modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/api')))

from app.services.extractors.ssis_deep import SSISDeepExtractor
from app.models.extraction import ExtractionResult

def verify_macro():
    # Path to the specific .dtsx file we know exists
    file_path = r"c:\proyectos_dev\discoverIA - gravity\apps\api\temp_uploads\1765870044878_build-etl-using-ssis-main\build-etl-using-ssis-main\Package-SSIS\ETL_nexttime.dtsx"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    print(f"Reading file: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    extractor = SSISDeepExtractor()
    print("\n--- Testing extract_macro ---")
    
    try:
        result = extractor.extract(file_path, content)
        
        if not result:
            print("❌ extract_macro returned None")
            return

        print(f"✅ Extraction Result Type: {type(result)}")
        
        if hasattr(result, 'nodes'):
            print(f"Found {len(result.nodes)} nodes:")
            for node in result.nodes:
                print(f"  - [{node.node_type}] {node.name} (ID: {node.node_id}) Attrs: {node.attributes}")
        
        if hasattr(result, 'edges'):
             print(f"Found {len(result.edges)} edges:")
             for edge in result.edges:
                 print(f"  - [{edge.edge_type}] {edge.from_node_id} -> {edge.to_node_id} (Reason: {edge.rationale})")
        else:
             print("❌ Result object has no 'edges' attribute")

    except Exception as e:
        print(f"❌ Exception during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_macro()
