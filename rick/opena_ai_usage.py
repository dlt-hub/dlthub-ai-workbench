from typing import Any, List, Optional

import dlt
from dlt.common.pendulum import pendulum
from dlt.sources.rest_api import RESTAPIConfig, rest_api_resources


@dlt.source(name="openai_usage")
def openai_usage_source(
    admin_api_key: str = dlt.secrets.value,
    start_time: Optional[int] = None,
    bucket_width: str = "1d",
    group_by: Optional[List[str]] = None,
) -> Any:
    """Load usage data from OpenAI platform Usage API.

    Args:
        admin_api_key: OpenAI Admin API key (not a regular key).
            Generated in org settings at platform.openai.com.
            Auto-loaded from secrets.toml [sources] section.
        start_time: Start of range as unix seconds. Defaults to 30 days ago.
        bucket_width: Aggregation interval: '1m', '1h', or '1d'. Defaults to '1d'.
        group_by: Fields to group results by. Defaults to ['user_id', 'model']
            for per-user spend tracking.

    Example:
        pipeline.run(openai_usage_source())  # auto-inject from TOML, last 30 days
        pipeline.run(openai_usage_source(bucket_width="1h", group_by=["project_id"]))
    """
    if start_time is None:
        start_time = int(
            pendulum.now("UTC").subtract(days=14).start_of("day").timestamp()
        )

    if group_by is None:
        group_by = ["user_id", "model"]

    config: RESTAPIConfig = {
        "client": {
            "base_url": "https://api.openai.com/v1/",
            "auth": {
                "type": "bearer",
                "token": admin_api_key,
            },
        },
        "resources": [
            {
                "name": "completions_usage",
                "endpoint": {
                    "path": "organization/usage/completions",
                    "params": {
                        "start_time": start_time,
                        "bucket_width": bucket_width,
                        "group_by[]": group_by,
                    },
                    "data_selector": "data",
                    "paginator": {
                        "type": "cursor",
                        "cursor_path": "next_page",
                        "cursor_param": "page",
                    },
                },
            },
            {
                "name": "costs",
                "endpoint": {
                    "path": "organization/costs",
                    "params": {
                        "start_time": start_time,
                        "bucket_width": "1d",
                        "group_by[]": ["line_item"],
                        "limit": 180,
                    },
                    "data_selector": "data",
                    "paginator": {
                        "type": "cursor",
                        "cursor_path": "next_page",
                        "cursor_param": "page",
                    },
                },
            },
            {
                "name": "users",
                "endpoint": {
                    "path": "organization/users",
                    "params": {
                        "limit": 100,
                    },
                    "data_selector": "data",
                    "paginator": {
                        "type": "cursor",
                        "cursor_path": "last_id",
                        "cursor_param": "after",
                    },
                },
                "primary_key": "id",
            },
        ],
    }

    yield from rest_api_resources(config)


def load_openai_usage() -> None:
    pipeline = dlt.pipeline(
        pipeline_name="openai_usage",
        destination="duckdb",
        dataset_name="openai_usage_data",
        dev_mode=True,
    )

    load_info = pipeline.run(openai_usage_source(), loader_file_format="insert_values")
    print(load_info)


if __name__ == "__main__":
    load_openai_usage()
