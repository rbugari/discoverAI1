from supabase import Client
from ..models.extraction import ExtractionResult, ExtractedNode, ExtractedEdge, Evidence
import uuid

class CatalogService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def sync_extraction_result(self, result: ExtractionResult, project_id: str, artifact_id: str = None):
        """
        Writes nodes, edges, and evidences to the SQL Catalog.
        """
        
        # 1. Assets (Nodes)
        node_id_map = {} # Map local node_id to UUID
        
        for node in result.nodes:
            # Check if asset exists by canonical name? 
            # For now, generate a UUID or use a stable hash?
            # MD says: "asset_id uuid pk". "Reutilizar asset_id como ID estable".
            
            # Simple deduplication strategy: project_id + name + type
            # We will use upsert based on name/type if possible, but asset_id is PK.
            # Supabase upsert requires ON CONFLICT.
            # If we don't have a unique constraint on (project_id, name, type), upsert won't work easily without fetching.
            
            # Let's try to find existing asset
            existing = self.supabase.table("asset")\
                .select("asset_id")\
                .eq("project_id", project_id)\
                .eq("name_display", node.name)\
                .eq("asset_type", node.node_type)\
                .execute()
                
            if existing.data:
                asset_id = existing.data[0]["asset_id"]
            else:
                asset_id = str(uuid.uuid4())
                asset_data = {
                    "asset_id": asset_id,
                    "project_id": project_id,
                    "asset_type": node.node_type,
                    "name_display": node.name,
                    "canonical_name": node.name, # logic to canonicalize?
                    "system": node.system,
                    "tags": node.attributes,
                    "created_at": "now()",
                    "updated_at": "now()"
                }
                self.supabase.table("asset").insert(asset_data).execute()
                
            node_id_map[node.node_id] = asset_id
            
            # Asset Version? (Skip for MVP/Release A, stick to Asset)
            
        # 2. Evidences
        evidence_id_map = {}
        for ev in result.evidences:
            ev_uuid = str(uuid.uuid4())
            evidence_data = {
                "evidence_id": ev_uuid,
                "project_id": project_id,
                "artifact_id": artifact_id,
                "file_path": result.meta.get("source_file"),
                "kind": ev.kind,
                "locator": ev.locator.model_dump(),
                "snippet": ev.snippet,
                "hash": ev.hash
            }
            self.supabase.table("evidence").insert(evidence_data).execute()
            evidence_id_map[ev.evidence_id] = ev_uuid

        # 3. Edges
        for edge in result.edges:
            from_uuid = node_id_map.get(edge.from_node_id)
            to_uuid = node_id_map.get(edge.to_node_id)
            
            if not from_uuid or not to_uuid:
                continue # Skip if nodes not found
                
            edge_uuid = str(uuid.uuid4())
            edge_data = {
                "edge_id": edge_uuid,
                "project_id": project_id,
                "from_asset_id": from_uuid,
                "to_asset_id": to_uuid,
                "edge_type": edge.edge_type,
                "confidence": edge.confidence,
                "extractor_id": result.meta.get("extractor_id"),
                "is_hypothesis": edge.is_hypothesis
            }
            self.supabase.table("edge_index").insert(edge_data).execute()
            
            # Edge Evidence Link
            for ref in edge.evidence_refs:
                if ref in evidence_id_map:
                    link_data = {
                        "edge_id": edge_uuid,
                        "evidence_id": evidence_id_map[ref]
                    }
                    self.supabase.table("edge_evidence").insert(link_data).execute()
                    
        return node_id_map

