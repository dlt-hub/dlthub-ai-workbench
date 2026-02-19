"""Rick and Morty API pipeline using dlt rest_api source."""

from typing import Any

import dlt
from dlt.sources.rest_api import RESTAPIConfig, rest_api_resources


@dlt.source(name="rick_and_morty")
def rick_and_morty_source() -> Any:
    """Load data from the public Rick and Morty API.

    No authentication required. Base URL: https://rickandmortyapi.com/api

    Example:
        pipeline.run(rick_and_morty_source())
    """
    config: RESTAPIConfig = {
        "client": {
            "base_url": "https://rickandmortyapi.com/api",
            "paginator": {
                "type": "json_link",
                "next_url_path": "info.next",
            },
        },
        "resource_defaults": {
            "primary_key": "id",
            "write_disposition": "replace",
            "endpoint": {
                "data_selector": "results",
            },
        },
        "resources": [
            "character",
            "location",
            "episode",
        ],
    }

    yield from rest_api_resources(config)


if __name__ == "__main__":
    pipeline = dlt.pipeline(
        pipeline_name="rick_and_morty",
        destination="duckdb",
        dataset_name="rick_and_morty_data",
        dev_mode=True,
    )

    load_info = pipeline.run(rick_and_morty_source())
    print(load_info)  # noqa: T201
