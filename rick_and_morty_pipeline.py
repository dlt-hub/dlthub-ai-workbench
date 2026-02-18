import dlt
from dlt.sources.rest_api import rest_api_source, RESTAPIConfig


@dlt.source
def rick_and_morty():
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
                "endpoint": {
                    "path": "/character",
                },
            },
            {
                "name": "episodes",
                "endpoint": {
                    "path": "/episode",
                },
            },
        ],
    }
    yield from rest_api_source(config).resources.values()


if __name__ == "__main__":
    pipeline = dlt.pipeline(
        pipeline_name="rick_and_morty_pipeline",
        destination="duckdb",
        dataset_name="rick_and_morty_data",
    )


    load_info = pipeline.run(rick_and_morty())
    print(load_info)
