---
name: create-marimo-report
description: Create an interactive marimo notebook to visualize and report on pipeline data. Use when the user wants a dashboard, charts, visual analysis, or a marimo notebook for data exploration. For data access patterns, see explore-data skill.
argument-hint: "[pipeline-name] [report-description]"
---

# Create a data report

Create an interactive marimo notebook to visualize and explore data loaded by a dlt pipeline. Uses the dlt dataset API from `explore-data` skill for data access.

Parse `$ARGUMENTS`:
- `pipeline-name` (optional): the dlt pipeline name. If omitted, infer from session context. If ambiguous, ask the user and stop.
- `report-description` (optional, after `--`): describes what reports/views the notebook should contain (e.g., `-- daily cost breakdown by model and cache hit rates`). When provided, skip the "ask the user what they want to explore" step and use this description to drive the analysis.

## When coming from the workflow (overview or in-depth)

If `ground-ontology` and `plan-visualizations` have already been run, you have:
- **Ontology map**: entities, metrics, dimensions, relationships, grain (auto or confirmed)
- **Visualization plan**: chart list with column mappings, tiers, and intent
- **Mode**: `overview` or `in-depth`

**Skip section 1 entirely** — go straight to section 2. Use the ontology for ibis query construction and the viz plan for chart cells.

Restate the commitment: "Generating [overview/in-depth] notebook for [intent] analyzing [entity] with [N] charts."

### Mode differences in notebook generation

| Aspect | Overview | In-Depth |
|---|---|---|
| Max charts | 5 | 10 |
| Interactive filter controls | No — static altair charts | Yes — `mo.ui.altair_chart()` with click-to-filter |
| Ontology header | One-line summary | Full ontology map in markdown |
| Stat cards | Basic (row count, date range) | Detailed (per-metric aggregates) |
| Notebook filename | `<pipeline>_overview.py` | `<pipeline>_analysis.py` |
| Cell count | 6–10 | 8–20 |

## 1. Understand the data (standalone mode)

Use this section when running **without** the upstream workflow (no ontology or viz plan).

Before writing code, understand what data is available and what the user wants from it.

### Inspect the schema
```
dlt pipeline <pipeline_name> schema --format mermaid
```
Show the mermaid diagram to the user — tables, columns, types, relationships.

### Query sample data

Use MCP tools or the `explore-data` dataset API to get:
- Row counts per table
- Sample rows from key tables
- Value distributions for important columns (distinct values, min/max, nulls)

### Research the data domain

Do a short web search to understand the data source context:
- What do the fields mean?
- What are typical analysis patterns for this kind of data?
- What metrics matter to users of this data?

### Present a data summary to the user

Describe the data in **business terms**, not technical terms. Example:
```
Your data covers Feb 10–17, 2026 and contains:
- Daily API usage by model (3 models, ~335M tokens on opus alone)
- Daily costs ($491 total over 7 days)
- Cache efficiency metrics (cache reads vs uncached input)

Available dimensions: model, api_key_id, workspace_id, service_tier
```

### Ask the user what they want to explore

Suggest 3-4 concrete analysis directions based on the data. Ask: **What's the goal — monitoring, optimization, reporting, or something else?**

## 2. Create a marimo notebook

Create `<pipeline_name>_explore.py` as a marimo notebook. marimo notebooks are pure Python files with `@app.cell` decorators.

Install if needed: `pip install "dlt[workspace]"` (includes marimo + ibis).

**Before launching, verify the notebook runs without errors:**
```
uv run python <pipeline_name>_explore.py
```
Fix any errors before proceeding. Only launch once it runs cleanly.

Launch with watch mode so edits auto-reload:
```
marimo edit --watch --no-token <pipeline_name>_explore.py
```

## 3. Connect to pipeline data

Use `dlt.attach()` and `dataset()` — see `explore-data` skill for the full API reference.

```python
@app.cell
def _():
    import dlt
    pipeline = dlt.attach("<pipeline_name>")
    dataset = pipeline.dataset()
    return dataset, pipeline
```

Get ibis table expressions from the dataset:
```python
@app.cell
def _(dataset):
    my_table = dataset["table_name"].to_ibis()
    return (my_table,)
```

## 4. Build analysis cells with ibis

Use **ibis expressions** for all data queries — NOT raw SQL, NOT pandas operations. Return bare ibis expressions from cells — marimo renders them in its built-in interactive data explorer:

```python
@app.cell
def _(my_table, ibis):
    user_summary = (
        my_table
        .group_by("user")
        .aggregate(total=my_table.amount.sum())
        .order_by(ibis.desc("total"))
    )
    return (user_summary,)

@app.cell
def _(user_summary):
    user_summary  # bare return → marimo data explorer
    return
```

## 5. Add charts with altair

Use `mo.ui.altair_chart()` for interactive charts with click-to-filter.

**IMPORTANT — marimo naming rule:** Variable names must be unique across all cells. If you reuse a name like `chart` in multiple cells, marimo will raise a `MultipleDefinitionError` and break those cells. Use `_`-prefixed names (e.g. `_chart`) for cell-local variables — they are private and exempt from the uniqueness rule. The preferred pattern is to inline the chart as the last expression so no variable is needed at all:

```python
# Preferred: inline as last expression — no naming conflict possible
@app.cell
def _(mo, alt, my_data):
    mo.ui.altair_chart(
        alt.Chart(my_data.to_pandas()).mark_bar().encode(x="category", y="total")
    )
    return

# Also fine: use _ prefix to make the variable cell-local
@app.cell
def _(mo, alt, my_data):
    _chart = mo.ui.altair_chart(
        alt.Chart(my_data.to_pandas()).mark_bar().encode(x="category", y="total")
    )
    _chart
    return

# WRONG: reusing `chart` across cells causes MultipleDefinitionError
@app.cell
def _(mo, alt, my_data):
    chart = mo.ui.altair_chart(...)  # breaks if another cell also defines `chart`
    chart
    return (chart,)
```

## 6. Add markdown headers

Use `mo.md()` for section titles and context. Keep text short — the data explorer does the heavy lifting.

```python
@app.cell
def _(mo):
    mo.md("## Cost by User and Model")
    return
```

## 7. Verify capabilities before generation

When coming from the full workflow with a viz plan: all standard chart types (line, bar, area, scatter, table, stat cards) are available via `mo.ui.altair_chart`, `mo.ui.table`, `mo.md()`. Only exception: if the viz plan includes a **custom widget**, verify the `anywidget-generator` skill is available — if not, remove that chart and note the removal to the user.

## 8. Notebook generation contract

The generated notebook MUST satisfy:

- **Format**: single `.py` file with `@app.cell` decorators, PEP 723 inline dependency metadata
- **Data access**: `dlt.attach()` + `pipeline.dataset()` — no hardcoded connection strings
- **Query layer**: ibis expressions only — no raw SQL, no pandas transformations
- **Charts**: `mo.ui.altair_chart()` for interactivity (in-depth) or static altair (overview). Max chart cells = viz plan total.
- **Variables**: `_` prefix for cell-local. Unique names across cells. One concern per cell.
- **No conditional wrapping**: let marimo reactivity handle state. `mo.app_meta().mode` check only in data connection cell.
- **Documentation**: `mo.md()` header with title, intent summary, ontology summary

### Overview notebook structure

```
Cell 0: PEP 723 metadata + imports
Cell 1: dlt.attach() + dataset connection
Cell 2: ibis table expressions
Cell 3: Header markdown (title, one-line ontology summary)
Cell 4: Basic stat cards (row count, date range)
Cells 5-N: One chart per cell (3–5 charts, static altair)
Final cell: "For deeper analysis, re-run with in-depth mode."
```

### In-depth notebook structure

```
Cell 0: PEP 723 metadata + imports
Cell 1: dlt.attach() + dataset connection
Cell 2: ibis table expressions (one per source table)
Cell 3: Header markdown (title, intent, full ontology summary)
Cell 4: Detailed stat cards (per-metric aggregates)
Cells 5-N: One chart per cell, core tier first (up to 10, interactive altair)
Final cell: Summary / key takeaways placeholder
```

### Final checkpoint

Present the notebook outline to the user before writing the file:
```
NOTEBOOK READY ([overview/in-depth])
---
File: [filename].py
Cells: [N]
Charts: [chart count] ([mode])

Run with: marimo edit [filename].py
```

## 9. Iterate with the user

The notebook is a conversation tool. After the initial version:
- Ask if the views are useful
- Add/modify cells based on feedback
- Suggest additional analyses based on what the data reveals
- If data is missing, suggest pipeline changes (new endpoints, different params)
