"""dlt pipeline to load Luma events data into DuckDB."""

import dlt
from dlt.sources.rest_api import rest_api_resources
from dlt.sources.rest_api.typing import RESTAPIConfig


@dlt.source
def luma_events_source(access_token: str = dlt.secrets.value):
    """Load events from the Luma API."""
    config: RESTAPIConfig = {
        "client": {
            "base_url": "https://public-api.luma.com/",
            "auth": {
                "type": "api_key",
                "name": "x-luma-api-key",
                "api_key": access_token,
                "location": "header",
            },
        },
        "resource_defaults": {
            "write_disposition": "replace",
        },
        "resources": [
            {
                "name": "events",
                "endpoint": {
                    "path": "v1/calendar/list-events",
                    "data_selector": "entries",
                    "paginator": {
                        "type": "cursor",
                        "cursor_path": "next_cursor",
                        "cursor_param": "pagination_cursor",
                    },
                },
            },
        ],
    }
    yield from rest_api_resources(config)


pipeline = dlt.pipeline(
    pipeline_name="luma_events_pipeline",
    destination="duckdb",
    dataset_name="luma_events_data",
    progress="log",
)

if __name__ == "__main__":
    load_info = pipeline.run(luma_events_source())
    print(load_info)