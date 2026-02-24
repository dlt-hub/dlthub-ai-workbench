"""Standalone data quality verification for a dlt pipeline.

Copy this file to <pipeline_name>_quality.py, then:
1. Set PIPELINE_NAME
2. Fill in CHECKS_BY_TABLE and METRICS_BY_TABLE
3. Run: uv run python <pipeline_name>_quality.py [table_name]
"""

import sys

import dlt
from dlt.hub import data_quality as dq


PIPELINE_NAME = "TODO_PIPELINE_NAME"  # TODO: set pipeline name

# TODO: add checks per table
CHECKS_BY_TABLE: dict[str, list] = {
    # "orders": [
    #     dq.checks.is_unique("order_id"),
    #     dq.checks.is_not_null("order_id"),
    #     dq.checks.is_in("status", ["pending", "shipped", "delivered"]),
    #     dq.checks.case("amount >= 0"),
    # ],
}

# TODO: add metrics per table
METRICS_BY_TABLE: dict[str, list] = {
    # "orders": [
    #     dq.metrics.column.null_count("order_id"),
    #     dq.metrics.column.mean("amount"),
    #     dq.metrics.table.row_count(),
    # ],
}


def run_checks(pipeline_name: str, table_name: str | None = None) -> None:
    """Run checks and metrics against loaded data. Exit 1 on failures."""
    dataset = dlt.attach(pipeline_name).dataset()
    tables = [table_name] if table_name else list(dataset.tables)
    failed = False
    anything_ran = False

    for table in tables:
        checks = CHECKS_BY_TABLE.get(table, [])
        metrics = METRICS_BY_TABLE.get(table, [])
        if not checks and not metrics:
            continue
        anything_ran = True
        print(f"\n--- {table} ---")

        # Read check results (written by enable_data_quality during pipeline.run)
        if checks:
            for check in checks:
                col = getattr(check, "column", None)
                try:
                    df = dq.read_check(dataset, table=table, column=col).df()
                    print(f"  Check ({col}): {df.to_string(index=False)}")
                except Exception as e:
                    print(f"  Check ({col}): ERROR - {e}")
                    failed = True

        # Read metric results
        if metrics:
            for metric in metrics:
                col = getattr(metric, "column", None)
                name = getattr(metric, "name", None)
                try:
                    df = dq.read_metric(
                        dataset, table=table, column=col, metric=name
                    ).df()
                    print(f"  Metric {name}({col}): {df.to_string(index=False)}")
                except Exception as e:
                    print(f"  Metric {name}({col}): ERROR - {e}")

    if not anything_ran:
        print("No checks or metrics configured. Update CHECKS_BY_TABLE / METRICS_BY_TABLE.")
        raise SystemExit(2)

    if failed:
        raise SystemExit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    if PIPELINE_NAME == "TODO_PIPELINE_NAME":
        raise SystemExit("Set PIPELINE_NAME before running.")
    table_name = sys.argv[1] if len(sys.argv) > 1 else None
    run_checks(PIPELINE_NAME, table_name)
