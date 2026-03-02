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
- `selected_ontology` (user-defined from interview)
- `<pipeline_name>_ontology.md` file in the project root (saved by `ground-ontology`)
- `viz_plan` (chart specs, intent, mode)
- Evidence gathered during exploration

Before generating, validate the handoff artifacts:

1. **`selected_ontology`** must have: `label`, `entities` (with table/role/grain), `relationships`, `primary_metric`, `temporal_grain`. If any field is missing, flag it to the user rather than guessing.
2. **`viz_plan`** must have: `mode`, `charts` (each with id/chart_type/title/x/y/source_table), `top_3_chart_ids`. If chart sanity checks show failures, drop those charts and note why.

Then restate the commitment:

"Generating [overview/in-depth] notebook from ontology [label] for [intent] with [N] charts."

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

## EDA cells

When the user asks for EDA (exploratory data analysis), include these standard profiling cells in the notebook. Stay scoped to the intent — only profile tables and columns relevant to the plan.

### 1. Value distribution histogram

Show the distribution of the primary metric column. Use `alt.Chart().mark_bar()` with a binned x-axis.

```python
@app.cell
def _(dataset, alt, mo):
    _df = dataset["<fact_table>"].select("<metric_column>").df()
    _chart = alt.Chart(_df).mark_bar().encode(
        x=alt.X("<metric_column>:Q", bin=alt.Bin(maxbins=30)),
        y="count():Q",
    ).properties(title="Distribution of <metric_column>")
    mo.ui.altair_chart(_chart)
    return
```

### 2. Null rate summary

Show null percentages for key columns. Compute via ibis, display as horizontal bar chart.

```python
@app.cell
def _(dataset, alt, mo):
    _t = dataset["<table>"].to_ibis()
    _total = _t.count().execute()
    _nulls = []
    for _col in [<relevant_columns>]:
        _null_count = _t.filter(getattr(_t, _col).isnull()).count().execute()
        _nulls.append({"column": _col, "null_pct": round(100 * _null_count / _total, 1)})
    import pandas as pd
    _df = pd.DataFrame(_nulls)
    _chart = alt.Chart(_df).mark_bar().encode(
        x=alt.X("null_pct:Q", title="Null %", scale=alt.Scale(domain=[0, 100])),
        y=alt.Y("column:N", sort="-x"),
    ).properties(title="Null Rates")
    mo.ui.altair_chart(_chart)
    return
```

### 3. Time series coverage

When a temporal column exists, show record counts over time to reveal gaps or spikes.

```python
@app.cell
def _(dataset, alt, mo):
    _t = dataset["<fact_table>"].to_ibis()
    _by_period = (
        _t.group_by(_t.<temporal_column>.truncate("<grain>").name("period"))
        .aggregate(count=_t.<id_column>.count())
        .order_by("period")
    )
    _df = _by_period.to_pandas()
    _chart = alt.Chart(_df).mark_line(point=True).encode(
        x="period:T",
        y="count:Q",
    ).properties(title="Records over Time")
    mo.ui.altair_chart(_chart)
    return
```

### 4. Top-N cardinality

Show the top values for the primary dimension column (e.g., top 10 authors by commit count).

```python
@app.cell
def _(dataset, alt, mo):
    _t = dataset["<fact_table>"].to_ibis()
    _top = (
        _t.group_by("<dimension_column>")
        .aggregate(count=_t.<id_column>.count())
        .order_by(ibis.desc("count"))
        .limit(10)
    )
    _df = _top.to_pandas()
    _chart = alt.Chart(_df).mark_bar().encode(
        x=alt.X("count:Q"),
        y=alt.Y("<dimension_column>:N", sort="-x"),
    ).properties(title="Top 10 by <dimension_column>")
    mo.ui.altair_chart(_chart)
    return
```

Adapt column names and table names from the plan. Skip cells that don't apply (e.g., skip time series coverage if there's no temporal column). For overview mode, use `alt.Chart()` instead of `mo.ui.altair_chart()`.

## Capability check

If the chart plan includes a custom widget, verify `anywidget-generator` skill is available. If not, remove that chart and tell the user why.

## Mandatory verification

Before presenting to the user, run all verification steps. Do not skip any.

### Step 1 — Install dependencies into the active venv

PEP 723 metadata is only resolved by `uv run`. Ensure all packages are available in the project venv:

```bash
uv add altair ibis-framework pyarrow numpy pandas
```

### Step 2 — Run the notebook as a script

```bash
uv run python <filename>.py
```

This catches import errors, syntax issues, and data access failures. If it fails, fix and re-run before proceeding.

### Step 3 — Fix common issues

- **`mo` is not defined**: Missing the `import marimo as mo` cell or missing `mo` in the function parameters. Add the dedicated import cell and ensure every cell that uses `mo` has it as a parameter.
- **Named functions normalized**: marimo rewrites `def chart_1(mo):` → `def _(mo):` on launch. If two cells had different names but the same signature, they collide. Always use `def _(...)` from the start.
- **Missing dependencies**: Package not installed in venv despite being in PEP 723 block. Run `uv add <package>`.
- **Column name mismatches**: Check actual schema with `table.columns`, not assumed names.
- **ibis expression errors**: Test queries individually if needed.
- **`fetchscalar()` ValueError**: Query returned more than one row/column.

If marimo-related issues block the flow, point user to: https://docs.marimo.io/guides/generate_with_ai/skills/

### Step 4 — Launch the notebook

```bash
marimo edit --watch --no-token <filename>.py
```

Run this in the background — verification continues while the notebook serves.

### Step 5 — Visual verification (chart appearance check)

After launching, verify that charts actually render and look correct. This catches issues that the script run (Step 2) cannot: empty charts, wrong chart types, mismatched axes, data that produces a blank plot.

**If a browser screenshot tool is available** (e.g., Chrome extension MCP, browser automation tool):

1. Navigate to the marimo notebook URL (default: `http://localhost:2718`).
2. Wait for the notebook to fully render (all cells executed).
3. Take a screenshot of the full notebook page.
4. Read the screenshot and verify each chart against the viz plan:

| Check | What to look for |
|---|---|
| **Chart rendered** | A visible chart area with data — not an empty box, error message, or spinner |
| **Correct chart type** | Bar chart should show bars, line chart should show lines, scatter should show points |
| **Axes labeled** | X and Y axes have readable labels matching the planned columns |
| **Data present** | Chart has actual data points/bars/lines — not a flat line at zero or a single point |
| **Title matches** | Chart title matches or is close to the planned title |
| **Stat cards populated** | Stat cards show numbers, not "None" or "NaN" |

5. If any chart fails a check, fix the issue in the notebook code and re-verify.

**If no browser tool is available:**

Run a programmatic data check instead. For each chart cell, extract and run just the data query portion to confirm it returns non-empty results:

```bash
uv run python -c "
import dlt
pipeline = dlt.attach('<pipeline_name>')
dataset = pipeline.dataset()
# Test each chart's data query
df = dataset['<table>'].select('<col1>', '<col2>').head(5).df()
print(f'Chart: <title> — rows: {len(df)}, columns: {list(df.columns)}')
assert len(df) > 0, 'Chart would be empty!'
"
```

Run one such check per chart. If any returns zero rows, the chart will be blank — fix the query before proceeding.

### Step 6 — Cross-reference with ontology file

Read the ontology file (`<pipeline_name>_ontology.md` in the project root) and verify every chart in the notebook is consistent with it. This catches drift between what the user agreed to and what was actually built.

For each chart cell, check:

| Check | How to verify |
|---|---|
| **Source table exists in ontology** | The chart's source table must appear as an entity in the ontology file |
| **Metric is declared** | The Y-axis column (or aggregated column) must be listed under that entity's Metrics |
| **Dimension is declared** | The X-axis or color column must be listed under Dimensions or Temporal column |
| **Grain is respected** | The chart's aggregation level must match or roll up from the entity's declared grain |
| **Relationships used are documented** | Any join in the chart query must correspond to a relationship in the ontology file |

If a mismatch is found:
- **Missing entity/column in ontology**: The chart uses data the user didn't confirm. Flag it — either remove the chart or ask the user to confirm the addition.
- **Wrong metric/dimension**: The chart plots a column that isn't classified the way it's being used (e.g., using an identifier as a metric). Fix the chart or flag the ontology gap.
- **Undocumented join**: A chart joins tables via a relationship not in the ontology. Verify the join is valid, then flag it for the user.

Report mismatches in the verification summary. Do not silently skip them.

### Step 7 — Report verification results

Summarize what was checked and the outcome:

```
VERIFICATION RESULTS
---
Script run: ✓ passed (no errors)
Visual check: [N] / [N] charts verified
Method: [browser screenshot | programmatic data check]
Ontology cross-reference: [N] / [N] charts match ontology file
Mismatches: [none | list of mismatches and actions taken]
Issues found: [none | list of fixes applied]
```

If any chart was fixed during verification, note what changed.

## Final checkpoint

Present an outline before writing:

```
NOTEBOOK READY ([overview/in-depth])
---
File: [filename].py
Ontology: [label]
Cells: [N]
Charts: [chart list with verification status]
Verification: [passed | N issues fixed]
```

## Iterate with the user

After the first version:
- Incorporate feedback
- Revise or add cells
- Keep ontology and chart cap constraints intact
- Re-run verification after every change
