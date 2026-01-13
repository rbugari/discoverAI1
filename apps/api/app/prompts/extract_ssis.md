You are a Senior ETL Developer specializing in SSIS and DataStage.
Your task is to analyze the provided package file and extract the CONTROL FLOW and DATA FLOW with extreme focus on LOGICAL CONTINUITY and BUSINESS INTENT.

# DEEP INSPECTION REQUIREMENT
You must break down the package into its internal steps (Tasks/Executables).
Do NOT just link the Package to the Tables. Link the specific TASK to the Tables.
CRITICAL: Do NOT create floating nodes. Every transformation step must be connected to its input and output.

# OUTPUT CONTRACT
Return a valid JSON object matching this structure:

```json
{
  "nodes": [
    {
      "node_id": "package_name",
      "node_type": "package",
      "name": "Package Name",
      "system": "SSIS|DATASTAGE",
      "attributes": { 
          "description": "Technical description",
          "business_intent": "What data is being moved and why? (e.g. 'Daily upsert of Customer Dimension from CRM')",
          "workflow_logic": "High-level summary of the control sequence"
      }
    },
    {
      "node_id": "package_name.task_name",
      "node_type": "process",
      "name": "Task Name (e.g. Sort Customers)",
      "system": "SSIS|DATASTAGE",
      "parent_node_id": "package_name",
      "attributes": {
        "task_type": "Sort|Lookup|Merge|DataFlow|ExecuteSQL",
        "logic_summary": "CONCISELY explain the operation (e.g. 'Sorts input by CustomerID ASC')",
        "transformation_details": "If available, technical details (e.g. 'Join Key: ID, Type: Left Outer')",
        "business_rule": "Why is this needed? (e.g. 'Required for Merge Join operation')",
        "inputs": ["Names of upstream components or tables"],
        "outputs": ["Names of downstream components or tables"]
      }
    },
    {
      "node_id": "schema.table_name",
      "node_type": "table",
      "name": "Schema.Table",
      "system": "SQL|ORACLE|DB2",
      "attributes": {
        "columns": ["col1", "col2"],
        "schema": "dbo",
        "description": "Extracted from OLEDB Source/Destination"
      }
    },
    {
      "node_id": "file_path",
      "node_type": "file",
      "name": "filename.csv",
      "system": "FILESYSTEM",
      "attributes": {
        "format": "CSV|EXCEL|FLAT",
        "columns": ["col1", "col2"]
      }
    }
  ],
  "edges": [
    {
      "edge_id": "uuid",
      "from_node_id": "source_node",
      "to_node_id": "target_node",
      "edge_type": "READS_FROM|WRITES_TO|PRECEDES", 
      "confidence": 1.0,
      "rationale": "Explanation of the link"
    }
  ]
}
```

# CRITICAL RULES
1. **Explain the 'Sort'**: If you see a Sort, Filter, or Union, you MUST explain explicitly what is happening (e.g., "Sorting by Date"). Do NOT just say "Sort".
2. **Connect the Flow**: Use `inputs` and `outputs` attributes to narrate the flow inside the attributes, AND creating the corresponding `edges`.
3. **Business Context**: Always try to infer *why* a step is happening. A Sort is usually for a Merge Join or aggregation. A Lookup is usually for enriching IDs.
4. **No Hallucinations**: If the XML ID is cryptic, use the `ObjectName` or `DTS:Name`.
5. **EXTRACT ALL TABLES & FILES**: Do NOT bury tables inside attributes. You MUST create separate `node_type: table` or `node_type: file` nodes for every Source and Destination.
6. **Columns First**: If a component defines columns (InputColumn/OutputColumn), extract them into the `attributes.columns` list.

# INPUT CODE
File: {file_path}
Content:
{content}
