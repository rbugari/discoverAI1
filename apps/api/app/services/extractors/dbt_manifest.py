import json
import uuid
import logging
from typing import Dict, Any
from .base import BaseExtractor
from ...models.extraction import ExtractionResult, ExtractedNode, ExtractedEdge, Evidence, Locator

logger = logging.getLogger(__name__)

class DbtManifestExtractor(BaseExtractor):
    def extract(self, file_path: str, content: str) -> ExtractionResult:
        """
        Parses dbt manifest.json and extracts nodes (models, seeds, sources) 
        and edges (depends_on).
        """
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse dbt manifest: {file_path}")
            return ExtractionResult(meta={"error": "invalid json"}, nodes=[], edges=[], evidences=[])

        nodes = []
        edges = []
        evidences = []
        
        # 1. Process dbt Nodes (Models, Seeds, Tests, etc.)
        dbt_nodes = data.get("nodes", {})
        for key, node_data in dbt_nodes.items():
            if node_data.get("resource_type") not in ["model", "seed", "source"]:
                continue
                
            node_id = str(uuid.uuid4())
            nodes.append(ExtractedNode(
                node_id=node_id,
                node_type="table" if node_data["resource_type"] in ["model", "seed"] else "source",
                name=node_data.get("name"),
                system="dbt",
                attributes={
                    "dbt_unique_id": key,
                    "database": node_data.get("database"),
                    "schema": node_data.get("schema"),
                    "description": node_data.get("description"),
                    "tags": node_data.get("tags")
                }
            ))
            
            # Map unique_id to our node_id for edge creation
            node_data["_nexus_id"] = node_id

        # 2. Process Sources
        sources = data.get("sources", {})
        for key, src_data in sources.items():
            node_id = str(uuid.uuid4())
            nodes.append(ExtractedNode(
                node_id=node_id,
                node_type="source",
                name=f"{src_data.get('source_name')}.{src_data.get('name')}",
                system="dbt",
                attributes={
                    "dbt_unique_id": key,
                    "database": src_data.get("database"),
                    "schema": src_data.get("schema")
                }
            ))
            src_data["_nexus_id"] = node_id

        # 3. Process Edges (Depends On)
        # Helper map
        all_dbt_resources = {**dbt_nodes, **sources}
        
        for key, node_data in dbt_nodes.items():
            nexus_id = node_data.get("_nexus_id")
            if not nexus_id: continue
            
            depends_on = node_data.get("depends_on", {}).get("nodes", [])
            for dep_key in depends_on:
                dep_node = all_dbt_resources.get(dep_key)
                if dep_node and dep_node.get("_nexus_id"):
                    edges.append(ExtractedEdge(
                        edge_id=str(uuid.uuid4()),
                        edge_type="DEPENDS_ON",
                        from_node_id=nexus_id,
                        to_node_id=dep_node["_nexus_id"],
                        confidence=1.0,
                        rationale=f"dbt manifest dependency: {key} -> {dep_key}"
                    ))

        return ExtractionResult(
            meta={"extractor": "DbtManifestExtractor", "source_file": file_path},
            nodes=nodes,
            edges=edges,
            evidences=[]
        )
