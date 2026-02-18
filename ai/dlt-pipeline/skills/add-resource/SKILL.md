---
name: add-resource
description: Add a single minimal resource (endpoint) to an existing dlt REST API pipeline. Loads page 1 only to verify structure before adding pagination or incremental loading. Always edit the existing scaffolded pipeline file — never create a new one.
argument-hint: <resource_name> <endpoint_path> (e.g. characters character)
---

# Add a Minimal Resource

Add one resource to the pipeline in its simplest form: page 1 only, no incremental loading. The goal is to verify the data structure lands correctly in the destination before adding complexity.

**Always edit the existing scaffolded pipeline file. Never create a new file.**

Parse `$ARGUMENTS`:
- `resource_name` (required): name for the resource/table (e.g. `characters`)
- `endpoint_path` (required): API endpoint path relative to base_url (e.g. `character`)

## Steps

### 1. Read the existing pipeline file

Find and read the scaffolded pipeline file (e.g. `rest_api_pipeline.py`). Understand its structure before editing. If the file does not exist, run `/init-pipeline` first.

### 2. Add ONE resource to the resources list

Add **only this one resource** to the `resources` list in the `RESTAPIConfig`. Do not add other endpoints at the same time — the recipe requires one endpoint fully working before adding others.

```python
{
    "name": "<resource_name>",
    "endpoint": {
        "path": "<endpoint_path>",
        "data_selector": "results",   # adjust to match actual response envelope
        "paginator": {"type": "single_page"},   # REQUIRED — see note below
    },
}
```

Set in `resource_defaults`:
- `primary_key`: the resource's PK field (e.g. `"id"`)
- `write_disposition`: `"replace"` for this minimal step

**Critical**: always specify `{"type": "single_page"}` explicitly. Omitting the paginator does NOT fetch one page — dlt will attempt to auto-detect pagination and may load all pages, defeating the purpose of this step.

Ask the user about `data_selector` if uncertain — check what key in the API response contains the records (common values: `results`, `data`, `items`).

### 3. Run the pipeline

```bash
uv run python <pipeline_file>.py
```

### 4. Verify

Check that the expected number of rows landed (typically ~20 for page-1 of paginated APIs):

```bash
uv run python -c "
import dlt
p = dlt.pipeline(pipeline_name='<pipeline_name>', destination='duckdb', dataset_name='<dataset_name>')
with p.sql_client() as c:
    with c.execute_query('SELECT COUNT(*) FROM <resource_name>') as cur:
        print(cur.fetchone()[0])
"
```

Also verify that nested objects were flattened inline (e.g. `origin__name`) and arrays produced child tables (e.g. `<resource_name>__<array_field>`).

### 5. Open the dashboard

Run `/open-dashboard` so the user can inspect the loaded data.
