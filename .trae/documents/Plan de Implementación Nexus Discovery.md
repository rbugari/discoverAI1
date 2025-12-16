# Especificación Funcional y Técnica Detallada: Nexus Discovery Platform

Este documento detalla el funcionamiento interno, flujos de datos y arquitectura del sistema Nexus Discovery, expandiendo la visión original con detalles de implementación técnica.

---

## 1. Flujo de Usuario (User Journey)

### 1.1. Onboarding y Autenticación
*   **Acción:** El usuario se registra/loguea vía Supabase Auth (Email/Password o GitHub/Google).
*   **Sistema (Backend):**
    *   Supabase genera un JWT.
    *   **Trigger (Postgres):** Al crearse un usuario en `auth.users`, se inserta automáticamente una fila en la tabla `public.organizations` (Plan FREE por defecto) y se vincula al usuario.
*   **Resultado:** El usuario accede al Dashboard viendo solo los datos de su `org_id`.

### 1.2. Creación de una "Solución" (Proyecto)
*   **Acción:** Usuario hace clic en "Nueva Solución", ingresa nombre ("Migración DW") y sube un archivo `.zip` con scripts SQL/Python.
*   **Sistema (Frontend):**
    *   Sube el archivo directamente a Supabase Storage (Bucket: `source-code/{org_id}/{solution_id}.zip`).
    *   Inserta registro en tabla `solutions` con estado `DRAFT`.
*   **Resultado:** El proyecto aparece listado. El usuario puede configurar API Keys si no quiere usar las default.

### 1.3. Ejecución del Análisis (The Heavy Lifting)
*   **Acción:** Usuario hace clic en "Iniciar Análisis".
*   **Sistema (Orquestación):**
    1.  **Frontend:** Llama a `POST https://api.nexus.com/v1/jobs/start` con el `solution_id`.
    2.  **API (FastAPI):**
        *   Valida JWT y permisos sobre la solución.
        *   Crea registro en tabla `jobs` (Status: `QUEUED`).
        *   Envía mensaje a Broker (Redis): `task_analyze_solution(job_id)`.
    3.  **Worker (Python/Celery):**
        *   Recibe mensaje. Actualiza Job a `RUNNING`.
        *   Descarga Zip de Supabase Storage.
        *   **File Walker:** Descomprime y recorre archivos. Filtra por extensión.
        *   **AI Processing (Bucle):**
            *   Lee archivo -> Selecciona Prompt según extensión.
            *   Llama a LLM (OpenRouter).
            *   Valida JSON respuesta.
        *   **Graph Persistance:**
            *   Conecta a Neo4j.
            *   Ejecuta `MERGE` (Upsert) de nodos y relaciones.
        *   **Fin:** Actualiza Job a `COMPLETED` o `FAILED`.

### 1.4. Visualización y Edición
*   **Acción:** Usuario entra al "Canvas".
*   **Sistema:**
    *   Frontend pide grafo a `GET /v1/graph/{solution_id}`.
    *   API consulta Neo4j y devuelve JSON compatible con React Flow.
    *   **Interactividad:** Al hacer clic en un nodo, el Frontend muestra el código fuente original (traído desde Storage o metadatos) y la explicación de la IA.

---

## 2. Arquitectura de Datos (Source of Truth)

### 2.1. Modelo Relacional (PostgreSQL)
Este esquema maneja la "Administración" del SaaS.

```sql
-- Tabla: Organizations (Tenant raíz)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla: Solutions (Contenedor de proyectos)
CREATE TABLE solutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id),
    name TEXT NOT NULL,
    storage_path TEXT NOT NULL, -- Ruta al ZIP
    status TEXT DEFAULT 'DRAFT', -- DRAFT, PROCESSING, READY, ERROR
    config JSONB DEFAULT '{}' -- Configs extra (ej: ignore_patterns)
);

-- Tabla: Jobs (Historial de ejecuciones)
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    solution_id UUID REFERENCES solutions(id),
    status TEXT NOT NULL, -- QUEUED, RUNNING, COMPLETED, FAILED
    logs TEXT[], -- Array de strings para debug simple
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);
```

### 2.2. Modelo de Grafo (Neo4j)
Este esquema maneja el "Conocimiento" extraído.

*   **Restricciones (Constraints):**
    *   `Constraint: (n:Asset) REQUIRE n.uid IS UNIQUE` (donde uid = `org_id + file_path` hash).
*   **Nodos:**
    *   `(:Asset {path: '/src/etl.py', type: 'FILE', summary: '...'})`
    *   `(:Table {name: 'dim_customers', schema: 'sales'})`
*   **Relaciones:**
    *   `(:Asset)-[:READS_FROM]->(:Table)`
    *   `(:Asset)-[:WRITES_TO]->(:Table)`
    *   `(:System)-[:CONTAINS]->(:Asset)`

---

## 3. Especificación de Componentes Técnicos

### 3.1. API Backend (FastAPI)
Servirá como puente seguro y orquestador. No procesa IA directamente (para no bloquear), delega a Celery.
*   `POST /auth/login`: (Opcional si usamos Supabase directo en front, pero útil para validar tokens).
*   `POST /jobs`: Crea y encola un análisis.
*   `GET /jobs/{id}`: Polling de estado.
*   `GET /graph/{solution_id}`: Consulta Cypher optimizada para frontend.

### 3.2. Worker de IA (Celery)
*   **Lógica de Router:**
    *   Si es `.sql` -> Prompt: "Analiza este DDL/DML, extrae tablas origen/destino". Modelo: DeepSeek V2.
    *   Si es `.py` -> Prompt: "Analiza flujo de datos (Pandas/PySpark)". Modelo: Claude 3.5 Sonnet.
    *   Si es `.dtsx` (XML) -> Prompt: "Extrae DataFlow Tasks". Modelo: Gemini 1.5 Pro (Contexto largo).
*   **Resiliencia:** Retry policy exponencial si la API de IA da timeout (5s, 10s, 30s).

### 3.3. Frontend (Next.js)
*   **Estado Global:** Zustand para manejar la selección de nodos y estado del panel lateral.
*   **Visualización:** `React Flow` con nodos custom.
    *   *CustomNode:* Muestra icono según tecnología (Python, SQL) y badge de tipo (Source, Sink, Process).

---

## 4. Plan de Trabajo Inmediato

Si esta especificación cubre tus expectativas, procederé a:

1.  **Configurar Entorno:** Crear `docker-compose.yml` (Redis, Neo4j) y estructura de carpetas.
2.  **Base de Datos:** Ejecutar el script SQL en Supabase/Postgres local.
3.  **Backend:** Inicializar FastAPI y Celery.
4.  **Frontend:** Inicializar Next.js.
