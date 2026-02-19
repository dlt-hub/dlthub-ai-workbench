---
name: debug-pipeline
description: Debug and inspect a dlt pipeline after running it. Use after a pipeline run (success or failure) to inspect traces, load packages, schema, data, and diagnose errors like missing credentials or failed jobs.
argument-hint: <pipeline_name>
---

# Debug a dlt pipeline

**Essential Reading** https://dlthub.com/docs/reference/explainers/how-dlt-works

Parse `$ARGUMENTS`:
- `pipeline_name` (required): the dlt pipeline name

## Run the pipeline

```
uv run python <source>_pipeline.py
```

Common exceptions and what they mean:
- `ConfigFieldMissingException` - config / secrets are missing. inspect exception message
- `PipelineFailedException` - pipeline failed in one of the steps. inspect exception trace to find a root cause. find **load_id** to identify load package that failed

In extract step most of the exceptions are coming from source/resource code that you wrote!

### First run of the pipeline

**Suggest to run** the pipeline before asking the user to fill in credentials:

Expected: a `ConfigFieldMissingException` or `401 Unauthorized` error confirming:
- The pipeline structure is correct
- Config/secrets resolution is wired up properly
- The right API endpoint is being hit

Tell the user what credentials to fill in and how to get them. If credentials are unknown, research the data source (web search for API docs, auth setup guides — similar to what `find-source` does).

After any run (success or failure), use the dlt CLI for inspection:

## Trace

```
dlt pipeline -vv <pipeline_name> trace
```
Note: `-vv` goes BEFORE the pipeline name. Shows config/secret resolution, step timing, failures.

## Load packages

```
dlt pipeline -v <pipeline_name> load-package          # most recent package
dlt pipeline -v <pipeline_name> load-package <load_id> # specific package
```
Shows package state, per-job details (table, file type, size, timing), and **error messages for failed jobs**. With `-v` also shows schema updates applied.

```
dlt pipeline <pipeline_name> failed-jobs
```
Scans all packages for failed jobs and displays error messages from the destination.

## Inspecting raw load files

Load packages are stored at `~/.dlt/pipelines/<pipeline_name>/load/loaded/<load_id>/`. Job files live in `completed_jobs/` and `failed_jobs/` subdirectories.

File format depends on the destination:

| Format | Default for | File extension |
|---|---|---|
| INSERT VALUES | duckdb, postgres, redshift, mssql, motherduck | `.insert_values.gz` |
| JSONL | bigquery, snowflake, filesystem | `.jsonl.gz` |
| Parquet | athena, databricks (also supported by duckdb, bigquery, snowflake) | `.parquet` |
| CSV | filesystem | `.csv.gz` |

Inspect gzipped files with `zcat`:
```
zcat ~/.dlt/pipelines/<pipeline_name>/load/loaded/<load_id>/completed_jobs/<file>.gz
```
Useful for verifying data transformations and debugging destination errors.

## Next steps

- **Load successful** → use `validate-data` to inspect schema and data
- **Config/secrets missing** → check TOML sections, revisit `create-pipeline` step 6b for credential setup
- **No pipeline exists** → use `create-pipeline` to scaffold one first
