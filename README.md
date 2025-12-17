# Nexus Discovery Platform (Direct Run / No Docker)

## Overview
Nexus Discovery is a SaaS platform for automated reverse engineering of data code using AI.

## Prerequisites
1.  **Python 3.11+**
2.  **Node.js 18+**
3.  **Supabase Project** (Free Tier): [Create one here](https://supabase.com/)
    *   You need the `URL` and `ANON_KEY`.
    *   Run the `db.sql` script in the Supabase SQL Editor.
4.  **Neo4j AuraDB** (Free Tier): [Create one here](https://neo4j.com/cloud/aura/)
    *   You need the `URI`, `Username`, and `Password`.

## Setup & Run

### 1. Configuration
Create a `.env` file in the root `discoverIA` folder (copy from `.env.example`) and fill in your cloud credentials:
```ini
NEO4J_URI=neo4j+s://your-aura-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
OPENAI_API_KEY=your-key
```

### 2. Backend (FastAPI)
Open a terminal in `apps/api`:
```bash
cd apps/api
# Install dependencies
pip install -r requirements.txt
# Run Server
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Worker (Background Processor)
**Crucial:** You need a separate terminal for the worker that processes the files.
Open a new terminal in `apps/api`:
```bash
cd apps/api
python -m app.worker
```

### 4. Frontend (Next.js)
Open a new terminal in `apps/web`:
```bash
cd apps/web
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.