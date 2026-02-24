# Reference: README and semantic layer structure

For **technique and tools** (inspect raw schema, use target ERD, transformation options, validation, dashboard), see the main [SKILL.md](SKILL.md) steps 2, 4, 7, and 8.

## README section order

1. **Pipeline** – purpose, source, destination, default limit (e.g. 1000), how to override.
2. **Raw schema** – DBML block + image (e.g. from dbdiagram.io).
3. **Canonical schema** – DBML block + image; all views prefixed `c_`.
4. **Dimensional (star) schema** – DBML block + image; `fct_` and `dim_` views.
5. **Semantic layer** – short description + link to `SEMANTIC_LAYER.md`.
6. **20 questions** – each with SQL and outcome.
7. **Lineage** – diagram: raw → canonical → dim.

## DBML tips

- Use `Table` for each view/table; note in comments which are views (`c_`, `fct_`, `dim_`).
- Use `Ref` for relationships (e.g. `fct_orders.dim_customer_id > dim_customers.id`).
- Export to PNG/SVG from [dbdiagram.io](https://dbdiagram.io) or similar and embed in README.

## Semantic layer file (e.g. SEMANTIC_LAYER.md)

Include:

- **Metrics** – definitions (e.g. revenue, count of orders) and which fact/dim columns they use.
- **Dimensions** – attributes used for grouping/filtering (e.g. customer segment, date, product).
- **Filters** – common filter logic or parameters.
- **How to use** – which tables to join, recommended grain, and any caveats.

## View naming

| Layer     | Prefix | Example       | Notes |
|-----------|--------|---------------|-------|
| Canonical | `c_`   | `c_orders`    | Cleaned views from raw; explicit FKs (e.g. company_id, owner_id). |
| Fact      | `fct_` | `fct_sales`   | Built from canonical; references dim_ by key. |
| Dimension | `dim_` | `dim_customer`| Built from canonical; referenced by facts. |

In the dashboard schema viz, show **Dimensions (dim_)** and **Facts (fct_)** as separate sections so the star schema is clear.
