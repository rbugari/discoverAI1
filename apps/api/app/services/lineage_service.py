from supabase import Client
from typing import List, Dict, Any, Set
import uuid

class LineageService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def trace_column_upstream(self, project_id: str, asset_id: str, column_name: str, max_depth: int = 5) -> Dict[str, Any]:
        """
        Recursively traces the origins of a column upstream.
        Returns a graph of (Asset, Column) nodes and their transformation edges.
        """
        nodes = []
        edges = []
        visited = set() # (asset_id, column_name)

        # Queue for BFS: (asset_id, column_name, current_depth)
        queue = [(asset_id, column_name, 0)]
        
        # Add start node
        start_node_id = f"{asset_id}:{column_name}"
        
        while queue:
            curr_asset_id, curr_col, depth = queue.pop(0)
            node_key = f"{curr_asset_id}:{curr_col}"
            
            if node_key in visited or depth > max_depth:
                continue
                
            visited.add(node_key)
            
            # 1. Fetch Asset Metadata to get a nice label
            asset_res = self.supabase.table("asset").select("name_display, asset_type").eq("asset_id", curr_asset_id).single().execute()
            asset_name = asset_res.data["name_display"] if asset_res.data else "Unknown"
            asset_type = asset_res.data["asset_type"] if asset_res.data else "TABLE"
            
            nodes.append({
                "id": node_key,
                "asset_id": curr_asset_id,
                "asset_name": asset_name,
                "asset_type": asset_type,
                "column_name": curr_col,
                "depth": depth
            })

            # 2. Find Upstream Lineage
            # Source: source_asset_id, source_column
            # Target: target_asset_id, target_column
            # We are tracing UPSTREAM, so we look for rows where TARGET = our current
            lineage_res = self.supabase.table("column_lineage")\
                .select("*")\
                .eq("project_id", project_id)\
                .eq("target_asset_id", curr_asset_id)\
                .eq("target_column", curr_col)\
                .execute()
            
            for row in (lineage_res.data or []):
                src_asset_id = row.get("source_asset_id")
                src_col = row.get("source_column")
                
                if not src_asset_id or not src_col:
                    continue
                
                upstream_key = f"{src_asset_id}:{src_col}"
                
                edges.append({
                    "id": row["lineage_id"],
                    "source": upstream_key,
                    "target": node_key,
                    "transformation_rule": row.get("transformation_rule"),
                    "confidence": row.get("confidence", 1.0)
                })
                
                queue.append((src_asset_id, src_col, depth + 1))

        return {
            "nodes": nodes,
            "edges": edges
        }
