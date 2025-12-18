# SPEC — Multi-Model Routing (Opción A) + Pipeline de Procesamiento + Persistencia en Supabase

> Proyecto: DiscoverAI / Nexus Discovery Platform  
> Objetivo: implementar un sistema de **model routing por acción** (Opción A) + mejorar el procesamiento de archivos (repos/ZIP) con foco en **jobs, etapas y guardado en DB (Supabase)**.  
> Nota: el generador de código puede re-evaluar librerías/framework, pero debe cumplir el contrato funcional.

---

## 0) Contexto y principio de diseño

Hoy el sistema usa un **único modelo** definido en `.env` (OpenRouter) y un único prompt principal.

Problema:
- No es costo/latencia eficiente (todos los archivos pasan por el mismo modelo).
- Mezcla tareas (triage, extracción, resumen) en una sola llamada.
- Se vuelve difícil soportar “legacy complejo” (DTSX, DataStage) sin disparar costos.

Solución:
- Introducir un **router por acción** con configuración versionable y auditable.
- Estructurar el pipeline en etapas y persistir resultados + evidencias + trazas por etapa.

---

## 1) Requerimientos funcionales

### 1.1 Model Routing por acción (Opción A)
- Definir **qué modelo usar para cada acción** (triage, extract, summarize, etc.) sin tocar `.env`.
- Soportar **fallbacks** por acción (si el primer modelo falla o devuelve JSON inválido).
- Versionarse con `prompt_version` y registrarse en `job_stage_run.metrics`.

Acciones mínimas:
- `triage_fast` (barato y rápido)
- `extract_strict` (heavy: calidad/robustez)
- `summarize` (barato, para documentación)

### 1.2 Pipeline de procesamiento de repos/ZIP (enfocado a DB)
Para cada Job:
- ingestar artefacto
- listar archivos
- detectar tipo por archivo
- procesar por estrategia (parser nativo / extractor estructural / LLM)
- normalizar a un modelo común
- persistir en Supabase: assets, edges, evidencias, versiones, métricas por etapa

### 1.3 Persistencia: “DB como fuente de verdad operacional”
SQL/Supabase debe permitir:
- rastrear cada run (`job_run`)
- cada etapa (`job_stage_run`)
- inventario de activos (`asset`, `asset_version`)
- relaciones (`edge_index`) + evidencias (`evidence`, `edge_evidence`)

Neo4j queda como “serving graph” si ya está, pero el foco de este spec es **persistencia SQL**.

---

## 2) Configuración requerida

### 2.1 `.env` (solo credenciales y defaults)
Mantener `.env` mínimo:

```env
OPENROUTER_API_KEY=...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
PROMPT_VERSION=2025-12-17
MODEL_ROUTING_FILE=config/models.yml
```

### 2.2 Nuevo archivo `config/models.yml`
Formato requerido:

```yaml
version: 1
defaults:
  temperature: 0.1
  max_tokens: 1800
  timeout_ms: 60000

actions:
  triage_fast:
    model: qwen/qwen-2.5-instruct
    prompt_file: prompts/triage_fast.md
    temperature: 0.1
    max_tokens: 900

  extract_strict:
    model: deepseek/deepseek-chat
    prompt_file: prompts/extract_strict_json.md
    temperature: 0.0
    max_tokens: 2500

  summarize:
    model: qwen/qwen-2.5-instruct
    prompt_file: prompts/summarize.md
    temperature: 0.2
    max_tokens: 900

fallbacks:
  extract_strict:
    - model: qwen/qwen-2.5-coder
      prompt_file: prompts/extract_strict_json.md
      temperature: 0.0
      max_tokens: 2200
```

Reglas:
- Cada acción define: `model`, `prompt_file`, parámetros.
- `fallbacks` es opcional por acción.
- El router debe exponer `get_action_config(action_name)`.

---

## 3) Arquitectura lógica (componentes a implementar)

### 3.1 `ModelRouter`
Responsabilidades:
- leer `config/models.yml`
- validar esquema (version, defaults, actions)
- devolver config por acción (`model`, `prompt`, params)
- exponer fallbacks

### 3.2 `PromptLoader`
- lee archivo `prompt_file`
- permite interpolación controlada (ej: insertar contexto, reglas, JSON schema)
- soporta `PROMPT_VERSION`

### 3.3 `LLMClient` (OpenRouter)
- método `run(model, messages, temperature, max_tokens, timeout)`
- manejo de errores + timeouts
- retorna: `raw_text`, `usage` (tokens si existe), `latency_ms`

### 3.4 `ActionRunner`
- método `run_action(action_name, input, context)`:
  - obtiene config del router
  - construye prompt
  - llama LLMClient
  - valida salida si aplica (JSON schema)
  - aplica fallbacks si falla
- registra auditoría en `job_stage_run.metrics`:
  - `action_name`
  - `model_used`
  - `fallback_used`
  - `tokens/latency/cost_estimate` (si se puede)

---

## 4) Pipeline de procesamiento de archivos (lógica de ejecución)

### 4.1 Etapas recomendadas (job_stage_run)
1. `ingest` (crear job, guardar artifact, hash)
2. `enumerate_files` (unpack/checkout + listado)
3. `detect_types` (clasificación sin LLM)
4. `extract` (parser/structural/LLM)
5. `normalize` (IDs, canonical names, dedup)
6. `persist_sql` (assets/edges/evidence/versions)
7. `graph_sync` (opcional Neo4j)
8. `summarize_docs` (opcional: resúmenes por asset)

Cada etapa debe:
- actualizar `job_run.progress_pct` y `current_stage`
- registrar en `job_stage_run`:
  - `duration_ms`
  - `metrics` (contadores, archivos procesados, etc.)
  - `status`

### 4.2 Procesamiento por archivo (router de estrategia)
Para cada archivo (o unidad lógica):

1) **Detector** (sin LLM):
- extensión + magic bytes + tamaño
- output: `doc_type`, `complexity_hint`, `parse_available`

2) Si `parse_available=true` → ejecutar parser nativo (Nivel A)
- output: JSON parcial (nodes/edges/evidence)

3) Si no hay parser nativo:
- ejecutar `triage_fast` (acción LLM barata) con excerpt
- output: `needs_heavy`, `signals`, `candidates`, `why`

4) Decisión:
- si `needs_heavy=false` → extractor estructural (Nivel B) (regex/rules + opcional LLM barato)
- si `needs_heavy=true` → `extract_strict` (DeepSeek) (Nivel C)

5) Validación:
- `extract_strict` debe devolver JSON estricto validable
- si JSON inválido → fallback (modelo alternativo) → si sigue inválido, degradar a Nivel B

6) **Normalizer** produce entidades finales: assets, edges, evidences

---

## 5) Contratos de salida (JSON) para acciones LLM

### 5.1 `triage_fast` output (JSON simple)

```json
{
  "doc_type": "ssis_dtsx|sql|python|unknown|...",
  "signals": ["ConnectionManager", "OLEDB", "FROM dbo.X", "..."],
  "candidates": {
    "tables": ["dbo.Customer"],
    "endpoints": [],
    "files": []
  },
  "needs_heavy": true,
  "why": "Found multiple SQL tasks + many connections + large file"
}
```

### 5.2 `extract_strict` output (JSON estricto)
Debe cumplir:
- `nodes[]`, `edges[]`, `evidences[]`
- evidencia con locator (line/xpath/offset)
- edges con `confidence` + `rationale` + `evidence_refs[]`
- reglas anti-invención:
  - sin evidencia → `is_hypothesis=true` y `confidence<=0.3` (o no crear edge)

---

## 6) Cambios / extensiones de DB (Supabase)

El esquema actual ya contiene gran parte de lo necesario. Se requieren **ajustes menores** para soportar routing, auditoría y artefactos multi-model.

### 6.1 Cambios en `job_run` (agregar columnas)
Agregar:
- `artifact_hash text` (para cache/idempotencia)
- `prompt_version text`
- `routing_version text` (ej: hash o version de `models.yml`)
- `llm_provider text` (ej: "openrouter")
- `llm_default_model text` (opcional)

### 6.2 Convención en `job_stage_run.metrics`
Estandarizar claves:
- `action_name`
- `model_used`
- `fallback_used`
- `tokens_in`, `tokens_out`, `total_tokens`
- `latency_ms`
- `files_processed`, `nodes_created`, `edges_created`, `evidences_created`
- `cost_estimate_usd` (si aplica)

### 6.3 Ajustes recomendados en `evidence`
Recomendado:
- FK real a `solutions(id)` con `ON DELETE CASCADE` (si no rompe migraciones).
- agregar:
  - `artifact_id uuid`
  - `hash text` (dedup)
  - `created_at timestamptz default now()`

### 6.4 Ajustes recomendados en `edge_index`
Agregar:
- `extractor_id text`
- `rationale text`
- `created_at timestamptz default now()`
- (opcional) `edge_hash text` (upsert/dedup)

### 6.5 Ajustes recomendados en `asset_version`
Agregar:
- `artifact_id uuid`
- `last_seen_at timestamptz`
- (opcional) `metadata jsonb`

---

## 7) Persistencia: reglas de guardado

### 7.1 IDs estables + deduplicación
- `asset.canonical_name` debe ser único por `project_id` + `system` + `asset_type` (o equivalente).
- `edge_index` debe upsert por:
  - (`project_id`, `from_asset_id`, `to_asset_id`, `edge_type`) o `edge_hash`

### 7.2 Evidencias
- Guardar evidencias antes o junto con edges.
- Insertar relación en `edge_evidence` (many-to-many).

### 7.3 Atomicidad por etapa
- `persist_sql` debe ser transaccional:
  - o inserta todo el batch
  - o rollback y marca etapa failed

---

## 8) Integración con el resto del sistema

- El pipeline debe actualizar:
  - `solutions.status`: `QUEUED` → `PROCESSING` → `READY` / `ERROR`.
- `job_queue` ya existe y puede mantenerse (MVP) o reemplazarse por Redis, pero el estado se persiste en `job_run`.

---

## 9) Criterios de aceptación

### Model Routing
- Cambiar modelos por acción editando `config/models.yml`.
- Cada acción registra `model_used` y `fallback_used` en `job_stage_run.metrics`.
- Fallback se activa si:
  - timeout / error
  - JSON inválido (para `extract_strict`)
  - confidence bajo (si se implementa umbral)

### Pipeline + DB
- Para un repo/ZIP real:
  - se crea `job_run`
  - se registran etapas en `job_stage_run`
  - se crean `asset`, `asset_version`
  - se crean `edge_index`
  - se crean `evidence` + `edge_evidence`
- Si un archivo es “unknown”:
  - se registra como asset unknown y se guarda evidencia mínima (si hay señales)
- El estado del job y de la solución se actualiza correctamente.

---

## 10) Entregables esperados del generador

1. Implementación `ModelRouter`, `PromptLoader`, `LLMClient`, `ActionRunner`.
2. Creación de `config/models.yml` + carpeta `prompts/` con 3 prompts mínimos.
3. Refactor del pipeline para usar `run_action(action)` (no un único modelo global).
4. Migraciones SQL para las extensiones de tablas indicadas.
5. Guardado en DB siguiendo reglas de dedup/upsert.
6. Logs y métricas por etapa en `job_stage_run.metrics`.

