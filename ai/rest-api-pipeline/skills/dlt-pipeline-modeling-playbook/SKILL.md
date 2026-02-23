---
name: dlt-pipeline-modeling-playbook
description: Run a dlt pipeline with configurable record limit, capture raw schema, define 20 business questions, build canonical and dimensional (star) models, document semantic layer and lineage, answer questions with SQL, and optionally add a dashboard. Use when setting up or documenting a dlt-based analytics pipeline, star schema, raw→canonical→dim workflow, or when the user wants full README documentation with DBML schemas and lineage. Source-agnostic (any data source).
---

# dlt Pipeline → Canonical → Dimensional Model Documentation

Run the full workflow below. Use **dlt** for ingestion. Use the dlt **dataset** API for reading data, running SQL, and using Ibis; use **pipeline.default_schema** for raw schema export. Deploy views by running DDL on the destination; then query and validate via **pipeline.dataset()** (SQL or Ibis). Optionally use **marimo** with the dataset (and dlt's marimo helpers) for a dashboard.

**Dataset and schema access (use these for queries and docs):**

- **Read data / run SQL**: `dataset = pipeline.dataset()`. Use `dataset.table("name")` or `dataset("SELECT ... FROM t1 JOIN t2 ...")` to get a `Relation`; then `.df()`, `.arrow()`, `.fetchall()`, `.limit()`, etc. [Access datasets in Python](https://dlthub.com/docs/general-usage/dataset-access/dataset).
- **Python (Ibis)**: `dataset.ibis()` returns a native Ibis connection; build expressions, then pass to `dataset(expr)` to execute and get `.df()` / `.arrow()`. [Access datasets with Ibis](https://dlthub.com/docs/general-usage/dataset-access/ibis-backend).
- **Raw schema for README**: `pipeline.default_schema.to_dbml()` or `to_mermaid()` (and optionally `to_dict()` / `to_pretty_json()` for tooling). [Review dlt schema](https://dlthub.com/docs/general-usage/dataset-access/view-dlt-schema).
- **Dashboard**: Use **marimo**; feed it data via `pipeline.dataset()` (SQL or Ibis). Optionally use `dlt.helpers.marimo.render`, `load_package_viewer`. [Explore data with marimo](https://dlthub.com/docs/general-usage/dataset-access/marimo).

---

## 1. Run the dlt pipeline

- Run the project's dlt pipeline.
- Apply a **sensible record limit** (e.g. 1000 or fewer) so runs finish quickly.
- **Tell the user explicitly** that this limit is used and that they can override it if they prefer.
- In the README, document that the pipeline uses this default limit and how to change it so users are not surprised.

---

## 2. Capture raw schema (inspect first)

- **Raw schema from dlt**: Use `pipeline.default_schema` after the pipeline run. Export with **`pipeline.default_schema.to_mermaid()`** for the canonical raw schema (tables and columns as dlt sees them); see [Export to Mermaid](https://dlthub.com/docs/general-usage/dataset-access/view-dlt-schema#export-to-mermaid). Also `to_dbml()` or `to_dict()` / `to_pretty_json()` for README or tooling. **Persist the Mermaid** to a file (e.g. `raw_schema.mmd`) after each pipeline run so the dashboard can display it (e.g. via Kroki).
- **Inspect tables and sample data** via the **dataset** API: `dataset = pipeline.dataset()`; `dataset.row_counts().df()` to list tables and row counts; `dataset.table("table_name").limit(1).df()` or `.arrow()` to see columns and a sample row. For custom SQL (e.g. JOINs), use `dataset("SELECT ... FROM t1 JOIN t2 ...").df()`.
- **Optional**: If the user provides a **target ERD or schema** (e.g. Fivetran connector ERD, vendor docs, or a PDF/spec), use it as the reference for the canonical/normalized shape. Stay source-agnostic.
- Document the **raw schema** in the README: **DBML** (from `to_dbml()` or hand-tuned) and a **rendered image** (e.g. dbdiagram.io or embedded Mermaid).

---

## 3. Define 20 business questions

- Create a list of **20 questions** that a business should be able to answer from this data.
- Make them the kind of questions answered from a **dimensional model**: metric by dimension (e.g. "X by Y", "count of Z by segment", "trend of A over time").
- Document these 20 questions in the README.

---

## 4. Canonical model (technique and tools)

- Propose a **canonical model** from the raw data that supports the 20 questions and cleans/normalizes the data. **Canonical = cleaned views** with consistent names and **explicit foreign keys** (e.g. `company_id` on deals, `hubspot_owner_id` → owners). When a target ERD/schema is provided, align table and column names and relationships to it where practical.
- **Transformation techniques** to use as needed:
  - **Unnest/explode** nested structures (arrays, JSON) into rows or dedicated tables.
  - **Deduplicate** entities that appear in multiple raw sources (e.g. UNION + DISTINCT, or window dedup).
  - **Foreign keys**: Resolve IDs to the right parent (e.g. link deals to company via junction table → `company_id` on canonical deals; link contacts → company; link deals/tickets/quotes → owner).
  - **Nulls**: Handle missing values (COALESCE, explicit defaults, or document where nulls are allowed).
- **How to deploy** (choose one or both, depending on project):
  - **Option A – SQL views in the destination**: Execute DDL (e.g. `CREATE OR REPLACE VIEW <schema>.c_<name> AS SELECT ...`) on the destination (via its native connection or SQL client). The dlt **dataset** is for *reading* data, not DDL. After views exist, query them via `pipeline.dataset()` (see step 7). Use prefix **`c_`** for canonical view names.
  - **Option B – dlt transformation resources**: Implement `@dlt.resource` functions that read from the loaded data (e.g. via `pipeline.dataset()` Relation `.iter_arrow()` / `.iter_df()` or Ibis) and load into the same or another destination. Use **`c_`**-prefixed table names.
- **Querying canonical (and dim)**: Use **pipeline.dataset()** with SQL or Ibis (see step 7).
- **Dashboard / layer-flow diagram**: For the canonical layer, show **real FK relationships** (e.g. c_contacts → c_companies, c_deals → c_companies, c_deals → c_contacts [primary contact from junction], c_deals → c_owners, c_tickets / c_quotes → c_owners). Document in the README: canonical model description, and schema in **DBML** plus a **rendered image**.

---

## 5. Dimensional (star) model

- Design a **dimensional star schema**: **facts** (fct_*) and **dimensions** (dim_*) that can answer the 20 questions. Facts reference dimensions by key (e.g. fct_deals.company_id → dim_company, fct_deals.owner_id → dim_owner).
- Implement as **views** (or dlt-loaded tables) built from the canonical model. Use **`fct_`** for fact tables and **`dim_`** for dimension tables. After deployment, all querying (step 7, dashboard) uses **pipeline.dataset()** (SQL or Ibis).
- **Dashboard / schema viz**: Show **Dimensions (dim_)** and **Facts (fct_)** as separate groups so the star is clear. In the layer-flow Mermaid, show only **real fact→dimension relationships** (e.g. fct_deals → dim_company, dim_contact, dim_owner; fct_tickets, fct_quotes → dim_owner). Document in the README: star schema description, and schema in **DBML** plus a **rendered image**.

---

## 6. Semantic layer

- Document the **semantic layer** in the README: how the dimensional model is meant to be used (metrics, dimensions, filters, etc.).
- Create a **separate Markdown file** for the semantic layer (e.g. `SEMANTIC_LAYER.md`) with the full semantic model definition and usage.

---

## 7. Answer the 20 questions and validate

- For each of the 20 questions, write a **query** against the **dimensional model** (fct_ / dim_ views or tables).
- **Run the queries using the dlt dataset API** (SQL or Ibis), not ad hoc CLI scripts:
  - **SQL**: `dataset = pipeline.dataset()` then e.g. `dataset("SELECT ... FROM schema.fct_deals JOIN schema.dim_company ...").df()` (or `.arrow()`, `.fetchall()`). Use the pipeline's dataset/schema name so tables/views are in scope.
  - **Ibis**: `conn = dataset.ibis()`; build the expression (filter, join, aggregate); then `dataset(expr).df()` to execute. Suited for programmatic or reusable query logic.
- Capture outcomes (DataFrame, sample rows, or summary) and document in the README: each question, the SQL (or Ibis snippet), and the outcome.
- **Validation**: Run checks via the same dataset API (SQL or Ibis) to ensure: no duplicate PKs, foreign keys resolve, no unexpected nulls in required fields.

---

## 8. Lineage and optional dashboard

- Add a **lineage diagram** to the README: **raw → canonical → dim** (and optionally semantic layer).
- **Optional – Interactive dashboard**: Either **Streamlit** or **marimo**:
  - **Streamlit (recommended for stable diagram display)**: Build a Streamlit app with tabs for Overview, Diagrams (Mermaid for raw/canonical/dim/semantic), and the 20 questions. Encode Mermaid with zlib + base64 and use **Kroki** (`https://kroki.io/mermaid/svg/{encoded}`) with `st.image(url)` so diagrams render reliably on refresh. Read from the same dlt dataset (e.g. DuckDB connection). Run: `streamlit run <dashboard_script>.py` and open the URL. See the **Streamlit dashboard: create and open** section below.
  - **Marimo**: Create a marimo notebook that uses the **dlt dataset** for data. Get data via **pipeline.dataset()** (SQL or Ibis). Include 3–5 visualizations using the dim model. Optionally use **dlt's marimo helpers**: `from dlt.helpers.marimo import render, load_package_viewer`. Document how to run: `marimo edit <project>_dashboard.py`. See [Explore data with marimo](https://dlthub.com/docs/general-usage/dataset-access/marimo).
- When the workflow is complete, tell the user:
  - They can ask follow-up questions.
  - If the model or questions change, **re-run this workflow from step 3** (20 questions, canonical, dim, semantic layer, queries, validation, docs, and dashboard if present).

---

## README structure (checklist)

Ensure the README includes:

1. **Pipeline information** – what the pipeline does, source, destination, default record limit and how to override it.
2. **Raw schema** – DBML and rendered image.
3. **Canonical schema** – DBML and rendered image.
4. **Dimensional (star) schema** – DBML and rendered image.
5. **Semantic layer** – how to use the dim model and reference to the separate semantic layer file.
6. **20 questions and their SQL** – each question, SQL against the dim model, and the outcome.
7. **Lineage diagram** – raw → canonical → dim.
8. **Dashboard** (optional) – how to run the dashboard and what it shows.

---

## Interfaces and tools

- **Ingestion**: **dlt** (run the project pipeline with the chosen record limit).
- **Reading data / running queries**: Use the **dlt dataset** API. `dataset = pipeline.dataset()`; then SQL via `dataset("SELECT ...")` or tables via `dataset.table("name")`; get results with `.df()`, `.arrow()`, `.fetchall()`, etc. For a Python dataframe API, use **dataset.ibis()** and pass Ibis expressions to `dataset(expr)` to execute. [Dataset (Python)](https://dlthub.com/docs/general-usage/dataset-access/dataset) · [Ibis](https://dlthub.com/docs/general-usage/dataset-access/ibis-backend).
- **Raw schema (docs)**: **pipeline.default_schema** → `.to_dbml()`, `.to_mermaid()`, `.to_dict()`, `.to_pretty_json()`. [Review dlt schema](https://dlthub.com/docs/general-usage/dataset-access/view-dlt-schema).
- **Views (DDL)**: Create canonical/dim **views** by executing DDL on the destination (dlt dataset is read-only for DDL). Or use **dlt** transformation resources that read via dataset and load to the same/other destination. Naming: **`c_`** (canonical), **`fct_`** (fact), **`dim_`** (dimension).
- **Dashboard**: **Streamlit** (20 questions + **raw schema** from dlt `to_mermaid()` + **schema (tables & columns)** as embedded HTML via `st.components.v1.html` + optional **layer-flow** Mermaid via Kroki) or **marimo**. For schema viz: **schema_viz** helper fetches from DB and groups into **Raw**, **Canonical (c_)**, **Dimensions (dim_)**, **Facts (fct_)**; build HTML cards and embed with `st.components.v1.html()`. Layer-flow Mermaid: show real FKs for canonical and real fact→dim relationships for star. [Explore data with marimo](https://dlthub.com/docs/general-usage/dataset-access/marimo).

---

## Refinements and troubleshooting

- **Target schema mismatch**: If the user provides an ERD or spec and column/table names differ, use the exact names from that target; clarify in comments if you map from raw names.
- **Incremental / merge**: If the user wants repeatable loads without duplicates, use **merge** write disposition and **primary keys** in dlt resources (e.g. `@dlt.resource(write_disposition="merge", primary_key="id")`).
- **Materialize views**: If the user asks for better performance, materialize critical views as tables (e.g. `CREATE TABLE ... AS SELECT * FROM ...` or load via dlt).
- **Sample rows**: If transformations fail or look wrong, ask for or run `SELECT * FROM <raw_table> LIMIT 1` (or a few rows) and fix UNNEST/column names/types accordingly.

---

## Additional resources

- For README section order, DBML tips, and semantic layer structure, see [reference.md](reference.md).
- **dlt dataset access (official docs)**: [Access datasets in Python](https://dlthub.com/docs/general-usage/dataset-access/dataset) (SQL, Relation, .df/.arrow) · [Access datasets with Ibis](https://dlthub.com/docs/general-usage/dataset-access/ibis-backend) · [Review dlt schema](https://dlthub.com/docs/general-usage/dataset-access/view-dlt-schema) (to_dbml, to_mermaid) · [Explore data with marimo](https://dlthub.com/docs/general-usage/dataset-access/marimo).

## Re-running after changes

If the user asks for model or question changes, **re-run from step 3**: redefine or adjust the 20 questions, then canonical model, then dimensional model, then semantic layer, then answer the questions (and validation), update the README and lineage, and refresh the dashboard if present.

---

## Streamlit dashboard: create and open

- **Create** a Streamlit app that:
  - Shows the **20 business questions** (each with chart + table + SQL), e.g. in tabs (Overview + Diagrams + Q1–Q20).
  - **Diagrams tab** — three parts:
    1. **Raw schema (dlt export)** — Show the **official** raw schema from **`pipeline.default_schema.to_mermaid()`** ([Export to Mermaid](https://dlthub.com/docs/general-usage/dataset-access/view-dlt-schema#export-to-mermaid)). Persist it to a file (e.g. `raw_schema.mmd`) after each pipeline run so the dashboard can load and display it via Kroki (`st.image(kroki_url)`). The pipeline script can write the file after `pipeline.run()` (e.g. `open("raw_schema.mmd","w").write(pipeline.default_schema.to_mermaid())`).
    2. **Schema (tables & columns)** — Use the **actual** schema from the destination: query the DB (e.g. `information_schema.columns`), group tables into **Raw**, **Canonical (c_)**, **Dimensions (dim_)**, and **Facts (fct_)** so the star schema is clear (dimensions and facts as separate sections). Show table names and column names/types in **embedded HTML** via **`st.components.v1.html(html_string, height=...)`** (cards per table, escaped text). Re-use a **schema_viz** helper: `get_schema_by_layer(conn, schema_name)` returns `{"Raw", "Canonical (c_)", "Dimensions (dim_)", "Facts (fct_)}`; `build_schema_html(layers)`.
    3. **Layer flow (overview)** — Optional Mermaid diagrams for canonical and dimensional layers. **Canonical**: show cleaned c_ views and **real FK relationships** (e.g. c_contacts → c_companies, c_deals → c_companies and c_owners). **Dimensional**: show Facts (fct_*) and Dimensions (dim_*) with only **real fact→dimension relationships** (e.g. fct_deals → dim_company, dim_owner). Render via Kroki; optionally show Mermaid source in an expander.
  - Reads data from the **same dlt dataset** (canonical/dim views), e.g. DuckDB connection to the pipeline DB.
- **Run and open** the dashboard:
  - `streamlit run <dashboard_script>.py`
  - Open the URL shown (e.g. http://localhost:8501) in the browser.
- Document in the README how to run the dashboard and that it includes the 20 questions, the **raw schema (dlt to_mermaid export)** and **schema (tables & columns)** as embedded HTML, and optionally the layer-flow Mermaid diagrams via Kroki.
