Entendido. El error que ves en la terminal (`git exit code 128`) ocurre porque ese repositorio contiene archivos con dos puntos (`:`) en el nombre (ej. `03. Implement CDC... : ... .py`), lo cual es ilegal en Windows. Git clona los objetos pero falla al crear los archivos en disco ("Checkout failed").

Este fallo expone un **Gap Crítico en Discovery**: la **Robustez ante Errores de Entorno**. Actualmente, si un solo archivo falla, todo el trabajo muere.

Aquí está el plan ajustado para solucionar el error inmediato y luego mejorar la arquitectura de Discovery como solicitaste.

### Fase 1: Solución Inmediata (Robustez)
El sistema no debe colapsar por un nombre de archivo inválido.
1.  **Modificar `apps/api/app/services/storage.py`:**
    *   Envolver `git.Repo.clone_from` en un bloque `try/except`.
    *   Capturar `GitCommandError`. Si el error es "Checkout failed" pero el directorio existe, **ignorar el error y continuar**.
    *   Esto permitirá que el Worker procese el 99% de los archivos válidos del repositorio en lugar de fallar por completo.

### Fase 2: Evolución del Discovery (Lo que falta según el Plan)
Una vez estabilizado el error, implementaremos la arquitectura necesaria para el futuro del producto (Release B).

1.  **Crear `ExtractorRegistry` (El "Traffic Cop"):**
    *   Actualmente el worker llama directo al LLM. Necesitamos un intermediario.
    *   Crear `apps/api/app/services/extractors/registry.py`.
    *   Lógica:
        *   ¿Es `.py` o `.sql` simple? -> Usar **RegexExtractor** (Nuevo, rápido, gratis).
        *   ¿Es complejo o desconocido? -> Usar **LLMExtractor**.

2.  **Implementar `RegexExtractor` (Nivel B - Estructural):**
    *   Crear un extractor simple que busque patrones de texto (`import ...`, `FROM ...`).
    *   Esto es fundamental para:
        *   Ahorrar tokens (costo).
        *   Aumentar la confianza (Score 0.8 vs 0.2 del LLM).
        *   Detectar dependencias obvias que a veces el LLM alucina u olvida.

3.  **Actualizar `worker.py`:**
    *   Reemplazar la llamada directa a `LLMService` por `registry.extract(file_path)`.

Esta hoja de ruta soluciona tu bloqueo actual y sienta las bases para un Discovery profesional y escalable. ¿Te parece bien empezar por el "Fix de Robustez" en `storage.py`?