import sys
import os

# Add apps/api to path
sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))

from app.services.extractors.sql_glot import SqlGlotExtractor

def test_sql():
    path = r"apps\api\temp_uploads\build-etl-using-ssis-main\build-etl-using-ssis-main\Scripts\AVW_datawarehouse_createDatabase.sql"
    with open(path, 'r') as f:
        content = f.read()
        
    extractor = SqlGlotExtractor()
    result = extractor.extract(path, content)
    
    print(f"Nodes found: {len(result.nodes)}")
    for node in result.nodes:
        print(f" - {node.node_type}: {node.name}")
        
    print(f"Edges found: {len(result.edges)}")
    for edge in result.edges:
        print(f" - {edge.edge_type}: {edge.from_node_id} -> {edge.to_node_id}")

if __name__ == "__main__":
    test_sql()