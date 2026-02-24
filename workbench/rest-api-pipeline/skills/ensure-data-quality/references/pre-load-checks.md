# Adding checks and metrics inline with resources

Attach checks and metrics directly to resources using decorators. They execute post-load via `enable_data_quality()`.

## Decorator pattern (static)

```python
import dlt
from dlt.hub import data_quality as dq

@dq.with_checks(
    dq.checks.is_not_null("order_id"),
    dq.checks.is_unique("order_id"),
    dq.checks.is_in("status", ["pending", "shipped", "delivered"]),
)
@dq.with_metrics(
    dq.metrics.column.null_count("order_id"),
    dq.metrics.column.mean("amount"),
    dq.metrics.table.row_count(),
)
@dlt.resource(primary_key="order_id")
def orders():
    yield ...
```

## Dynamic pattern (for instantiated resources)

```python
source = my_api_source()

dq.with_checks(
    source.orders,
    dq.checks.is_not_null("order_id"),
    dq.checks.is_unique("order_id"),
)

dq.with_metrics(
    source.orders,
    dq.metrics.column.mean("amount"),
    dq.metrics.table.row_count(),
)
```

## Enable and run

```python
pipeline = dlt.pipeline("my_pipeline", destination="duckdb")
dq.enable_data_quality(pipeline)
load_info = pipeline.run(source)
```

## Read results

```python
dataset = pipeline.dataset()

# Check results
dq.read_check(dataset, table="orders", column="order_id").df()

# Metric results
dq.read_metric(dataset, table="orders", column="amount", metric="mean").df()
dq.read_metric(dataset, table="orders", metric="row_count").fetchall()
```
