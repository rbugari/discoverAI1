from supabase import Client
from ..models.extraction import ExtractionResult, ExtractedNode, ExtractedEdge, Evidence
from ..models.deep_dive import DeepDiveResult, Package, PackageComponent, TransformationIR, ColumnLineage
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
                # Update existing asset (Upsert logic)
                self.supabase.table("asset").update({
                    "tags": node.attributes,
                    "updated_at": "now()",
                    "system": node.system
                }).eq("asset_id", asset_id).execute()
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
            # Check if evidence exists (hash + file + project)? 
            # For now, simplistic check or just insert (assuming 'Update' might want history)
            # But to avoid duplicates on re-run, we should check.
            # Using hash if available
            existing_ev = None
            if ev.hash:
                existing_ev = self.supabase.table("evidence")\
                    .select("evidence_id")\
                    .eq("project_id", project_id)\
                    .eq("hash", ev.hash)\
                    .eq("file_path", result.meta.get("source_file"))\
                    .execute()
            
            if existing_ev and existing_ev.data:
                ev_uuid = existing_ev.data[0]["evidence_id"]
            else:
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
                
            # Check existing edge
            existing_edge = self.supabase.table("edge_index")\
                .select("edge_id")\
                .eq("project_id", project_id)\
                .eq("from_asset_id", from_uuid)\
                .eq("to_asset_id", to_uuid)\
                .eq("edge_type", edge.edge_type)\
                .execute()
            
            if existing_edge.data:
                edge_uuid = existing_edge.data[0]["edge_id"]
                # Update confidence/metadata
                self.supabase.table("edge_index").update({
                    "confidence": edge.confidence,
                    "is_hypothesis": edge.is_hypothesis,
                    "extractor_id": result.meta.get("extractor_id")
                }).eq("edge_id", edge_uuid).execute()
            else:
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
                    # Check link existence to avoid PK violation if (edge_id, evidence_id) is PK
                    # Assuming edge_evidence has no ID or composite PK.
                    # Best effort: delete and re-insert or ignore error.
                    # Or check first.
                    ev_uuid = evidence_id_map[ref]
                    try:
                        self.supabase.table("edge_evidence").insert({
                            "edge_id": edge_uuid,
                            "evidence_id": ev_uuid
                        }).execute()
                    except:
                        pass # Ignore duplicate link error
                    
        return node_id_map

    def sync_deep_dive_result(self, result: DeepDiveResult, project_id: str):
        """
        Writes packages, components, transformations, and lineage to the SQL Catalog.
        """
        # 1. Package
        pkg = result.package
        pkg_data = pkg.model_dump()
        # Ensure dates are strings or handled by JSON
        pkg_data["created_at"] = pkg_data["created_at"].isoformat()
        pkg_data["updated_at"] = pkg_data["updated_at"].isoformat()
        if pkg_data.get("package_id"): pkg_data["package_id"] = str(pkg_data["package_id"])
        if pkg_data.get("project_id"): pkg_data["project_id"] = str(pkg_data["project_id"])
        if pkg_data.get("asset_id"): pkg_data["asset_id"] = str(pkg_data["asset_id"])

        self.supabase.table("package").upsert(pkg_data).execute()

        # 2. Components
        comp_id_map = {} # local/input id to UUID if needed, but components should have UUIDs
        for comp in result.components:
            comp_data = comp.model_dump()
            comp_data["created_at"] = comp_data["created_at"].isoformat()
            if comp_data.get("component_id"): comp_data["component_id"] = str(comp_data["component_id"])
            if comp_data.get("package_id"): comp_data["package_id"] = str(comp_data["package_id"])
            if comp_data.get("parent_component_id"): comp_data["parent_component_id"] = str(comp_data["parent_component_id"])
            
            self.supabase.table("package_component").upsert(comp_data).execute()
        
        # 3. Transformation IR
        for ir in result.transformations:
            ir_data = ir.model_dump()
            ir_data["created_at"] = ir_data["created_at"].isoformat()
            if ir_data.get("ir_id"): ir_data["ir_id"] = str(ir_data["ir_id"])
            if ir_data.get("project_id"): ir_data["project_id"] = str(ir_data["project_id"])
            if ir_data.get("source_component_id"): ir_data["source_component_id"] = str(ir_data["source_component_id"])
            
            self.supabase.table("transformation_ir").upsert(ir_data).execute()

        # 4. Column Lineage
        for lin in result.lineage:
            lin_data = lin.model_dump()
            lin_data["created_at"] = lin_data["created_at"].isoformat()
            if lin_data.get("lineage_id"): lin_data["lineage_id"] = str(lin_data["lineage_id"])
            if lin_data.get("project_id"): lin_data["project_id"] = str(lin_data["project_id"])
            if lin_data.get("package_id"): lin_data["package_id"] = str(lin_data["package_id"])
            if lin_data.get("ir_id"): lin_data["ir_id"] = str(lin_data["ir_id"])
            if lin_data.get("source_asset_id"): lin_data["source_asset_id"] = str(lin_data["source_asset_id"])
            if lin_data.get("target_asset_id"): lin_data["target_asset_id"] = str(lin_data["target_asset_id"])
            
            self.supabase.table("column_lineage").upsert(lin_data).execute()

    def get_solution_context(self, project_id: str) -> dict:
        """
        Gathers all relevant context for the Reasoning Agent.
        """
        # 1. Assets Summary
        assets = self.supabase.table("asset").select("asset_type, count").eq("project_id", project_id).execute()
        
        # 2. Key Lineage
        edges = self.supabase.table("edge_index")\
            .select("edge_type, from_asset_id, to_asset_id, is_hypothesis, confidence")\
            .eq("project_id", project_id)\
            .order("confidence", desc=False)\
            .limit(100)\
            .execute()
            
        # 3. Packages
        packages = self.supabase.table("package").select("name, type").eq("project_id", project_id).execute()
        
        return {
            "inventory": assets.data,
            "hotspots": [e for e in edges.data if e["confidence"] < 0.7 or e["is_hypothesis"]],
            "packages": packages.data
        }
