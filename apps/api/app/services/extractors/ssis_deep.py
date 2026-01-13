import xml.etree.ElementTree as ET
import uuid
import logging
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.models.deep_dive import DeepDiveResult, Package, PackageComponent, TransformationIR, ColumnLineage
from app.models.extraction import ExtractionResult, ExtractedNode, ExtractedEdge, Locator, Evidence
from app.services.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)

class SSISDeepExtractor(BaseExtractor):
    """
    Deep extractor for SSIS packages (.dtsx).
    Extracts Data Flow components, transformations, and formulas.
    Adapted from legacy diggerAI/ssis_deep.py to produce DeepDiveResult.
    """
    
    def extract(self, file_path: str, content: str) -> Optional[ExtractionResult]:
        """
        Shallow / Macro extraction: Finds ALL tables (Assets) and simple relationships.
        This effectively replaces the LLM 'extract.lineage.package' step with deterministic parsing.
        """
        return self.extract_macro(file_path, content)

    def extract_macro(self, file_path: str, content: str) -> Optional[ExtractionResult]:
        try:
            # Handle bytes/string
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            
            root = ET.fromstring(content)
            
            def local_tag(tag): return tag.split('}')[-1] if '}' in tag else tag
            
            nodes = []
            edges = []
            evidences = []
            seen_nodes = set()
            
            # 1. Identify Package (PROCESS Node)
            package_name = "UnknownPackage"
            for elem in root.iter():
                 if local_tag(elem.tag) == "Executable":
                     package_name = elem.attrib.get(f"{{www.microsoft.com/SqlServer/Dts}}ObjectName") or elem.attrib.get("DTS:ObjectName") or "Package"
                     break
            
            pkg_node_id = package_name
            nodes.append(ExtractedNode(
                node_id=pkg_node_id,
                node_type="PROCESS",
                name=package_name,
                system="ssis",
                attributes={"file_path": file_path}
            ))
            seen_nodes.add(pkg_node_id)

            # 2. Traverse for Components (Tables & Columns)
            for component in root.findall(".//{*}component"):
                 name = component.attrib.get("name")
                 ref_id = component.attrib.get("refId")
                 comp_class = component.attrib.get("componentClassID", "")
                 
                 # Look for OpenRowset (Table Name) or SqlCommand
                 table_name = None
                 sql_command = None
                 
                 for prop in component.findall(".//{*}property"):
                     p_name = prop.attrib.get("name")
                     val = prop.text
                     if p_name == "OpenRowset": table_name = val
                     elif p_name == "SqlCommand": sql_command = val
                 
                 # Extract Columns for this component
                 # We look for 'outputColumns' or 'externalMetadataColumns' to get the schema of the table
                 columns = []
                 for section in component:
                     tag_name = local_tag(section.tag)
                     if tag_name in ["outputs", "inputs"]: # usually outputs for source, inputs for dest
                         for io in section:
                             for col_container in io:
                                 if local_tag(col_container.tag) in ["outputColumns", "inputColumns", "externalMetadataColumns"]:
                                     for col in col_container:
                                         c_name = col.attrib.get("name")
                                         if c_name: columns.append(c_name)
                 
                 # Deduplicate columns
                 columns = list(set(columns))

                 # If we found a table name, create NODE + EDGE
                 if table_name:
                     clean_name = table_name.replace("[", "").replace("]", "")
                     node_id = clean_name
                     
                     attrs = {"columns": columns} if columns else {}
                     
                     if "Source" in comp_class or "Source" in name:
                         # Table -> Process (Read)
                         # Add Table Node
                         if node_id not in seen_nodes:
                             nodes.append(ExtractedNode(node_id=node_id, node_type="TABLE", name=clean_name, system="sqlserver", attributes=attrs))
                             seen_nodes.add(node_id)
                         
                         # Add Edge
                         edges.append(ExtractedEdge(
                             edge_id=str(uuid.uuid4()),
                             from_node_id=node_id,
                             to_node_id=pkg_node_id,
                             edge_type="READS_FROM", # Updated to match model enum-ish description usually
                             confidence=1.0,
                             rationale=f"SSIS Source Component '{name}' reads from '{node_id}'"
                         ))
                         
                     elif "Destination" in comp_class or "Destination" in name:
                         # Process -> Table (Write)
                         if node_id not in seen_nodes:
                             nodes.append(ExtractedNode(node_id=node_id, node_type="TABLE", name=clean_name, system="sqlserver", attributes=attrs))
                             seen_nodes.add(node_id)

                         edges.append(ExtractedEdge(
                             edge_id=str(uuid.uuid4()),
                             from_node_id=pkg_node_id,
                             to_node_id=node_id,
                             edge_type="WRITES_TO", # Updated
                             confidence=1.0,
                             rationale=f"SSIS Destination Component '{name}' writes to '{node_id}'"
                         ))
                 
                 # If SQL Command, try to extract table (fallback)
                 if sql_command and not table_name:
                     import re
                     # extremely basic regex
                     tbl_pat = r"(?:FROM|JOIN|INTO|UPDATE)\s+([\[\]a-zA-Z0-9_.]+)"
                     matches = re.findall(tbl_pat, sql_command, re.IGNORECASE)
                     for m in matches:
                         clean_m = m.replace("[", "").replace("]", "")
                         if clean_m not in seen_nodes:
                              nodes.append(ExtractedNode(node_id=clean_m, node_type="TABLE", name=clean_m, system="sqlserver", attributes={"derived_from_sql": True}))
                              seen_nodes.add(clean_m)
                         # Assume READS for SQL Query usually, unless UPDATE
                         is_write = "UPDATE" in sql_command.upper() or "INSERT" in sql_command.upper()
                         edge_type = "WRITES_TO" if is_write else "READS_FROM"
                         
                         if edge_type == "READS_FROM":
                             edges.append(ExtractedEdge(
                                 edge_id=str(uuid.uuid4()),
                                 from_node_id=clean_m, 
                                 to_node_id=pkg_node_id, 
                                 edge_type="READS_FROM", 
                                 confidence=0.8,
                                 rationale="Inferred from SQL Command in component"
                             ))
                         else:
                             edges.append(ExtractedEdge(
                                 edge_id=str(uuid.uuid4()),
                                 from_node_id=pkg_node_id, 
                                 to_node_id=clean_m, 
                                 edge_type="WRITES_TO", 
                                 confidence=0.8,
                                 rationale="Inferred from SQL Command in component"
                             ))

            return ExtractionResult(
                meta={"source": "SSISDeepExtractor", "file": file_path},
                nodes=nodes,
                edges=edges,
                evidences=evidences
            )
            
        except Exception as e:
            logger.error(f"Error in SSISDeepExtractor.extract_macro: {e}")
            return None

    def extract_deep(self, file_path: str, content: str) -> Optional[DeepDiveResult]:
        try:
            # Handle bytes/string content
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
                
            root = ET.fromstring(content)
            
            # Helper to strip namespace
            def local_tag(tag):
                return tag.split('}')[-1] if '}' in tag else tag

            package_name = "Unknown"
            # Project ID is required by models, generating a temporary one if context not available
            # Ideally this comes from the caller context, but for extraction we gen new UUIDs
            project_id = uuid.uuid4() 
            package_id = uuid.uuid4()
            
            # 1. Package Node
            for elem in root.iter():
                 if local_tag(elem.tag) == "Executable":
                     package_name = elem.attrib.get(f"{{www.microsoft.com/SqlServer/Dts}}ObjectName") or elem.attrib.get("DTS:ObjectName") or "Package"
                     break
            
            # Collections for the flattened result
            components: List[PackageComponent] = []
            transformations: List[TransformationIR] = []
            lineage_list: List[ColumnLineage] = []
            
            # 2. Recursive Traversal for Hierarchy
            self._traverse_executables(root, package_id, project_id, components, transformations, lineage_list)

            # Create Package Model
            package_model = Package(
                package_id=package_id,
                project_id=project_id,
                name=package_name,
                type="SSIS",
                source_system="SSIS",
                config={"file_path": file_path},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            return DeepDiveResult(
                package=package_model,
                components=components,
                transformations=transformations,
                lineage=lineage_list
            )

        except Exception as e:
            logger.error(f"Error in SSISDeepExtractor: {e}")
            traceback.print_exc()
            return None

    def _traverse_executables(self, element, parent_id, project_id, components, transformations, lineage_list):
        def local_tag(tag):
            return tag.split('}')[-1] if '}' in tag else tag

        for child in element:
            tag = local_tag(child.tag)
            
            if tag == "Executable":
                exe_name = child.attrib.get(f"{{www.microsoft.com/SqlServer/Dts}}ObjectName") or child.attrib.get("DTS:ObjectName")
                exe_type = child.attrib.get(f"{{www.microsoft.com/SqlServer/Dts}}ExecutableType") or child.attrib.get("DTS:ExecutableType")
                
                # Check if it's a Data Flow (Pipeline)
                is_data_flow = "Pipeline" in (exe_type or "")
                
                comp_id = uuid.uuid4()
                
                # Create Component for this Executable (Container or Task)
                comp_config = {"original_type": exe_type or "SSIS::Task"}
                
                # Try to extract SQL or Config from ObjectData
                for obj_data in child.findall(".//{*}ObjectData"):
                    # 1. Execute SQL Task
                    sql_task = obj_data.find(".//{*}SqlTaskData")
                    if sql_task is not None:
                        sql_stmt = sql_task.attrib.get(f"{{www.microsoft.com/SqlServer/Dts}}SqlStatementSource") or \
                                   sql_task.attrib.get("SQLTask:SqlStatementSource")
                        if sql_stmt:
                            comp_config["sql_command"] = sql_stmt
                            comp_config["connection"] = sql_task.attrib.get(f"{{www.microsoft.com/SqlServer/Dts}}Connection") or \
                                                        sql_task.attrib.get("SQLTask:Connection")
                
                comp = PackageComponent(
                    component_id=comp_id,
                    package_id=parent_id, 
                    parent_component_id=None,
                    name=exe_name or "Task",
                    type="CONTAINER" if not is_data_flow else "TRANSFORM",
                    config=comp_config,
                    created_at=datetime.utcnow()
                )
                
                # Add to list
                components.append(comp)

                # If Data Flow, parse internal pipeline
                if is_data_flow:
                    for obj_data in child.findall(".//{*}ObjectData"):
                        for pipeline in obj_data.findall(".//{*}pipeline"):
                             self._parse_pipeline(
                                 pipeline, 
                                 parent_id, # Package ID as parent for these components? Or the DataFlowTask ID?
                                 # Usually Data Flows components are children of the Data Flow Task.
                                 comp_id,
                                 project_id,
                                 components, 
                                 transformations, 
                                 lineage_list
                             )
                else:
                    # Generic Container/Task, keep walking for nested tasks (Sequence Containers etc)
                    # For nested containers, the parent for children is this container.
                    # But PackageComponent model parent_component_id is optional.
                    # Let's pass simple recursion. Note: recursive traversal here passes 'parent_id' which was package_id.
                    # If we want hierarchy, we should pass comp_id.
                    # For now keep it flat-ish or simple hierarchy.
                    self._traverse_executables(child, parent_id, project_id, components, transformations, lineage_list)
            
            # Also check for executables inside DTS:Executables collection
            elif tag == "Executables":
                self._traverse_executables(child, parent_id, project_id, components, transformations, lineage_list)

    def _local_tag(self, tag):
        return tag.split('}')[-1] if '}' in tag else tag

    def _parse_pipeline(self, pipeline_elem, package_id, parent_component_id, project_id, components, transformations, lineage_list):
        
        # 1. Extract Components
        components_node = None
        for child in pipeline_elem:
            if self._local_tag(child.tag) == "components":
                components_node = child
                break
        
        comp_id_map = {} # Map refId (internal SSIS ID) -> component_id (UUID)

        if components_node is not None:
            for component in components_node:
                if self._local_tag(component.tag) == "component":
                    # Get Attributes
                    ref_id = component.attrib.get("refId")
                    name = component.attrib.get("name") or ref_id
                    comp_class = component.attrib.get("componentClassID", "")
                    
                    c_uuid = uuid.uuid4()
                    comp_id_map[ref_id] = c_uuid 

                    # Determine Type
                    c_type = "TRANSFORM"
                    if "Source" in comp_class or "Source" in name: c_type = "SOURCE"
                    elif "Destination" in comp_class or "Destination" in name: c_type = "SINK"
                    
                    # Extract Properties
                    properties = {}
                    local_transforms = [] # Collect transforms for this component
                    
                    for child in component:
                        if self._local_tag(child.tag) == "properties":
                            for prop in child:
                                if self._local_tag(prop.tag) == "property":
                                    p_name = prop.attrib.get("name")
                                    p_val = prop.text
                                    if p_name and p_val:
                                        properties[p_name] = p_val
                                        
                                        # Capture Transformation Logic (SQL Command)
                                        if p_name == "SqlCommand":
                                            local_transforms.append({
                                                "raw": p_val,
                                                "op": "SQL_QUERY"
                                            })
                    
                    # Check for all columns (schema metadata)
                    column_list = self._extract_all_columns(component)
                    if column_list:
                         properties["columns_metadata"] = column_list

                    # Create Component Node
                    components.append(PackageComponent(
                        component_id=c_uuid,
                        package_id=package_id,
                        parent_component_id=parent_component_id,
                        name=name,
                        type=c_type,
                        config=properties,
                        created_at=datetime.utcnow()
                    ))
                    
                    # Register SQL transformations if any
                    for lt in local_transforms:
                        transformations.append(TransformationIR(
                            ir_id=uuid.uuid4(),
                            project_id=project_id,
                            source_component_id=c_uuid,
                            operation=lt["op"],
                            logic_summary=lt["raw"],
                            metadata={"type": "SqlCommand"},
                            created_at=datetime.utcnow()
                        ))

                    # Check Output Columns for Derived Column expressions
                    self._extract_column_formulas(component, c_uuid, project_id, transformations)

        # 2. Extract Data Flows (Paths) -> Lineage/Mapping
        # This part is harder to map directly to 'ColumnLineage' without column-level detail,
        # but we can infer dependency between components.
        # DeepDiveResult expects 'lineage' as ColumnLineage list.
        # Ideally we map Component -> Component edges. 
        # But 'PackageComponent' has source_mapping/target_mapping lists.
        # Let's see if we can populate source_mapping for components based on paths.

        if paths_node is not None:
            path_updates = [] # Store (target_uuid, source_uuid)
            
            for path in paths_node:
                if self._local_tag(path.tag) == "path":
                    start_id_raw = path.attrib.get("startId")
                    end_id_raw = path.attrib.get("endId")
                    
                    source_node_id = self._find_node_id_by_ref(start_id_raw, comp_id_map)
                    target_node_id = self._find_node_id_by_ref(end_id_raw, comp_id_map)
                    
                    if source_node_id and target_node_id:
                        path_updates.append((target_node_id, source_node_id))
                        
                        # --- ADD COLUMN LINEAGE ENTRY ---
                        # At this level (DataFlow Path), we usually represent component-level lineage
                        # unless we parse the detailed mapping. 
                        # We create a ColumnLineage entry for the 'flow' itself.
                        lineage_list.append(ColumnLineage(
                            lineage_id=uuid.uuid4(),
                            project_id=project_id,
                            package_id=package_id,
                            source_asset_id=source_node_id, # Bridge will resolve this to Asset UUID
                            target_asset_id=target_node_id,
                            source_column="*",
                            target_column="*",
                            transformation_rule="Data Flow Path",
                            confidence=1.0,
                            created_at=datetime.utcnow()
                        ))

            # Update components with source/target mapping (in-memory update)
            # Find target component object
            for t_uuid, s_uuid in path_updates:
                target_comp = next((c for c in components if c.component_id == t_uuid), None)
                if target_comp:
                    target_comp.source_mapping.append({"from_component_id": str(s_uuid)})
                
                source_comp = next((c for c in components if c.component_id == s_uuid), None)
                if source_comp:
                    source_comp.target_mapping.append({"to_component_id": str(t_uuid)})


    def _extract_column_formulas(self, component_elem, node_id, project_id, transforms):
        # Look for output columns with "Expression" properties
        for child in component_elem:
            if self._local_tag(child.tag) == "outputs":
                for output in child:
                    if self._local_tag(output.tag) == "output":
                        for out_child in output:
                            if self._local_tag(out_child.tag) == "outputColumns":
                                for col in out_child:
                                    if self._local_tag(col.tag) == "outputColumn":
                                        col_name = col.attrib.get("name")
                                        lin_id = col.attrib.get("lineageId")
                                        
                                        # Check properties of column
                                        expr = None
                                        
                                        # Check nested properties
                                        for prop_container in col:
                                            if self._local_tag(prop_container.tag) == "properties": 
                                                for prop in prop_container:
                                                    if self._local_tag(prop.tag) == "property":
                                                        if prop.attrib.get("name") == "Expression":
                                                            expr = prop.text

                                            # Check direct properties
                                            if self._local_tag(prop_container.tag) == "property" and prop_container.attrib.get("name") == "Expression":
                                                 expr = prop_container.text
                                        
                                        if expr:
                                             transforms.append(TransformationIR(
                                                ir_id=uuid.uuid4(),
                                                project_id=project_id,
                                                source_component_id=node_id,
                                                operation="DERIVE",
                                                logic_summary=expr,
                                                metadata={"column": col_name, "lineage_id": lin_id},
                                                created_at=datetime.utcnow()
                                            ))

    def _find_node_id_by_ref(self, path_ref: str, comp_map: Dict[str, uuid.UUID]) -> Optional[uuid.UUID]:
        # Tries to find which component refId matches the path_ref prefix
        if not path_ref: return None
        
        # Sort keys by length desc to match longest prefix first
        sorted_keys = sorted(comp_map.keys(), key=len, reverse=True)
        
        for ref_id in sorted_keys:
            if ref_id in path_ref:
                return comp_map[ref_id]
        return None

    def _extract_all_columns(self, component_elem) -> List[Dict[str, Any]]:
        """Extracts a list of column metadata for any component."""
        cols = []
        for child in component_elem.iter():
            tag = self._local_tag(child.tag)
            if tag in ["outputColumn", "inputColumn", "externalMetadataColumn"]:
                name = child.attrib.get("name")
                lin_id = child.attrib.get("lineageId")
                if name:
                    cols.append({
                        "name": name,
                        "lineage_id": lin_id,
                        "kind": tag
                    })
        return cols
