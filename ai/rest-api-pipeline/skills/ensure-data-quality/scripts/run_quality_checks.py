"""Post-load data quality checks for a dlt pipeline.

Copy this file to <pipeline_name>_quality.py, then:
1. Set PIPELINE_NAME
2. Fill in _get_checks() with your checks
3. Run: uv run python <pipeline_name>_quality.py [table_name]
"""

import sys

import dlt
from dlt.hub import data_quality as dq


PIPELINE_NAME = "TODO_PIPELINE_NAME"  # TODO: set pipeline name


def run_checks(pipeline_name: str, table_name: str | None = None) -> dict:
    """Run checks. Exit 1 on failed checks, exit 2 when no checks are configured."""
    dataset = dlt.attach(pipeline_name).dataset()
    results = {}
    failed = False
    checks_executed = 0

    for table in ([table_name] if table_name else dataset.tables):
        checks = _get_checks(table)
        if not checks:
            continue
        checks_executed += len(checks)
        check_plan = dq.prepare_checks(dataset[table], checks=checks)
        df = check_plan.df()
        results[table] = df
        print(f"\n--- {table} ---")
        print(df.to_string(index=False))
        # Wide-format: one row, row_count + one column per check (count of passing rows)
        row_count = df["row_count"].iloc[0]
        failed_checks = [
            col for col in df.columns
            if col != "row_count" and df[col].iloc[0] < row_count
        ]
        if failed_checks:
            print(f"FAILED: {', '.join(failed_checks)}")
            failed = True

    if checks_executed == 0:
        print("No checks configured. Add checks in _get_checks() before running.")
        raise SystemExit(2)

    if failed:
        raise SystemExit(1)
    print("\nAll checks passed.")
    return results


def _get_checks(table: str) -> list:
    # TODO: add checks per table
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
    if PIPELINE_NAME == "TODO_PIPELINE_NAME":
        raise SystemExit("Set PIPELINE_NAME before running.")
    table_name = sys.argv[1] if len(sys.argv) > 1 else None
    run_checks(PIPELINE_NAME, table_name)
