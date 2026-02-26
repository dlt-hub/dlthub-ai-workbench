---
name: explore-data
description: Query, explore, or view data loaded by a dlt pipeline using Python. Use when the user asks to query data, explore loaded tables, check row counts, write Python that reads pipeline data, or asks questions like "show me the data", "what did we load". Covers dlt dataset API, ibis expressions, and ReadableRelation.
---

# Explore pipeline data

Query data loaded by a dlt pipeline using Python. Use in standalone scripts, inline code, or as the data access layer for reports.

Parse `$ARGUMENTS`:
- `pipeline-name` (optional): the dlt pipeline name. If omitted, infer from session context. If ambiguous, ask the user and stop.
- `hints` (optional, after `--`): additional requirements or focus areas (e.g., `-- show spending by model`)

## Model routing and token policy

Use explicit routing metadata for deterministic execution:

- `model_tier`: `FAST`
- `max_output_tokens`: `1200`
- `context_budget_strategy`: `minimal`
- `escalation_rule`: escalate to `BALANCED` only if pipeline ambiguity remains after one clarification.
- `caching_rule`: cache profile digest by `pipeline_name + schema_hash`.

Token budget guidance:
- connection/profile summary + row counts: `<= 900`
- path-selection prompt: `<= 300`

## Workspace Dashboard UI if just exploring

Tell the user to run Workspace Dashboard **if no precise query or instructions were given**, this
assumes user wants to just look at the data. Otherwise
```
dlt pipeline <pipeline_name> show
```
This opens a browser with table schemas, row counts, and sample data.

## dlt dataset API

**Essential Reading:**
- `https://dlthub.com/docs/general-usage/dataset-access/dataset.md`
- `https://dlthub.com/docs/general-usage/dataset-access/ibis-backend.md`

Use `pipeline.dataset()` to access loaded data. This is **destination agnostic** — works the same on duckdb, postgres, bigquery, etc. NEVER import destination libraries (like `duckdb`) directly.

### Attach to pipeline and get dataset
```python
import dlt
pipeline = dlt.attach("<pipeline_name>")
dataset = pipeline.dataset()
```

### ReadableRelation (dlt native)
Think about it as a subset of ibis with slightly different syntax.
```python
table = dataset["my_table"]
table.head().df()                              # first rows as pandas
table.select("id", "name").limit(50).arrow()   # select columns, arrow format
table.where("id", "in", [1, 2, 3]).df()        # parametric filter
table.select("amount").max().fetchscalar()      # scalar aggregate
dataset.row_counts().df()                       # row counts for all tables
```

### Ibis expressions (preferred for complex queries)
```python
t = dataset["my_table"].to_ibis()
expr = t.filter(t.amount > 100).group_by("category").aggregate(total=t.amount.sum())
dataset(expr).df()  # execute ibis expression via dataset
```

Ibis is lazy, composable, and destination agnostic. Key operations:
- `table.group_by("col").aggregate(total=table.col.sum())` — aggregation
- `table.filter(table.col > 0)` — filtering
- `table.join(other, table.id == other.parent_id)` — joins
- `table.order_by(ibis.desc("col"))` — sorting
- `table.mutate(new_col=table.col * 100)` — computed columns
- `table.select("col1", "col2")` — column selection

Read ibis docs: `https://ibis-project.org/reference/expression-collections`

### Joining parent/child tables

dlt creates child tables for nested data (e.g., `my_table__results`). Join on `_dlt_id` / `_dlt_parent_id`:
```python
parent = dataset["my_table"].to_ibis()
child = dataset["my_table__results"].to_ibis()
joined = parent.join(child, parent._dlt_id == child._dlt_parent_id)
```

### Raw SQL (when needed)
```python
dataset("SELECT * FROM my_table WHERE amount > 100").df()
```

## Next steps

After profiling, present path selection (see `rules/workflow.md`):

```
How would you like to explore this data?

1. Overview (Recommended for first look)
   Quick summary, 3–5 auto-recommended charts. Minimal questions.

2. In-Depth Analysis
   Full ontology mapping, business intent, up to 10 interactive charts.
```

- Default selection remains `Overview`.
- Preserve recommendation label and choice architecture.
- Emit `mode: overview | in-depth` for deterministic gating.

## Required artifact output

When used in workflow mode, emit the compact `evidence_pack` artifact for downstream BALANCED/DEEP agents:

```
evidence_pack:
  schema_excerpt:
    tables: list[str]
    key_edges: list[{from_table, from_col, to_table, to_col}]
    child_edges: list[{parent_table, child_table, parent_key, child_key}]
  summary_stats:
    row_counts: list[{table, rows}]
    cardinality_notes: list[str]
    null_rate_notes: list[str]
    temporal_ranges: list[{table, column, min, max}] | []
  anomaly_flags: list[str]
  user_responses_compressed:
    mode_rationale: str
    constraints: list[str]
  mode: overview | in-depth
```

Rules:
- Include only relevant schema excerpts, not full dumps.
- Include only key summary statistics needed for ontology and visualization planning.
- Keep user responses compressed and deterministic.

- **Overview** → `ground-ontology --mode overview` (bounded parallel A/B/C ontology inference + synthesis + selection) → `plan-visualizations --mode overview` → `create-marimo-report --mode overview`
- **In-Depth** → `ground-ontology --mode in-depth` (bounded parallel A/B/C ontology inference + synthesis + selection) → `plan-visualizations --mode in-depth` → `create-marimo-report --mode in-depth`
- **Standalone** → use `create-marimo-report` directly (skips ontology + viz planning)
