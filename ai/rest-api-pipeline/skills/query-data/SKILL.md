---
name: query-data
description: Query, explore, or analyze data loaded by a dlt pipeline. Use when the user asks to query data, explore loaded tables, check row counts, write Python scripts or marimo notebooks against pipeline data, or asks questions like "show me the data", "what users are there", "how much did we spend". Covers dlt dataset API, ibis expressions, and ReadableRelation.
argument-hint: <pipeline-name>
---

# Explore pipeline data in Python

Write Python code that queries data loaded by a dlt pipeline. This can be a standalone script, a marimo notebook, or inline code.

Parse `$ARGUMENTS`:
- `pipeline-name` (required): the dlt pipeline name (e.g., `anthropic_usage_pipeline`)

## Accessing data: dlt dataset API

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

## Marimo notebooks

For interactive exploration, create a marimo notebook. marimo notebooks are pure Python files with `@app.cell` decorators.

Install if needed: `pip install "dlt[workspace]"` (includes marimo + ibis).

Launch with watch mode so edits auto-reload:
```
marimo edit --watch --no-token <pipeline_name>_explore.py
```

### Steps

#### 1. Understand the data

Before writing code, understand what's available. Inspect schema, query sample data, research the data domain. Present a summary in **business terms** and ask the user what they want to explore.

#### 2. Connect to pipeline data
```python
@app.cell
def _():
    import dlt
    pipeline = dlt.attach("<pipeline_name>")
    dataset = pipeline.dataset()
    return dataset, pipeline
```

#### 3. Build analysis cells with ibis

Return bare ibis expressions from cells — marimo renders them in its built-in interactive data explorer:

```python
@app.cell
def _(dataset, ibis):
    user_summary = (
        dataset["my_table"].to_ibis()
        .group_by("user")
        .aggregate(total=_.amount.sum())
        .order_by(ibis.desc("total"))
    )
    return (user_summary,)

@app.cell
def _(user_summary):
    user_summary  # bare return → marimo data explorer
    return
```

#### 4. Add charts with altair

Use `mo.ui.altair_chart()` for interactive charts with click-to-filter:
```python
@app.cell
def _(mo, alt, my_data):
    chart = mo.ui.altair_chart(
        alt.Chart(my_data.to_pandas()).mark_bar().encode(x="category", y="total")
    )
    chart
    return (chart,)
```

#### 5. Iterate with the user

The notebook is a conversation tool. Add/modify cells based on feedback. If data is missing, suggest pipeline changes (new endpoints, different params).
