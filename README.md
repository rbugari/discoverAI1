# DiscoverAI Platform (v4.0 Full Base)

DiscoverAI is a premium SaaS platform for automated reverse engineering and documentation of legacy data systems (SSIS, DataStage, SQL, Python). It combines **Structural Parsing** with **Hierarchical LLM Orchestration** to extract high-fidelity lineage and build enterprise knowledge graphs.

## 🚀 Key Features (v4.0)

### 1. High-Fidelity Structural Parsers
Deep extraction of internal ETL logic without the noise of pure LLM analysis:
- **SSIS (.dtsx)**: Detailed traversal of Control Flow, Data Flow Tasks, and embedded SQL.
- **DataStage (.dsx)**: Structural extraction of stages, links, and metadata.

### 2. Hierarchical Prompting (The Brain)
A 4-layer intelligence model that respects both global standards and local project nuances:
- **Base Layer**: Core technical logic.
- **Domain Layer**: Specialist knowledge (SSIS, DataStage, DB2, etc.).
- **Org Layer**: Corporate standards and quality guidelines.
- **Solution Layer**: Project-specific rules (e.g., "Northwind" mappings and normalization).

### 3. Governance Hub (Manual Gateway)
Bridge findings to enterprise catalogs via platform-specific export gateways:
- **Microsoft Purview**: Bulk upload CSV format.
- **Unity Catalog**: Lineage & Asset CSV exports.
- **dbt**: Automated `sources.yml` generation.

### 4. Integrated Documentation
Self-service guidance directly within the UI (Prompt Manager & Model Config) to help users understand and tune the system's "IQ".

---

## 🛠️ Architecture & Core Components

- **V4 Orchestrator**: Stage-based engine (Ingest → Plan → Extract → Persist → Neo4j Sync).
- **Prompt Matrix**: Unified dashboard for managing multi-layer agent instructions.
- **Model Router**: Dynamic dispatching of tasks across LLM providers (Gemini, Llama, GPT-4o).
- **Audit System**: Granular tracking of all AI reasoning and file processing logs.

---

## ⚡ Quick Start

1.  **Configure Environment**:
    Rename `.env.example` to `.env` and provide your API keys (Supabase, Neo4j, LLM providers).
2.  **Launch Platform**:
    ```bash
    python start_dev.py
    ```
    This launches the Backend (FastAPI), Worker, and Frontend (Next.js) concurrently.

---

## 📖 Documentation
- [Evolution History (v4.0)](docs/v4_EVOLUTION_HISTORY.md)
- [Functional Specification](docs/FUNCTIONAL_SPEC.md)
- [Database Schema](docs/DATABASE_SCHEMA.md)
- [Roadmap & Issues](docs/ROADMAP.md)

---
© 2025 DiscoverAI | Advanced Data Discovery
