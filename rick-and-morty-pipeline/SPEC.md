# Rick and Morty Pipeline — Spec

## WHY
Load all Rick and Morty universe data (characters, locations, episodes) into a local DuckDB for analysis and exploration. No business-critical use case — this is a reference pipeline demonstrating the full dlt recipe on a public, auth-free API.

---

## Source

**API**: https://rickandmortyapi.com/api
**Auth**: none
**Rate limits**: none documented
**dlt source type**: `rest_api` core source (`dlt init rest_api duckdb`)

---

## Resources

### `characters`
- Endpoint: `GET /character?page=N`
- Total: ~826 records, 42 pages, 20 per page
- Primary key: `id`

| Field | Type | Notes |
|---|---|---|
| id | int | PK |
| name | string | |
| status | string | "Alive" / "Dead" / "unknown" |
| species | string | |
| type | string | |
| gender | string | |
| origin | object | → dlt flattens to `origin__name`, `origin__url` |
| location | object | → dlt flattens to `location__name`, `location__url` |
| image | string | URL |
| episode | array[string] | URLs → dlt creates child table `characters__episode` |
| url | string | |
| created | string (ISO) | incremental cursor |

### `locations`
- Endpoint: `GET /location?page=N`
- Total: ~126 records, 7 pages

| Field | Type | Notes |
|---|---|---|
| id | int | PK |
| name | string | |
| type | string | |
| dimension | string | |
| residents | array[string] | URLs → dlt creates child table `locations__residents` |
| url | string | |
| created | string (ISO) | incremental cursor |

### `episodes`
- Endpoint: `GET /episode?page=N`
- Total: ~51 records, 3 pages

| Field | Type | Notes |
|---|---|---|
| id | int | PK |
| name | string | |
| air_date | string | |
| episode | string | season/episode code e.g. S01E01 |
| characters | array[string] | URLs → dlt creates child table `episodes__characters` |
| url | string | |
| created | string (ISO) | incremental cursor |

---

## Pagination

The API uses **page-based pagination** with a `next` URL in the response envelope:

```json
{
  "info": { "count": 826, "pages": 42, "next": "https://...?page=2", "prev": null },
  "results": [...]
}
```

Use dlt `rest_api` with:
- `paginator`: `json_link` pointing at `info.next`
- `data_selector`: `results`

---

## Incremental loading

All three resources have a `created` (ISO 8601) field.
The API has **no server-side filter** for `created_after`, so:

- Use `dlt.sources.incremental("created")` as a **client-side cursor**
- dlt will track the max `created` value seen; on subsequent runs it filters out already-seen records after fetching
- Write disposition: **`merge`** with `id` as primary key — safe against duplicates if pages overlap

> Note: because the API always returns full pages, early termination via incremental will kick in once dlt sees records older than the cursor. This is efficient enough given the small dataset size.

---

## Schema

dlt will produce these tables in DuckDB:

```
characters              ← main character fields (origin/location flattened inline)
characters__episode     ← one row per (character_id, episode_url)
locations               ← main location fields
locations__residents    ← one row per (location_id, resident_url)
episodes                ← main episode fields
episodes__characters    ← one row per (episode_id, character_url)
```

No custom transformations needed — rely entirely on dlt's built-in flattening.

---

## Build steps (following the recipe)

> One endpoint fully working before adding others.

### Step 1 — Minimal pipeline
- `dlt init rest_api duckdb`
- One resource: `characters`, page 1 only, no pagination, no auth, no incremental
- Test: 20 rows land in DuckDB, `origin` and `location` are flattened inline
- `dlt dashboard`

### Step 2 — Add pagination (`characters` only)
- Wire up `json_link` paginator on `info.next`, `data_selector: results`
- Test: ~826 rows in `characters`, child table `characters__episode` populated
- `dlt dashboard`

### Step 3 — Add incremental loading (`characters` only)
- Add `dlt.sources.incremental("created")` cursor, write disposition `merge`, primary key `id`
- Run twice: second run loads 0 new rows
- `dlt dashboard`

### Step 4 — Add `locations` endpoint
- Same pattern: minimal first (page 1) → pagination → incremental
- Test: ~126 rows in `locations`, child table `locations__residents` populated
- `dlt dashboard`

### Step 5 — Add `episodes` endpoint
- Same pattern: minimal first (page 1) → pagination → incremental
- Test: ~51 rows in `episodes`, child table `episodes__characters` populated
- `dlt dashboard`

### Step 6 — MCP setup
- `/add-pipeline-mcp rick_and_morty_pipeline`
- Verify with `query_sql`: check row counts across all tables, spot-check child tables

---

## Files to create

```
rick-and-morty-pipeline/
├── WHY.md
├── rick_and_morty_pipeline.py   ← pipeline entrypoint
├── rest_api_source.py           ← RESTAPIConfig definition
├── test_pipeline.py             ← step-by-step tests
└── .dlt/
    └── config.toml              ← non-secret config (destination, dataset name)
```

---

## Decisions

1. **Child tables**: store full URLs as-is — no parsing, no custom code.
2. **Destination**: DuckDB (local).
