---
name: inspect
description: Use dlt native methods to inspect pipelines without writing database scripts. Triggers when the user asks to: check row counts, inspect pipeline state, see what's loaded in the destination, view load history, check for failed jobs, inspect schemas, understand incremental cursors, or debug what a pipeline has done. Always prefer these built-in methods over raw SQL, direct DB connections, or writing one-off query scripts.
---

# Inspect

Prefer these approaches in order — from fastest to most powerful:

1. **CLI** — no code, instant, great for post-mortem
2. **Python API** — programmatic, chainable, scriptable
3. **Dashboard** — visual, interactive exploration

---

## 1. CLI

Always `uv run` in the project venv.

```bash
# State: dataset name, destination, schemas, completed packages, source/resource state
dlt pipeline <name> info
dlt pipeline <name> info -v    # more detail
dlt pipeline <name> info -vv   # maximum detail

# Last run: extract/normalize/load timing, row counts, exceptions
dlt pipeline <name> trace
dlt pipeline <name> trace -v

# Schema: tables, columns, data types
dlt pipeline <name> schema --format yaml    # human-readable
dlt pipeline <name> schema --format json
dlt pipeline <name> schema --format mermaid

# Load package: job details, file sizes, destination errors
dlt pipeline <name> load-package           # most recent
dlt pipeline <name> load-package <id>      # specific load ID
dlt pipeline <name> load-package -v        # include schema changes

# Failed jobs across all completed packages
dlt pipeline <name> failed-jobs

# List all local pipelines
dlt pipeline list-pipelines
dlt pipeline -l
```

---

## 2. Python API

### Row counts — fastest destination check

```python
dataset = pipeline.dataset()
print(dataset.row_counts().df())       # DataFrame: table → row count
print(dataset.row_counts().fetchall()) # list of (table, count) tuples
```

### Inspect a table

```python
rel = dataset["my_table"]             # or dataset.table("my_table")

rel.df()                              # full table as DataFrame
rel.limit(10).df()                    # first 10 rows
rel.select("id", "name").where("status = 'active'").order_by("created_at").df()
rel.count().fetchone()[0]             # row count for this table
```

### Raw SQL query

```python
result = dataset("SELECT a.id, COUNT(b.id) FROM a LEFT JOIN b ON a.id = b.a_id GROUP BY 1")
result.df()
```

### Last run trace

```python
print(pipeline.last_trace)            # extract / normalize / load steps, timing, errors

for step in pipeline.last_trace.steps:
    print(step.step_kind, step.duration, step.step_exception)
```

### Pipeline state (incremental cursors, resource checkpoints)

```python
print(pipeline.state)                 # full state dict
```

### Schema

```python
print(pipeline.default_schema.to_pretty_yaml())   # tables, columns, hints
schema.tables                                      # dict of table schemas
```

### Load packages

```python
pipeline.list_completed_load_packages()
pipeline.list_extracted_load_packages()
pipeline.list_normalized_load_packages()
```

### Quick health checks

```python
pipeline.has_data           # bool: has schemas, files, or loaded data
pipeline.has_pending_data   # bool: packages awaiting normalization/load
```

---

## 3. Dashboard (visual)

```bash
dlt pipeline <name> show              # marimo dashboard (recommended)
dlt pipeline <name> show --streamlit  # legacy Streamlit version
dlt dashboard                         # all pipelines
```

Good for: browsing schemas interactively, tracking incremental state per resource, reviewing run history, querying destination data without code.

---

## Avoid

- `pipeline.sql_client()` for inspection — use `pipeline.dataset()` instead
- Raw DB drivers (psycopg2, sqlalchemy, duckdb.connect) just to check row counts
- Re-running the pipeline to observe its behavior
- One-off query scripts — the CLI and dataset API cover almost every inspection need
