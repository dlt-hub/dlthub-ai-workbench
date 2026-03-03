---
name: create-transformation
description: Create dlt transformations that map source data to a canonical model (ontology). Use when the user wants to transform raw data into standardized entities, create canonical models, map source tables to ontology classes, or build data transformations based on their data model.
argument-hint: [pipeline-name] [-- <entity-or-hints>]
---

# Create transformation to canonical model

**Transforms raw source data into a canonical model based on your ontology.** The ontology defines your business entities and relationships; transformations map messy source data into that clean structure.

Parse `$ARGUMENTS`:
- `pipeline-name` (optional): the dlt pipeline containing source data. If omitted, infer from session context or ask the user.
- `entity-or-hints` (optional, after `--`): specific entity to transform (e.g., `-- Company`) or hints about transformation goals.

## Prerequisites

### 1. Check for ontology

Read `.schema/ontology.jsonld` to understand the target canonical model.

If the file doesn't exist or is empty:
> No ontology found. The ontology defines your canonical data model — the entities and relationships your transformations will produce.
>
> Run `create-ontology` first to define your business entities and relationships.

**STOP and wait for ontology to be created.**

### 2. Connect to source data and extract schema

Ask the user where their source data lives:
- **destination**: e.g. `duckdb`, `postgres`, `bigquery`, `snowflake`
- **dataset_name**: the database/schema name where data lives

**Requirements** (must be installed in the environment):
```
dlt[<destination>]  # e.g. dlt[bigquery], dlt[postgres]
ibis-framework
```

**Before executing any code:**
1. Check for a Python environment in the repo (look for `.venv/`, `venv/`, or check if `uv` is available)
2. If using uv: run with `uv run python <script>`
3. If using venv: activate it first (`.venv/Scripts/activate` on Windows, `source .venv/bin/activate` on Unix), then run `python <script>`
4. If no environment found: ask the user how to run Python in their setup
5. If the script takes too long to run (>30 seconds), ask the user to execute it themselves in terminal

Create `extract_schema.py` with the user's connection details:

```python
import dlt

def schema_to_ison(db) -> str:
    """Convert ibis schema to ISON format (https://ison.dev)."""
    lines = []
    
    # Schema table block
    lines.append("table.schema")
    lines.append("table_name column_name column_type nullable")
    
    for table_name in sorted(db.list_tables()):
        schema = db.table(table_name).schema()
        for col_name, col_type in schema.items():
            type_str = str(col_type)
            nullable = "true" if "nullable" in type_str.lower() or not type_str.startswith("!") else "false"
            clean_type = type_str.lstrip("!")
            lines.append(f"{table_name} {col_name} {clean_type} {nullable}")
    
    lines.append("")
    
    # Parent-child relationships (dlt convention: __ separator)
    lines.append("table.relationships")
    lines.append("child_table parent_table relationship")
    
    tables = set(db.list_tables())
    for table_name in sorted(tables):
        if "__" in table_name:
            parts = table_name.split("__")
            for i in range(len(parts) - 1, 0, -1):
                potential_parent = "__".join(parts[:i])
                if potential_parent in tables:
                    lines.append(f"{table_name} :{potential_parent} :CHILD_OF")
                    break
    
    return "\n".join(lines)


if __name__ == "__main__":
    import os
    
    dataset_name = "<dataset_name>"  # REPLACE: database/schema name
    
    pipeline = dlt.pipeline(
        pipeline_name="source_data",
        destination="<destination>",  # REPLACE: e.g. "bigquery", "postgres"
        dataset_name=dataset_name
    )
    dataset = pipeline.dataset()
    db = dataset.ibis()
    
    ison_output = schema_to_ison(db)
    print(ison_output)
    
    os.makedirs(".schema", exist_ok=True)
    output_path = f".schema/{dataset_name}.ison"
    with open(output_path, "w") as f:
        f.write(ison_output)
    print(f"\nSaved to {output_path}")
```

Run the script from within THE ACTIVE ENVIRONMENT OF THIS REPO:
```bash
python extract_schema.py
```
Then read `.schema/<dataset_name>.ison` to confirm success.

The output contains:
- All tables and their columns with types
- Parent-child relationships based on dlt's `__` naming convention

**Essential Reading:**
- Dataset access: `https://dlthub.com/docs/general-usage/dataset-access/dataset`
- ISON format: `https://ison.dev/spec.html`
