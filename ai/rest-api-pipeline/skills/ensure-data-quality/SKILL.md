---
name: ensure-data-quality
description: Writes and runs dlt.hub.data_quality checks (NOT pytest) against a loaded pipeline's destination. Use when the user says "ensure data quality", wants to guard against nulls, duplicates, or invalid values in loaded data. Requires dlt[hub]. Run after validate-data.
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

> "What data quality matters most? For example: no null IDs? status restricted to known values? no duplicate records?"

## 2. Review schema and data

Use `validate-data` output if already run. Otherwise peek at data:

```python
import dlt
dataset = dlt.attach("<pipeline_name>").dataset()
print(dataset["<table_name>"].head().df())
```

Identify candidates: primary keys, required fields, enum columns, numeric ranges.

## 3. Available checks

```python
from dlt.hub import data_quality as dq

dq.checks.is_not_null("user_id")                              # completeness
dq.checks.is_unique("order_id")                               # uniqueness
dq.checks.is_primary_key("order_id")                          # unique + not null
dq.checks.is_primary_key(["tenant_id", "order_id"])           # composite key
dq.checks.is_in("status", ["active", "inactive", "pending"])  # validity
dq.checks.case("amount >= 0")                                 # row-level SQL condition
```

### Known issues (dlthub ≤0.22.0)

- **`is_primary_key()`** — hardcoded `value` column causes `LineageFailedException`. Workaround: `is_unique("col")` + `is_not_null("col")`. Test first — prefer `is_primary_key` if it works on the installed version.
- **`where()`** — listed in docs but not yet implemented. Use `case()` as workaround.
- **`.df()` import error** — `uv add numpy pandas`

## 4. Write and run checks (post-load)

Copy `scripts/run_quality_checks.py` to `<pipeline_name>_quality.py`. Customize:
1. Set `PIPELINE_NAME`
2. Fill in `_get_checks()` with checks from step 3

Run: `uv run python <pipeline_name>_quality.py [table_name]`

Result format: wide DataFrame — one row with `row_count` column + one column per check (count of passing rows). A check **fails** when its value < `row_count`.

**Pre-load alternative** (attach to resources, can halt pipeline on failure): See [references/pre-load-checks.md](references/pre-load-checks.md).

## 5. Integrate into pipeline

Add to the pipeline's `__main__` block to run checks after every load:

```python
load_info = pipeline.run(source)
print(load_info)
from <pipeline_name>_quality import run_checks
run_checks(pipeline.pipeline_name)
```

## Next steps

- Schema/types wrong → `validate-data` first
- Ready for production → `adjust-endpoint`
