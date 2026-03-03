---
name: create-transformation
description: Create dlt transformations that map source data to a Canonical Data Model (CDM). Use when the user wants to transform raw data into standardized CDM entities, map source tables to canonical structures, or build data transformations based on their ontology and CDM.
argument-hint: [pipeline-name] [-- <entity-or-hints>]
---

# Create transformation to canonical model

**Transforms raw source data into a Canonical Data Model (CDM) using dlt transformations.** The ontology defines your business semantics; the CDM formalizes those semantics into implementation-ready entities; transformations map messy source data into that clean structure using `@dlt.hub.transformation`.

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
- **dlt Transformations**: `https://dlthub.com/docs/hub/features/transformations`
- Dataset access: `https://dlthub.com/docs/general-usage/dataset-access/dataset`
- ISON format: `https://ison.dev/spec.html`

### 3. Check for CDM

Read `.schema/CDM.ison` to understand the target canonical model structure.

If the file doesn't exist:
> No CDM found. The CDM defines your canonical entities and how source data maps to them.
>
> Run `generate-cdm` first to create the canonical data model from your ontology.

**STOP and wait for CDM to be created.**

## Steps

### 1. Analyze source-to-CDM mapping

Compare the source schema (`.schema/<dataset>.ison`) against the CDM (`.schema/CDM.ison`):

For each CDM entity, identify:
- Which source table(s) map to it
- Column mappings (source column → CDM attribute)
- Type conversions needed (e.g., `string` → `float` for amounts)
- Joins required (for denormalized CDM entities from multiple source tables)

Create a mapping table:

| CDM Entity | CDM Attribute | Source Table | Source Column | Transform |
|------------|---------------|--------------|---------------|-----------|
| Customer | customer_id | contacts | id | direct |
| Customer | email | contacts | properties__email | direct |
| Customer | name | contacts | properties__firstname, properties__lastname | concat |
| Deal | amount | deals | properties__amount | cast to float |

### 2. Identify mapping discrepancies

Look for gaps and ambiguities:

**Source columns without CDM mapping:**
- Columns in source that don't map to any CDM attribute
- Ask: "Should `properties__slack_user_name` be added to the CDM, or ignored?"

**CDM attributes without source mapping:**
- CDM attributes with no corresponding source column
- Ask: "The CDM expects `customer_status` but the source has no status field. Should we derive it from another field, use a default, or mark as UNKNOWN?"

**Cardinality mismatches:**
- CDM expects one-to-one but source has one-to-many
- Ask: "A contact can have multiple companies via `contacts__associations__companies__results`. Should we pick the primary company, or create multiple Customer records?"

**Type conflicts:**
- Source type incompatible with CDM type
- Ask: "Source `properties__amount` is string but CDM expects float. Should we cast it, or handle parse errors?"

**Present all discrepancies to the user and STOP.** Resolve each before generating transformations.

### 3. Generate dlt transformation script

After resolving discrepancies, create `transformations/<dataset>_to_cdm.py`.

**Structure guidelines:**

1. **One transformation function per CDM entity** — Each CDM entity from `.schema/CDM.ison` gets its own `@dlt.hub.transformation` decorated function

2. **Transformation function signature:**
   - Takes `dataset: dlt.Dataset` as input
   - Yields an ibis expression or SQL relation
   - Use `write_disposition="merge"` for entities with primary keys
   - Set `primary_key` to the CDM entity's canonical identifier

3. **Building the select expression:**
   - Read source table: `dataset.table("<source_table>").to_ibis()`
   - Map each CDM attribute to its source column(s) using the mapping table from Step 1
   - Apply transforms (casting, concatenation, coalesce) as identified

4. **Handling relationships (many-to-many):**
   - CDM relationship tables need joins between association tables and parent tables
   - Use `_dlt_parent_id` → `_dlt_id` join pattern for dlt nested tables

5. **Grouping transformations:**
   - Wrap all entity transformations in a `@dlt.source` function
   - This allows running all transformations together

6. **Main execution block:**
   - Create source pipeline pointing to raw data location
   - Create CDM pipeline pointing to CDM dataset location
   - Run: `cdm_pipeline.run(cdm_transformations(source_pipeline.dataset()))`

### 4. Transformation patterns

Apply these patterns based on the mapping table:

| Scenario | Pattern |
|----------|---------|
| Direct mapping | `cdm_attr=table.source_column` |
| Concatenation | `full_name=table.first + " " + table.last` |
| Type casting | `amount=table.amount_str.cast("float64")` |
| Null → sentinel | `status=ibis.coalesce(table.status, "UNKNOWN")` |
| dlt parent-child join | Join on `child._dlt_parent_id == parent._dlt_id` |
| SQL alternative | `yield dataset("SELECT ... FROM ...")` instead of ibis |

Refer to [dlt transformations docs](https://dlthub.com/docs/hub/features/transformations) for full syntax.

### 5. Validate and test

After generating the script:

1. **Dry run** — Check computed schema before execution:
```python
dataset = source_pipeline.dataset()
relation = dataset.table("contacts").to_ibis().select(...)
print(dataset(relation).columns)
```

2. **Run transformations** — Execute in the user's environment
3. **Verify row counts** — `cdm_pipeline.dataset().row_counts().df()`
4. **Spot check data** — Sample a few rows from each CDM table

## Output

```
Transformation script created: transformations/<dataset>_to_cdm.py

Mappings:
- CDM Customer ← contacts (<X> columns mapped)
- CDM Company ← companies (<Y> columns mapped)
- CDM Deal ← deals (<Z> columns mapped)
- CDM CustomerCompany ← contacts__associations__companies__results

Resolved discrepancies:
- <question>: <answer>
...

Next steps:
- Review transformations/<dataset>_to_cdm.py
- Run: python transformations/<dataset>_to_cdm.py
- Verify CDM tables in destination
```