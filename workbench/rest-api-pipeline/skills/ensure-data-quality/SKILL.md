---
name: ensure-data-quality
description: Add runtime data quality checks (nulls, uniqueness, valid values) and metrics to pipeline resources using dlt.hub.data_quality decorators. Use after validate-data confirms schema is correct. Requires dlt[hub].
argument-hint: <pipeline_name> [table_name]
---

# Ensure data quality

Essential reading: https://dlthub.com/docs/hub/features/quality/data-quality

> **Setup**: `uv add "dlt[hub]"` — also `uv add numpy pandas` for `.df()` support.

Parse `$ARGUMENTS`:
- `pipeline_name` (required): the dlt pipeline name
- `table_name` (optional): specific table; defaults to all tables

## 1. Understand quality requirements

Read `WHY.md` for business definitions. If absent, ask the user:

> "What data quality matters most? For example: no null IDs? status restricted to known values? no duplicate records? track statistical metrics?"

## 2. Review schema and data

Use `validate-data` output if already run. Otherwise peek at data:

```python
import dlt
dataset = dlt.attach("<pipeline_name>").dataset()
print(dataset["<table_name>"].head().df())
```

Identify candidates: primary keys, required fields, enum columns, numeric ranges, columns worth tracking metrics on.

## 3. Add checks to resources (decorator approach)

The preferred pattern is decorating resources directly in the pipeline source code:

```python
import dlt
from dlt.hub import data_quality as dq

@dq.with_checks(
    dq.checks.is_not_null("user_id"),
    dq.checks.is_unique("order_id"),
    dq.checks.is_in("status", ["active", "inactive", "pending"]),
    dq.checks.case("amount >= 0"),
)
@dlt.resource(primary_key="order_id")
def orders():
    yield ...
```

For instantiated resources/sources (e.g. from a verified source), use the dynamic approach:

```python
source = my_api_source()
dq.with_checks(
    source.orders,
    dq.checks.is_not_null("order_id"),
    dq.checks.is_unique("order_id"),
)
```

### Available checks

```python
dq.checks.is_not_null("col")                              # completeness
dq.checks.is_unique("col")                                # uniqueness
dq.checks.is_primary_key("col")                           # unique + not null
dq.checks.is_primary_key(["tenant_id", "order_id"])       # composite key
dq.checks.is_in("status", ["active", "inactive"])         # validity
dq.checks.case("amount >= 0")                             # row-level SQL condition
```

## 4. Add metrics to resources (decorator approach)

Metrics track statistical properties of your data across loads:

```python
@dq.with_metrics(
    dq.metrics.column.mean("amount"),
    dq.metrics.column.null_count("email"),
    dq.metrics.table.row_count(),
)
@dlt.resource
def customers():
    yield ...
```

Dataset-level metrics go on sources:

```python
@dq.with_metrics(
    dq.metrics.dataset.total_row_count(),
)
@dlt.source
def crm():
    return [customers]
```

Dynamic approach for instantiated objects:

```python
dq.with_metrics(
    customers,
    dq.metrics.column.mean("amount"),
    dq.metrics.column.null_count("email"),
    dq.metrics.table.row_count(),
)
```

### Available metrics

**Column-level:** `maximum`, `minimum`, `mean`, `median`, `mode`, `sum`, `standard_deviation`, `quantile` (takes `quantile=` kwarg), `null_count`, `null_rate`, `unique_count`, `average_length`, `minimum_length`, `maximum_length` — all called as `dq.metrics.column.<name>("col")`.

**Table-level:** `row_count`, `unique_count`, `null_row_count` — called as `dq.metrics.table.<name>()`.

**Dataset-level:** `total_row_count`, `load_row_count`, `latest_loaded_at` — called as `dq.metrics.dataset.<name>()`.

## 5. Enable data quality and run pipeline

After decorating resources, enable data quality on the pipeline before running:

```python
pipeline = dlt.pipeline("my_pipeline", destination="duckdb")
dq.enable_data_quality(pipeline)
load_info = pipeline.run(source)
print(load_info)
```

Checks and metrics execute **post-load** — after the standard Extract-Normalize-Load cycle on the destination.

## 6. Read results

```python
dataset = pipeline.dataset()

# Read check results
dq.read_check(dataset, table="orders", column="order_id").df()

# Read column metric
dq.read_metric(dataset, table="customers", column="amount", metric="mean").df()

# Read table metric
dq.read_metric(dataset, table="customers", metric="row_count").fetchall()

# Read dataset metric
dq.read_metric(dataset, metric="total_row_count").arrow()
```

## 7. Standalone verification script (optional)

Copy `scripts/run_quality_checks.py` to `<pipeline_name>_quality.py` for ad-hoc verification outside the pipeline. Customize:
1. Set `PIPELINE_NAME`
2. Fill in `CHECKS_BY_TABLE` and `METRICS_BY_TABLE`

Run: `uv run python <pipeline_name>_quality.py [table_name]`

## Next steps

- Schema/types wrong → `validate-data` first
- View quality results interactively → `view-data`
- Ready for production → `adjust-endpoint`
