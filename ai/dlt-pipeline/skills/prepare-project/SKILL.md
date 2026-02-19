---
name: build-project
description: Iterative workflow for building dlt pipelines. Use when starting a new dlt project or implementing a new pipeline. Prevents one-shotting — enforces a build → run → verify loop, one resource at a time.
---

# Build Project

**Core rule: never implement more than one resource at a time. Build → run → verify → repeat.**

## Phase 0: Prepare the Environment

Before anything else, ensure the Python environment is ready. Use the `prepare-environment` skill.

## Phase 1: Understand the Source

Before writing any code, read the source documentation:
- Auth method (API key, OAuth, connection string?)
- Available endpoints and data model
- Pagination style (cursor, offset, link header?)
- Rate limits

Identify the single simplest or most important resource to start with.

## Phase 2: Scaffold

```bash
echo Y | uv run dlt init <source> <destination>
```

Set up credentials in `.dlt/secrets.toml`. Confirm auth works before writing pipeline logic.

## Phase 3: One Resource Loop

Repeat this loop for every resource, one at a time:

### 3a. Implement

Add exactly one resource. No more.

### 3b. Run

```bash
uv run python pipeline.py
```

### 3c. Verify

```bash
dlt pipeline <pipeline_name> show    # schema + row counts
dlt pipeline <pipeline_name> trace   # load trace, timing, errors
```

Check:
- Did rows actually load? (not just "no errors")
- Is the schema what you expect?
- Are data types correct?
- Any warnings in the trace?

### 3d. Fix or Continue

If something is wrong — fix it now. Do not add the next resource until this one is clean.

If everything looks good — go back to 3a with the next resource.

## Hard Rules

- **Never** implement multiple resources at once
- **Never** skip the run + verify step
- **Never** move forward while something is broken or unclear
- **Always** check actual data, not just absence of errors
- **Always** use unambiguous, distinct string arguments — `pipeline_name`, `dataset_name`, `source_name` etc. must each be clearly different so there's no confusion about what each refers to (e.g. `pipeline_name="github_pipeline"`, `dataset_name="github_raw"`, not the same string reused for all)
