import dlt
from dlt.sources.rest_api import RESTAPIConfig, rest_api_source


def load_rick_and_morty() -> None:
    pipeline = dlt.pipeline(
        pipeline_name="ricknmorty_pipeline",
        destination="duckdb",
        dataset_name="ricknmorty_raw",
    )

    source = rest_api_source(
        {
            "client": {
                "base_url": "https://rickandmortyapi.com/api/",
                "paginator": {
                    "type": "json_link",
                    "next_url_path": "info.next",
                },
            },
            "resource_defaults": {
                "primary_key": "id",
                "write_disposition": "replace",
            },
            "resources": [
                {
                    "name": "character",
                    "endpoint": {
                        "path": "character",
                        "data_selector": "results",
                    },
                },
                {
                    "name": "location",
                    "endpoint": {
                        "path": "location",
                        "data_selector": "results",
                    },
                },
                {
                    "name": "episode",
                    "endpoint": {
                        "path": "episode",
                        "data_selector": "results",
                    },
                },
            ],
        },
        name="rick_and_morty",
    )

    load_info = pipeline.run(source)
    print(load_info)


if __name__ == "__main__":
    load_rick_and_morty()
