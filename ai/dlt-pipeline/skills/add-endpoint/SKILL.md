---
name: add-endpoint
description: Add a complete endpoint to an existing dlt pipeline following the recipe — minimal first, then pagination, then incremental loading. Confirms before each step so you can skip any you want to handle separately. For users who know dlt and want to follow the recipe for one endpoint without hand-holding.
argument-hint: <resource_name> <endpoint_path> (e.g. locations location)
---

# Add a Complete Endpoint

Add one endpoint to an existing pipeline following the full recipe: minimal → pagination → incremental. Asks before each step so you can skip if you want to proceed differently.

Parse `$ARGUMENTS`:
- `resource_name` (required): name for the resource/table (e.g. `locations`)
- `endpoint_path` (required): API path (e.g. `location`)

## Steps

### 1. Minimal resource

Run `/add-resource <resource_name> <endpoint_path>`.

After the pipeline runs and the dashboard opens, ask:

> "Minimal load done. Add pagination now? (yes / skip)"

If skip: stop here. The user will run `/add-pagination` when ready.

### 2. Pagination

Run `/add-pagination <resource_name>`.

After the pipeline runs and the dashboard opens, ask:

> "Pagination done. Add incremental loading now? (yes / skip)"

If skip: stop here. The user will run `/add-incremental` when ready.

### 3. Incremental loading

Run `/add-incremental <resource_name>`.

### 4. Done

Report the final state: table name, row count, write disposition, cursor field.
