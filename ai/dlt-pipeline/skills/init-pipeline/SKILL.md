---
name: init-pipeline
description: Scaffold a new dlt pipeline using dlt init, set up the Python venv with uv, and create the initial configuration. Use this as the first step when starting a new pipeline project.
argument-hint: <source_type> <destination> (e.g. rest_api duckdb)
---

# Initialise a dlt Pipeline

Scaffold a new dlt pipeline using `dlt init`, set up the project, and create the baseline config. This is always the first step — never hand-write pipeline files from scratch.

Parse `$ARGUMENTS`:
- `source_type` (required): dlt source type (e.g. `rest_api`, `sql_database`, `filesystem`)
- `destination` (required): destination type (e.g. `duckdb`, `bigquery`, `postgres`)

## Steps

### 1. Check WHY.md

Look for a `WHY.md` file in the current directory. If it does not exist, ask the user:

> "What is the goal for having this data? What will you do with it?"

Create `WHY.md` from their answer before proceeding.

### 2. Check uv is installed

```bash
which uv
```

If not found, tell the user to install it: `brew install uv` or `pip install uv`.

### 3. Initialise the uv project

If `pyproject.toml` does not exist in the current directory:

```bash
uv init --no-readme
```

### 4. Scaffold with dlt init

**Always use the scaffold — never create pipeline files by hand.**

```bash
uv run dlt init <source_type> <destination>
```

This generates the pipeline file with working examples. Read the generated file and show the user what was created.

### 5. Install dependencies

Install both the destination extra AND the workspace extra (required for `dlt dashboard`). Install workspace upfront to avoid dashboard issues later.

```bash
uv add "dlt[<destination>]"
uv add "dlt[workspace]"
```

### 6. Create .dlt/config.toml

Create `.dlt/config.toml` with pipeline metadata. **Critical rule for DuckDB: `dataset_name` MUST differ from `pipeline_name`.** Using the same name causes a DuckDB "Ambiguous reference to catalog or schema" error that breaks pipeline runs.

Good pattern: if pipeline is `rick_and_morty`, use dataset `rick_morty_data`.

```toml
[pipeline]
pipeline_name = "<name_from_project_dir>"
destination = "<destination>"
dataset_name = "<pipeline_name>_data"   # never identical to pipeline_name

[runtime]
log_level = "WARNING"
```

### 7. Inform the user

Show the generated pipeline file and explain:
- Which file to edit (the scaffolded `*_pipeline.py`)
- The structure (client config, resource_defaults, resources list)
- Next step: `/add-resource` to add the first endpoint
