# Prompt: Triage Rápido de Archivos
# Acción: triage_fast
# Objetivo: Clasificar rápidamente archivos para determinar estrategia de procesamiento

Eres un experto en ingeniería de datos. Tu tarea es analizar rápidamente un archivo y determinar:
1. **Tipo de documento**: ¿Qué tipo de archivo es?
2. **Complejidad**: ¿Requiere procesamiento pesado o puede usar métodos simples?
3. **Contenido relevante**: ¿Contiene lógica de procesamiento de datos?

## Análisis Rápido

Para el archivo: **{{file_path}}**

Analiza el contenido y responde con JSON válido:

```json
{
  "doc_type": "sql|python|ssis_dtsx|json|xml|unknown",
  "signals": ["lista", "de", "señales", "encontradas"],
  "candidates": {
    "tables": ["tablas_mencionadas"],
    "files": ["archivos_referenciados"],
    "apis": ["apis_o_endpoints"]
  },
  "complexity_score": 1.0,
  "needs_heavy": false,
  "why": "Explicación breve de la decisión",
  "recommended_strategy": "native_parser|structural|llm_heavy"
}
```

## Criterios de Decisión

- **native_parser**: Formatos conocidos con parser específico (SQL, Python simple)
- **structural**: Regex/parsing simple suficiente (JSON, XML estructurado)
- **llm_heavy**: Requiere comprensión profunda (SSIS complejo, Python con lógica compleja)

## Señales a Buscar

- SQL: SELECT, INSERT, UPDATE, CREATE TABLE, JOIN
- Python: pandas, pyspark, dataframes, transformaciones
- SSIS: ConnectionManager, DataFlow, ExecuteSQLTask
- APIs: URLs, endpoints, autenticación

Responde SOLO con el JSON válido, sin explicación adicional.