# DiscoverAI — Master Technical Spec v4.0 (Full Base)

> Documento maestro para implementación técnica (backend + frontend + config + DB).  
> Destinatario: **Generador de código / equipo técnico**.  
> Estado: **v4.0 Full Base - Estabilizado**.

---

## 0. Visión y posicionamiento (v4.0 Core)

DiscoverAI es una **herramienta de Discovery de sistemas de datos complejos y legacy**, orientada a repositorios heterogéneos (SQL + ETL + configs + ruido). Su valor reside en **descubrir, estructurar y documentar** lo que hoy está mal o no documentado, preparando salidas para catálogos empresariales y procesos de modernización.

Principio rector:
> *“Primero descubrir, luego gobernar. Primero entender, luego transformar.”*

---

## 1. Principios de diseño (Evolución v4.0)

1. **DB-first**: Supabase es la fuente de verdad. El grafo es una proyección.
2. **Schema-first**: La estructura del dato se descubre antes que los flujos.
3. **Plan → Approve → Execute**: Nada pesado corre sin plan aprobado.
4. **Structural Analytics**: Priorización de parsers estructurales (SSIS, DataStage) sobre LLM para máxima fidelidad.
5. **Tiered Prompting**: Inteligencia jerárquica (Base → Domain → Org → Solution).
6. **Evidence-first**: Todo hallazgo debe estar soportado por un fragmento de código (evidence).

---

## 2. Arquitectura de Ejecución (v4.0 Pipeline)

### Fase A — Planning
- Análisis rápido (fast scan) del repositorio.
- Clasificación de artefactos (`SQL`, `SSIS`, `DSX`, `PY`, `CONFIG`).
- Generación de un **Job Plan** con estrategias diferenciadas (`PARSER_ONLY`, `LLM_ONLY`, `SKIP`).
- **Truly Incremental**: Hash SHA256 para saltar archivos sin cambios.

### Fase B — Multi-Core Extraction
- **Parsers Estructurales**: Motores internos para SSIS (XML) y DataStage (.dsx).
- **LLM extraction**: Fallback y enriquecimiento para lógica compleja y summarization.
- **Hierarchical Prompt Engine**: Fusión dinámica de 4 capas de conocimiento.

### Fase C — Contextual Enrichment
- **Package Deep Dive**: Extracción de componentes internos y dependencias.
- **Transformation IR**: Modelo intermedio agnóstico para reglas de negocio.
- **Column-level Lineage**: Trazabilidad campo a campo.

---

## 3. Kernel II: Jerarquía de Prompts

El corazón de la v4.0 es el `PromptService`, que gestiona la jerarquía de instrucciones:

1. **BASE**: Lógica técnica fundamental.
2. **DOMAIN**: Especialización técnica (ej. "Experto en SQL Server").
3. **ORG**: Estándares de calidad y gobernanza de la organización.
4. **SOLUTION**: Reglas ad-hoc para un proyecto específico (ej. "Normalización Northwind").

---

## 4. Governance Hub (Manual Bridge)

DiscoverAI v4.0 actúa como un gateway hacia catálogos externos:
- **Purview Gateway**: Exportación CSV para carga masiva de activos.
- **Unity Catalog Gateway**: Mapeo de linaje técnico para Databricks.
- **dbt Gateway**: Generación automática de `sources.yml`.

---

## 5. Auditoría y Resiliencia
- **Audit Logs**: Registro granular de cada llamada al LLM (tokens, latencia, coste).
- **Retry Engine**: Manejo automático de errores 429 con backoff exponencial.
- **Integrated Help**: Guías contextuales integradas en la UI para democratizar el ajuste técnico.

---

## 6. Roadmap Proyectado (v5.0+)
- Ingesto de dbt Manifest.
- Sincronización automática vía API (Direct Sync).
- Visualización interactiva de linaje nivel columna.
- UI Moderna con micro-interacciones.

---
© 2025 DiscoverAI | Engineering Mastery
