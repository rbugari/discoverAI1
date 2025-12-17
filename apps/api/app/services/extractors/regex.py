import re
import os
import uuid
from .base import BaseExtractor
from ...models.extraction import ExtractionResult, ExtractedNode, ExtractedEdge, Evidence, Locator

class RegexExtractor(BaseExtractor):
    def extract(self, file_path: str, content: str) -> ExtractionResult:
        ext = os.path.splitext(file_path)[1].lower()
        
        nodes = []
        edges = []
        evidences = []
        
        # Self Node (The file itself)
        # We assume the caller handles the main file node creation usually, but here we emit it to be safe/complete.
        # However, LLM extractor usually returns the file node too.
        file_node_id = f"file::{file_path}"
        nodes.append(ExtractedNode(
            node_id=file_node_id,
            node_type="FILE",
            name=os.path.basename(file_path),
            system="files",
            attributes={"path": file_path, "extension": ext}
        ))
        
        if ext == '.py':
            self._extract_python(file_path, content, file_node_id, nodes, edges, evidences)
        elif ext in ['.sql', '.hql']:
            self._extract_sql(file_path, content, file_node_id, nodes, edges, evidences)
            
        # Deduplicate nodes by ID just in case
        unique_nodes = {n.node_id: n for n in nodes}.values()
        
        return ExtractionResult(
            meta={"source_file": file_path, "extractor_id": "regex_v1"},
            nodes=list(unique_nodes),
            edges=edges,
            evidences=evidences,
            assumptions=[]
        )

    def _extract_python(self, file_path, content, from_id, nodes, edges, evidences):
        # Imports: from x import y OR import x
        import_pattern = re.compile(r'^\s*(?:from|import)\s+([\w\.]+)', re.MULTILINE)
        
        for match in import_pattern.finditer(content):
            lib_name = match.group(1)
            target_id = f"lib::{lib_name}"
            
            # Evidence
            ev_id = str(uuid.uuid4())
            locator = Locator(
                file=file_path,
                line_start=content.count('\n', 0, match.start()) + 1,
                line_end=content.count('\n', 0, match.end()) + 1
            )
            evidences.append(Evidence(
                evidence_id=ev_id,
                kind="regex_match",
                locator=locator,
                snippet=match.group(0).strip()
            ))
            
            # Edge
            edges.append(ExtractedEdge(
                edge_id=str(uuid.uuid4()),
                edge_type="DEPENDS_ON",
                from_node_id=from_id,
                to_node_id=target_id,
                confidence=0.8,
                rationale=f"Imported library {lib_name}",
                evidence_refs=[ev_id],
                is_hypothesis=False
            ))
            
            # Library Node
            nodes.append(ExtractedNode(
                node_id=target_id,
                node_type="PACKAGE",
                name=lib_name,
                system="python",
                attributes={}
            ))

    def _extract_sql(self, file_path, content, from_id, nodes, edges, evidences):
        # Tables (Simple FROM/JOIN)
        # Matches: FROM table_name, JOIN table_name
        table_pattern = re.compile(r'(?:FROM|JOIN)\s+([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)?)', re.IGNORECASE)
        
        for match in table_pattern.finditer(content):
            table_name = match.group(1)
            target_id = f"table::{table_name}"
            
            ev_id = str(uuid.uuid4())
            locator = Locator(
                file=file_path,
                line_start=content.count('\n', 0, match.start()) + 1,
                line_end=content.count('\n', 0, match.end()) + 1
            )
            evidences.append(Evidence(
                evidence_id=ev_id,
                kind="regex_match",
                locator=locator,
                snippet=match.group(0).strip()
            ))
            
            edges.append(ExtractedEdge(
                edge_id=str(uuid.uuid4()),
                edge_type="READS_FROM",
                from_node_id=from_id,
                to_node_id=target_id,
                confidence=0.8,
                rationale=f"SQL Query reads from {table_name}",
                evidence_refs=[ev_id],
                is_hypothesis=False
            ))
            
            nodes.append(ExtractedNode(
                node_id=target_id,
                node_type="TABLE",
                name=table_name,
                system="sql",
                attributes={}
            ))
