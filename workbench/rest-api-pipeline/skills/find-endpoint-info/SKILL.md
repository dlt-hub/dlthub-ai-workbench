---
name: find-endpoint-info
description: Decompose a user's data request into specific API endpoints, then look up those endpoints in the official API documentation. Use before create-pipeline or add-endpoint when endpoint details are unknown.
argument-hint: <api-name> <data-description>
---

# Find endpoint info for a data request

Translate what the user wants to load into concrete API endpoint details by researching the official documentation.

Parse `$ARGUMENTS`:
- `api-name` (required): the name of the API/service (e.g., "PostHog", "Stripe", "HubSpot")
- `data-description` (required): what the user wants to load (e.g., "page views per URL", "contacts and companies", "orders from last 30 days")

## Steps

### 1. Decompose the request into endpoints

Analyse `data-description` and list the likely API endpoints needed to satisfy it. Think about:
- What object types are involved? (e.g., "page views" → events filtered by type; "orders" → orders resource)
- Are there parent/child relationships? (e.g., contacts belong to a project — need project ID first)
- Is aggregation needed, or raw records? (e.g., "views per page" could be raw events + SQL group-by, or a pre-aggregated insights endpoint)

Write out a short candidate list before searching, e.g.:
```
Candidates for "page views per URL" in PostHog:
  1. GET /api/projects/{id}/events/?event=$pageview  — raw pageview events
  2. GET /api/projects/{id}/insights/           — pre-aggregated trend data
```

### 2. Find the official API docs URL

Use web search to locate the official API reference — **only the provider's own domain**:
```
query: <api-name> API reference <endpoint-topic> documentation
```

Accepted domains: the provider's own docs site (e.g., `posthog.com/docs`, `stripe.com/docs`, `developers.hubspot.com`).

**Never use**: GitHub repos, Airbyte docs, Fivetran docs, connector aggregators, or any third-party site.

If multiple doc pages are likely (one per endpoint), identify all URLs before fetching.

### 3. Fetch each endpoint's documentation

For each candidate endpoint, fetch the relevant official docs page:

```
WebFetch: <official-docs-url>
prompt: What is the exact endpoint path? HTTP method? Required and optional query params?
        What does the response look like — top-level keys, pagination fields, data array path?
        What fields does each record contain? Are there filters for [specific filter the user needs]?
```

Fetch pages in parallel when they are independent.

**If the page fails to load or returns CSS/fonts instead of content**, try:
- A more specific sub-page URL (e.g., `/docs/api/events` instead of `/docs/api`)
- A web search for the exact endpoint: `<api-name> <endpoint-path> API docs`
- The provider's OpenAPI/Swagger spec if linked from their docs

### 4. Summarise findings

For each confirmed endpoint, present a structured summary:

```
Endpoint: <name>
  Path:          GET /api/projects/{project_id}/events/
  Auth:          Bearer <personal_api_key>  (header: Authorization)
  Key params:
    - event       filter by event name (e.g. "$pageview")
    - after       ISO8601 timestamp — load events after this time (for incremental)
    - before      ISO8601 timestamp
    - limit       page size (default 100, max 1000)
  Pagination:    cursor-based — response has `next` field with full URL
  Response:
    data_selector: "results"
    Record fields: uuid, event, timestamp, properties.$current_url, properties.$pathname,
                   distinct_id, person
  Incremental:   yes — use `timestamp` as cursor, `after` as param
  Notes:         Requires project_id — fetch from GET /api/projects/ first
```

If a candidate endpoint turned out to be wrong or unnecessary, say why and drop it.

### 5. Recommend the best approach

Based on findings, recommend which endpoint(s) to use and why:
- Prefer raw-record endpoints over pre-aggregated ones (more flexible for downstream analysis)
- Flag if a parent resource ID (e.g., project_id, account_id) needs to be fetched first
- Note any rate limits or quota concerns

State clearly what the next step is:
- If building from scratch → hand off to `create-pipeline`
- If adding to an existing pipeline → hand off to `add-endpoint`