---
name: create-marimo-report
description: Create an interactive marimo notebook to visualize and report on pipeline data. Works standalone or as the final step after ground-ontology and plan-visualizations. Use this skill whenever the user wants to build a notebook, dashboard, report, or interactive visualization from their dlt pipeline data — even if they just say "make me a dashboard" or "I want to see charts".
---

# Create a data report

Create an interactive marimo notebook to visualize data loaded by a dlt pipeline.

Parse `$ARGUMENTS`:
- `pipeline-name` (optional): dlt pipeline name
- `report-description` (optional, after `--`): custom report intent

## When coming from the workflow (overview or in-depth)

If upstream steps (explore-data → ground-ontology → plan-visualizations) are complete, you have:
- `selected_ontology` (A/B/C)
- `viz_plan` (chart specs, intent, mode)
- Evidence gathered during exploration

Restate the commitment before generating:

"Generating [overview/in-depth] notebook from ontology [A|B|C] for [intent] with [N] charts."

### Mode differences

| Aspect | Overview | In-Depth |
|---|---|---|
| Max charts | 5 | 10 |
| Interactive controls | No (static altair) | Yes (`mo.ui.altair_chart`) |
| Ontology header | One-line summary | Full ontology map |
| Stat cards | Basic | Detailed |
| Filename | `<pipeline>_overview.py` | `<pipeline>_analysis.py` |
| Cell count | 6-10 | 8-20 |

## Standalone mode

If `selected_ontology` and `viz_plan` are not available:
1. Attach to the pipeline and inspect the schema (use MCP tools or `pipeline.dataset()`).
2. Summarize what the data looks like — tables, row counts, key columns.
3. Ask the user what they want to see — what question should the report answer?
4. Pick 3-5 sensible charts based on the data shape and user's answer.
5. Proceed with notebook generation below.

---

## Data access

Full API is in the `dlt-relation-api` rule (loaded every session). Key points for notebook generation:

- **Use Relation methods first** — `select()`, `where()`, `order_by()`, `head()`, `limit()`, `.df()`
- **Escalate to ibis** (`table.to_ibis()`) for joins, group-by, computed columns
- **Raw SQL** (`dataset("SELECT ...")`) as last resort
- **Never** import destination libraries (`duckdb`, `psycopg2`) directly
- **Never** use pandas as the query layer — materialize to pandas only at the display boundary

---

## Critical marimo cell rules

These rules are **non-negotiable**. Violating them produces broken notebooks.

### 1. Dedicated `import marimo as mo` cell (REQUIRED)

`mo` is NOT auto-injected. You MUST have a cell that imports and returns it. Other cells receive `mo` as a function parameter. Without this cell, every cell that uses `mo` will fail.

```python
@app.cell
def _():
    import marimo as mo
    return (mo,)
```

### 2. Always use `def _(...)` for cell functions

marimo's convention is anonymous cells: `def _(...)` or `def __(...)`. **Never** use named functions like `def header(mo):` or `def chart_1(mo, alt):` — marimo will normalize them to `def _(...)` on first launch, which can cause confusion and breakage if names collide.

### 3. Every dependency must be a function parameter

A cell can only use variables that are either: (a) defined within that cell, or (b) declared as function parameters (injected by marimo from other cells' return values). If a cell uses `mo`, `alt`, `dataset`, etc., those must appear in `def _(...):`.

### 4. Return tuples for shared variables

Variables a cell produces for other cells MUST appear in the return tuple. Use parenthesized form: `return (mo,)`, `return (alt, dlt, mo)`, `return (dataset, pipeline)`. Cells that don't share variables use bare `return`.

### 5. Install dependencies in the active venv

PEP 723 script metadata is only resolved by `uv run`. If running with the project's `.venv/bin/python` directly, dependencies may be missing. Always install chart/data deps into the active venv before verification:

```bash
uv add altair ibis-framework pyarrow numpy pandas
```

---

## Notebook structure

Generate a single `.py` marimo notebook with `@app.cell` functions:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "dlt[duckdb]",
#     "marimo",
#     "altair",
#     "ibis-framework",
#     "pyarrow",
# ]
# ///

import marimo

app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    import altair as alt
    import dlt
    return (alt, dlt)


@app.cell
def _(dlt):
    pipeline = dlt.attach("<pipeline_name>")
    dataset = pipeline.dataset()
    return (dataset, pipeline)


@app.cell
def _(mo):
    mo.md("# Report Title\n\nOntology summary and context here.")
    return


# ... data query cells, chart cells, stat cards ...

if __name__ == "__main__":
    app.run()
```

Key rules:
- PEP 723 metadata block at the top with all dependencies
- Adjust `dlt[duckdb]` to match the actual destination (e.g., `dlt[postgres]`, `dlt[bigquery]`)
- **Separate import cells**: `import marimo as mo` in its own cell; other imports in a second cell
- One chart per cell
- Core charts before supporting charts
- Use `_` prefix for cell-local variables to avoid name collisions
- Use `mo.ui.altair_chart()` for interactive charts (in-depth mode only)
- Use plain `alt.Chart()` for static charts (overview mode)
- No conditional control flow outside connection setup
- marimo renders only the **final expression** of a cell — don't put display calls inside `if` blocks

## Parallel cell generation

When the notebook has 3+ chart cells, generate them in parallel using haiku subagents. This is faster than writing them sequentially and each cell is independent.

First, decide the notebook architecture yourself (cell order, which tables feed which charts, shared query cells). Then spawn one haiku subagent per chart cell in the **same message**:

```
Generate a single marimo @app.cell function for a chart.

CRITICAL FORMAT RULES:
- Use `def _(...)` for the function name — NEVER a named function like `def chart_1(...)`.
- List all dependencies as function parameters: `def _(dataset, alt, mo):`
- Use `_` prefix for cell-local variables (e.g., `_df`, `_chart`).
- End with bare `return` (chart cells don't export variables).
- Use `alt.Scale(type="log")` for axes where values span 2+ orders of magnitude.

Chart spec:
- Title: [from viz_plan]
- Type: [line/bar/scatter/etc.]
- X: [column], Y: [column], Color: [column or null]
- Source table: [table name]
- Mode: [overview → static alt.Chart | in-depth → mo.ui.altair_chart]

Data access: the cell receives `dataset` from a prior cell.
Use dlt Relation methods for simple queries (select, where, order_by, head).
Use dataset["table"].to_ibis() for joins and group-by aggregations.
Materialize to pandas only at the altair boundary.

Return only the @app.cell function, nothing else.
```

Assemble the returned cells into the notebook skeleton in the correct order (core charts first, then supporting).

The boilerplate cells (imports, pipeline attach, markdown header, stat cards) are simple enough to write directly — no subagent needed.

## Chart cells

Each chart cell should:
1. Use `def _(...)` with all dependencies as parameters
2. Query via Relation (simple) or ibis (complex) from the `dataset`
3. Materialize to DataFrame at the boundary: `.df()` or `.to_pandas()`
4. Build the altair chart
5. Display via `mo.ui.altair_chart()` (in-depth) or as final expression (overview)
6. End with bare `return`

### Log scales

Use `alt.Scale(type="log")` when values span 2+ orders of magnitude (e.g., star counts, revenue distributions, population data). Check the data range during query — if `max / min > 100`, a log scale likely improves readability. Reference: https://docs.marimo.io/api/plotting/#reactive-charts-with-altair

```python
# Log scale on Y axis
y=alt.Y("stars:Q", scale=alt.Scale(type="log"))

# Log scale on both axes (scatter)
x=alt.X("followers:Q", scale=alt.Scale(type="log")),
y=alt.Y("contributions:Q", scale=alt.Scale(type="log"))
```

**Example — simple query using Relation:**
```python
@app.cell
def _(dataset, alt, mo):
    # Relation: no joins or group-by needed
    _df = dataset["users"].select("status", "created_at").df()
    _chart = alt.Chart(_df).mark_bar().encode(
        x="status:N",
        y="count():Q",
    ).properties(title="Users by Status")
    mo.ui.altair_chart(_chart)
    return
```

**Example — aggregation using ibis:**
```python
@app.cell
def _(dataset, alt, mo):
    _t = dataset["orders"].to_ibis()
    _daily = (
        _t.group_by(_t.created_at.date().name("date"))
        .aggregate(total=_t.amount.sum(), count=_t.id.count())
        .order_by("date")
    )
    _df = _daily.to_pandas()
    _chart = alt.Chart(_df).mark_line().encode(
        x="date:T",
        y="total:Q",
        tooltip=["date:T", "total:Q", "count:Q"]
    ).properties(title="Daily Order Revenue")
    mo.ui.altair_chart(_chart)
    return
```

**Example — joining parent/child tables:**
```python
@app.cell
def _(dataset, alt, mo):
    _parent = dataset["repos"].to_ibis()
    _child = dataset["repos__contributors"].to_ibis()
    _joined = _parent.join(_child, _parent._dlt_id == _child._dlt_parent_id)
    _by_repo = (
        _joined.group_by("name")
        .aggregate(contributors=_joined.contributor_id.nunique())
        .order_by(ibis.desc("contributors"))
        .limit(15)
    )
    _df = _by_repo.to_pandas()
    _chart = alt.Chart(_df).mark_bar().encode(
        x=alt.X("contributors:Q"),
        y=alt.Y("name:N", sort="-x"),
    ).properties(title="Top 15 Repos by Contributor Count")
    mo.ui.altair_chart(_chart)
    return
```

**Example — log scale for power-law data:**
```python
@app.cell
def _(dataset, alt, mo):
    _df = dataset["repos"].select("name", "stargazers_count", "forks_count").head(50).df()
    _chart = alt.Chart(_df).mark_circle().encode(
        x=alt.X("stargazers_count:Q", scale=alt.Scale(type="log"), title="Stars"),
        y=alt.Y("forks_count:Q", scale=alt.Scale(type="log"), title="Forks"),
        tooltip=["name:N", "stargazers_count:Q", "forks_count:Q"]
    ).properties(title="Stars vs Forks (log scale)")
    mo.ui.altair_chart(_chart)
    return
```

## Stat cards

Use `mo.stat()` for key metrics. Relation's `fetchscalar()` is ideal here:

```python
@app.cell
def _(mo, dataset):
    with dataset:
        _total_orders = dataset("SELECT COUNT(*) FROM orders").fetchscalar()
        _total_revenue = dataset["orders"].select("amount").max().fetchscalar()
        _user_count = dataset("SELECT COUNT(DISTINCT user_id) FROM orders").fetchscalar()
    mo.hstack([
        mo.stat(value=_total_orders, label="Total Orders"),
        mo.stat(value=f"${_total_revenue:,.0f}", label="Max Order"),
        mo.stat(value=_user_count, label="Unique Users"),
    ])
    return
```

## Capability check

If the chart plan includes a custom widget, verify `anywidget-generator` skill is available. If not, remove that chart and tell the user why.

## Mandatory verification

Before presenting to the user:

### Step 1 — Install dependencies into the active venv

PEP 723 metadata is only resolved by `uv run`. Ensure all packages are available in the project venv:

```bash
uv add altair ibis-framework pyarrow numpy pandas
```

### Step 2 — Run the notebook

```bash
uv run python <filename>.py
```

### Step 3 — Fix common issues

- **`mo` is not defined**: Missing the `import marimo as mo` cell or missing `mo` in the function parameters. Add the dedicated import cell and ensure every cell that uses `mo` has it as a parameter.
- **Named functions normalized**: marimo rewrites `def chart_1(mo):` → `def _(mo):` on launch. If two cells had different names but the same signature, they collide. Always use `def _(...)` from the start.
- **Missing dependencies**: Package not installed in venv despite being in PEP 723 block. Run `uv add <package>`.
- **Column name mismatches**: Check actual schema with `table.columns`, not assumed names.
- **ibis expression errors**: Test queries individually if needed.
- **`fetchscalar()` ValueError**: Query returned more than one row/column.

If marimo-related issues block the flow, point user to: https://docs.marimo.io/guides/generate_with_ai/skills/

### Step 4 — Launch

Only after verification:
```bash
marimo edit --watch --no-token <filename>.py
```

## Final checkpoint

Present an outline before writing:

```
NOTEBOOK READY ([overview/in-depth])
---
File: [filename].py
Ontology: [A|B|C]
Cells: [N]
Charts: [chart list]
```

## Iterate with the user

After the first version:
- Incorporate feedback
- Revise or add cells
- Keep ontology and chart cap constraints intact
- Re-run verification after every change
