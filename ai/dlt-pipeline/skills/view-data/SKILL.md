---
name: view-data
description: View the schema and a data preview of a loaded dlt pipeline. Shows table structure and row counts using the dlt CLI.
argument-hint: <pipeline-name>
---

# View loaded pipeline data

Parse `$ARGUMENTS`:
- `pipeline-name` (required): the dlt pipeline name (e.g., `rick_and_morty_pipeline`)

## Steps

### 1. Show the schema

```bash
uv run dlt pipeline <pipeline_name> schema
```

Parse the output and present a clean summary:
- List each user-facing table with its columns, excluding dlt internal columns (`_dlt_id`, `_dlt_load_id`, `_dlt_parent_id`, `_dlt_list_idx`, `_dlt_root_id`)
- Note child tables and which parent they belong to
- Skip dlt system tables (`_dlt_version`, `_dlt_loads`, `_dlt_pipeline_state`)

### 2. Show row counts

```bash
uv run dlt pipeline <pipeline_name> info
```

Extract and display the row counts per table from the output.

### 3. Show a data sample

```bash
uv run dlt pipeline <pipeline_name> show
```

If `dlt pipeline show` is not available or errors, display a note that the user can explore the DuckDB file directly using a SQL client or the DuckDB CLI:

```bash
uv run python -c "import duckdb; conn = duckdb.connect('<pipeline_name>.duckdb'); print(conn.execute('SHOW TABLES').fetchall())"
```

Present results as clean tables — schema first, then row counts, then a sample of each main table.