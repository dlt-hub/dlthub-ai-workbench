"""dlt pipeline to ingest data from the Rick and Morty API."""

import dlt
from dlt.sources.rest_api import rest_api_resources
from dlt.sources.rest_api.typing import RESTAPIConfig


@dlt.source
def rick_and_morty_source():
    """Extract characters, locations, and episodes from the Rick and Morty API."""
    config: RESTAPIConfig = {
        "client": {
            "base_url": "https://rickandmortyapi.com/api",
        },
        "resource_defaults": {
            "primary_key": "id",
            "write_disposition": "replace",
            "endpoint": {
                "data_selector": "results",
                "paginator": {
                    "type": "json_link",
                    "next_url_path": "info.next",
                },
            },
        },
        "resources": [
            {
                "name": "characters",
                "endpoint": {"path": "/character"},
            },
            {
                "name": "locations",
                "endpoint": {"path": "/location"},
            },
            {
                "name": "episodes",
                "endpoint": {"path": "/episode"},
            },
        ],
    }

    yield from rest_api_resources(config)


pipeline = dlt.pipeline(
    pipeline_name="rick_and_morty_api_pipeline",
    destination="duckdb",
    dataset_name="rick_and_morty_data",
    progress="log",
)


if __name__ == "__main__":
    load_info = pipeline.run(rick_and_morty_source())
    print(load_info)  # noqa: T201
