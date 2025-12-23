# Prompt: Extracción SQL Especializada
# Acción: extract_sql
# Objetivo: Análisis profundo de scripts SQL

Eres un experto en SQL y linaje de datos. Analiza este script SQL y extrae:

## Objetivos de Extracción

1. **Tablas y Vistas**
   - Tablas en FROM, JOIN, WITH, subqueries
   - Vistas referenciadas
   - Tablas temporales (CTE)

2. **Operaciones**
   - SELECT (lecturas)
   - INSERT (escrituras)
   - UPDATE (modificaciones)
   - CREATE TABLE/VIEW (creaciones)
   - DELETE (eliminaciones)

3. **Relaciones**
   - JOINs entre tablas
   - Dependencias de subqueries
   - Relaciones CTE

## Formato de Salida JSON

```json
{
  "meta": {
    "extractor_id": "sql_specialized",
    "source_file": "{{file_path}}",
    "sql_type": "ddl|dml|mixed",
    "confidence": 0.95
  },
  "nodes": [
    {
      "node_id": "table_dbo_customers",
      "node_type": "table",
      "name": "dbo.customers",
      "system": "sqlserver",
      "attributes": {
        "schema": "dbo",
        "operation": "read",
        "columns": ["customer_id", "name", "email"],
        "transformation_logic": "Filter by active status",
        "business_intent": "Synchronize active customers to target",
        "line_number": 15
      }
    }
  ],
  "edges": [
    {
      "edge_id": "edge_join_customers_orders",
      "edge_type": "JOINS_WITH",
      "from_node_id": "table_dbo_orders",
      "to_node_id": "table_dbo_customers",
      "confidence": 0.9,
      "rationale": "JOIN customers ON orders.customer_id = customers.id",
      "join_type": "INNER",
      "join_condition": "orders.customer_id = customers.id",
      "evidence_refs": ["ev_1"]
    }
  ],
  "evidences": [
    {
      "evidence_id": "ev_1",
      "kind": "sql",
      "locator": {
        "file": "{{file_path}}",
        "line_start": 20,
        "line_end": 25,
        "snippet": "JOIN customers c ON o.customer_id = c.customer_id"
      },
      "snippet": "JOIN customers c ON o.customer_id = c.customer_id",
      "hash": "sha256_del_snippet"
    }
  ]
}
```

## Patrones SQL a Detectar

### Lecturas (SELECT)
```sql
SELECT col1, col2 FROM schema.table WHERE condition
SELECT * FROM view_name
WITH cte_name AS (SELECT * FROM table1) SELECT * FROM cte_name
```

### Escrituras (INSERT/UPDATE/DELETE)
```sql
INSERT INTO target_table SELECT * FROM source_table
UPDATE table SET col = value WHERE condition
DELETE FROM table WHERE condition
```

### Creaciones (DDL)
```sql
CREATE TABLE new_table AS SELECT * FROM old_table
CREATE VIEW view_name AS SELECT * FROM table
```

### JOINs
```sql
SELECT * FROM t1 JOIN t2 ON t1.id = t2.id
SELECT * FROM t1 LEFT JOIN t2 ON t1.id = t2.id
SELECT * FROM t1, t2 WHERE t1.id = t2.id
```

## Reglas de Confianza

- **0.95**: Nombres de tablas explícitos en FROM/JOIN
- **0.90**: Columnas mencionadas en SELECT
- **0.85**: JOINs con condiciones claras
- **0.70**: Subqueries con alias
- **0.60**: CTEs (Common Table Expressions)
- **0.50**: Vistas (requiere inferencia)

## Validaciones

- Cada nodo debe tener node_id único
- Cada edge debe referenciar nodos existentes
- Evidencias deben incluir snippet real del código
- Confianza debe estar entre 0.0 y 1.0

Analiza el siguiente script SQL:

**Archivo**: {{file_path}}
**Contenido**: {{sql_content}}

Responde SOLO con el JSON válido.