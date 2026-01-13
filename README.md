# DiggerAI: Enterprise Knowledge Discovery (v7.0)

**DiggerAI** is a premium, AI-native platform for the automated reverse engineering and documentation of complex legacy data ecosystems. By combining **High-Fidelity Structural Parsing** with **Autonomous Reasoning Agents**, DiggerAI transforms opaque code (SSIS, SQL, DataStage) into actionable, navigable intelligence.

---

## 🚀 Key Features (v7.0)

### 1. Multi-Perspective Graph Intelligence
Move beyond flat lineage to multi-tiered architectural understanding:
- **Global View**: Full asset inventory and global dependencies.
- **Architecture View**: High-level execution blueprint showing flow between **Packages** and systems.
- **Package Deep Dive**: Localized, clutter-free view of a single package's internal logic and immediate context.

### 2. Autonomous Reasoning Agents
Deep extraction of logic using advanced LLM orchestration:
- **X-Ray Analysis**: AI-driven lineage with rationale and confidence scores visible in the graph.
- **Structural Parsers**: Deep traversal of **SSIS (.dtsx)** and **DataStage (.dsx)** packages.
- **Ghost Node Detection**: Identification of missing dependencies and hypothesized assets.

### 3. Interactive Lineage & Discovery
- **Deep Dive Interaction**: Seamless transition from architectural nodes to detailed column-level lineage.
- **Smart Filters**: Data-driven catalog and package filtering for instant subsetting.
- **Autonomous Discovery Agent**: An embedded chat assistant that understands the global solution graph.

### 4. Enterprise Governance Hub
Bridge findings to industry-standard catalogs:
- **Microsoft Purview**: Bulk upload format support.
- **Unity Catalog**: Lineage and Asset mapping exports.
- **dbt-Ready**: Automated `sources.yml` generation.

---

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python), Neo4j (Graph Database), Supabase (PostgreSQL).
- **Frontend**: Next.js 14, React Flow, Tailwind CSS (Glassmorphic Design).
- **Intelligence**: Gemini 2.0 Flash / GPT-4o / Claude 3.5 Sonnet orchestration.
- **Layout**: Dagre / Circular algorithmic graph positioning.

---

## ⚡ Quick Start

1.  **Configure Environment**:
    Rename `.env.example` to `.env` and provide your credentials (Supabase, LLM Providers, etc.).
2.  **Launch Platform**:
    ```bash
    python start_dev.py
    ```
    This concurrently launches the Backend, Worker, and Frontend (available at `http://localhost:3000`).

---

## 📖 Project Intelligence
- [Architecture & Logic](docs/ARCHITECTURE.md) - Deep dive into how DiggerAI "thinks".
- [Database Schema](docs/DATABASE.md) - Graph and Relational schemas.
- [Roadmap](docs/ROADMAP.md) - Release v7.5 & v8.0 plans.

---
© 2026 DiggerAI | Advanced Agentic Coding
