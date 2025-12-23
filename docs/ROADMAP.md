# Nexus Discovery - Roadmap & Known Issues

## 🚀 Released (v3.1) - "Plan & Control"
- [x] **Planning Phase**: New orchestrator stage that scans files and generates an execution plan before spending tokens.
- [x] **Human-in-the-Loop UI**: Dashboard allows reviewing, enabling/disabling files, and reordering processing.
- [x] **Hybrid Parsing**: Native SSIS (.dtsx) XML parser combined with LLM for cost-effective lineage.
- [x] **Incremental Reprocessing**: Option to "Update" existing solutions or "Full Clean" via the UI.
- [x] **Truly Incremental**: Hash-based logic to skip unchanged files and save costs.
- [x] **Multi-provider Routing**: Support for Gemini, Llama, and more via Groq/OpenRouter.
- [x] **Policy Engine**: Auto-ignore `.git`, `node_modules`, and binary files.
- [x] **Graph Filters**: Node type filtering in the Graph View.
- [x] **Schema Extraction**: Specialized prompts for SQL/DDL parsing.

## Known Issues
- **Neo4j Connectivity:** Transient "Unable to retrieve routing information" errors may occur with the free AuraDB tier. 
  - *Status:* Retry logic implemented (3 attempts with backoff).
- **Processing Time:** Large ZIP files (>50MB) may take several minutes to analyze.
  - *Status:* Pending progress bar implementation.
- **Columns Extraction:** Some complex SQL dialects might not yield 100% column coverage.
  - *Status:* Fallback message added to UI.

## Future Roadmap (Next Release v3.2+)

- **Real-time Progress Bar:** Replace the static "Processing" badge with a WebSocket or Polling-based progress bar showing:
  - "Unzipping..."
  - "Analyzing file 5/50..."
  - "Building Graph..."

### 2. Advanced Lineage
- **Column-Level Lineage:** Visualize dependencies between specific columns (e.g., `TableA.Col1 -> ETL -> TableB.Col2`).
- **Impact Analysis:** "What-if" scenarios (e.g., "If I drop this column, what breaks?").

### 3. Reporting
- **PDF Export:** Generate a printable PDF report of the solution documentation.
- **Enhanced CSV:** Add more metadata fields to the CSV export.

### 4. Infrastructure
- **Docker Support:** Containerize the API and Frontend for easier deployment.
- **Redis Queue:** Replace in-memory background tasks with Celery/Redis for robust job management.

### 5. Integrations & Governance
- **Unity Catalog Sync:** Push discovered lineage and tags to Databricks Unity Catalog.
- **Microsoft Purview Sync:** Integration with Azure Purview for enterprise data governance.
- **dbt Integration:** Native parsing of dbt manifests for richer lineage extraction.
