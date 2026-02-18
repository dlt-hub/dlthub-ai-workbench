import dlt
from dlt.sources.rest_api import RESTAPIConfig, rest_api_source


def rick_and_morty() -> dlt.sources.DltSource:
    config: RESTAPIConfig = {
        "client": {
            "base_url": "https://rickandmortyapi.com/api",
        },
        "resource_defaults": {
            "primary_key": "id",
            "write_disposition": "merge",
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
                    "path": "character",
                    "incremental": {
                        "cursor_path": "created",
                        "initial_value": "1970-01-01T00:00:00.000Z",
                    },
                },
            },
            {
                "name": "locations",
                "endpoint": {
                    "path": "location",
                    "incremental": {
                        "cursor_path": "created",
                        "initial_value": "1970-01-01T00:00:00.000Z",
                    },
                },
            },
            {
                "name": "episodes",
                "endpoint": {
                    "path": "episode",
                    "incremental": {
                        "cursor_path": "created",
                        "initial_value": "1970-01-01T00:00:00.000Z",
                    },
                },
            },
        ],
    }
    return rest_api_source(config, name="rick_and_morty")


def load() -> None:
    pipeline = dlt.pipeline(
        pipeline_name="rick_and_morty",
        destination="duckdb",
        dataset_name="rick_morty_data",
    )
    load_info = pipeline.run(rick_and_morty())
    print(load_info)


if __name__ == "__main__":
    load()
