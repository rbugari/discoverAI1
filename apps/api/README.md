# Nexus Discovery API & Worker

This directory contains the FastAPI backend and the Asynchronous Worker for the Nexus Discovery Platform.

## Architecture

### 1. API (FastAPI)
- Handles User Management, File Uploads, Job Creation, and Dashboard endpoints.
- **Entry Point**: `app/main.py`
- **Port**: 8000

### 2. Worker (Pipeline V2)
- Polling-based worker that processes jobs from the `jobs` table in Supabase.
- **Entry Point**: `app/worker.py`
- **Logic**: `app/services/pipeline_v2.py`
- **Features**:
    - **Stage-based Processing**: Ingest, EnumerateFiles, ExtractLineage, PersistResults, UpdateGraph.
    - **ActionRunner**: Wrapper for LLM calls with Fallback logic (70B -> 8B) and Error Handling.
    - **LLM Adapter**: Unified interface for Groq, OpenAI, Azure.

## Configuration

### Environment Variables
Managed via `.env` in the project root. See `README.md` in root for details.

### AI Models Configuration (`config/models.yml`)
We use a YAML configuration file to define strategies and models for different tasks.
Location: `apps/api/config/models.yml`

Structure:
- **Strategies**: Define which model to use for `triage`, `extract_strict`, `summarize`, etc.
- **Fallbacks**: Define backup models if the primary fails.

**Current Default (Groq):**
- **Heavy Tasks** (SSIS/SQL Extraction): `llama-3.3-70b-versatile`
- **Light Tasks** (Triage/Simple Extraction): `llama-3.1-8b-instant`

### Prompts
Prompts are stored in `apps/api/app/prompts/` as text or markdown files.
They are referenced in `models.yml`.
**Note:** Prompts do NOT contain `{content}` placeholders anymore. The file content is sent as a User Message to the LLM to handle large files correctly.

## Development

### Running Tests
Integration tests simulate the full pipeline flow.
```bash
# Run V3 Integration Test (Full Repo)
python scripts/test_integration_v3.py
```

### Debugging
- Worker logs are printed to stdout.
- Use `check_command_status` in Trae/Agent to view logs.
- `ActionRunner` prints DEBUG info about Prompt Lengths.

### Utility Scripts
- `scripts/system_reset.py`: Wipes Supabase (Postgres) and Neo4j completely. Useful for starting fresh.
- `scripts/test_integration_v3.py`: Runs a full pipeline test with a sample SSIS project.

## Troubleshooting

### "Please reduce the length of the messages" (Groq 400)
- This means the input file is too large for the model's context or Groq's API limit.
- **Solution**: The `ActionRunner` automatically truncates inputs to ~400k characters for paid keys (or lower for free tier).
- If persistent, check `app/actions/__init__.py` truncation logic.

### 0 Assets Found
- Check if `extract_strict` prompt is correctly extracting JSON.
- Verify `models.yml` is pointing to the right prompt file.
- Ensure `LLM_PROVIDER` is set correctly in `.env`.
