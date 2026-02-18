---
name: add-incremental
description: Add incremental loading to an existing resource in a dlt pipeline. Uses a cursor field (e.g. created, updated_at) so re-runs only fetch new or updated records. Run after add-pagination has verified the full dataset loads correctly.
argument-hint: <resource_name> (e.g. characters)
---

# Add Incremental Loading to a Resource

Upgrade a resource to incremental loading so re-runs only fetch records newer than the last run. Run this after `/add-pagination` has confirmed the full dataset loads correctly.

Parse `$ARGUMENTS`:
- `resource_name` (required): the resource to add incremental loading to (e.g. `characters`)

## Steps

### 1. Read the pipeline file

Find and read the pipeline file to understand the current resource configuration, particularly the current `write_disposition`.

### 2. Check for replace → merge migration

Read the current `write_disposition` for this resource:

**If `write_disposition` is currently `replace`:**

Warn the user:
> "Switching from `replace` to `merge` requires the existing table to be dropped and recreated. dlt needs to add a `_dlt_root_id` NOT NULL column to child tables, which DuckDB cannot do on existing data. I'll need to delete the `.duckdb` file. The pipeline will reload all data on the next run."

Ask for confirmation. Once confirmed:
- Delete the `.duckdb` file: `rm <pipeline_name>.duckdb`
- Also drop any pending packages: `uv run dlt pipeline <pipeline_name> drop-pending-packages`

**If `write_disposition` is already `merge`:** proceed directly.

### 3. Identify the cursor field

Check what timestamp/date field to use as the incremental cursor. Common fields: `created`, `updated_at`, `created_at`, `modified_at`. Ask the user if unclear.

For APIs that have no server-side filter (the cursor is applied client-side by dlt), use `dlt.sources.incremental` as a client-side filter — dlt will fetch pages and filter out records already seen.

### 4. Update the resource configuration

Edit the resource to add incremental loading and switch to merge:

```python
{
    "name": "<resource_name>",
    "primary_key": "<pk_field>",
    "write_disposition": "merge",
    "endpoint": {
        "path": "<endpoint_path>",
        "data_selector": "results",
        "paginator": { ... },   # keep existing paginator
        "incremental": {
            "cursor_path": "<cursor_field>",       # e.g. "created"
            "initial_value": "1970-01-01T00:00:00.000Z",   # load all history on first run
        },
    },
}
```

If the API supports server-side filtering (e.g. `?since=<timestamp>` parameter), add it to `params`:
```python
"params": {
    "since": "{incremental.start_value}",
}
```

### 5. First run — load all data

```bash
uv run python <pipeline_file>.py
```

Verify full record count loaded.

### 6. Second run — verify 0 new rows

```bash
uv run python <pipeline_file>.py
```

Verify the second run produces 0 load packages (nothing new to load). This confirms incremental loading is working correctly.

```bash
uv run dlt pipeline <pipeline_name> info
```

### 7. Open the dashboard

Run `/open-dashboard` so the user can inspect the data and confirm the load history.
