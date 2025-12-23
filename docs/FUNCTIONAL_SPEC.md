# Nexus Discovery - Functional Specification (v3.1)

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

## 4. Key Features (Release v3.1)

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

### 4.5. Governance & Export
*   **Project Isolation:** Secure workspaces ensure data from different projects (e.g., "Marketing Migration" vs "Finance Audit") never mixes.
*   **CSV Export:** Full export capability for offline analysis or integration with other documentation tools.

## 5. Use Cases

### Case A: The "Black Box" Migration
**Scenario:** A retailer needs to migrate 500 SSIS packages to Databricks. The original developers left years ago.
**Solution:** The team uploads the SSIS ZIP to Nexus Discovery. Within minutes, they have a visual map of all data flows. They identify that only 50 tables are critical for the migration, prioritizing effort and identifying redundant pipelines immediately.

### Case B: Impact Analysis
**Scenario:** A DBA needs to change the schema of the `DimCustomer` table but fears breaking downstream reports.
**Solution:** Using the Graph View, the DBA selects `DimCustomer` and instantly sees 3 ETL scripts and 2 Reporting Views that depend on it. They can now plan the schema change with zero unexpected downtime.

### Case C: New Hire Onboarding
**Scenario:** A new Senior Engineer joins the team and asks, "How does our data warehouse get populated?"
**Solution:** Instead of reading thousands of lines of code, they spend 15 minutes exploring the Nexus Discovery graph, using the "Chat" feature to ask high-level architectural questions.

## 6. Design Objectives
1.  **Zero-Config:** No need to connect to live databases or configure connection strings. The analysis is static and safe, running purely on source code.
2.  **Visual First:** Complex dependencies are abstracted into intuitive visual flows.
3.  **Explainable:** Every edge and node in the graph is backed by AI explanation, removing ambiguity.

## 7. Future Roadmap (Preview)
*   **Enterprise Sync:** Integration with Microsoft Purview and Databricks Unity Catalog.
*   **Column-Level Lineage:** Deep tracing of individual fields through transformations.
*   **Compliance Reporting:** Automated generation of PDF audit reports.
