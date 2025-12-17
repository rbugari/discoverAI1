import os
import uuid
import re
import sqlglot
from sqlglot import exp
from .base import BaseExtractor
from ...models.extraction import ExtractionResult, ExtractedNode, ExtractedEdge, Evidence, Locator

class SqlGlotExtractor(BaseExtractor):
    def extract(self, file_path: str, content: str) -> ExtractionResult:
        nodes = []
        edges = []
        evidences = []
        
        file_node_id = f"file::{file_path}"
        ext = os.path.splitext(file_path)[1].lower()
        
        # 1. Create File Node
        nodes.append(ExtractedNode(
            node_id=file_node_id,
            node_type="FILE",
            name=os.path.basename(file_path),
            system="files",
            attributes={"path": file_path, "extension": ext}
        ))

        # 2. Parse SQL
        # Pre-process: Split by 'GO' (case insensitive) on its own line
        # Regex: ^\s*GO\s*$ (multiline)
        batches = re.split(r'^\s*GO\s*$', content, flags=re.MULTILINE | re.IGNORECASE)
        
        dialect = "tsql" 
        
        for batch in batches:
            if not batch.strip():
                continue
                
            try:
                # parse returns a list of expressions
                parsed_statements = sqlglot.parse(batch, read=dialect)
                for stmt in parsed_statements:
                    self._analyze_statement(stmt, file_path, content, file_node_id, nodes, edges, evidences)
            except Exception as e:
                print(f"SqlGlot parse error in {file_path}: {e}")
                # We continue with next batch/statement
                continue

        # Deduplicate
        unique_nodes = {n.node_id: n for n in nodes}.values()
        
        return ExtractionResult(
            meta={"source_file": file_path, "extractor": "sqlglot_v1"},
            nodes=list(unique_nodes),
            edges=edges,
            evidences=evidences,
            assumptions=[]
        )

    def _analyze_statement(self, stmt, file_path, content, from_id, nodes, edges, evidences):
        # 1. Tables (Inputs)
        # sqlglot finds all tables. We need to filter out CTEs defined in this query.
        
        # Find CTE definitions first
        ctes = set()
        for cte in stmt.find_all(exp.CTE):
            ctes.add(cte.alias_or_name.upper())

        # Find all tables
        for table in stmt.find_all(exp.Table):
            table_name = table.name
            schema_name = table.db # db is often used as schema in sqlglot (table.db = schema, table.catalog = db)
            full_name = f"{schema_name}.{table_name}" if schema_name else table_name
            
            # Skip if it is a CTE defined in this statement
            if table_name.upper() in ctes:
                continue
                
            # Node for Table
            table_node_id = f"table::{full_name}"
            nodes.append(ExtractedNode(
                node_id=table_node_id,
                node_type="TABLE",
                name=full_name,
                system="sql",
                attributes={"schema": schema_name or "dbo", "pure_name": table_name}
            ))
            
            # Edge: File READS_FROM Table
            # But wait, is it a READ or WRITE?
            # If table is in FROM or JOIN, it's READ.
            # If table is in INSERT INTO or UPDATE, it's WRITE.
            
            parent = table.find_ancestor(exp.Insert, exp.Update, exp.Create, exp.Merge)
            if parent:
                # It might be the target.
                # For Insert, this_table is the target.
                if isinstance(parent, exp.Insert) and parent.this == table:
                     self._add_edge(from_id, table_node_id, "WRITES_TO", nodes, edges, evidences, file_path, table)
                     continue
                # For Update, this is the target
                if isinstance(parent, exp.Update) and parent.this == table:
                     self._add_edge(from_id, table_node_id, "WRITES_TO", nodes, edges, evidences, file_path, table)
                     continue
                # For Create, this is the target
                if isinstance(parent, exp.Create) and parent.this == table:
                     self._add_edge(from_id, table_node_id, "CREATES", nodes, edges, evidences, file_path, table)
                     continue
            
            # Default to READS_FROM
            self._add_edge(from_id, table_node_id, "READS_FROM", nodes, edges, evidences, file_path, table)

    def _add_edge(self, source_id, target_id, rel_type, nodes, edges, evidences, file_path, token):
        edge_id = str(uuid.uuid4())
        
        # Evidence
        # sqlglot tokens usually have line info if track_locations=True (default in some versions?)
        # Safely access lineno
        line = 1
        if hasattr(token, 'lineno') and token.lineno:
             line = token.lineno
        elif hasattr(token, 'this') and hasattr(token.this, 'lineno') and token.this.lineno:
             line = token.this.lineno
        
        ev_id = str(uuid.uuid4())
        evidences.append(Evidence(
            evidence_id=ev_id,
            kind="sqlglot_parse",
            locator=Locator(file=file_path, line_start=line, line_end=line),
            snippet=token.sql()[:200] # Truncate snippet
        ))

        edges.append(ExtractedEdge(
            edge_id=edge_id,
            edge_type=rel_type,
            from_node_id=source_id,
            to_node_id=target_id,
            confidence=1.0, # High confidence for parser
            rationale=f"Detected via SQL Parser ({rel_type})",
            evidence_refs=[ev_id],
            is_hypothesis=False
        ))
