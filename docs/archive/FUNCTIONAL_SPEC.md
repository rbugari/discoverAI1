# Nexus Discovery - Functional Specification (v4.0)

## 1. Executive Summary
**Nexus Discovery** is an AI-powered Reverse Engineering & Data Lineage platform designed to accelerate the understanding, documentation, and migration of complex data ecosystems. 

By leveraging Generative AI (LLMs) and Graph Database technology, Nexus Discovery transforms opaque legacy code (SQL, SSIS, Python) into interactive, navigable intelligence. This tool addresses the critical business challenge of "Data Knowledge Debt"—where the logic of critical business processes is locked inside code files that no one fully understands.

## 2. Business Value Proposition
*   **Accelerate Cloud Migrations:** Reduce the "Assessment & Planning" phase of migration projects by 40-60% by automatically mapping existing dependencies.
*   **Reduce Onboarding Time:** Enable new Data Engineers to understand years of legacy development in minutes through interactive visual graphs and natural language summaries.
*   **Mitigate Operational Risk:** Visualize upstream and downstream dependencies to prevent breaking changes during refactoring.
*   **Automate Documentation:** Replace stale, manual documentation with a living, AI-generated knowledge base that updates with the code.

## 3. Target Audience
*   **Data Architects:** For high-level system design and migration planning.
*   **Migration Engineers:** To deconstruct legacy ETL pipelines (e.g., SSIS) and re-implement them in modern platforms (e.g., Databricks, dbt).
*   **Data Stewards/Governance Officers:** To discover data flows and ensure compliance.

## 4. Key Features (Release v4.0)

### 4.0. Plan-Driven Orchestration & Incremental Updates
*   **Discovery Phase**: A light-speed scan identifies file types and strategies before deep analysis.
*   **Review Dashboard**: Users approve the execution plan, categorize files, and manage costs.
*   **Truly Incremental**: SHA256 hashing allows skipping unchanged files, saving time and tokens.

### 4.1. Intelligent Code Ingestion
*   **Multi-Format Support:** Natively parses and analyzes:
    *   **SSIS Packages (.dtsx):** Extracts data flow tasks, sources, and destinations from complex XML structures.
    *   **SQL Scripts (.sql):** Parses DDL (Create Table) and DML (Select/Insert) to understand table structures and transformations.
    *   **Python/PySpark (.py):** Analyzes dataframes and API calls to map code-based data movement.
*   **Zip & Git Integration:** Users can upload local ZIP archives or provide Git repository URLs for analysis.

### 4.2. Automated Data Lineage Graph
*   **Visual Dependency Mapping:** Automatically constructs a directed graph showing the flow of data:
    *   `Source Table` -> `ETL Process` -> `Target Table`
*   **Auto-Layout:** Uses intelligent layout algorithms (DAG) to organize complex pipelines into readable, left-to-right flows.
*   **Node Classification:** Visually distinguishes between Tables, Pipelines, Scripts, and APIs using color-coded nodes.

### 4.3. AI-Powered Metadata & Documentation
*   **Automated Summaries:** Every node in the graph includes a concise, AI-generated summary explaining *what* the code does in plain English.
*   **Schema Extraction:** Automatically extracts column names and data types from source code where available, creating a preliminary Data Dictionary without accessing the production database.
*   **Contextual Navigation:** Users can navigate the graph via an interactive side panel, jumping between upstream inputs and downstream outputs.

### 4.4. "Chat with Data" Assistant (RAG)
*   **Context-Aware Q&A:** An embedded AI assistant that understands the specific graph topology.
*   **Natural Language Queries:** Users can ask complex questions like:
    *   *"Which pipelines read from the Employee table?"*
    *   *"What is the transformation logic in the Sales_ETL script?"*
    *   *"List all tables modified by the Finance workflow."*

### 4.6. Deep Understanding (v4.0)
*   **Package Deep Dive**: Granular extraction of internal ETL logic (.dtsx, .dsx), identifying steps, variables, and embedded SQL.
*   **Column-Level Lineage**: Precise tracing of individual fields through transformations, including business rules.
*   **Intermediate Representation (IR)**: Platform-agnostic mapping of logic to facilitate system modernization.

### 4.7. Hierarchical Prompting (v4.0 Sprint 2)
*   **Layered Knowledge Fusion**: Final instructions are built by merging 4 distinct layers:
    *   **Base**: Fundamental technical logic.
    *   **Domain**: Technology expertise (SSIS, DataStage, etc.).
    *   **Org**: Corporate standards and quality rules.
    *   **Solution**: Project-specific context and local normalizations.
*   **Prompt Matrix UI**: An administrative dashboard for managing these layers at scale or per-project.

### 4.8. Governance Hub & Exports (v4.0 Sprint 3)
*   **Enterprise Bridge**: Bridges the gap between technical discovery and enterprise governance.
*   **Manual Export Gateways**:
    *   **Purview**: CSV bulk upload format.
    *   **Unity Catalog**: Lineage and Asset CSV mapping.
    *   **dbt**: Automated `sources.yml` generation for source documentation.

### 4.9. Resilience & integrated Help
*   **LLM Resilience**: Integrated backoff system to handle provider rate limits (429).
*   **Integrated Documentation**: In-app "Guides" explaining complex configuration logic (V5.0 Phase 1).

## 5. Use Cases

### Case A: The "Black Box" Migration
**Scenario:** A retailer needs to migrate 500 SSIS packages to Databricks. The original developers left years ago.
**Solution:** The team uploads the SSIS ZIP to DiscoverAI. Within minutes, they have a visual map of all data flows. They use the **Governance Hub** to export a `sources.yml` and start their dbt project immediately.

### Case B: Complex Normalization (Northwind)
**Scenario:** A project has inconsistent database names across environment files (`LocalDB`, `PROD_DB`, `Legacy_DB`) resulting in fragmented linage.
**Solution:** The user adds a **Solution Layer** prompt: *"Normalize all variations of DB names to 'Warehouse_Gold'."* The system re-analyzes and consolidates the lineage automatically.

### Case C: Impact Analysis
**Scenario:** A DBA needs to change the schema of the `DimCustomer` table but fears breaking downstream reports.
**Solution:** Using the Graph View, the DBA selects `DimCustomer` and instantly sees 3 ETL scripts and 2 Reporting Views that depend on it. They can now plan the schema change with zero unexpected downtime.

### Case D: New Hire Onboarding
**Scenario:** A new Senior Engineer joins the team and asks, "How does our data warehouse get populated?"
**Solution:** Instead of reading thousands of lines of code, they spend 15 minutes exploring the DiscoverAI graph and using the **Integrated Guides** to understand the prompting logic.

## 6. Design Objectives
1.  **Zero-Config:** No need to connect to live databases or configure connection strings. The analysis is static and safe, running purely on source code.
2.  **Visual First:** Complex dependencies are abstracted into intuitive visual flows.
3.  **Explainable:** Every edge and node in the graph is backed by AI explanation, removing ambiguity.

*   **Active Comparison:** Diffing schemas and lineage between different environments/projects.
*   **Compliance Dashboard:** Automated generation of PDF audit reports for governance.

---
© 2025 DiscoverAI | Advanced Data Discovery
