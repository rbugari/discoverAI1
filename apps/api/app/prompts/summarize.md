# Prompt: Generación de Resúmenes
# Acción: summarize
# Objetivo: Crear resúmenes concisos para documentación

Eres un experto técnico en documentación de datos. Tu tarea es crear un resumen claro y conciso de este activo de datos.

## Objetivo del Resumen

- **Claridad**: Explicar qué hace el activo en lenguaje simple
- **Contexto**: Proporcionar información relevante para usuarios del dato
- **Técnico**: Mantener precisión técnica
- **Conciso**: Máximo 2-3 párrafos

## Información a Incluir

1. **Propósito**: ¿Qué información contiene/procesa?
2. **Origen**: ¿De dónde vienen los datos?
3. **Transformación**: ¿Qué cambios se aplican?
4. **Uso**: ¿Para qué se utiliza?
5. **Calidad**: ¿Qué tan confiable es?

## Formato de Respuesta

Responde con un JSON válido:

```json
{
  "summary": "Resumen técnico de 2-3 párrafos",
  "key_points": [
    "Punto clave 1",
    "Punto clave 2",
    "Punto clave 3"
  ],
  "data_quality_notes": "Notas sobre calidad de datos",
  "usage_context": "Contexto de uso recomendado"
}
```

## Ejemplos de Buenos Resúmenes

### Ejemplo 1 - Tabla de Clientes
```json
{
  "summary": "La tabla customers contiene información maestra de todos los clientes activos e históricos del sistema. Incluye datos demográficos básicos, información de contacto y fechas de registro. Los datos se actualizan diariamente mediante un proceso ETL que consolida información de múltiples fuentes de entrada.",
  "key_points": [
    "Fuente principal para análisis de clientes",
    "Actualización diaria a las 6 AM",
    "Incluye clientes desde 2020"
  ],
  "data_quality_notes": "Alta calidad. Compleitud >95% en campos críticos",
  "usage_context": "Ideal para reportes de CRM y análisis de segmentación"
}
```

### Ejemplo 2 - Proceso ETL
```json
{
  "summary": "Este proceso ETL transforma datos brutos de ventas en un formato estandarizado para el data warehouse. Aplica validaciones de negocio, limpia datos inconsistentes y enriquece la información con códigos de producto maestros. El proceso maneja aproximadamente 50,000 registros diarios con una tasa de error inferior al 0.1%.",
  "key_points": [
    "Procesa ventas de todas las regiones",
    "Valida contra catálogo maestro",
    "Genera alertas por anomalías"
  ],
  "data_quality_notes": "Validación rigurosa. Rechaza registros inválidos",
  "usage_context": "Crítico para reportes financieros diarios"
}
```

## Reglas de Documentación

- **Longitud**: 100-300 palabras para el resumen principal
- **Tono**: Profesional pero accesible
- **Foco**: En el valor del dato, no en la implementación técnica
- **Audiencia**: Analistas de datos, ingenieros, usuarios de negocio
- **Evitar**: Jerga excesiva, acrónimos sin explicar, detalles de código

## Criterios de Calidad

- ¿Explica claramente el propósito?
- ¿Proporciona contexto suficiente?
- ¿Es útil para alguien nuevo en el proyecto?
- ¿Menciona limitaciones o consideraciones importantes?

Analiza el siguiente activo de datos y crea un resumen profesional:

**Tipo**: {{asset_type}}
**Nombre**: {{asset_name}}
**Sistema**: {{system}}
**Contenido/Metadata**: {{asset_content}}

Responde SOLO con el JSON válido.