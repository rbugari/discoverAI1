# Cómo Funciona DiscoverAI: Una Autopsia Lógica

Este documento explica el proceso de razonamiento interno de DiscoverAI ("El Sistema"), detallando exactamente qué sucede cuando subes un repositorio o seleccionas un proyecto. Desglosa el "proceso de pensamiento", los criterios utilizados para las decisiones y el flujo de datos desde el código sin procesar hasta un grafo de conocimiento inteligente.

---

## 🏗️ Fase 1: Ingesta y el Escaneo "Sensorial"
**Objetivo:** Crear un inventario estructurado de lo desconocido.

Cuando apuntas el sistema a un repositorio (ej. un archivo ZIP o repo de GitHub), no solo lo "lee"; lo **audita**.

### 1.1 La Caminata (Los Sentidos)
El `PlannerService` del sistema recorre físicamente cada directorio y archivo. Construye un manifiesto de lo que existe, ignorando el ruido (como `.git`, `node_modules`).

### 1.2 Estrategia de Clasificación (La Corteza)
Para cada archivo encontrado, el `Planner` aplica una **Clasificación Heurística** para decidir *cómo* procesarlo. No trata todos los archivos por igual.

*   **Lógica:**
    *   **¿Es Fundación?** (`.sql`, `.ddl`, carpetas `schema`) -> **Alta Prioridad**. Estos definen la "Verdad".
        *   *Estrategia:* `PARSER_PLUS_LLM`. Usa un parser SQL estricto primero, luego LLM para contexto.
    *   **¿Es Orquestación?** (`.dtsx` para SSIS, `.dsx` para Datastage, carpetas `jobs`) -> **Crítico**. Estos definen el "Movimiento".
        *   *Estrategia:* `HYBRID_PARSER`. Extrae flujos hard-codeados programáticamente, usa IA para entender la intención del negocio.
    *   **¿Es Scripting?** (`.py`, `.sh`, `.ps1`) -> **Contexto**.
        *   *Estrategia:* `LLM_ONLY`. Lectura pura por el Modelo de IA para entender la lógica.
    *   **¿Es Configuración?** (`.xml`, `.json`, `.yaml`) -> **Soporte**.
        *   *Estrategia:* `PARSER_ONLY`. Extrae pares clave-valor (conexiones, credenciales).

**Resultado:** Se crea un `JobPlan`. Este es un plan de batalla. Agrupa archivos en "Áreas" (Fundación, Paquetes, Auxiliar) y asigna un estimado de costo/tiempo de procesamiento.

### 🔬 Profundización Técnica: Planner
*   **Archivo de Lógica**: `apps/api/app/services/policy_engine.py`
*   **Entrada**: Metadatos del archivo (`path`, `size`, `extension`).
*   **Función Clave**: `evaluate(file_path, size_bytes)`
*   **Matriz de Decisión**:
    *   `node_modules/` O `.git/` → `RecommendedAction.SKIP`
    *   `tamaño > 500MB` → `RecommendedAction.SKIP`
    *   `.sql` → `Strategy.PARSER_PLUS_LLM`
    *   `.py` → `Strategy.LLM_ONLY`


---

## 🧠 Fase 2: Razonamiento Autónomo (Procesamiento IA)
**Objetivo:** Convertir "Archivos" en "Significado".

Una vez aprobado el Plan (o auto-ejecutado), el **Orquestador de Pipeline** despierta a los Agentes. Aquí es donde ocurre el "Pensamiento".

### 2.1 La Descomposición (Agente Refinador)
El Sistema toma un archivo (ej. `UpdateSales.sql`) y lo envía al LLM (ej. Gemini 2.0 / GPT-4o) con un **Prompt Cognitivo** específico.

**La Estructura del Prompt:**
> "Eres un Arquitecto de Datos Experto. Meticuloso y preciso.
> **Contexto:** Este archivo es parte de [Nombre del Proyecto].
> **Tarea:** Aplica ingeniería inversa al linaje de datos.
> **Criterios:**
> 1. Identifica todas las **ENTRADAS** (Tablas, Vistas, APIs).
> 2. Identifica todas las **SALIDAS** (Tablas Objetivo).
> 3. Extrae **TRANSFORMACIONES** (joins, filtros, reglas de negocio).
> 4. Asigna un **PUNTAJE DE CONFIANZA** (0.0 - 1.0) a tus hallazgos."

**El Resultado:** La IA no devuelve solo un resumen de texto; devuelve un **Grafo JSON Estructurado**. Dice: *"Estoy 95% seguro de que `Table_A` alimenta a `Table_B` usando un Left Join en `customer_id`"*.

### 🔬 Profundización Técnica: Agente Refinador
*   **Archivo de Lógica**: `apps/api/app/prompts/extract_deep_dive.md` (Plantilla)
*   **Mecanismo de Inyección**: `apps/api/app/services/prompt_service.py`
*   **Variables de Entrada**:
    *   `{content}`: El contenido crudo del archivo (leído del disco).
    *   `{file_type}`: ej. "SQL Script" o "SSIS Package".
    *   `{macro_nodes}`: Contexto de escaneos superficiales previos.
*   **Salida Esperada del LLM (JSON)**:
    ```json
    {
      "package": { "name": "UpdateSales", "type": "SQL" },
      "lineage": [
        { "source_asset_name": "Staging_Sales", "target_asset_name": "Fact_Sales", "confidence": 0.95 }
      ]
    }
    ```

### 🔬 Profundización Técnica: Visualización Rayos X (X-Ray)
El "Modo X-Ray" en el frontend cierra la brecha entre el razonamiento del Backend y el ojo del Usuario.
*   **Flujo de Datos**: `GraphService` -> `edge.data` -> `rationale` & `confidence`.
*   **Visual**: Un tooltip "Glassmorphic" renderiza estos metadatos al pasar el mouse, permitiendo auditar el "Puntaje de Confianza" de la IA sin salir del gráfico.

### 2.2 El Análisis del "Eslabón Perdido"
Si la IA ve una referencia a `crm.users` pero no ha visto esa definición de tabla aún, crea un **Nodo Fantasma** (una Hipótesis).
*   *Lógica:* "Veo uso, pero no definición. Marcador: `IS_HYPOTHESIS = True`."
*   *Propósito:* Esto ayuda a identificar archivos faltantes o dependencias externas.

---

## 🔗 Fase 3: Síntesis y Construcción del Grafo
**Objetivo:** Conectar los puntos.

El `GraphService` toma miles de estos análisis de archivos individuales y los une en un único **Grafo de Conocimiento Neo4j**.

### 3.1 Resolución de Enlaces
*   Archivo A dice: "Yo escribo en `Sales_Final`".
*   Archivo B dice: "Yo leo de `Sales_Final`".
*   **Lógica del Sistema:** "¡Coincidencia! Crear una arista: `Archivo A` -> [Lineage] -> `Archivo B`."

### 3.2 La Auditoría (Auto-Reflexión)
Después de construir el grafo, el `DiscoveryAuditor` ejecuta una auto-verificación.

**Criterios para "Brechas" (Gaps):**
1.  **Activos Huérfanos:** Nodos con 0 conexiones. (¿Por qué existe este script si no habla con nada?)
2.  **Clusters de Baja Confianza:** Áreas donde la IA no estaba segura (< 50% confianza).
    *   *Decisión del Sistema:* Marcar como "Área de Riesgo" para revisión humana.
3.  **Dependencias Cíclicas:** Bucles lógicos que podrían romper pipelines.

---

## ✨ Fase 4: Síntesis Ejecutiva ("El Cerebro")
**Objetivo:** Explicar *por qué* importa.

Finalmente, el `ReasoningService` mira todo el grafo (Inventario + Puntos Calientes + Brechas) y le pide al Modelo de Nivel Superior (Gemini 2.0 Flash / Pro) que escriba un resumen.

**El Prompt:**
> "Revisa el inventario completo de arquitectura proporcionado abajo.
> Identifica clusters lógicos.
> Detecta riesgos arquitectónicos (código espagueti, puntos únicos de fallo).
> Sugiere 3 mejoras estratégicas."

**Salida:** ESTO es lo que ves en el Dashboard bajo "Salud de Descubrimiento" (Discovery Health) y "Brechas de Conocimiento".

---

## Resumen de Toma de Decisiones

| Paso | ¿Quién Decide? | Criterios |
| :--- | :--- | :--- |
| **Estrategia de Parsing** | `PlannerService` (Código) | Extensión de Archivo + Ruta de Carpeta (Regex) |
| **Lógica de Linaje** | `RefinerAgent` (IA) | Sintaxis SQL, Flujo de Datos de Variables, Referencias a Tablas |
| **Banderas de Riesgo/Brecha** | `DiscoveryAuditor` (Código) | Confianza < 0.5, Centralidad de Grado = 0 (Huérfano) |
| **Insight Global** | `ReasoningService` (IA) | Reconocimiento de Patrones en todo el Inventario |

Este enfoque híbrido (Lógica de Código Estricta + Razonamiento de IA Fluido) permite a DiscoverAI ser preciso con la sintaxis (SQL) pero adaptativo con la intención (Lógica de Negocio).
