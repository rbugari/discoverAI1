# DiscoverAI v3.0 — Anexos técnicos (LEGACY)

> [!NOTE]
> Este documento se mantiene como **referencia técnica histórica**. Todos los contratos de la v4.0 están ahora consolidados en [MASTER_SPEC_v4.md](../MASTER_SPEC_v4.md).

Este documento **complementa** la SPEC v3.0 principal y debe entregarse **junto al spec** al generador de código.

Incluye:
1. **Contratos JSON de salida por acción** (para evitar ambigüedad del generador / LLM).
2. **Reglas de SKIP / IGNORE configurables** (policy-driven) para repositorios de data heterogéneos.

---

## 1) Contratos JSON de salida por acción (Action Profiles)

> Regla global:
> - Todo output debe ser **JSON válido**.
> - No se permite texto fuera del JSON.
> - Si no hay evidencia clara, debe marcarse como `hypothesis=true`.

---

### 1.1 Acción: `planner.classifier`

**Objetivo**: clasificar archivos dudosos durante la fase Planning.

**Input (contextual)**:
- file_path
- extension
- size_bytes
- sample_head (primeros N chars)

**Output JSON obligatorio**:

```json
{
  "doc_type": "SQL|DDL|DTSX|DSX|PYTHON|CONFIG|MEDIA|BINARY|UNKNOWN",
  "category": "FOUNDATION|ORCHESTRATION|ETL_PACKAGE|TRANSFORM_SCRIPT|CONFIG|MEDIA|NOISE",
  "strategy": "PARSER_ONLY|PARSER_PLUS_LLM|LLM_ONLY|SKIP",
  "risk_score": 0,
  "value_score": 0,
  "recommended_action": "PROCESS|SKIP|REVIEW",
  "why": "short explanation",
  "signals": ["string", "string"]
}
```

**Reglas**:
- `risk_score` y `value_score` deben estar en rango **0–100**.
- `signals` deben ser *tokens reales* detectados en el archivo (no inventados).

---

### 1.2 Acción: `extract.schema`

**Objetivo**: extraer estructura de datos (schema-first).

**Output JSON obligatorio**:

```json
{
  "assets": [
    {
      "asset_type": "database|schema|table|column",
      "canonical_name": "string",
      "parent": "string|null",
      "metadata": {
        "datatype": "string|null",
        "nullable": true,
        "comment": "string|null"
      }
    }
  ],
  "evidence": [
    {
      "evidence_id": "e1",
      "type": "ddl|comment",
      "locator": {
        "file": "path",
        "line_start": 10,
        "line_end": 20
      },
      "snippet": "short exact snippet"
    }
  ]
}
```

**Reglas**:
- No inventar columnas.
- Si no hay comentario explícito, no generar `comment`.

---

### 1.3 Acción: `extract.lineage.sql`

**Objetivo**: extraer lineage a partir de SQL DML.

```json
{
  "edges": [
    {
      "from": "schema.table_or_column",
      "to": "schema.table_or_column",
      "edge_type": "reads|writes|transforms",
      "confidence": 0.0,
      "is_hypothesis": false,
      "evidence_refs": ["e1"]
    }
  ],
  "evidence": [
    {
      "evidence_id": "e1",
      "type": "sql",
      "locator": {
        "file": "path",
        "line_start": 30,
        "line_end": 45
      },
      "snippet": "SELECT ..."
    }
  ]
}
```

**Reglas**:
- Si la tabla destino no es clara → `is_hypothesis=true`.
- `confidence` ≤ 0.3 si es hipótesis.

---

### 1.4 Acción: `extract.lineage.package` (SSIS / DataStage)

```json
{
  "process": {
    "name": "string",
    "type": "SSIS|DATASTAGE",
    "connections": ["conn1", "conn2"]
  },
  "edges": [
    {
      "from": "source",
      "to": "target",
      "edge_type": "reads|writes",
      "confidence": 0.0,
      "is_hypothesis": false,
      "evidence_refs": ["e1"]
    }
  ],
  "evidence": [
    {
      "evidence_id": "e1",
      "type": "xml|text",
      "locator": {
        "file": "path",
        "xpath": "//DTS:Executable"
      },
      "snippet": "<DTS:Executable ...>"
    }
  ]
}
```

**Reglas**:
- Priorizar parsing estructural.
- Usar LLM solo para enriquecer nombres o mapping ambiguo.

---

### 1.5 Acción: `summarize.asset`

```json
{
  "summary": "concise description",
  "confidence": 0.0,
  "based_on": ["evidence_id"]
}
```

---

### 1.6 Acción: `qa.chat`

```json
{
  "answer": "text",
  "referenced_assets": ["canonical_name"],
  "referenced_edges": ["edge_id"],
  "limitations": "if any"
}
```

---

## 2) Reglas de SKIP / IGNORE (Policy Engine)

> Estas reglas deben evaluarse **antes de cualquier LLM heavy**.

### 2.1 Reglas por extensión (default SKIP)

```yaml
skip_extensions:
  - bak
  - dump
  - dmp
  - tar
  - gz
  - zip
  - rar
  - 7z
  - iso
```

### 2.2 Reglas por tamaño

```yaml
max_file_size_bytes: 524288000   # 500 MB
```

- Si supera el límite → `NOISE`, `recommended_action=SKIP`.

---

### 2.3 Reglas por path

```yaml
skip_paths:
  - "**/node_modules/**"
  - "**/.git/**"
  - "**/target/**"
  - "**/dist/**"
  - "**/build/**"
  - "**/venv/**"
  - "**/__pycache__/**"
```

---

### 2.4 Reglas por contenido

- Archivos binarios sin strings útiles → `NOISE`.
- Dumps de base de datos completos → `REVIEW` (no procesar por defecto).
- Media (png/jpg/pdf):
  - default `SKIP`
  - solo `PROCESS` si `vision_enabled=true`.

---

### 2.5 Overrides por solución

Cada `solution` puede definir:

```yaml
solution_policy:
  allow_media: false
  max_file_size_bytes: 200000000
  allow_unknown_text: true
```

Estas reglas **sobrescriben los defaults**.

---

## 3) Regla final (no negociable)

> Ningún archivo puede consumir LLM heavy si:
> - está marcado como `SKIP`
> - supera el tamaño permitido
> - pertenece a `NOISE`
> - el plan no fue aprobado

---

## 4) Objetivo del anexo

- El generador **no decide formatos**: los contratos están definidos.
- El sistema es **predecible, auditable y costeable**.
- DiscoverAI v3 se posiciona como **ingeniería de discovery**, no scraping con IA.

