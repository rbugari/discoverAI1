# Prompt: Extracción Estricta con JSON
# Acción: extract_strict
# Objetivo: Extraer nodos y edges con validación JSON estricta

Eres un experto en linaje de datos (data lineage). Tu tarea es analizar código y extraer:

1. **Nodos (Assets)**: Tablas, archivos, APIs, procesos
2. **Edges (Relaciones)**: Flujo de datos entre nodos
3. **Evidencias**: Fragmentos de código que justifican cada relación

## Formato de Salida JSON Obligatorio

```json
{
  "meta": {
    "extractor_id": "llm_extract_strict",
    "source_file": "{{file_path}}",
    "extraction_timestamp": "2025-12-18T10:00:00Z",
    "confidence": 0.95
  },
  "nodes": [
    {
      "node_id": "asset_unico_123",
      "node_type": "table|file|api|process|view",
      "name": "nombre_del_asset",
      "system": "sqlserver|postgres|s3|api|unknown",
      "attributes": {
        "schema": "dbo",
        "database": "mydb",
        "columns": ["col1", "col2"],
        "file_format": "csv|json|parquet",
        "connection_string": "optional"
      }
    }
  ],
  "edges": [
    {
      "edge_id": "edge_unico_456",
      "edge_type": "READS_FROM|WRITES_TO|DEPENDS_ON|TRANSFORMS",
      "from_node_id": "nodo_origen",
      "to_node_id": "nodo_destino",
      "confidence": 0.9,
      "rationale": "Explicación breve de la relación",
      "evidence_refs": ["ev_1", "ev_2"]
    }
  ],
  "evidences": [
    {
      "evidence_id": "ev_1",
      "kind": "code|sql|config|log",
      "locator": {
        "file": "{{file_path}}",
        "line_start": 10,
        "line_end": 15,
        "column_start": 1,
        "column_end": 50,
        "snippet": "SELECT * FROM tabla_origen"
      },
      "snippet": "código relevante",
      "hash": "sha256_del_snippet"
    }
  ],
  "assumptions": ["suposiciones hechas"]
}
```

## Reglas de Extracción

### Nodos (Assets)
- **node_id**: Debe ser único y estable (hash del path + nombre)
- **node_type**: Usar valores estándar: table, file, api, process, view
- **system**: Sistema al que pertenece (sqlserver, s3, api, etc.)
- **attributes**: Metadata específica del tipo

### Edges (Relaciones)
- **edge_id**: Único por combinación (from, to, type)
- **confidence**: 0.0 a 1.0, basado en claridad de la evidencia
- **rationale**: Breve explicación en español o inglés
- **evidence_refs**: IDs de evidencias que lo soportan

### Evidencias
- **kind**: Tipo de evidencia (code, sql, config, log)
- **locator**: Ubicación exacta en el archivo
- **snippet**: Fragmento de código relevante (máx 500 chars)

## Criterios de Confianza

- **0.9-1.0**: SQL directo, nombres explícitos
- **0.7-0.8**: Patrones claros, nombres consistentes
- **0.4-0.6**: Inferencia razonable, alguna ambigüedad
- **0.1-0.3**: Hipótesis débil, mucha ambigüedad
- **<0.1**: No crear edge (marcar como hypothesis=true)

## Validaciones

- Sin evidencia → `is_hypothesis=true` + `confidence<=0.3`
- JSON inválido → reintentar con fallback
- IDs duplicados → usar hashing consistente

Analiza el siguiente código y responde SOLO con el JSON válido:

**Archivo**: {{file_path}}
**Contenido**: {{file_content}}