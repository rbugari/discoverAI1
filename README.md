# Nexus Discovery Platform (v4.0)

## Overview
Nexus Discovery is a SaaS platform for automated reverse engineering of data code (SSIS, SQL, Python) using Generative AI. It extracts data lineage, creates documentation, and visualizes relationships in a Knowledge Graph.

## 🚀 What's New in v4.0 (Deep Understanding)
- **Package Deep Dive**: Granular extraction of internal ETL logic (SSIS/DataStage), mapping tasks, components, and embedded SQL.
- **Column-Lineage Backend**: Precise field-to-field tracking and transformation rule extraction.
- **Silent Mode (Auto-Approval)**: Automated E2E processing without manual plan confirmation (`requires_approval: false`).
- **LLM Resilience**: Native retry & exponential backoff system for 429 rate limit errors.
- **Gemini 2.0 Integration**: Optimized routing to Gemini 2.0 Flash Lite for superior technical discovery.
- **Tracing & Diagnostics**: Enhanced worker-level logging for loop integrity and file read validation.

## 🛠️ Utility Scripts
Useful scripts for debugging and maintenance:
*   `apps/api/scripts/system_reset.py`: **Hard Reset**. Wipes Neo4j and Supabase data.
*   `scripts/check_llm_env.py`: Verifies LLM API keys and connectivity.
*   `scripts/check_db_status.py`: Reports synchronization status between Supabase and Neo4j.
*   `start_dev.py`: Unified launcher for API, Web, and Worker from the root.

---

## 📋 Prerequisites
1.  **Python 3.11+**
2.  **Node.js 18+**
3.  **Supabase Project** (Free Tier)
4.  **Neo4j AuraDB** (Free Tier)

## ⚡ Quick Start
1.  **Configure Environment**:
    Create a `.env` file in the root directory (use `.env.example` as a template).
2.  **Unified Launch**:
    Run the launcher from the project root:
    ```bash
    python start_dev.py
    ```
    This script automatically starts the **Backend (FastAPI)**, **Worker (Celery)**, and **Frontend (Next.js)** in separate windows.

---

## 🏗️ Architecture Highlights
- **V3 Orchestrator**: Stage-based engine (Ingest -> Plan -> Extract -> Persist -> Neo4j Sync).
- **ConfigManager**: Centralized configuration for providers (`config/providers/`) and routings (`config/routings/`).
- **ActionRunner**: Modular AI execution with automatic error fallbacks and rate limiting.
- **Truly Incremental**: Hash-based file tracking ensures you never pay twice for the same analysis.

## 📝 Documentation
- [Functional Specification](docs/FUNCTIONAL_SPEC.md)
- [V3 Technical Spec](docs/V3_SPEC.md)
- [Database Schema](docs/DATABASE_SCHEMA.md)
