---
name: connect-and-profile
description: This skill should be used when the user wants to attach to a pipeline, query loaded data, check what tables exist, show row counts, preview sample rows, inspect table schemas, profile data quality, explore loaded tables, or understand what a pipeline produced — even if they don't say "connect" or "profile" explicitly. Trigger phrases include "what tables do I have", "show me the data", "show me sample data", "how many rows", "how many rows in the X table", "what does the schema look like", "show me the schemas", "connect to my pipeline", "what did the pipeline load", "what did it produce".
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

Full reference is in the `dlt-relation-api` rule (loaded every session). Use Relation methods first, escalate to ibis for joins/group-by, raw SQL as last resort.

## Development row cap

Cap materialized query outputs at **1,000 rows** during development:
- Relation: `order_by(...)` then `limit(1000)` or `head(1000)`
- ibis: `.order_by(...)` then `.limit(1000)` before materialization
- Raw SQL: include `LIMIT 1000`

Only remove this cap if the user explicitly requests full-load results.

## Profiling protocol

After connecting, profile only the tables relevant to the user's question (or all tables if the question is broad):

1. **Narrow first** — use `list_tables` MCP tool (or `dataset.row_counts().df()`) to see all tables and row counts, then identify which tables matter based on hints, user context, or table names. Do not profile the entire database.
2. **Get schemas** — use `get_table_schemas` MCP tool (or `table.columns_schema`) for column names and types of relevant tables.
3. **For each table**, gather per-column stats:
   - Cardinality, null rate, min/max for numeric/temporal
   - Anomalies: >50% null, single-value columns, suspicious distributions
   - Use `execute_sql_query` MCP tool, `.to_ibis()` with group_by/aggregate, or raw SQL via `dataset(...)`.
4. **For 1–2 tables**, profile inline. For 3+ tables, profile in parallel using haiku subagents (one per table, all spawned in the same message).

Each profiling subagent prompt:
```
Profile this dlt table and return structured stats.

Table: [table_name]
Schema: [column names, types]
Sample (first 5 rows): [paste sample]

IMPORTANT: Relation has no .count() method. For row counts use either:
- The `execute_sql_query` MCP tool, or
- dataset("SELECT COUNT(*) FROM [table_name]").fetchscalar()
For per-column stats, use .to_ibis() with group_by/aggregate or raw SQL.

Return: row count, per-column cardinality, null rate, min/max for numeric/temporal,
any anomalies (>50% null, single-value, suspicious distributions).
No prose — structured output only.
```

## Output for downstream skills

After profiling, the following must be established:

- **Schema excerpt**: tables involved, key columns, foreign keys, parent/child edges
- **Summary stats**: row counts, cardinality, null rates, temporal ranges
- **Anomaly flags**: anything surprising in the data
- **User context**: any constraints or focus areas they mentioned
- **Cap state**: whether the 1,000-row development cap is active (default: yes)

This evidence feeds into `analyze-questions`.

## Next step

Hand off to `analyze-questions` with the profiling evidence and user's business question.
