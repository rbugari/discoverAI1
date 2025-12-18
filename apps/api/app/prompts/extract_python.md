# Prompt: Extracción Python Especializada
# Acción: extract_python
# Objetivo: Análisis de código Python para linaje de datos

Eres un experto en Python, PySpark y Pandas. Analiza este código Python y extrae:

## Objetivos de Extracción

1. **DataFrames y Datasets**
   - pandas.DataFrame
   - pyspark.sql.DataFrame
   - Variables que contienen datos
   - Lecturas de archivos (CSV, JSON, Parquet)

2. **Operaciones de Transformación**
   - .merge(), .join()
   - .groupby(), .agg()
   - .filter(), .where()
   - .select(), .withColumn()

3. **Lecturas y Escrituras**
   - pd.read_csv(), spark.read.parquet()
   - df.to_csv(), df.write.parquet()
   - Conexiones a bases de datos

4. **APIs y Servicios**
   - requests.get(), post()
   - Conexiones a APIs externas
   - Autenticaciones y endpoints

## Formato de Salida JSON

```json
{
  "meta": {
    "extractor_id": "python_specialized",
    "source_file": "{{file_path}}",
    "python_type": "pandas|pyspark|mixed|api",
    "confidence": 0.9
  },
  "nodes": [
    {
      "node_id": "df_sales_data",
      "node_type": "dataframe",
      "name": "sales_data",
      "system": "pandas",
      "attributes": {
        "library": "pandas",
        "type": "DataFrame",
        "source_file": "sales.csv",
        "operation": "read",
        "line_number": 15
      }
    }
  ],
  "edges": [
    {
      "edge_id": "edge_merge_sales_customers",
      "edge_type": "JOINS_WITH",
      "from_node_id": "df_sales",
      "to_node_id": "df_customers",
      "confidence": 0.95,
      "rationale": "pd.merge(sales, customers, on='customer_id')",
      "join_keys": ["customer_id"],
      "join_type": "inner",
      "evidence_refs": ["ev_1"]
    }
  ],
  "evidences": [
    {
      "evidence_id": "ev_1",
      "kind": "code",
      "locator": {
        "file": "{{file_path}}",
        "line_start": 25,
        "line_end": 25,
        "snippet": "merged_df = pd.merge(sales_df, customers_df, on='customer_id', how='inner')"
      },
      "snippet": "merged_df = pd.merge(sales_df, customers_df, on='customer_id', how='inner')",
      "hash": "sha256_del_snippet"
    }
  ]
}
```

## Patrones Python a Detectar

### Pandas
```python
import pandas as pd

# Lecturas
df = pd.read_csv('file.csv')
df = pd.read_json('data.json')
df = pd.read_parquet('data.parquet')

# Transformaciones
df_merged = pd.merge(df1, df2, on='key')
df_grouped = df.groupby('category').agg({'sales': 'sum'})
df_filtered = df[df['amount'] > 1000]

# Escrituras
df.to_csv('output.csv', index=False)
df.to_json('output.json')
df.to_parquet('output.parquet')
```

### PySpark
```python
from pyspark.sql import SparkSession

# Lecturas
df = spark.read.csv('file.csv', header=True, inferSchema=True)
df = spark.read.parquet('data.parquet')

# Transformaciones
df_joined = df1.join(df2, 'key', 'inner')
df_grouped = df.groupBy('category').agg(sum('sales').alias('total_sales'))
df_filtered = df.filter(df.amount > 1000)

# Escrituras
df.write.parquet('output.parquet')
df.write.csv('output.csv', header=True)
```

### APIs
```python
import requests

# Lecturas de API
response = requests.get('https://api.example.com/data')
data = response.json()
df = pd.DataFrame(data)

# Escrituras a API
requests.post('https://api.example.com/upload', json=data)
```

## Reglas de Confianza

- **0.95**: Operaciones directas de pandas/pyspark
- **0.90**: Nombres de archivos en strings literales
- **0.85**: Variables con nombres descriptivos
- **0.80**: Métodos de transformación estándar
- **0.70**: Operaciones complejas con múltiples pasos
- **0.50**: Variables intermedias (requiere tracking)

## Validaciones

- Cada nodo debe tener node_id único basado en nombre de variable
- Cada edge debe referenciar nodos existentes
- Evidencias deben incluir línea exacta del código
- Confianza debe reflejar complejidad del análisis

Analiza el siguiente código Python:

**Archivo**: {{file_path}}
**Contenido**: {{python_content}}

Responde SOLO con el JSON válido.