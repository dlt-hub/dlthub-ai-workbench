---
name: prepare-environment
description: Prepare a Python environment for a dlt project using uv. Use when starting a new dlt project, setting up an existing project for the first time, or adding new dependencies to an existing dlt environment. Triggers on requests like "set up environment", "install dlt", "prepare environment", "install dependencies", or any request to start working with a dlt pipeline.
---

# Prepare Environment

## 1. Check uv

```bash
uv --version
```

If missing, install:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 2. Create venv

From the project root:
```bash
uv venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

## 3. Install dlt

First install always uses the `workspace` extra:
```bash
uv pip install "dlt[workspace]"
```

## 4. Add Dependencies

Before installing any library, check whether dlt provides an extra for it:
```bash
uv pip index versions dlt   # scan extras list
# or check: https://dlthub.com/docs/reference/installation
```

Prefer the dlt extra when one exists:
```bash
uv pip install "dlt[duckdb]"       # ✓ use extra
uv pip install some-other-lib      # only if no dlt extra exists
```

**Known dlt extras:**

| Extra | Use for |
|---|---|
| `bigquery` | Google BigQuery |
| `gcp` | BigQuery + GCS (alias) |
| `postgres` | PostgreSQL |
| `postgis` | PostGIS |
| `redshift` | Amazon Redshift |
| `snowflake` | Snowflake |
| `duckdb` | DuckDB |
| `ducklake` | DuckLake |
| `motherduck` | MotherDuck |
| `databricks` | Databricks |
| `clickhouse` | ClickHouse |
| `mssql` | SQL Server |
| `synapse` | Azure Synapse |
| `fabric` | Microsoft Fabric |
| `oracle` | Oracle DB |
| `dremio` | Dremio |
| `athena` | AWS Athena |
| `s3` / `filesystem` | S3 / generic filesystem |
| `gs` | Google Cloud Storage |
| `az` | Azure Data Lake |
| `sftp` | SFTP |
| `parquet` | Parquet (installs pyarrow) |
| `deltalake` | Delta Lake |
| `pyiceberg` | Apache Iceberg |
| `lancedb` | LanceDB |
| `weaviate` | Weaviate |
| `qdrant` | Qdrant |
| `sql_database` | SQLAlchemy read |
| `sqlalchemy` | SQLAlchemy + Alembic migrations |
| `http` | async HTTP (aiohttp) |
| `hub` | dltHub platform |
| `dbml` | DBML schema export |
| `cli` | CLI extras |
| `workspace` | DuckDB + ibis + pyarrow + marimo + MCP |

## 5. Run Everything via uv run

```bash
uv run python pipeline.py
uv run dlt pipeline show my_pipeline
```

Never invoke `python` or `dlt` directly — always prefix with `uv run` to ensure the venv is active.
