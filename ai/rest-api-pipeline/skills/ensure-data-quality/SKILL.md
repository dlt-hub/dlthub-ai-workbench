---
name: ensure-data-quality
description: Writes and runs dlt.hub.data_quality checks (NOT pytest) against a loaded pipeline's destination. Use when the user says "ensure data quality", wants to guard against nulls, duplicates, or invalid values in loaded data. Requires dlt[hub]. Run after validate-data.
argument-hint: <pipeline_name> [table_name]
---

# Ensure data quality

Essential reading: https://dlthub.com/docs/hub/features/quality/data-quality

> **Setup**: `uv add "dlt[hub]"` — also ensure `numpy` and `pandas` are installed (`uv add numpy pandas`) since `.df()` requires them.

> **Note:** `dlt.hub.data_quality` is under active development. Do a quick web search for `dlt.hub.data_quality site:dlthub.com` to confirm the API before writing checks.

Parse `$ARGUMENTS`:
- `pipeline_name` (required): the dlt pipeline name
- `table_name` (optional): specific table; defaults to all tables

## 1. Understand quality requirements

Read `WHY.md` for business definitions. If absent, ask the user:

> "What data quality matters most? For example: no null IDs? status restricted to known values? no duplicate records?"

## 2. Review schema and data

Use `validate-data` output if already run. Otherwise:

```
dlt pipeline <pipeline_name> schema --format mermaid
```

Peek at data before writing checks:

```python
import dlt
dataset = dlt.attach("<pipeline_name>").dataset()
df = dataset.ibis().table("<table_name>").to_pandas()
print(df.head()); print(df.dtypes)
```

Identify candidates: primary keys → `is_unique`/`is_primary_key`; required fields → `is_not_null`; enum columns → `is_in`; numeric → `case()`.

## 3. Available checks

```python
from dlt.hub import data_quality as dq

dq.checks.is_not_null("user_id")                              # completeness
dq.checks.is_unique("order_id")                               # uniqueness
dq.checks.is_in("status", ["active", "inactive", "pending"])  # validity
dq.checks.case("amount >= 0")                                 # row-level SQL, passes when true
```

> **Known bug (dlthub ≤0.22.0):** `is_primary_key()` generates SQL with a hardcoded `value` column instead of the actual column name, causing a `LineageFailedException`. **Workaround:** use `is_unique("col") + is_not_null("col")` instead. For composite keys, use both checks on each column.

> `where()` (table-level aggregates) is not in the current API — volume checks not supported.

## 4. Implement

Create `<pipeline_name>_quality.py`:

```python
import dlt
from dlt.hub import data_quality as dq


def run_checks(pipeline_name: str, table_name: str | None = None) -> dict:
    """Run data quality checks. Raises SystemExit(1) if any check fails."""
    dataset = dlt.attach(pipeline_name).dataset()
    results = {}
    failed = False

    for table in ([table_name] if table_name else dataset.tables):
        checks = _get_checks(table)
        if not checks:
            continue
        check_plan = dq.prepare_checks(dataset[table], checks=checks)
        df = check_plan.df()
        results[table] = df
        print(f"\n--- {table} ---")
        print(df.to_string(index=False))
        # Result is wide-format: one row with row_count + one column per check (count of passing rows)
        row_count = df["row_count"].iloc[0]
        failed_checks = [
            col for col in df.columns
            if col != "row_count" and df[col].iloc[0] < row_count
        ]
        if failed_checks:
            print(f"\nFAILED: {', '.join(failed_checks)}")
            failed = True

    if failed:
        raise SystemExit(1)
    print("\nAll checks passed.")
    return results


def _get_checks(table: str) -> list:
    checks_by_table = {
        # "orders": [
        #     dq.checks.is_unique("order_id"),
        #     dq.checks.is_not_null("order_id"),
        #     dq.checks.is_in("status", ["pending", "shipped", "delivered"]),
        #     dq.checks.case("amount >= 0"),
        # ],
    }
    return checks_by_table.get(table, [])


if __name__ == "__main__":
    import sys
    pipeline_name = "<pipeline_name>"
    table_name = sys.argv[1] if len(sys.argv) > 1 else None
    run_checks(pipeline_name, table_name)
```

Run:
```
uv run python <pipeline_name>_quality.py [table_name]
```

## 5. Act on failures

**Integrate post-load** (recommended — add to pipeline's `__main__` block):
```python
load_info = pipeline.run(source)
print(load_info)
from <pipeline_name>_quality import run_checks
run_checks(pipeline.pipeline_name)  # raises SystemExit(1) on failure
```

**Log without blocking**:
```python
for table, df in run_checks(pipeline_name).items():
    row_count = df["row_count"].iloc[0]
    failed = [c for c in df.columns if c != "row_count" and df[c].iloc[0] < row_count]
    if failed:
        print(f"ALERT: quality failures in {table}: {', '.join(failed)}")
```

## Next steps

- Schema/types wrong → `validate-data` first
- Ready for production → `adjust-endpoint`
