---
name: explore-data
description: Query, explore, or view data loaded by a dlt pipeline using Python. Use when the user asks to query data, explore loaded tables, check row counts, write Python that reads pipeline data, or asks questions like "show me the data", "what did we load", "how many rows", "what tables do we have". Also use when the user wants to profile data, check data quality, or understand what a pipeline loaded — even if they don't say "explore" explicitly.
---

# Explore pipeline data

Query data loaded by a dlt pipeline using Python. Use in standalone scripts, inline code, or as the data access layer for reports.

Parse `$ARGUMENTS`:
- `pipeline-name` (optional): the dlt pipeline name. If omitted, infer from session context. If ambiguous, ask the user and stop.
- `hints` (optional, after `--`): additional requirements or focus areas (e.g., `-- show spending by model`)

## Pipeline targeting

Before doing anything, you need to know which pipeline to work with:
- Ask for the exact pipeline name if unclear.
- Also ask for the pipeline path if the workspace has multiple pipeline roots or non-default locations.
- If either is ambiguous, stop and clarify before continuing.

## Quick look: Workspace Dashboard

If the user just wants to look around without a specific query, tell them to run:
```
dlt pipeline <pipeline_name> show
```
This opens a browser with table schemas, row counts, and sample data.

## dlt dataset API

Full API reference is in the `dlt-relation-api` rule (loaded every session). Quick summary below.

```python
import dlt
pipeline = dlt.attach("<pipeline_name>")
dataset = pipeline.dataset()

# Relation: lazy, chainable, destination-agnostic
table = dataset["my_table"]
table.select("id", "name").where("amount", "gt", 100).limit(50).df()
table.select("amount").max().fetchscalar()
dataset.row_counts().df()

# Escalate to ibis for joins, group-by, computed columns
t = dataset["my_table"].to_ibis()
expr = t.filter(t.amount > 100).group_by("category").aggregate(total=t.amount.sum())
dataset(expr).df()

# Parent/child joins (dlt nested data)
parent = dataset["my_table"].to_ibis()
child = dataset["my_table__results"].to_ibis()
joined = parent.join(child, parent._dlt_id == child._dlt_parent_id)

# Raw SQL escape hatch
dataset("SELECT * FROM my_table WHERE amount > 100").df()
```

Priority: Relation first → ibis for complex queries → raw SQL as last resort. Never import destination libraries directly.

## Entry mode detection

Classify the user's request to decide what happens next:
- **Intent-driven** (dashboard, metric, hypothesis, EDA goal): Skip the overview prompt. Proceed to planning — restate their intent, identify entities/grain/metrics, narrow to relevant tables. Before handing off to `ground-ontology`, disambiguate grain (see below).
- **Exploratory** (just wants to look around): Offer the choice below.

## Grain disambiguation (intent mode)

After restating intent and listing candidate tables, ask the user about temporal grain and primary breakdown dimension. This determines what aggregations and time axes make sense downstream — the ontology and visualization steps depend on it.

Use `AskUserQuestion` with up to 2 questions:

**Time granularity** (ask when the intent involves trends or "how many over time"):
- Monthly (Recommended) — good default for dashboards
- Weekly — more detail, noisier
- Daily — high resolution, works for recent data
- All-time total — single number, no time axis

**Primary breakdown** (ask when multiple grouping dimensions exist):
- Pick from the actual dimension columns found in the schema (e.g., "by repository", "by author", "by file type")

Skip these questions when the intent is unambiguous (e.g., "show me the total count" clearly means all-time, no breakdown needed). Include the chosen grain in the plan artifact and pass it through to `ground-ontology`.

## Exploration paths

After profiling, present the path selection:

```
How would you like to explore this data?

1. Overview (Recommended for first look)
   Quick summary, 3–5 auto-recommended charts. Minimal questions.

2. In-Depth Analysis
   Full ontology mapping, business intent, up to 10 interactive charts.
```

Default: Overview.

## Parallel profiling

When multiple tables are in scope (3+), profile them in parallel using haiku subagents. Spawn one per table in the **same message**:

```
Profile this dlt table and return structured stats.

Table: [table_name]
Schema: [column names, types]
Sample (first 5 rows): [paste sample]

IMPORTANT: Relation has no .count() method. For row counts use either:
- The `get_row_counts` MCP tool, or
- dataset("SELECT COUNT(*) FROM [table_name]").fetchscalar()
For per-column stats, use .to_ibis() with group_by/aggregate or raw SQL.

Return: row count, per-column cardinality, null rate, min/max for numeric/temporal,
any anomalies (>50% null, single-value, suspicious distributions).
No prose — structured output only.
```

Collect the results and assemble the evidence summary. For 1-2 tables, just profile inline — the subagent overhead isn't worth it.

## What to gather before handing off

When feeding into the workflow (ground-ontology → plan-visualizations → create-marimo-report), make sure you've established:

- **Schema excerpt**: tables involved, key relationships (foreign keys, parent/child edges)
- **Summary stats**: row counts, cardinality notes, null rates, temporal ranges
- **Anomaly flags**: anything surprising in the data
- **User context**: their chosen mode (overview/in-depth), any constraints they mentioned
- **Plan** (intent mode): restated intent, entities, grain (temporal granularity + primary breakdown), metrics, dimensions, candidate tables

Narrow to relevant tables before gathering any of this — don't profile the entire database.

## Next steps

- **Overview** → `ground-ontology --mode overview` → `plan-visualizations --mode overview` → `create-marimo-report --mode overview`
- **In-Depth** → `ground-ontology --mode in-depth` → `plan-visualizations --mode in-depth` → `create-marimo-report --mode in-depth`
- **Standalone** → use `create-marimo-report` directly (skips ontology + viz planning)
