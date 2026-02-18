---
name: open-dashboard
description: Safely launch the dlt workspace dashboard. Handles all prerequisites — checks dlt[workspace] is installed, kills any conflicting DuckDB process, and ensures read_only is configured in secrets.toml before starting.
argument-hint: (no arguments)
---

# Open the dlt Dashboard

Launch the `dlt dashboard` safely, handling all the prerequisites that cause it to fail if skipped.

Parse `$ARGUMENTS`: none

## Steps

### 1. Check dlt[workspace] is installed

```bash
uv run dlt dashboard --help
```

If this fails with "You must install additional dependencies", install the workspace extra:

```bash
uv add "dlt[workspace]"
```

### 2. Check for conflicting DuckDB lock

Only relevant for DuckDB destinations. Another process holding the DuckDB file open (e.g. a previous dashboard session) will cause "Connection Error: Can't open a connection to same database file".

```bash
lsof <pipeline_name>.duckdb
```

If any process is listed, kill it:

```bash
kill <PID>
```

Wait 1 second and confirm the file is released.

### 3. Verify read_only is set in secrets.toml

The dlt dashboard opens multiple concurrent DuckDB connections (one for loads, one for the dataset browser, etc.). DuckDB only allows this if all connections use the same `access_mode`. Without `read_only = true`, the dashboard dataset browser fails with "Can't open a connection to same database file with a different configuration".

Check whether `read_only = true` is present under `[destination.duckdb.credentials]` in `.dlt/secrets.toml`. Do NOT read the full secrets.toml file — only check for this key.

If it is not set, ask the user to add it:

> "Please add the following to your `.dlt/secrets.toml`:
> ```toml
> [destination.duckdb.credentials]
> read_only = true
> ```
> This lets the dashboard open multiple connections. When you want to run the pipeline to load new data, set it back to `false` or remove it first."

Wait for the user to confirm before proceeding.

### 4. Launch the dashboard in the background

```bash
uv run dlt dashboard
```

Run in background. Wait 4–5 seconds, then check the output for the URL.

### 5. Report the URL

Report the dashboard URL (e.g. `http://localhost:2718`) to the user.

---

## Note on running the pipeline after using the dashboard

Before running `uv run python <pipeline_file>.py` to load new data:
1. Set `read_only = false` (or remove the setting) in `.dlt/secrets.toml`
2. Stop the dashboard if it is running (it holds a DuckDB lock)

The pipeline and dashboard cannot both be active against the same DuckDB file at the same time.
