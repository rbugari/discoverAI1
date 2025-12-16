from apps.api.app.config import settings
from neo4j import GraphDatabase

def debug_neo4j():
    print(f"Connecting to {settings.NEO4J_URI} as {settings.NEO4J_USER}")
    driver = GraphDatabase.driver(
        settings.NEO4J_URI, 
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    )
    
    with driver.session() as session:
        # Count nodes
        result = session.run("MATCH (n) RETURN count(n) as count")
        print(f"Total Nodes: {result.single()['count']}")
        
        # Count relationships
        result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
        print(f"Total Relationships: {result.single()['count']}")
        
        # Sample data
        print("\nSample Relationships:")
        result = session.run("MATCH (n)-[r]->(m) RETURN n.name, type(r), m.name LIMIT 5")
        for record in result:
            print(f"{record['n.name']} -[{record['type(r)']}]-> {record['m.name']}")

    driver.close()

if __name__ == "__main__":
    debug_neo4j()