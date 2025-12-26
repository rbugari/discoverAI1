# Nexus Discovery - Roadmap & Known Issues

## 🚀 Released (v4.0) - "Deep Understanding"
- [x] **Package Deep Dive**: Granular extraction of SSIS/DataStage internal components.
- [x] **Column-Level Lineage**: Back-end support for field-to-field mapping and transformation rules.
- [x] **Silent Mode**: Automated end-to-end processing without manual approval.
- [x] **LLM Resilience**: Automatic retries for rate-limited (429) provider calls.
- [x] **Optmized Model**: Integration of Gemini 2.0 Flash Lite for technical extraction.

## 🚀 Released (v3.1) - "Plan & Control"
- [x] **Planning Phase**: New orchestrator stage that scans files and generates execution plans.
- [x] **Human-in-the-Loop UI**: Dashboard allows reviewing, enabling, and reordering.
- [x] **Truly Incremental**: Hash-based logic to skip unchanged files.
- [x] **Multi-provider Routing**: Support for Gemini/Llama via Groq/OpenRouter.

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

### 2. Advanced Lineage & UI
- [ ] **Column-Level Lineage UI**: Complete front-end visualization for field-level dependencies.
- [ ] **Interactive Deep Dive**: Drill-down from packages to specific components in the UI.
- [ ] **Impact Analysis**: "What-if" scenarios (e.g., "If I drop this column, what breaks?").

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
