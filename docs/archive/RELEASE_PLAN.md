# DiggerAI — Plan de implementación (Jobs + Evidencias/Confianza + Catálogo SQL + UX Grafo)
> [!NOTE]
> **Status: Implemented (v4.0 Full Base)**. Este documento sirvió como el blueprint original para la evolución a V3/V4 y se mantiene como referencia histórica del diseño y los principios de confianza.

---

## 0) Objetivo general

Evolucionar el producto para que:

1. **Procese proyectos grandes** (ZIPs/repos) de forma robusta: ejecución asíncrona, reintentos, estado persistido, métricas.
2. El lineage sea **confiable y auditable**: cada relación debe tener **evidencia + locator + confidence score + rationale** (o estar marcada explícitamente como hipótesis).
3. Haya **consulta/operación a escala**: materializar un **catálogo operacional en SQL/Supabase** (assets, edges, evidencias, ejecuciones) y dejar Neo4j para navegación/traversals.
4. El grafo sea **navegable** en “hairballs”: subgrafo por defecto, filtros, path finder, estilo por confidence, panel de evidencias.

---

## 1) Principios de diseño (no negociables)

### P1. Evidencia antes que “magia”
- **No se deben crear edges “fuertes” sin evidencia mínima**.
- Si no hay evidencia:
  - `is_hypothesis=true` y `confidence <= 0.3`, **o**
  - directamente no crear el edge (configurable).

### P2. Degradación elegante para formatos raros
Como pueden llegar **paquetes propietarios** (DTSX viejo, DataStage, formatos binarios/raros), el sistema debe funcionar por niveles:

- **Nivel A (Parser nativo):** cuando exista parsing determinista confiable.
- **Nivel B (Extracción estructural):** lectura de XML/JSON/config/logs/strings/regex para inputs/outputs.
- **Nivel C (LLM inference):** inferencia guiada y estricta, devolviendo JSON validable, siempre con evidencias/locators.

### P3. CQRS práctico (Graph + SQL)
- **Neo4j**: motor de navegación, upstream/downstream, paths, subgrafos.
- **SQL/Supabase**: catálogo operacional para consultas masivas, auditoría, reporting, búsqueda y estado de jobs.

### P4. Versionado y reproducibilidad
- Todo resultado debe quedar asociado a:
  - `artifact_hash`
  - `prompt_version`
  - `extractor_id`
  - `llm_provider/model` (si aplica)

---

## 2) Roadmap por releases (implementación incremental)

### Release A — Job System + Observabilidad mínima (Fiabilidad)

#### A1. Crear Job asíncrono para procesamiento de artefactos
**User story**
- Como usuario, quiero subir un ZIP o enlazar un repo, iniciar el procesamiento, y ver su progreso sin bloquear el API.

**Requerimientos funcionales**
- Crear `Job` al subir ZIP o al registrar un repo.
- Estados mínimos: `queued`, `running`, `completed`, `failed`, `canceled` (canceled opcional).
- Progreso por etapas + métricas básicas por etapa.
- Permitir `retry` de un job fallido sin re-subir el archivo (si el artefacto se conserva).

**Pipeline (etapas mínimas)**
1. `ingest` (guardar artefacto + calcular hash)
2. `unpack` (si ZIP)
3. `detect_formats`
4. `extract_raw` (extractores A/B/C)
5. `normalize`
6. `score_confidence`
7. `write_sql_catalog`
8. `write_neo4j_graph`
9. `index_search` (opcional)

**Requerimientos técnicos (orientativo, el generador puede elegir alternativa)**
- Cola: Redis + worker(s) recomendados; alternativa MVP: cola persistida en SQL.
- Workers: proceso separado del API, escalable horizontalmente.
- Idempotencia:
  - Si `artifact_hash` + `prompt_version` ya procesado para el mismo `project_id`, permitir reutilización/cache.

**Modelo de datos (SQL/Supabase)**
- `job_run`
  - `job_id uuid pk`
  - `project_id uuid`
  - `artifact_id uuid`
  - `artifact_hash text`
  - `prompt_version text`
  - `status text`
  - `progress_pct int`
  - `current_stage text`
  - `created_at timestamptz`
  - `started_at timestamptz`
  - `finished_at timestamptz`
  - `llm_provider text`
  - `llm_model text`
  - `error_message text`
  - `error_details jsonb`
- `job_stage_run`
  - `id uuid pk`
  - `job_id uuid fk`
  - `stage_name text`
  - `status text`
  - `started_at timestamptz`
  - `finished_at timestamptz`
  - `duration_ms bigint`
  - `metrics jsonb`
  - `error jsonb`

**API (backend)**
- `POST /api/projects/{project_id}/jobs`
  - body: `{ "source_type": "zip"|"github", "source_ref": "...", "options": {...} }`
  - response: `{ "job_id": "..." }`
- `GET /api/jobs/{job_id}` → estado + progreso + métricas
- `GET /api/projects/{project_id}/jobs?limit=...`
- `POST /api/jobs/{job_id}/retry`
- (opcional) `POST /api/jobs/{job_id}/cancel`

**Frontend**
- Vista de estado del job: barra de progreso + lista de etapas
- Acción retry (si failed)
- Polling cada X segundos (o SSE/websocket si se implementa)

**Criterios de aceptación**
- Un ZIP grande no bloquea el request.
- Se ve progreso por etapas.
- Si falla, queda registrado en DB con detalles.
- Retry funciona.

---

### Release B — Evidencias + Confidence como “first class” (Trust)

#### B1. Contrato JSON estricto para extractores (parsers y LLM)
**User story**
- Como usuario, quiero entender por qué existe una relación en el grafo y poder auditar su origen.

**Requerimientos funcionales**
- Cada edge debe incluir:
  - `confidence (0..1)`
  - `rationale` (texto breve)
  - `evidence_refs[]`
  - `extractor_id`
  - `is_hypothesis`

**Output obligatorio del extractor (JSON validable)**
```json
{
  "meta": {
    "extractor_id": "ssis_xml_parser|regex_fallback|llm_inference",
    "project_id": "...",
    "artifact_id": "...",
    "prompt_version": "...",
    "source_file": "path/in/artifact"
  },
  "nodes": [
    {
      "node_id": "stable-id",
      "node_type": "table|view|file|api|process|package|task|script",
      "name": "dbo.Customer",
      "system": "sqlserver|files|api|unknown",
      "attributes": { "schema": "dbo", "db": "...", "conn": "..." }
    }
  ],
  "edges": [
    {
      "edge_id": "stable-id",
      "edge_type": "READS_FROM|WRITES_TO|DEPENDS_ON|CALLS_API|CONTAINS",
      "from_node_id": "...",
      "to_node_id": "...",
      "confidence": 0.0,
      "rationale": "short string",
      "evidence_refs": ["ev_1","ev_2"],
      "is_hypothesis": false
    }
  ],
  "evidences": [
    {
      "evidence_id": "ev_1",
      "kind": "code|xml|log|config|regex_match",
      "locator": {
        "file": "....",
        "line_start": 10,
        "line_end": 18,
        "xpath": "....",
        "byte_start": 1200,
        "byte_end": 1400
      },
      "snippet": "short excerpt (max N chars)",
      "hash": "sha256(snippet+locator)"
    }
  ],
  "assumptions": ["..."]
}
```

**Reglas anti-invención**
- Si no hay evidencia mínima:
  - no crear edge, o
  - crear con `is_hypothesis=true` + `confidence <= 0.3`.
- Si el modelo no puede devolver JSON válido:
  - reintento con “repair prompt”,
  - si sigue fallando, degradar a extracción estructural.

#### B2. Persistir evidencias en SQL/Supabase
**Tabla `evidence`**
- `evidence_id uuid pk`
- `project_id uuid`
- `artifact_id uuid`
- `file_path text`
- `kind text`
- `locator jsonb`
- `snippet text`
- `hash text`
- `created_at timestamptz`

#### B3. Confidence scoring centralizado
**Módulo** `confidence_scoring`
- Base por extractor:
  - parser nativo: +0.6
  - extractor estructural: +0.4
  - LLM inference: +0.2
- Boost si evidencia explícita:
  - SQL literal / XML target / log directo: +0.2
- Clamp 0..1

#### B4. Neo4j: propiedades en edges
- Guardar en cada relación:
  - `edge_id`, `confidence`, `extractor_id`, `is_hypothesis`, `evidence_count`
- **Evitar** cargar snippets en Neo4j; deben vivir en SQL.

#### B5. UI: estilo por confidence + panel de evidencias
- Edges:
  - `>=0.75`: sólido
  - `0.4..0.74`: intermedio
  - `<0.4` o `is_hypothesis`: punteado + warning
- Click edge:
  - panel “Evidence”: snippets + locator (archivo/líneas/xpath/offset)
  - botón copiar snippet / abrir archivo (si hay viewer)

**Criterios de aceptación**
- Todo edge visible tiene confidence y evidencia consultable (o está marcado como hipótesis).
- El usuario puede ver “por qué”.

---

### Release C — Catálogo SQL + Edge Index (Consulta masiva)

#### C1. Materializar assets/edges para BI, búsqueda y auditoría
**User story**
- Como usuario, quiero listar assets, filtrar por tags/confidence, ver “top dependencias”, sin depender de queries pesadas en Neo4j.

**Tablas (mínimas)**
- `asset`
  - `asset_id uuid pk`
  - `project_id uuid`
  - `asset_type text`
  - `name_display text`
  - `canonical_name text`
  - `system text`
  - `tags jsonb`
  - `owner text`
  - `created_at timestamptz`
  - `updated_at timestamptz`
- `asset_version`
  - `asset_version_id uuid pk`
  - `asset_id uuid fk`
  - `artifact_id uuid`
  - `source_file text`
  - `hash text`
  - `first_seen_at timestamptz`
  - `last_seen_at timestamptz`
- `edge_index`
  - `edge_id uuid pk`
  - `project_id uuid`
  - `from_asset_id uuid`
  - `to_asset_id uuid`
  - `edge_type text`
  - `confidence numeric`
  - `extractor_id text`
  - `is_hypothesis bool`
  - `created_at timestamptz`
- `edge_evidence` (normalizado)
  - `edge_id uuid`
  - `evidence_id uuid`

**Sincronización**
- En `write_sql_catalog`:
  - upsert `asset`
  - upsert `asset_version`
  - upsert/insert `edge_index`
  - insert `edge_evidence`

**Neo4j**
- Reutilizar `asset_id` como ID estable del nodo (propiedad), para evitar duplicados.
- Guardar `edge_id` como propiedad para cruzar con SQL.

**API**
- `GET /api/projects/{project_id}/assets?search=...&type=...`
- `GET /api/projects/{project_id}/edges?min_conf=...&type=...&from=...&to=...`
- `GET /api/edges/{edge_id}/evidences`
- `GET /api/assets/{asset_id}/summary`
- `GET /api/assets/{asset_id}/neighbors?depth=1&direction=up|down&min_conf=...`

**Frontend**
- Nueva vista “Assets catalog” (tabla + búsqueda + filtros)
- Desde asset: abrir subgrafo centrado

**Criterios de aceptación**
- Consultas masivas (top assets, filtros) se resuelven en SQL.
- Neo4j queda para paths/traversals.

---

### Release D — UX Grafo a escala (Hairball killer)

#### D1. Subgrafo por defecto + filtros
**Requerimientos funcionales**
- No renderizar el grafo completo por defecto.
- Controles:
  - `Depth (k)` upstream/downstream
  - `Min confidence`
  - `Tipos de nodo`
  - `Mostrar hipótesis` (on/off)
  - `Límite de nodos/edges` (hard limit)

**Backend (Neo4j endpoints)**
- `POST /api/graph/subgraph`
  - body: `{ center_asset_id, depth, direction, min_conf, node_types, include_hypothesis, limit_nodes, limit_edges }`
- Respuesta: `{ nodes: [...], edges: [...] }`

#### D2. Path Finder
- `POST /api/graph/path`
  - body: `{ from_asset_id, to_asset_id, max_hops, min_conf, top_k_paths }`
- Respuesta: lista de paths (y opción de renderizarlos)

**Frontend**
- Panel de filtros siempre visible
- UI para seleccionar dos nodos y ejecutar “Find Path”
- Render path destacado

**Criterios de aceptación**
- Proyecto grande abre rápido (subgrafo).
- Se encuentran caminos y se renderizan sin colapsar la UI.

---

## 3) Piezas a construir/actualizar (impacto)

### Backend — Nuevos módulos sugeridos (orientativo)
- `jobs/`
  - `queue.py` (enqueue/dequeue)
  - `worker.py`
  - `stages/*.py`
  - `state_store.py`
- `extractors/`
  - `detector.py`
  - `ssis_parser.py`
  - `regex_extractor.py`
  - `llm_extractor.py`
  - `registry.py` (chain A/B/C)
- `normalizer/`
  - `model.py` (Node/Edge/Evidence)
  - `normalize.py`
  - `validators.py` (JSON schema)
- `scoring/confidence.py`
- `writers/`
  - `sql_catalog_writer.py`
  - `neo4j_writer.py`

### Backend — Cambios en endpoints
- Agregar endpoints de jobs, assets, edges, evidences, subgraph/path.
- Autorización estricta por `project_id` (multi-tenant).

### Frontend — Cambios principales
- Pantalla Job Status por proyecto
- Assets Catalog
- Grafo con subgrafo + filtros
- Panel evidence al click de edge
- Path finder

---

## 4) Prompting / LLM (requerimientos para el generador)

### Prompt versioning
- Almacenar `prompt_version` y “hash del prompt” (opcional) por job.

### Validación strict del output
- El extractor LLM debe devolver JSON acorde al esquema.
- Si JSON inválido:
  - reintentar (repair prompt),
  - si falla, degradar a extractor estructural.

### Control de costes
- Cache por `artifact_hash + prompt_version + extractor_id + source_file_hash`.
- Guardar métricas (tokens/costo estimado) en `job_stage_run.metrics`.

---

## 5) Seguridad / aislamiento (mínimo viable)
- Todo registro SQL debe incluir `project_id`.
- RLS (Row Level Security) en Supabase (si aplica).
- Auditoría básica:
  - quién subió artefacto
  - cuándo corrió job
  - qué modelo LLM se usó

---

## 6) Definición de Done (global)
- Jobs asíncronos con estado persistido + retry.
- Cada edge del grafo:
  - `confidence`, `extractor_id`, `is_hypothesis`
  - evidencias consultables desde UI (snippets + locator).
- SQL permite:
  - listar assets
  - filtrar edges por confidence/tipo
  - reporting básico (top dependencias)
- Grafo navegable con subgrafos, filtros y path finder.

---

## 7) Entregables esperados (para el generador)
1. Migraciones SQL (DDL) para tablas nuevas.
2. Implementación backend de jobs + workers + etapas pipeline.
3. Implementación de esquema JSON + validators + confidence scoring.
4. Writers para SQL y Neo4j (sin duplicación indebida).
5. Endpoints REST nuevos.
6. Cambios frontend: Job status, Assets catalog, Grafo (subgrafo/filtros/evidencias/path).
7. Tests mínimos: unit + integración end-to-end con ZIP de prueba.

---

## 8) Notas finales (libertad del generador)
- El generador puede elegir la librería/framework de cola (Redis+RQ/Celery/Arq/BullMQ/etc.) y la estrategia de worker; lo importante es cumplir:
  - asincronía real
  - estado persistido
  - reintentos
  - métricas por etapa
- El generador puede optimizar el modelo (edge_index vs edge_evidence array) según performance y simplicidad.
- El generador puede proponer mejoras de performance (batch writes, límites en subgrafo, caching) siempre que mantenga el contrato evidence/confidence.

