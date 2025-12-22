import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

print(f"Connecting to Neo4j at: {uri} with user {user}")

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    print("Connection Successful!")
    
    # Test a simple query
    with driver.session() as session:
        result = session.run("RETURN 'Hello Nexus' AS message")
        msg = result.single()["message"]
        print(f"Database says: {msg}")
        
    driver.close()
except Exception as e:
    print(f"Connection failed: {e}")
