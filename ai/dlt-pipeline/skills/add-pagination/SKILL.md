---
name: add-pagination
description: Add pagination to an existing resource in a dlt REST API pipeline. Replaces the single_page paginator with the appropriate paginator for the API. Run after add-resource has verified the data structure on page 1.
argument-hint: <resource_name> (e.g. characters)
---

# Add Pagination to a Resource

Upgrade a resource from loading page 1 only (`single_page`) to loading all pages. Run this after `/add-resource` has confirmed the data structure is correct.

Parse `$ARGUMENTS`:
- `resource_name` (required): the resource to add pagination to (e.g. `characters`)

## Steps

### 1. Read the pipeline file

Find and read the existing pipeline file to understand the current resource configuration.

### 2. Identify the paginator type

Check the API response envelope to determine the pagination mechanism. Common patterns for REST APIs:

| Pattern | Paginator type | Config |
|---|---|---|
| `next` URL in response body | `json_link` | `next_url_path: "info.next"` or `"next"` |
| `Link` header with `rel="next"` | `header_link` | (no extra config needed) |
| `offset` + `limit` params | `offset` | `limit: 100, offset_param: "offset"` |
| `page` query param | `page_number` | `page_param: "page"` |

If unsure, fetch the first page manually and inspect the response envelope, or ask the user.

### 3. Replace the paginator in the resource

Edit the resource's endpoint to replace `{"type": "single_page"}` with the appropriate paginator. Example for a `json_link` paginator:

```python
"endpoint": {
    "path": "<endpoint_path>",
    "data_selector": "results",
    "paginator": {
        "type": "json_link",
        "next_url_path": "info.next",   # path to the next-page URL in the response
    },
},
```

### 4. Run the pipeline

```bash
uv run python <pipeline_file>.py
```

### 5. Verify

Check that the full record count was loaded and child tables are populated:

```bash
uv run python -c "
import dlt
p = dlt.pipeline(pipeline_name='<pipeline_name>', destination='duckdb', dataset_name='<dataset_name>')
with p.sql_client() as c:
    for table in ['<resource_name>', '<resource_name>__<array_field>']:
        try:
            with c.execute_query(f'SELECT COUNT(*) FROM {table}') as cur:
                print(f'{table}: {cur.fetchone()[0]}')
        except Exception as e:
            print(f'{table}: {e}')
"
```

Expected: full record count (e.g. ~826 for all characters), child table populated.

### 6. Open the dashboard

Run `/open-dashboard` so the user can inspect the full dataset.
