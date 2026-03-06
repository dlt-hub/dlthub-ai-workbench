---
name: connect-and-profile
description: Connect to a dlt pipeline and profile its tables — schemas, row counts, null rates, anomalies, PII flags. Use when the user wants to attach to a pipeline, check what tables exist, show row counts, preview sample rows, inspect schemas, or understand what a pipeline produced. Trigger phrases include "what tables do I have", "show me the data", "how many rows", "what does the schema look like", "connect to my pipeline", "what did the pipeline load". Do NOT use for planning charts or dashboards (use analyze-questions), building or fixing pipelines (use rest-api-pipeline toolkit), or deploying pipelines (use dlthub-runtime toolkit).
---

# Connect to pipeline data and profile tables

Connect to a dlt pipeline, verify access, and profile the tables relevant to the user's question.

Parse `$ARGUMENTS`:
- `pipeline-name` (optional): the dlt pipeline name. If omitted, infer from session context. If ambiguous, ask the user and stop.
- `hints` (optional, after `--`): focus areas (e.g., `-- spending by model`)

## Pipeline discovery protocol

Use the dlt MCP tools as the primary discovery path — they work without writing Python:

1. **`list_pipelines`** — discover available dlt pipelines. If multiple exist and the target is ambiguous, ask the user and stop.
2. **`list_tables`** — enumerate tables in the selected pipeline.
3. **`get_table_schemas`** — fetch column names and types for relevant tables.

If MCP tools are unavailable or the data lives in a standalone `.duckdb` file without a managed pipeline, fall back to Python:

```python
import dlt

# Try attach first
pipeline = dlt.attach("<pipeline_name>")
# If that fails, explicit destination
pipeline = dlt.pipeline(
    pipeline_name="<name>",
    destination=dlt.destinations.duckdb("<path/to/file.duckdb>"),
    dataset_name="<dataset_name_if_known>",
)
dataset = pipeline.dataset()
dataset.row_counts().df()  # verify connection
```

Follow this sequence in order. Do not loop through random constructor variants. If the pipeline target is ambiguous, ask the user and stop.

## Quick look shortcut

If the user just wants to look around without a specific query:
```
dlt pipeline <pipeline_name> show
```
Opens a browser with table schemas, row counts, and sample data.

## dlt dataset API

Full reference is in the `dlt-relation-api` rule (loaded every session). Apply the 1,000-row development cap (see `workflow` rule) on all materialized outputs.

## Profiling protocol

After connecting, profile only the tables relevant to the user's question (or all tables if the question is broad):

1. **Narrow first** — use `list_tables` MCP tool (or `dataset.row_counts().df()`) to see all tables and row counts, then identify which tables matter based on hints, user context, or table names. Do not profile the entire database.
2. **Get schemas** — use `get_table_schemas` MCP tool (or `table.columns_schema`) for column names and types of relevant tables.
3. **For each table**, gather per-column stats:
   - Cardinality, null rate, min/max for numeric/temporal
   - Anomalies: >50% null, single-value columns, suspicious distributions
   - PII detection: flag columns whose names or sample values suggest personally identifiable information (e.g., `email`, `phone`, `ssn`, `address`, `ip_address`, full names). Check both column names and a sample of values.
   - Use `execute_sql_query` MCP tool, `.to_ibis()` with group_by/aggregate, or raw SQL via `dataset(...)`.
4. **For 1-2 tables**, profile inline. For 3+ tables, profile in parallel using subagents (one per table, all spawned in the same message).

Note: Relation has no `.count()` method. Use `execute_sql_query` MCP tool or `dataset("SELECT COUNT(*) FROM table_name").fetchscalar()` for row counts.

## Troubleshooting

### Pipeline not found
`dlt.attach("<name>")` raises `PipelineNotFound`.
1. Run `list_pipelines` MCP tool to see available pipelines.
2. Check spelling — pipeline names are case-sensitive.
3. If the user has a standalone `.duckdb` file, use `dlt.pipeline(..., destination=dlt.destinations.duckdb("<path>"))` instead.

### MCP tools unavailable
If `list_pipelines` or `list_tables` return connection errors:
1. Fall back to the Python path (`dlt.attach` / `dlt.pipeline`).
2. Tell the user the MCP server may not be running and suggest checking their `.mcp.json` config.

### Empty tables / no data loaded
If `row_counts()` returns all zeros or the pipeline has no tables:
1. Confirm the pipeline has been run at least once: `dlt pipeline <name> info`.
2. If no data, tell the user: "This pipeline has no loaded data yet. Run the pipeline first, then come back to explore."

### ibis expression errors
If `.to_ibis()` raises errors (e.g., missing backend, unsupported operation):
1. Fall back to raw SQL via `dataset("SELECT ...")`.
2. Check that `ibis-framework[duckdb]` is installed: `uv pip list | grep ibis`.

## Example

**User says:** "What data do I have in my github pipeline?"

**Actions:**
1. `list_pipelines` -> finds `github_data` pipeline
2. `list_tables` -> `issues`, `pull_requests`, `commits`, `issues__labels` (4 tables)
3. `get_table_schemas` -> fetches column info for all 4 tables
4. Profile `issues` and `pull_requests` inline (2 tables, no subagents needed):
   - `issues`: 1,200 rows, 12 columns, `created_at` spans 2023-01-01 to 2024-12-31, `assignee_email` flagged as PII
   - `pull_requests`: 800 rows, 15 columns, 23% null in `merged_at`

**Result:** Schema excerpt, summary stats, anomaly flags (high null rate on `merged_at`), PII flag on `assignee_email`, and recommendation to proceed to `analyze-questions`.

## Next step

Hand off to `analyze-questions` with the profiling evidence (schemas, stats, anomaly/PII flags).
