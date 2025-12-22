# Nexus Discovery Platform (v2.0)

## Overview
Nexus Discovery is a SaaS platform for automated reverse engineering of data code (SSIS, SQL, Python) using Generative AI. It extracts data lineage, creates documentation, and visualizes relationships in a Knowledge Graph.

## 🚀 What's New in v2.0
- **Advanced Pipeline Orchestrator**: A robust, stage-based engine (Ingest -> Enumerate -> Extract -> Persist) that handles failures gracefully.
- **Deep Lineage Extraction**: "Senior Data Engineer" prompts that extract granular details like SQL Queries, Column Transformations, and Complex Data Flows.
- **Resilient AI Execution**: The new `ActionRunner` handles Rate Limits, Context Windows, and JSON Validation errors automatically, with smart fallbacks (e.g., Llama 3 70B -> 8B).
- **Universal Ingestion**: Support for both **ZIP File Uploads** and **Git Repository Cloning**.
- **Self-Healing Jobs**: Automatic re-queuing of failed jobs and partial result persistence.

## Documentation
- [Functional Specification](docs/FUNCTIONAL_SPEC.md)
- [Release Plan](docs/RELEASE_PLAN.md)
- [Database Schema](docs/DATABASE_SCHEMA.md)
- [Roadmap & Known Issues](docs/ROADMAP.md)

## Prerequisites
1.  **Python 3.11+**
2.  **Node.js 18+**
3.  **Supabase Project** (Free Tier): [Create one here](https://supabase.com/)
    *   Required: `URL` and `ANON_KEY`.
    *   Setup: Run `db.sql` in Supabase SQL Editor.
4.  **Neo4j AuraDB** (Free Tier): [Create one here](https://neo4j.com/cloud/aura/)
    *   Required: `URI`, `Username`, and `Password`.
5.  **LLM Provider**:
    *   **Groq** (Recommended for speed/cost): Get API Key at [console.groq.com](https://console.groq.com).
    *   **OpenAI/Azure**: Supported but requires configuration adjustment.

## Setup & Run

### ⚡ Quick Start (Recommended)
We provide a unified launcher script to start all services (API, Worker, Web) simultaneously in separate windows.

1.  **Configure Environment**:
    Create `.env` in the root folder (see `.env.example`).
2.  **Run Launcher**:
    ```bash
    # From project root
    python start_dev.py
    ```
    This will launch:
    *   **API** on http://localhost:8000
    *   **Web** on http://localhost:3000
    *   **Celery Worker** (Background processing)

---

### 🔧 Manual Setup
If you prefer running services individually:

#### 1. Backend (FastAPI)
Open a terminal in `apps/api`:
```bash
cd apps/api
# Create venv (optional but recommended)
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run API Server
python -m uvicorn app.main:app --reload --port 8000
```

#### 2. Worker (Pipeline Engine)
**Crucial:** The worker processes file uploads asynchronously.
Open a NEW terminal in `apps/api`:
```bash
cd apps/api
# Activate venv if used
.\.venv\Scripts\activate

# Run Worker
python -m app.worker
```

#### 3. Frontend (Next.js)
Open a NEW terminal in `apps/web`:
```bash
cd apps/web
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

## 🛠️ Utility Scripts
Useful scripts for debugging and maintenance are located in `apps/api/scripts/`:
*   `system_reset.py`: **Hard Reset**. Wipes Neo4j and Supabase data for a fresh start.
*   `check_db_ready.py`: Verifies Supabase tables exist.
*   `check_neo4j.py`: Tests Neo4j connectivity.

## Architecture Highlights
- **Pipeline V2**: Robust, stage-based processing engine (Ingest -> Enumerate -> Extract -> Persist -> Graph).
- **ActionRunner**: Modular AI execution handling fallbacks (e.g., Llama 3 70B -> 8B) and rate limits.
- **Strict JSON Extraction**: Specialized prompts ensure clean data extraction for SSIS and SQL.
