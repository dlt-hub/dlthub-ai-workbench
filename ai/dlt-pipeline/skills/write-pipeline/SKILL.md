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
- If no dlthub page is found, search instead for: `<source-name> REST API documentation` and use the official API docs as the reference. Try and stick to a source's own rest api docs, no third party sources

### 2. Set up the environment

```bash
uv venv
source .venv/Scripts/activate   # Windows
# or: source .venv/bin/activate  # Mac/Linux
uv add "dlt[workspace]"
uv add numpy
uv add pandas
```

### 3. Write the pipeline

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

### 3b. (Optional) Chain detail endpoints with transformers

If the API has a **list endpoint → detail endpoint** pattern (e.g. `/users` returns a list, `/users/{id}` returns full details per user), use a `@dlt.transformer` instead of a separate resource:

```python
@dlt.resource
def users():
    yield from get_users()  # list endpoint

@dlt.transformer(data_from=users)
def user_details(user):
    yield get_user_detail(user["id"])  # detail endpoint per item

# Run with pipe syntax
pipeline.run(users | user_details)
```

Use this pattern when:
- A second endpoint requires an ID or field from the first endpoint's results
- Fetching details individually per item (avoids loading a flat partial list)

Skip this step if all required data is available from the list endpoint directly.

### 4. Show the loaded schema

Once the pipeline runs successfully, show the user a summary of what was loaded:

```bash
uv run dlt pipeline <pipeline_name> schema
```

Parse the output and present a clean summary to the user:
- List each table with its key columns (exclude dlt internal columns like `_dlt_id`, `_dlt_load_id`, `_dlt_parent_id`)
- Note any child tables and which parent they belong to

### 5. Show basic data stats

Use `pipeline.dataset()` to show the user a quick preview of what was loaded:

```python
import dlt

pipeline = dlt.pipeline(
    pipeline_name="<pipeline_name>",
    destination="duckdb",
    dataset_name="<dataset_name>",
)

dataset = pipeline.dataset()

# Row counts across all tables
print(dataset.row_counts().df().to_string())

# Sample 5 rows from each main table (exclude child tables and dlt system tables)
for table_name in ["<table_1>", "<table_2>"]:
    print(dataset[table_name].limit(5).df().to_string())
```

Present the output as a summary table to the user — row counts first, then a 5-row sample per main table showing only meaningful columns.
