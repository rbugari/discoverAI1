# Nexus Discovery — El Corazón de la Modernización de Datos

**Nexus Discovery** es la plataforma líder de *Reverse Engineering* y *Data Discovery* impulsada por Inteligencia Artificial Agéntica, diseñada específicamente para desentrañar la complejidad de ecosistemas de datos legacy y prepararlos para el futuro de la gobernanza y la nube.

---

## 1. Visión de Negocio (Business Vision)

### El Problema
Las grandes corporaciones se enfrentan a una "deuda de conocimiento" masiva. Sistemas críticos (ETL, SQL, Warehouses antiguos) operan como "cajas negras" sin documentación actualizada. Esto impide la migración a la nube, la adopción de nuevas tecnologías (como dbt o Databricks) y aumenta el riesgo operativo.

### La Solución: Nexus Discovery (by Over 55 IT)
No somos una herramienta de gestión de metadatos estática; somos un motor de **descubrimiento activo**. Nexus Discovery "lee" el código fuente, entiende la lógica y reconstruye el linaje técnico que se creía perdido.

### Propuesta de Valor
*   **Aceleración de Migraciones**: Reduce meses de análisis manual a días de procesamiento automatizado.
*   **Reducción de Riesgo**: Identifica dependencias ocultas antes de que rompan el sistema en una transición.
*   **Estandarización de Conocimiento**: Transforma archivos oscuros (XML, scripts legacy) en modelos de datos modernos y documentados.

---

## 2. Visión Funcional (Functional Vision)

El producto opera bajo una premisa de **Inteligencia Estructurada**, dividiendo el conocimiento en capas y tareas especializadas.

### El Motor de Inteligencia (Tiered Prompting)
La "sabiduría" de Nexus se organiza en 4 capas jerárquicas:
1.  **Capa Base**: El conocimiento técnico fundamental.
2.  **Capa de Dominio**: Especialización en tecnologías específicas (Microsoft SSIS, IBM DataStage, SQL Server, etc.).
3.  **Capa de Organización**: Estándares de calidad y gobernanza propios de la empresa cliente.
4.  **Capa de Solución**: Reglas ad-hoc para un repositorio específico (ej. "En este proyecto, las tablas `STG_` son temporales").

### Tareas Pre-configuradas (Task-specific Agents)
Contamos con 6 tipos de agentes (prompts) especializados:
*   **Análisis & Triage**: Escaneo inicial para determinar la complejidad.
*   **Extracción Estructural**: Lectura de metadatos y XMLs.
*   **Analista SQL/Python**: Entiende lógica de negocio dentro de stored procedures y scripts.
*   **Auditor de Brechas**: Identifica qué partes del código no se entendieron bien (Gaps).

---

## 3. Visión Técnica (Technical Vision)

### Arquitectura Híbrida (Parsers + LLM)
Nexus no depende solo de la IA. Para máxima precisión, utilizamos un motor híbrido:
*   **Structural Parsers**: Motores internos que leen "XMLs con esteroides" (SSIS, DataStage) para extraer la estructura exacta (flujos, conexiones).
*   **LLM Orchestrator**: Un cerebro que utiliza modelos de razonamiento (Groq, OpenAI, Google, OpenRouter) para "explicar" la lógica y rellenar los vacíos que el código crudo no revela.

### Resiliencia y Flexibilidad de Modelos
El usuario puede elegir el "músculo" computacional:
*   **Modelos Rápidos (Fast Tier)**: Para extracciones masivas de bajo costo.
*   **Modelos de Razonamiento (Thinking Tier)**: Como *Olmo-3.1-Think* o *GPT-4o*, para entender transformaciones de negocio complejas.
*   **Retry Engine**: Manejo inteligente de cuotas y errores 429 para procesos de largo aliento.

---

## 4. Guía de Uso: El Ciclo Nexus

Para obtener resultados óptimos, Nexus Discovery sigue un flujo de **Plan → Approve → Execute**.

### Paso 1: Creación de la Solución
Se define el origen de los datos:
*   **Directorio Local**: Una carpeta con todos los archivos recolectados.
*   **Conexión a Repositorio (GitHub)**: Sincronización directa con el control de versiones.

### Paso 2: Escaneo y Planificación
Nexus realiza un escaneo inicial y presenta un **Job Plan**. Aquí se decide qué archivos procesar, qué modelo de IA usar para cada uno y qué profundidad de análisis aplicar.

### Paso 3: Ejecución Híbrida
El orquestador lanza el proceso. Los parsers extraen la estructura y la IA genera el resumen, el linaje a nivel de columna y el propósito de negocio de cada objeto.

### Paso 4: Auditoría y Refinamiento (El Ciclo de Mejora)
Nexus presenta un Dashboard con el % de cobertura. Al detectar "gaps" (tablas no encontradas, lógica confusa), el **Auditor de IA** genera parches para los prompts. El usuario puede ajustar los prompts a mano o aplicar el parche sugerido y correr una nueva iteración para subir la precisión (ej. del 70% al 85%).

### Paso 5: Governance Gateway (Exportación)
El producto final se entrega a herramientas de mercado:
*   **Microsoft Purview / Unity Catalog**: Exportación de activos y linaje vía CSV/API.
*   **dbt Gateway**: Generación de `sources.yml` para proyectos de ingeniería modernos (BigQuery, Databricks, Snowflake).

---

## 5. Análisis de Situación Actual (v6.0 Closure)

| Concepto en la Visión | Estado Actual en v6.0 | Notas |
| :--- | :--- | :--- |
| **Layers (Base/Dom/Org/Sol)** | ✅ Implementado | Funcional a través del `Prompt Matrix`. |
| **Multi-Model Support** | ✅ Implementado | Groq, OpenRouter, OpenAI fully integrated. |
| **Plan → Approve → Execute** | ✅ Implementado | Flujo core del orquestador. |
| **Parsers SSIS/DataStage** | ✅ Implementado | Motores XML propietarios operativos. |
| **Auditoría & Repositorio de Gaps** | ✅ Implementado | Reporte de optimización activo en el Dashboard. |
| **Exportación Governance** | ✅ Implementado | Purview, Unity y dbt (Phase 1). |
| **Conexión GitHub Directa** | ⚠️ Parcial | Actualmente optimizado para repositorios clonados localmente. |
| **Linaje de Columna Interactiva** | 📅 Roadmap v7.0 | El dato se extrae, pero la visualización UI es el siguiente paso. |

---
© 2026 Nexus Discovery | Over 55 IT | Engineering Mastery
