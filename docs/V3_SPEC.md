# DiscoverAI — SPEC Completa v3.0 + v4

> Documento maestro para implementación técnica (backend + frontend + config + DB).  
> Destinatario: **Generador de código / equipo técnico**.  
> Objetivo: cerrar **v3.0** de forma sólida y dejar **v4** completamente diseñada sin ambigüedades.  
> Enfoque: **Discovery engineering**, coste controlado, evidencia primero, exportable a catálogos y motores modernos.

---

## 0. Visión y posicionamiento (no negociable)

- DiscoverAI **NO** es:
  - un administrador de metadatos
  - un catálogo tipo Purview / Unity Catalog
  - una herramienta de gobierno continuo

- DiscoverAI **ES**:
  - una **herramienta de Discovery de sistemas de datos complejos y legacy**
  - orientada a repositorios heterogéneos (SQL + ETL + configs + ruido)
  - que **descubre, estructura y documenta** lo que hoy está mal o no documentado
  - y **prepara salidas** para:
    - catálogos de mercado (Purview, Unity, etc.)
    - procesos de modernización / migración
    - generación futura de pipelines modernos

Principio rector:
> *“Primero descubrir, luego gobernar. Primero entender, luego transformar.”*

---

## 1. Principios de diseño (aplican a v3 y v4)

1. **DB-first**: Supabase es la fuente de verdad. El grafo es una proyección.
2. **Schema-first**: la estructura del dato se descubre antes que los flujos.
3. **Plan → Approve → Execute**: nada pesado corre sin plan aprobado.
4. **Evidence-first**: sin evidencia, todo es hipótesis.
5. **Cost-aware**: cada decisión tiene impacto de coste visible.
6. **Heterogeneidad real**: un repo de data no es “código uniforme”.
7. **Provider-agnostic**: los modelos se configuran, no se hardcodean.

---

## 2. Arquitectura funcional global

### Fase A — Planning (v3)
- Análisis rápido y barato del repositorio
- Generación de un **Plan de ejecución**
- Estimación de coste/tiempo
- Agrupación + orden + estrategia
- Aprobación explícita del usuario

### Fase B — Execution (v3)
- Ejecución guiada por el plan
- Descubrimiento estructural
- Lineage macro con evidencia

### Fase C — Deep Understanding (v4)
- Subgrafo por paquete
- Transformaciones internas
- Representación intermedia (IR)
- Base para migración y data products

---

## 3. V3 — Planning Phase (OBLIGATORIA)

### 3.1 Objetivo

Convertir un repo/ZIP caótico en un **Plan gobernado**, costeable y ordenable.

---

### 3.2 Clasificación de artefactos

Cada archivo se clasifica en una categoría:

- `FOUNDATION`
  - SQL DDL / migrations
  - diccionarios / docs base
- `CONFIG`
  - conexiones, variables, parámetros
- `ETL_PACKAGE`
  - SSIS (.dtsx)
  - DataStage (.dsx)
- `ORCHESTRATION`
  - jobs, schedulers, control flows
- `TRANSFORM_SCRIPT`
  - SQL DML, Python, notebooks
- `MEDIA`
  - imágenes, PDFs
- `NOISE`
  - backups, dumps, binarios

---

### 3.3 Áreas del Plan

El Plan se agrupa en **áreas**:

- **Área A — General / Foundation**
- **Área B — Packages / Orchestration / Transformations**
- **Área C — Aux / Noise / Media**

Cada área tiene:
- `order_index`
- `default_enabled`

---

### 3.4 Plan Item (unidad mínima)

Cada archivo o grupo lógico genera un `job_plan_item` con:

- `strategy`: `PARSER_ONLY | PARSER_PLUS_LLM | LLM_ONLY | SKIP`
- `risk_score` (0–100)
- `value_score` (0–100)
- `estimated_tokens`
- `estimated_time_ms`
- `estimated_cost_usd`
- `recommended_action`: `PROCESS | SKIP | REVIEW`
- `enabled` (editable)
- `order_index` (editable)

---

### 3.5 Resultado de Planning

- Persistir `job_plan`, `job_plan_area`, `job_plan_item`
- Estado del job: `WAITING_APPROVAL`
- UI muestra:
  - resumen
  - warnings
  - coste estimado
  - orden editable

---

## 4. V3 — Execution Phase

### 4.1 Reglas de ejecución

- Solo ejecutar items `enabled=true`
- Orden:
  1. Área A
  2. Área B
  3. Área C (solo si habilitada)

Dentro de cada área: `order_index`

---

### 4.2 Descubrimiento estructural

- SQL DDL → `extract.schema`
- SQL DML → `extract.lineage.sql`
- Configs → conexiones

Resultados:
- `asset`
- `asset_version`
- `edge_index`
- `evidence`

---

### 4.3 Lineage macro

- Qué lee qué
- Qué escribe qué
- Confidence + hypothesis

---

## 5. V4 — Package Deep Dive (DISEÑADO)

### 5.1 Subgrafo por paquete

Para cada paquete ETL:

- componentes internos
- dependencias internas
- variables y parámetros
- SQL embebido

Nueva entidad:
- `package`
- `package_component`

---

### 5.2 Transformations IR (Intermediate Representation)

Modelo común de transformaciones:

- Read
- Write
- Select
- Filter
- Join
- Aggregate
- Lookup
- Derive
- SCD

Entidad:
- `transformation_ir`

Con:
- column-level lineage parcial
- confidence + evidence

---

### 5.3 Intención del paquete

Uso de LLM para sintetizar:
- para qué existe el paquete
- qué problema resuelve
- riesgos

---

## 6. Data Products (v4+)

### 6.1 Inferencia gradual

- Clustering por targets
- Prefijos / esquemas
- Frecuencia de uso

Entidad:
- `data_product`

Editable por humano.

---

## 7. Sistema de Modelos — Multi Provider / Multi Routing

### 7.1 Separación de conceptos

- **Provider profile**: Groq / OpenRouter / OpenAI
- **Routing profile**: qué modelo usar por acción
- **Active config**: selección actual

---

### 7.2 Estructura de configuración

```
config/
  providers/
    groq.yml
    openrouter.yml
    openai.yml
  routings/
    routing-groq-fast.yml
    routing-openrouter-balanced.yml
    routing-openai-accurate.yml
  active.yml
```

---

### 7.3 active.yml

```yaml
active:
  provider: providers/groq.yml
  routing: routings/routing-groq-fast.yml
```

---

### 7.4 Action routing

Cada acción define:

- modelo
- prompt
- json_schema
- fallbacks
- budgets

Ejemplos de acciones:

- `planner.classifier`
- `extract.schema`
- `extract.lineage.sql`
- `extract.lineage.package`
- `summarize.asset`
- `qa.chat`

---

## 8. Backend — Componentes

- `ConfigManager`
- `LLMClientFactory`
- `PlannerService`
- `ExecutionService`
- `PolicyEngine`
- `Estimator`

Endpoints admin mínimos:

- `GET /admin/model-config`
- `POST /admin/model-config/activate`

---

## 9. Persistencia y auditoría

### 9.1 job_run

Guardar:
- provider activo
- routing activo
- config_hash
- prompt_version

### 9.2 job_stage_run.metrics

Guardar:
- modelo usado
- fallback
- tokens
- latencia
- coste estimado

---

## 10. UI (mínimo viable)

### 10.1 Planning UI

- vista por áreas
- enable/disable
- reorder
- coste estimado
- approve

### 10.2 Execution UI

- progreso por item
- estado

### 10.3 Package View (v4)

- subgrafo
- lógica interna
- intención

---

## 11. Export y outputs

### 11.1 Metadata catalogs

- assets
- lineage
- evidence
- dominios

### 11.2 Migration packs

- IR
- SQL
- dependencias

---

## 12. Roadmap

### v3.0
- Planning completo
- Schema-first
- Multi-provider config

### v3.1
- Reorder UI
- Cost estimator refinado

### v4.0
- Package deep dive
- Transformation IR

### v4.1+
- Data products
- Export avanzado

---

## 13. Criterios de aceptación

- Ningún job pesado corre sin plan aprobado
- Coste visible antes de ejecutar
- Evidencia presente en lineage
- Provider/model configurable sin tocar código
- DB consultable sin grafo

---

**Fin de la SPEC**

