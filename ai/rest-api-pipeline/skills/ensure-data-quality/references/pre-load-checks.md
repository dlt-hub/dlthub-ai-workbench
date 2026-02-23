# Pre-load quality checks

Attach checks to resources before loading. Checks run during the load step and can halt the pipeline on failure.

## Decorator pattern

```python
@dq.with_checks(dq.checks.is_not_null("order_id"), dq.checks.is_unique("order_id"))
@dlt.resource(primary_key="order_id")
def orders():
    yield ...
```

## Adapter pattern

```python
source = dq.with_checks(my_source(), dq.checks.is_not_null("user_id"))
```

## Run and persist results

```python
dq.run_checks(pipeline, checks={"orders": [dq.checks.is_unique("order_id")]})
```

## Inspect failures with CheckSuite

```python
suite = dq.CheckSuite(dataset, checks={"orders": [dq.checks.is_unique("order_id")]})
failures = suite.get_failures("orders", "order_id__is_unique").df()
```
