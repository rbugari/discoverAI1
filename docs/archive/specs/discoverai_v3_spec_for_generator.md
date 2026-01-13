# DiscoverAI v3.0 — Spec de implementación (para generador de código)

> Objetivo: evolucionar v2 (pipeline “Ingest → Enumerate → Extract → Persist”) hacia v3 con **Planificación previa**, **priorización por valor/riesgo**, **control de orden por el usuario**, **estimación de coste/tiempo**, y **ejecución guiada por plan**, manteniendo la persistencia en Supabase como fuente de verdad y el grafo como *vista* / derivado.

---

## 0) Contexto / baseline (estado v2)

### Qué ya existe (no romper)
- Motor por etapas (pipeline stage-based) y ejecución resiliente (ActionRunner con reintentos/fallbacks).  
- Ingesta universal: ZIP o Git repo.  
- Persistencia: Supabase (catálogo + evidencias + edges) y Neo4j para visualización/grafo.  

---

## 1) Principios de v3 (decisiones duras)

1. **Schema-first**: siempre que haya SQL/DDL/migrations, se procesa antes que los ETLs/paquetes.
2. **Lineage crítico = parsing + evidencia**, no solo “texto del LLM”.
3. **Plan primero, ejecución después**: la ejecución NO arranca sin plan aprobado.
4. **Heterogeneidad**: repos de data traen *de todo*; el sistema debe clasificar y definir estrategia por tipo.
5. **Cost-aware**: cada item tiene estimación de coste/tiempo y un “recommended action”.
6. **DB-first**: la DB debe ser consultable para modelos grandes: el grafo es una proyección; el catálogo es la verdad.

---

## 2) Feature principal v3: “Planner” (Fase 1) + “Executor” (Fase 2)

### 2.1 Fase 1 — Planner (barata, rápida, con heurísticas)
Dado un ZIP o repo:
1. Enumerar archivos + metadatos (path, size, extensión, hash, sample head)
2. Clasificar cada archivo en:
   - **FOUNDATION**: SQL/DDL/migrations, data contracts, diccionarios, readmes relevantes
   - **ORCHESTRATION**: jobs/pipelines (ADF/Airflow/etc), “control plane”
   - **ETL_PACKAGE**: SSIS (.dtsx), DataStage (.dsx), etc
   - **TRANSFORM_SCRIPT**: .py/.ipynb/.sql DML, etc
   - **CONFIG/CONNECTIONS**: yamls/envs/configs (sin secretos)
   - **MEDIA**: png/jpg/pdf (opcional)
   - **NOISE**: backups, binarios, dumps ilegibles
3. Agrupar en “Áreas” (mínimo 2, recomendado 3):
   - **Área A — General / Foundation**
   - **Área B — Paquetes / Orquestación / Ejecución**
   - **Área C — Aux/Noise/Media** (default SKIP salvo toggle)
4. Para cada item, generar:
   - `strategy`: PARSER_ONLY | PARSER_PLUS_LLM | LLM_ONLY | SKIP
   - `risk_score` (0..100)
   - `value_score` (0..100)
   - `estimated_tokens`, `estimated_seconds`, `estimated_cost_usd` (aprox)
   - `recommended_action`: PROCESS | SKIP | REVIEW
   - `dependencies_hint`: (ej: “este SSIS parece referenciar tablas X” si se detecta rápido)
5. Devolver “Plan” persistido en DB.

### 2.2 Fase 2 — Executor (costosa, precisa, guiada por plan)
- Ejecuta estrictamente el plan aprobado.
- Respeta orden:
  1) Primero Área A (Foundation)
  2) Luego Área B
  3) Área C solo si el usuario habilita
- Dentro de cada área, respeta `order_index` definido por usuario o por heurística.
- Guarda siempre:
  - evidencias (snippets/locators)
  - assets (y versiones)
  - edges con confianza y flag hypothesis

---

## 3) UI/UX v3 (mínimo viable)
Agregar una pantalla / paso intermedio “Plan Review”:

- Vista por áreas (tabs/accordion)
- Lista de items con:
  - checkbox (process/skip)
  - badge de tipo
  - estimación (tiempo/costo)
  - warning (archivo enorme/ilegible/backup)
  - sugerencia (recommended action)
- Reordenamiento:
  - drag & drop dentro del área
  - (opcional) reordenamiento de áreas
- Botón: **Approve & Run**
- Toggle: `Low-cost plan` / `Deep plan` (impacta heurísticas vs LLM en planning)
- Toggle: `Enable media/vision`

---

## 4) Cambios en DB (Supabase) — NUEVAS TABLAS v3

> Basado en el esquema actual (solutions, job_run, job_stage_run, job_queue, asset, edge_index, evidence, edge_evidence).

### 4.1 `job_plan` (1 por job_run)
- `plan_id` UUID PK
- `job_id` UUID FK → job_run.job_id
- `status` TEXT: draft | ready | approved | rejected | superseded
- `mode` TEXT: low_cost | deep_scan
- `created_at`, `updated_at`
- `summary` JSONB (totales por tipo, total_est_cost, total_est_time)
- `user_overrides` JSONB (opcional)

### 4.2 `job_plan_area`
- `area_id` UUID PK
- `plan_id` UUID FK
- `area_key` TEXT: FOUNDATION | PACKAGES | AUX
- `title` TEXT
- `order_index` INT
- `default_enabled` BOOL

### 4.3 `job_plan_item`
- `item_id` UUID PK
- `plan_id` UUID FK
- `area_id` UUID FK
- `path` TEXT
- `file_hash` TEXT
- `size_bytes` BIGINT
- `file_type` TEXT (SQL, DTSX, DSX, PY, etc)
- `classifier` JSONB (features que llevaron a la clasificación)
- `strategy` TEXT
- `recommended_action` TEXT (PROCESS/SKIP/REVIEW)
- `enabled` BOOL (editable por usuario)
- `order_index` INT (editable por usuario)
- `risk_score` INT
- `value_score` INT
- `estimate` JSONB (tokens/seconds/cost)
- `planning_notes` TEXT
- `created_at`

### 4.4 Ajustes a `job_run`
- agregar:
  - `plan_id` UUID (FK lógico al plan vigente)
  - `requires_approval` BOOL default true
  - `current_item_id` UUID (para progreso fino)

---

## 5) Backend — endpoints y servicios (FastAPI)

### 5.1 Endpoints nuevos
- `POST /solutions/{solution_id}/plans`  
  Crea plan para la última carga (ZIP/Git) y devuelve `plan_id`.

- `GET /plans/{plan_id}`  
  Devuelve plan completo (areas + items + estimaciones).

- `PATCH /plans/{plan_id}`  
  Permite:
  - enable/disable items
  - cambiar order_index
  - cambiar mode
  - cambiar area order_index (opcional)

- `POST /plans/{plan_id}/approve`  
  Cambia estado a approved y encola ejecución del job.

- `POST /plans/{plan_id}/reject`  
  Rechaza plan (no ejecuta).

### 5.2 Servicios nuevos
- `PlannerService`
  - `inventory(repo|zip) -> FileIndex[]`
  - `classify(file) -> classification`
  - `estimate(file, strategy) -> estimate`
  - `build_plan(index) -> job_plan + items`
- `ExecutionService`
  - `run_plan(plan_id)`
  - iteración por (area.order_index, item.order_index) con checkpoint
- `Estimator`
  - heurísticas por tamaño/extensión + multiplicadores por modo/modelo
- `PolicyEngine`
  - reglas de “SKIP” (binarios grandes, backups, vendor caches, node_modules, etc)
  - allowlist/denylist configurable por solution.config

### 5.3 Worker / cola
- El worker debe aceptar 2 tipos de jobs:
  - `planning` (rápido) → genera plan
  - `execution` (largo) → procesa items habilitados

---

## 6) Modelo(s) y prompts — separación por acción (v3)

### 6.1 Solución v3: “Action Profiles”
Definir perfiles por acción:
1) **planner.classifier** (rápido/barato)
2) **extract.schema** (prioritario, alta precisión)
3) **extract.lineage.package** (SSIS/DataStage)
4) **extract.lineage.sql** (DML/transform)
5) **summarize.asset** (barato)
6) **qa.chat** (contexto grafo)

Cada profile define:
- `model`
- `temperature`
- `max_tokens`
- `prompt_template`
- `json_schema` esperado
- `fallback_models` (rápidos→más capaces)

---

## 7) Parsing “de verdad” para legacy (SSIS/DataStage)

### 7.1 Regla
Para lineage crítico, preferir:
1) Parser estructural (XML/exports)
2) Enriquecimiento con LLM solo para:
   - nombres amigables
   - explicación
   - mapping cuando el parser no llega

### 7.2 Implementación mínima v3
- SSIS `.dtsx`:
  - parse XML
  - extraer connection managers
  - detectar sources/destinations
  - capturar query text si existe
  - guardar evidence con xpath/atributos

- DataStage `.dsx`:
  - parsing por secciones / regex robusta
  - extraer stages, links, dataset/table refs
  - evidence por offsets de texto

---

## 8) Persistencia y consultabilidad (DB-first)

### 8.1 Qué persistir siempre
- `asset` + `asset_version` para cada hallazgo
- `edge_index` con confidence + hypothesis
- `evidence` por cada hallazgo importante
- `edge_evidence` linking

### 8.2 Evitar “todo en el grafo”
- Neo4j solo como:
  - proyección para UI
  - consultas exploratorias
- Supabase = fuente para reporting, export, métricas, auditoría

---

## 9) Métricas
Agregar métricas por job:
- total_files
- processed_files
- skipped_files (por razón)
- total_edges / edges_confident / edges_hypothesis
- evidence_count
- tokens_by_action
- cost_by_action
- time_by_stage + time_by_action

---

## 10) Plan de trabajo (v3.0 incremental)

### Sprint 1 — Planner + DB + UI básica
- nuevas tablas job_plan/*
- endpoint create/get/patch/approve
- UI Plan Review con enable/disable + reorder
- worker planning

### Sprint 2 — Executor por plan
- ejecución guiada por items
- checkpoint por item
- progreso fino

### Sprint 3 — Prompt + routing por acción
- action profiles en config
- prompts versionados
- fallbacks por acción

### Sprint 4 — Parsing legacy mejorado
- SSIS parser robusto + evidence
- DataStage parser base

---

## 11) Criterios de aceptación (Definition of Done)

1. Subo ZIP/repo → se crea plan en < 30-90s (dependiendo tamaño).
2. El plan viene con:
   - áreas (A/B/C)
   - orden por defecto (schema-first)
   - estimaciones y recommended action
3. Puedo:
   - desactivar items
   - reordenar items
   - aprobar plan
4. La ejecución respeta el orden y persiste:
   - assets/edges/evidence
5. Para cada edge importante existe al menos 1 evidencia vinculada.
6. Los edges sin evidencia quedan como hypothesis=true.
7. El grafo (Neo4j/UI) refleja lo persistido en DB.

---

## 12) Notas para el generador de código
- Priorizar implementación simple (sin colas externas) compatible con la cola SQL actual.
- Mantener compatibilidad con v2: si `requires_approval=false`, ejecutar como v2 (modo legacy).
- No introducir dependencia fuerte a Neo4j para lógica: usarlo solo como “sink” de proyección.
