Entendido. Para reducir la ambigüedad y entregarle al equipo de desarrollo una hoja de ruta precisa, vamos a redactar una **Especificación Funcional y Técnica Detallada (FSD)**.

Este documento cubre el **Qué** (Funcionalidad) y el **Cómo** (Lógica y Datos) paso a paso. Está listo para ser llevado a un Canva o entregado como PDF.

---

# Documento de Especificación Funcional: Nexus Discovery Platform (MVP)

## 1. Visión General del Sistema
**Nexus Discovery** es una plataforma SaaS diseñada para realizar ingeniería inversa automatizada sobre repositorios de código de datos. Utiliza Inteligencia Artificial (LLMs) para analizar código heterogéneo (SQL, Python, ETLs Legacy), extraer metadatos de linaje y construir un grafo de dependencias. Este grafo puede ser curado manualmente y exportado a catálogos corporativos (Microsoft Purview, Databricks Unity Catalog).

---

## 2. Arquitectura de Alto Nivel

### 2.1 Stack Tecnológico
*   **Frontend:** Next.js 14 (App Router), React Flow (Visualización), Shadcn/UI (Componentes), Tailwind CSS.
*   **Backend (Orquestador):** Python 3.11+ (FastAPI), LangChain (Framework de IA), Celery/Redis (Cola de tareas asíncronas).
*   **Gestión & Auth:** Supabase (Auth, PostgreSQL, Storage, Edge Functions).
*   **Base de Datos de Grafo:** Neo4j (AuraDB o Self-Hosted Cluster).
*   **Motor de IA:** OpenRouter API (Abstracción para modelos Gemini, GPT-4, Claude, DeepSeek).

### 2.2 Diagrama de Componentes Lógicos
1.  **Client Layer:** Interfaz Web SPA.
2.  **Service Layer:** API Gateway (Supabase) + Worker Nodes (Python).
3.  **Intelligence Layer:** Prompt Engineering + Model Router.
4.  **Persistence Layer:** Relational Metadata (Postgres) + Graph Topology (Neo4j).

---

## 3. Módulos Funcionales (Detalle)

### Módulo 1: Gestión de Identidad y Proyectos (SaaS Core)
**Responsabilidad:** Manejar usuarios, organizaciones y aislar los datos.

*   **RF 1.1 - Organización Multi-tenant:**
    *   Un usuario debe pertenecer a una `Organization`.
    *   Todos los datos (Proyectos, Keys, Grafos) tienen un `org_id` obligatorio.
*   **RF 1.2 - Gestión de Secretos (Vault):**
    *   El usuario debe poder guardar sus API Keys (OpenRouter, Azure Client Secret, Databricks Token).
    *   **Implementación:** Usar **Supabase Vault** o encriptación AES-256 en columna PostgreSQL. Estas claves *nunca* viajan al frontend, solo son desencriptadas por el Worker Python en tiempo de ejecución.
*   **RF 1.3 - ABM de Soluciones:**
    *   Una `Solution` es un contenedor lógico (ej: "Migración Data Lake").
    *   Estados de una Solución: `DRAFT`, `PROCESSING`, `READY`, `ERROR`.

### Módulo 2: Ingesta de Fuentes (The Harvester)
**Responsabilidad:** Obtener el código fuente crudo.

*   **RF 2.1 - Carga de Archivos (Zip):**
    *   Upload vía Frontend a Supabase Storage (Bucket privado).
    *   Límite inicial: 50MB por Zip.
    *   Validación de extensiones permitidas: `.sql`, `.py`, `.ipynb`, `.dtsx`, `.json`, `.xml`.
*   **RF 2.2 - Conexión Git (Fase 2):**
    *   Input: URL del repo + Token (Opcional).
    *   El Worker realiza un `git clone` efímero en el contenedor.
*   **RF 2.3 - File Walker:**
    *   El sistema descomprime y recorre recursivamente los directorios.
    *   Ignora carpetas irrelevantes (`.git`, `node_modules`, `__pycache__`).

### Módulo 3: Motor de Análisis (The Brain)
**Responsabilidad:** Transformar código en JSON estructurado.

*   **RF 3.1 - Router de Modelos (Model Dispatcher):**
    *   Lógica de decisión basada en extensión de archivo:
        *   `*.dtsx` (SSIS) -> **Gemini 1.5 Pro** (Ventana de contexto amplia para XMLs grandes).
        *   `*.sql`, `*.py` -> **DeepSeek Coder V2** o **Claude 3.5 Sonnet** (Mejor razonamiento de código).
*   **RF 3.2 - Estrategia de Prompting:**
    *   **System Prompt:** "Eres un Arquitecto de Datos experto en ingeniería inversa. Tu objetivo es extraer fuentes y destinos..."
    *   **Output Constraint:** El LLM **debe** responder únicamente en formato JSON válido (usar modo `JSON Mode` de la API si está disponible).
*   **RF 3.3 - Definición del JSON Schema (Contrato de Interfaz):**
    *   El LLM debe devolver esta estructura exacta:
    ```json
    {
      "file_path": "src/etl/load_sales.py",
      "summary": "Carga incremental de ventas desde CSV a Silver Table",
      "inputs": [
        {"name": "raw_sales.csv", "type": "FILE", "system_hint": "DataLake", "path": "/mnt/raw/"}
      ],
      "outputs": [
        {"name": "fact_sales", "type": "TABLE", "system_hint": "DataWarehouse", "schema": "silver"}
      ],
      "transformation_logic": "Filter nulls, Join with DimProduct"
    }
    ```

### Módulo 4: Construcción del Grafo y Jerarquía
**Responsabilidad:** Persistir la topología en Neo4j y normalizar entidades.

*   **RF 4.1 - Inferencia de Jerarquía (System/Subsystem):**
    *   **Regla 1 (Explícita):** Si el usuario cargó un archivo `domain_map.json`, se usa ese mapeo (Regex -> Sistema).
    *   **Regla 2 (IA):** Se usa el campo `system_hint` del JSON del LLM.
    *   **Regla 3 (Default):** Si no se sabe, se asigna al Sistema `Unassigned`.
*   **RF 4.2 - Upsert Idempotente:**
    *   Uso de `MERGE` en Cypher. Si se procesa el mismo archivo dos veces, no se duplican nodos, solo se actualizan propiedades.
*   **RF 4.3 - Detección de Linaje:**
    *   Creación de aristas: `(Input Node) -[:FLOWS_TO]-> (Process Node) -[:FLOWS_TO]-> (Output Node)`.

### Módulo 5: Visualización y Edición (Frontend)
**Responsabilidad:** Permitir al humano entender y corregir el trabajo de la IA.

*   **RF 5.1 - Renderizado del Grafo (React Flow):**
    *   Layout Automático: Usar **ELKjs** algoritmo `layered` (Left-to-Right).
    *   Nodos Colapsables: Los nodos `System` contienen nodos `Subsystem`, que contienen `Assets`.
*   **RF 5.2 - Inspección de Detalle:**
    *   Evento `OnClick` en nodo Proceso -> Abre Panel Lateral.
    *   Muestra: Resumen generado por IA y snippet del código original.
*   **RF 5.3 - Edición Manual (Human-in-the-Loop):**
    *   Permitir click derecho -> "Editar Propiedades" (Cambiar nombre, mover de Sistema).
    *   Permitir click derecho en arista -> "Eliminar Relación" (Si la IA alucinó).
    *   Los cambios impactan directamente en Neo4j.

### Módulo 6: Exportación (The Cartridges)
**Responsabilidad:** Traducir el grafo interno al mundo exterior.

*   **RF 6.1 - Cartridge Abstract Interface:**
    *   Métodos obligatorios: `authenticate()`, `map_entities()`, `push_payload()`.
*   **RF 6.2 - Cartridge: Microsoft Purview:**
    *   Uso de librería `pyapacheatlas`.
    *   Mapeo: `System` -> `Atlas Collection`, `Asset` -> `Atlas Entity`.
    *   Requisito: El usuario debe proveer `TenantID`, `ClientID`, `ClientSecret`.
*   **RF 6.3 - Cartridge: Databricks Unity Catalog:**
    *   Uso de API REST `2.1`.
    *   Requisito: El usuario debe proveer `Workspace URL` y `PAT Token`.
    *   Scope: Solo linaje de tablas que existan en el Metastore destino.
*   **RF 6.4 - Cartridge: Universal (Markdown/JSON):**
    *   Genera un zip descargable con documentación en Markdown y diagramas Mermaid embebidos.

---

## 4. Modelo de Datos (Esquema de Base de Datos)

### 4.1 PostgreSQL (Supabase)
Tablas críticas para la gestión del SaaS.

| Tabla | Columnas Clave | Descripción |
| :--- | :--- | :--- |
| `organizations` | `id`, `name`, `tier` | El cliente pagador. |
| `solutions` | `id`, `org_id`, `name`, `status`, `config` | Contenedor del proyecto. |
| `jobs` | `id`, `solution_id`, `status`, `logs`, `created_at` | Historial de ejecuciones. |
| `api_vault` | `id`, `org_id`, `service`, `encrypted_value` | Secretos encriptados. |
| `mappings` | `id`, `solution_id`, `regex`, `target_system` | Reglas de normalización manual. |

### 4.2 Neo4j (Graph Schema)
Nodos y relaciones para el linaje.

**Labels (Etiquetas de Nodos):**
*   `:Organization` (Root del tenant)
*   `:Solution` (Proyecto)
*   `:System` (Ej: SAP)
*   `:SubSystem` (Ej: Finance)
*   `:Asset` (Propiedades: `name`, `type`, `path`, `original_code_ref`)
*   `:Process` (Propiedades: `name`, `technology`, `ai_summary`)

**Relationships (Tipos de Relación):**
*   `(:Solution)-[:OWNS]->(:System)`
*   `(:System)-[:CONTAINS]->(:SubSystem)`
*   `(:SubSystem)-[:CONTAINS]->(:Asset)`
*   `(:Asset)-[:INPUT_OF]->(:Process)`
*   `(:Process)-[:OUTPUT_TO]->(:Asset)`

---

## 5. Requerimientos No Funcionales

1.  **Seguridad:**
    *   Aislamiento Lógico: Cada query a Neo4j **debe** incluir `WHERE n.org_id = $current_org`.
    *   Cifrado en reposo para claves API.
2.  **Escalabilidad:**
    *   El procesamiento (Worker Python) debe ser desacoplado. Si 10 usuarios suben zips a la vez, se encolan en Redis y los workers los toman de a uno.
3.  **Auditabilidad:**
    *   Registro de "Token Usage": Guardar cuántos tokens consumió cada Job para poder facturar o limitar al cliente según su plan.
4.  **Tolerancia a Fallos:**
    *   Si OpenRouter falla (timeout), el worker debe implementar "Exponential Backoff" (reintentar 3 veces esperando cada vez más).

---

## 6. UI Wireframes (Concepto de Pantallas)

1.  **Landing / Login:** Auth de Supabase.
2.  **Dashboard Home:** Tarjetas con las "Soluciones" creadas. Botón "Nueva Solución".
3.  **Config Wizard:**
    *   Paso 1: Nombre.
    *   Paso 2: Subir Zip o URL Git.
    *   Paso 3: Configurar Keys (o usar default).
    *   Paso 4: Iniciar Análisis.
4.  **Solution Canvas (Main View):**
    *   **Header:** Status del Job, Botón "Exportar".
    *   **Left Panel:** Árbol de Sistemas (Explorador de archivos).
    *   **Center:** Lienzo infinito (React Flow) con el grafo.
    *   **Right Panel (Drawer):** Propiedades del nodo seleccionado + Editor.
5.  **Settings:** Gestión de API Keys y Miembros del equipo.

---

Este documento debería ser suficiente para que un equipo de desarrollo Full Stack y un Ingeniero de Datos comiencen a trabajar sin bloquearse por falta de definiciones.