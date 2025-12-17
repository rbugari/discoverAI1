# Plan de Implementación Final (Confirmado)

Gracias por las credenciales y la confirmación. Todo está listo para comenzar.

**Resumen de la estrategia:**
*   **Cola de Jobs:** Usaremos **PostgreSQL (Supabase)** como backend de la cola (tabla `job_queue` o similar), lo cual simplifica la infraestructura actual sin perder robustez (persistencia, reintentos).
*   **Credenciales:** Recibidas y listas para configurar.

## Pasos de Ejecución Inmediata

1.  **Fase 1: Base de Datos (SQL-First)**
    *   Generar y ejecutar `01_init_schema.sql` con las nuevas tablas:
        *   `job_run`, `job_stage_run` (Ejecución de jobs)
        *   `asset`, `asset_version`, `edge_index`, `edge_evidence` (Catálogo SQL)
        *   `evidence` (Evidencias de auditoría)

2.  **Fase 2: Backend de Jobs**
    *   Implementar `SQLJobQueue` en `apps/api`.
    *   Refactorizar el endpoint `POST /jobs` para usar esta cola.
    *   Crear el worker que procesa la cola.

3.  **Fase 3: Lógica de Extracción**
    *   Actualizar `LLMService` para extraer JSON estricto con evidencias.
    *   Implementar `ConfidenceScoring`.

4.  **Fase 4: APIs de Consumo**
    *   Exponer endpoints para el catálogo y subgrafos.

**¿Procedo con la Fase 1 (Base de Datos)?**