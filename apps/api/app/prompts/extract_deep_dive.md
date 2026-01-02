# Prompt: Extract Deep Dive v4.0

You are an expert data engineer and solution architect. Your task is to perform a deep inspection of a data processing asset (SSIS Package, SQL Script, or Python code) to extract its "Functional Core" and granular lineage.

## Objectives
1. **Source-to-Target Mapping**: Identify the REAL data sources and targets. Ignore technical labels like "OLEDB Source" or "ODBC Destination". Look for actual table names, file paths, or API endpoints.
2. **Intermediate Representation (IR)**: Describe the logic of business transformations (Filters, Joins, Aggregations, Lookups, Derived Columns).
3. **Column-Level Lineage**: Map how specific columns from the source flow into the target, including the rules applied.
4. **Functional Objective**: Synthesize what this asset achieves from a business perspective (e.g., "Calculates monthly tax for individual clients and updates the fiscal ledger").
5. **Asset Resolution**: You MUST link lineage to the correct parent assets.

## Input Data
- **File Path**: {file_path}
- **File Type**: {file_type}
- **Macro Nodes**: {macro_nodes} (Results from previous shallow extraction - USE THESE NAMES)
- **Content**:
{content}

## Output Format
Return valid JSON only, following this structure:

```json
{
  "package": {
    "name": "Asset Name",
    "type": "SSIS|SQL|PYTHON",
    "source_system": "Origin System",
    "target_system": "Destination System",
    "description": "Technical description",
    "business_intent": "Functional objective summary"
  },
  "components": [
    {
      "component_id": "temp_id_1",
      "name": "Component Name",
      "type": "Source|Transformation|Target",
      "logic_raw": "Specific code/query snippet",
      "source_mapping": [{ "asset_name": "table_a", "columns": ["col1", "col2"] }],
      "target_mapping": [{ "asset_name": "table_b", "columns": ["colx"] }]
    }
  ],
  "transformations": [
    {
      "ir_id": "temp_ir_1",
      "source_component_id": "temp_id_1",
      "operation": "FILTER|JOIN|AGGREGATE|DERIVE",
      "logic_summary": "Filter records where status='A'",
      "metadata": {
        "expressions": "...",
        "input_cols": ["..."],
        "output_cols": ["..."]
      }
    }
  ],
  "lineage": [
    {
      "source_asset_name": "TableA", 
      "source_column": "Col1",
      "target_asset_name": "TableB",
      "target_column": "ColX",
      "transformation_rule": "Direct mapping",
      "confidence": 0.95
    },
    {
      "source_asset_name": "TableA",
      "source_column": "Col2",
      "target_asset_name": "TableB",
      "target_column": "ColY",
      "transformation_rule": "IF Col2 IS NULL THEN 0 ELSE Col2",
      "confidence": 0.9
    }
  ]
}
```

## Critical Rules
- **Asset Naming**: For `source_asset_name` and `target_asset_name`, you MUST use the exact `name` of one of the provided `Macro Nodes` if applicable. Do not invent new names if the table is already listed.
- **Prefixing**: If you cannot find the asset in macro nodes, use the best available name. If it's a qualified table name, include the schema (e.g., `dbo.MyTable`).
- **No Technical Hallucinations**: If you can't find a table name, do not invent one.
- **Focus on Business Logic**: Transformations should be explained in a way that a business analyst could understand.
