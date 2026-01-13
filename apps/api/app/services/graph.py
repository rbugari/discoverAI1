from abc import ABC, abstractmethod
from ..config import settings
import json
import time
from neo4j.exceptions import ServiceUnavailable, SessionExpired

class GraphService(ABC):
    @abstractmethod
    def upsert_node(self, label: str, properties: dict):
        pass

    @abstractmethod
    def upsert_relationship(self, source_props: dict, target_props: dict, rel_type: str):
        pass

    @abstractmethod
    def delete_solution_nodes(self, solution_id: str):
        pass

    @abstractmethod
    def get_graph_data(self, solution_file_path: str):
        pass

    @abstractmethod
    def get_subgraph(self, center_id: str, depth: int, limit: int):
        pass

    @abstractmethod
    def find_paths(self, from_id: str, to_id: str, max_hops: int):
        pass

class MockGraphService(GraphService):
    def __init__(self):
        print("Initialized Mock Graph Service (In-Memory)")
        self.nodes = []
        self.relationships = []

    def upsert_node(self, label: str, properties: dict):
        print(f"[MOCK GRAPH] Creating Node ({label}): {properties}")
        self.nodes.append({"label": label, **properties})

    def upsert_relationship(self, source_props: dict, target_props: dict, rel_type: str):
        print(f"[MOCK GRAPH] Creating Rel: {source_props.get('name')} -[:{rel_type}]-> {target_props.get('name')}")
        self.relationships.append({"source": source_props, "target": target_props, "type": rel_type})

    def delete_solution_nodes(self, solution_id: str):
        print(f"[MOCK GRAPH] Deleting nodes for solution {solution_id}")
        pass

    def get_graph_data(self, solution_file_path: str):
        return {"nodes": self.nodes, "edges": self.relationships}
        
    def get_subgraph(self, center_id: str, depth: int, limit: int):
        return {"nodes": self.nodes, "edges": self.relationships} # Mock returns all
        
    def find_paths(self, from_id: str, to_id: str, max_hops: int):
        return [] # Mock returns empty

class Neo4jGraphService(GraphService):
    def __init__(self):
        from neo4j import GraphDatabase
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI, 
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
    
    def close(self):
        self.driver.close()

    def _run_query_with_retry(self, query, params=None, max_retries=3):
        for attempt in range(max_retries):
            try:
                with self.driver.session() as session:
                    return list(session.run(query, **(params or {})))
            except (ServiceUnavailable, SessionExpired) as e:
                if attempt == max_retries - 1:
                    print(f"[NEO4J FATAL] Connection failed after {max_retries} attempts: {e}")
                    raise e
                print(f"[NEO4J WARNING] Connection failed ({e}). Retrying {attempt + 1}/{max_retries}...")
                time.sleep(2 * (attempt + 1))
            except Exception as e:
                print(f"[NEO4J ERROR] Unexpected error: {e}")
                raise e

    def upsert_node(self, label: str, properties: dict):
        # Simplified upsert logic
        # Ensure 'solution_id' is stored if available
        query = f"MERGE (n:{label} {{id: $id}}) SET n += $props"
        # Assuming 'id' is always in properties for uniqueness
        if 'id' not in properties:
             properties['id'] = properties.get('name', 'unknown')
             
        self._run_query_with_retry(query, params={"id": properties['id'], "props": properties})

    def upsert_relationship(self, source_props: dict, target_props: dict, rel_type: str):
        # This assumes nodes exist or uses merge
        query = f"""
        MATCH (a), (b)
        WHERE a.id = $source_id AND b.id = $target_id
        MERGE (a)-[r:{rel_type}]->(b)
        """
        source_id = source_props.get('id', source_props.get('name'))
        target_id = target_props.get('id', target_props.get('name'))
        
        self._run_query_with_retry(query, params={"source_id": source_id, "target_id": target_id})

    def delete_solution_nodes(self, solution_id: str):
        query = """
        MATCH (n)
        WHERE n.solution_id = $solution_id
        DETACH DELETE n
        """
        self._run_query_with_retry(query, params={"solution_id": solution_id})
        print(f"[NEO4J] Deleted nodes for solution {solution_id}")

    def _process_graph_query(self, query, params):
        nodes = {}
        edges = []
        
        try:
            records = self._run_query_with_retry(query, params=params)
            print(f"[NEO4J] Found {len(records)} records")
            
            for record in records:
                n = record["n"]
                m = record["m"]
                r = record["r"]
                
                # Safe property access
                n_props = dict(n) if n else {}
                m_props = dict(m) if m else {}
                
                # Ensure ID exists, fallback to element_id
                n_id = n_props.get("id")
                if not n_id: n_id = str(n.element_id)
                
                m_id = m_props.get("id")
                if not m_id: m_id = str(m.element_id)
                
                # Safe Label access
                n_label = list(n.labels)[0] if n.labels else "Unknown"
                m_label = list(m.labels)[0] if m.labels else "Unknown"
                
                # Use 'type' property if available, otherwise fallback to Label
                n_type = n_props.get("type", n_label)
                m_type = m_props.get("type", m_label)

                nodes[n_id] = {
                    "id": n_id, 
                    "data": {
                        "label": n_props.get("name", n_id), 
                        "type": n_type,
                        "summary": n_props.get("summary", ""),
                        "schema": n_props.get("schema_name", ""),
                        "columns": n_props.get("columns", [])
                    }
                }
                
                nodes[m_id] = {
                    "id": m_id, 
                    "data": {
                        "label": m_props.get("name", m_id), 
                        "type": m_type,
                        "summary": m_props.get("summary", ""),
                        "schema": m_props.get("schema_name", ""),
                        "columns": m_props.get("columns", [])
                    }
                }
                
                edges.append({
                    "id": str(r.element_id),
                    "source": n_id,
                    "target": m_id,
                    "label": r.type
                })
        except Exception as e:
            print(f"[NEO4J ERROR] {e}")
            return {"nodes": [], "edges": []}
                
        return {"nodes": list(nodes.values()), "edges": edges}

    def get_graph_data(self, solution_id: str):
        query = """
        MATCH (n)-[r]->(m)
        WHERE n.solution_id = $solution_id OR m.solution_id = $solution_id
        RETURN n, r, m
        LIMIT 5000
        """
        return self._process_graph_query(query, params={"solution_id": solution_id})

    def get_subgraph(self, center_id: str, depth: int, limit: int):
        query = f"""
        MATCH p = (n {{id: $center_id}})-[*1..{depth}]-(m)
        UNWIND relationships(p) AS rel
        WITH startNode(rel) AS a, rel, endNode(rel) AS b
        RETURN a AS n, rel AS r, b AS m
        LIMIT {limit}
        """
        return self._process_graph_query(query, params={"center_id": center_id})

    def find_paths(self, from_id: str, to_id: str, max_hops: int):
        query = f"""
        MATCH p = shortestPath((a {{id: $from_id}})-[*..{max_hops}]-(b {{id: $to_id}}))
        UNWIND relationships(p) AS rel
        WITH startNode(rel) AS a, rel, endNode(rel) AS b
        RETURN a AS n, rel AS r, b AS m
        """
        return self._process_graph_query(query, params={"from_id": from_id, "to_id": to_id})

class SupabaseGraphService(GraphService):
    def __init__(self):
        from supabase import create_client
        key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
        self.client = create_client(settings.SUPABASE_URL, key)
        print("[SUPABASE GRAPH] Initialized")

    def upsert_node(self, label: str, properties: dict):
        # No-op for now, managed by CatalogService
        pass

    def upsert_relationship(self, source_props: dict, target_props: dict, rel_type: str):
        # No-op for now, managed by CatalogService
        pass

    def delete_solution_nodes(self, solution_id: str):
        # Managed by Cascade in DB or manual clean endpoint
        pass

    def get_graph_data(self, solution_id: str, mode: str = "GLOBAL", package_id: str = None):
        """
        Fetches graph data based on perspective mode.
        - GLOBAL: All assets and edges.
        - ARCHITECTURE: Package-to-Package dependencies (based on common assets).
        - PACKAGE: Components and context of a specific package.
        """
        print(f"[SUPABASE GRAPH] Fetching {mode} graph for {solution_id}")

        if mode == "ARCHITECTURE":
            return self._get_architecture_graph(solution_id)
        elif mode == "PACKAGE" and package_id:
            return self._get_package_graph(solution_id, package_id)
        
        # DEFAULT: GLOBAL
        # 1. Fetch Assets (Nodes)
        assets_res = self.client.table("asset").select("*").eq("project_id", solution_id).execute()
        assets = assets_res.data or []
        
        # 2. Fetch Edges
        edges_res = self.client.table("edge_index").select("*").eq("project_id", solution_id).execute()
        edges = edges_res.data or []
        
        return self._transform_to_cytoscape(assets, edges)

    def _get_architecture_graph(self, solution_id: str):
        """
        Returns a high-level graph where nodes are Packages and edges 
        represent Data Flow (Package A -> Asset -> Package B).
        """
        # 1. Fetch Packages as Nodes
        pkg_res = self.client.table("package").select("*").eq("project_id", solution_id).execute()
        packages = pkg_res.data or []
        
        # 2. Fetch Edges to infer package links
        # We look for flows where a Package (or its components) interacts with external assets
        # For ARCHITECTURE, we treat Packages as the primary nodes.
        nodes = []
        for p in packages:
            nodes.append({
                "id": str(p["package_id"]),
                "data": {
                    "label": p["name"],
                    "type": "PACKAGE",
                    "system": p.get("type", "unknown"),
                    "summary": p.get("description", "")
                }
            })

        # 3. Infer links between packages
        # A link A -> B exists if:
        # Asset T is WRITTEN_BY A and READ_BY B
        # Let's fetch all column lineage for the project
        lin_res = self.client.table("column_lineage").select("source_asset_id, target_asset_id, package_id").eq("project_id", solution_id).execute()
        lineages = lin_res.data or []

        # Map Asset -> [Packages that write to it]
        # Map Asset -> [Packages that read from it]
        writers = {}
        readers = {}

        for l in lineages:
            if not l["package_id"]: continue
            
            src = str(l["source_asset_id"]) if l["source_asset_id"] else None
            tgt = str(l["target_asset_id"]) if l["target_asset_id"] else None
            pkg = str(l["package_id"])

            if tgt:
                if tgt not in writers: writers[tgt] = set()
                writers[tgt].add(pkg)
            if src:
                if src not in readers: readers[src] = set()
                readers[src].add(pkg)

        edges = []
        visited_links = set()
        for asset, p_writers in writers.items():
            p_readers = readers.get(asset, set())
            for w in p_writers:
                for r in p_readers:
                    if w != r and f"{w}->{r}" not in visited_links:
                        edges.append({
                            "id": f"flow_{w}_{r}",
                            "source": w,
                            "target": r,
                            "label": "DATA_FLOW"
                        })
                        visited_links.add(f"{w}->{r}")

        return {"nodes": nodes, "edges": edges}

    def _get_package_graph(self, solution_id: str, package_id: str):
        """
        Returns a focused graph of a single package's internal components 
        plus its immediate input/output tables.
        """
        # 1. Fetch Package Assets (Components)
        # Components are bridged to 'asset' and tagged with package_id
        assets_res = self.client.table("asset").select("*").eq("project_id", solution_id).execute()
        all_assets = assets_res.data or []
        
        package_assets = [a for a in all_assets if a.get("tags", {}).get("package_id") == package_id]
        package_asset_ids = set(str(a["asset_id"]) for a in package_assets)

        # 2. Fetch edges where at least one end is in the package
        edges_res = self.client.table("edge_index").select("*").eq("project_id", solution_id).execute()
        all_edges = edges_res.data or []
        
        relevant_edges = []
        external_node_ids = set()
        for e in all_edges:
            src = str(e["from_asset_id"])
            tgt = str(e["to_asset_id"])
            if src in package_asset_ids or tgt in package_asset_ids:
                relevant_edges.append(e)
                if src not in package_asset_ids: external_node_ids.add(src)
                if tgt not in package_asset_ids: external_node_ids.add(tgt)

        # 3. Add external context nodes (Tables/Files)
        external_assets = [a for a in all_assets if str(a["asset_id"]) in external_node_ids]
        
        return self._transform_to_cytoscape(package_assets + external_assets, relevant_edges)

    def _transform_to_cytoscape(self, assets: list, edges: list):
        nodes_list = []
        for a in assets:
            tags = a.get("tags", {}) or {}
            nodes_list.append({
                "id": a["asset_id"],
                "data": {
                    "label": a["name_display"],
                    "type": a["asset_type"],
                    "system": a.get("system", "unknown"),
                    "tags": tags,
                    "parent_id": tags.get("parent_node_id"),
                    "schema": tags.get("schema", ""),
                    "columns": tags.get("columns", []),
                    "summary": tags.get("description", "") or tags.get("summary", "")
                }
            })
            
        edges_list = []
        for e in edges:
            edges_list.append({
                "id": e["edge_id"],
                "source": e["from_asset_id"],
                "target": e["to_asset_id"],
                "label": e["edge_type"],
                "data": {
                    "confidence": e.get("confidence", 1.0),
                    "is_hypothesis": e.get("is_hypothesis", False),
                    "rationale": e.get("rationale", None)
                }
            })
            
        return {"nodes": nodes_list, "edges": edges_list}

    def get_subgraph(self, center_id: str, depth: int, limit: int):
        # (Recursive neighbors logic remains similar but uses _transform_to_cytoscape)
        out_edges = self.client.table("edge_index").select("*").eq("from_asset_id", center_id).execute().data or []
        in_edges = self.client.table("edge_index").select("*").eq("to_asset_id", center_id).execute().data or []
        all_edges = out_edges + in_edges
        node_ids = set([center_id] + [e["from_asset_id"] for e in all_edges] + [e["to_asset_id"] for e in all_edges])
        assets = self.client.table("asset").select("*").in_("asset_id", list(node_ids)).execute().data or []
        return self._transform_to_cytoscape(assets, all_edges)

    def find_paths(self, from_id: str, to_id: str, max_hops: int):
        return {"nodes": [], "edges": []}

    def find_paths(self, from_id: str, to_id: str, max_hops: int):
        # Not implemented for SQL yet (requires recursive query)
        return {"nodes": [], "edges": []}

def get_graph_service() -> GraphService:
    print(f"[GRAPH SERVICE] Mode: {settings.GRAPH_MODE}")
    print(f"[GRAPH SERVICE] URI: {settings.NEO4J_URI}")
    
    if settings.GRAPH_MODE == "NEO4J":
        try:
            return Neo4jGraphService()
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}. Falling back to SUPABASE.")
            return SupabaseGraphService()
    elif settings.GRAPH_MODE == "SUPABASE":
        return SupabaseGraphService()
    else:
        # Default to Supabase instead of Mock if not specified, assuming we want persistence
        # Or keep Mock if explicitly MOCK
        if settings.GRAPH_MODE == "MOCK":
            return MockGraphService()
        else:
            print(f"Unknown GRAPH_MODE '{settings.GRAPH_MODE}'. Defaulting to SUPABASE.")
            return SupabaseGraphService()
