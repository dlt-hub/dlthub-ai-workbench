---
name: create-pipeline
description: Guided end-to-end pipeline creation for users new to dlt. Walks through every step with explanations — WHY.md, scaffold, one endpoint at a time (minimal → pagination → incremental), dashboard inspection after each step, and MCP setup at the end. For experienced dlt users, use the atomic skills directly or /add-endpoint instead.
argument-hint: (no arguments — the skill will ask)
---

# Create a dlt Pipeline (Guided)

A fully guided workflow for building a dlt pipeline from scratch. Each step is explained before it runs, and the user is asked to confirm before proceeding. Designed for users who are new to dlt.

Parse `$ARGUMENTS`: none — the skill asks for everything it needs.

---

## Steps

### 1. Understand the goal

Ask the user:

> "What data do you want to load, and what will you do with it once it's in your database?"

Use the answer to create `WHY.md`. This is not optional — knowing the business goal shapes every decision in the pipeline.

### 2. Find the right dlt source

Run `/find-source` with the data source the user described. This identifies whether to use `rest_api`, `sql_database`, `filesystem`, or a verified source connector.

Explain the result to the user before proceeding.

### 3. Initialise the project

Run `/init-pipeline <source_type> <destination>`.

Explain what was created:
- The scaffolded pipeline file with working examples to learn from
- The `.dlt/config.toml` with pipeline metadata
- Why `dataset_name` is different from `pipeline_name`

### 4. Plan the endpoints

Ask the user:

> "What are the main data entities you want to load? List them in priority order (e.g. users, orders, products). We'll add them one at a time."

For each entity, note the endpoint path and primary key.

### 5. For each endpoint — follow the recipe

Repeat this loop for each endpoint, **in order, one at a time**:

#### 5a. Add the minimal resource

Run `/add-resource <resource_name> <endpoint_path>`.

Explain: "We're loading just the first page of results to verify the data structure looks right before loading everything. This is intentional."

After it runs, show the row count and ask:

> "Does the data look correct? Can you see the columns you expected? Ready to load all pages?"

#### 5b. Add pagination

Run `/add-pagination <resource_name>`.

Explain: "Now we'll load all pages of data for this endpoint."

After it runs, show the total row count and child tables. Ask:

> "All [N] records are loaded. Ready to set up incremental loading so future runs only fetch new or updated records?"

#### 5c. Add incremental loading

Run `/add-incremental <resource_name>`.

Explain: "Incremental loading uses a timestamp field to track what's already been loaded. Re-runs will only fetch new data, making the pipeline efficient."

After both runs (first full load, second with 0 new rows), confirm it worked. Ask:

> "Incremental loading is working. Do you want to add another endpoint, or are you done?"

If the user wants another endpoint, repeat from 5a.

### 6. Set up MCP

Run `/add-pipeline-mcp <pipeline_name>`.

Explain: "This sets up a database connection so you (or an AI agent) can query the loaded data directly with SQL."

### 7. Summary

Report:
- All tables created and their row counts
- How to re-run the pipeline: `uv run python <pipeline_file>.py`
- Remember to set `read_only = false` in `.dlt/secrets.toml` before re-running
- How to reopen the dashboard: `/open-dashboard`
- How to query data via MCP: restart Claude Code to activate
