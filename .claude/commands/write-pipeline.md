---
name: write-pipeline
description: Write a dlt pipeline for a given source or API. Guides through source discovery, pipeline creation, and loading data.
argument-hint: <source-name>
---

# Write a dlt pipeline

Parse `$ARGUMENTS`:
- `source-name` (required): the API or data source to build a pipeline for (e.g., "stripe", "github", "my postgres database")

## Steps

### 1. Find the source

Search the web for: `dlthub <source-name>`

- If a result matching `dlthub.com/context/source/<slug>` or `dlthub.com/workspace/source/<slug>` is found:
  - Fetch that page and extract the `dlt init` command (e.g. `dlt init dlthub:<source_identifier> duckdb`)
  - Run the command: `uv run <dlt init command>`
  - This generates a pipeline script and a YAML spec file — use those as the source reference for writing the pipeline
- If no dlthub page is found, search instead for: `<source-name> REST API documentation` and use the official API docs as the reference.

### 2. Handle authentication

If the source requires credentials (API key, token, etc.), follow the `/setup-auth` skill.
**Never ask the user to provide credentials in the chat.** Write placeholders to `.dlt/secrets.toml` and tell them to fill it in.

### 4. Set up the environment

```bash
uv venv
source .venv/Scripts/activate   # Windows
# or: source .venv/bin/activate  # Mac/Linux
uv add "dlt[workspace]"
uv add numpy
uv add pandas
```

### 5. Write the pipeline

Using the source docs found above, write a dlt REST API pipeline following this pattern:

**3.1 Init the project**
```
dlt init rest_api duckdb
pip install -r requirements.txt
```

**3.2 Configure the pipeline**

Build a Python script using the `rest_api` source with three sections:

- **`client`** — base URL of the API and authentication (e.g. API key, bearer token)
- **`resource_defaults`** — shared settings across endpoints (e.g. pagination)
- **`resources`** — list of endpoints to extract, each with:
  - `name` — table name in the destination
  - `endpoint` — the API path
  - `write_disposition` — how to load: `"append"`, `"replace"`, or `"merge"`

**3.3 Run the pipeline**
```python
pipeline = dlt.pipeline(
    pipeline_name="<source_name>_pipeline",
    destination="duckdb",
    dataset_name="<source_name>_data"
)
pipeline.run(source)
```

### 6. View the data

Once the pipeline has run successfully, follow the `/view-data` skill to show the user the loaded schema and a data preview.