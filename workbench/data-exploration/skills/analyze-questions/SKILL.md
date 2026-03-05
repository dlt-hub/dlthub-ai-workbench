---
name: analyze-questions
description: This skill should be used when the user wants to plan a dashboard, decide what charts to make, map data to business concepts, figure out what metrics to track, prepare for building a report, or understand what their data means — even if they don't use the word "ontology" or "visualization". Trigger phrases include "plan a dashboard", "what charts should I make", "what can I analyze", "map my data to business concepts", "help me understand this data". Run after connect-and-profile and before handing off to marimo-notebook.
---

# Analyze questions and plan charts

Interview the user about their business domain, build an ontology from their answers, then plan charts that answer their questions. The output is a requirements summary that feeds the `marimo-notebook` skill for notebook generation.

Model business reality first, then map the schema to it.

## Prerequisites

Requires evidence from `connect-and-profile`:
- Schema excerpts for relevant tables
- Summary stats (row counts, cardinality, null rates, temporal ranges)
- Anomaly flags
- User context and constraints

If missing, run `connect-and-profile` first.

## Library contract

All chart plans must target this stack:
- `dlt` (pipeline/dataset access)
- `ibis-framework` (query layer) — https://ibis-project.org/reference/expression-tables
- `marimo` (notebook runtime)
- `altair` (chart layer)
- `pyarrow` (interchange/materialization)

Do not plan around pandas-first, raw SQL-first, or destination-specific query paths.

## Interview flow

Use `AskUserQuestion` at every step. Present concrete options inferred from the schema evidence — never ask open-ended questions when toggles can be offered. The user can always pick "Other" for custom input.

Before starting, summarize the schema evidence in 3–5 bullets: table names, row counts, key columns.

### Step 1: Business domain

Infer 2–4 domain labels from table names, column names, and data patterns. Present as options.

```
question: "What does this data represent?"
options:
  - label: "E-commerce / Orders"
    description: "Tables suggest order transactions, products, and customers"
  - label: "Developer Activity"
    description: "Tables suggest repositories, commits, and contributors"
```

### Step 2: Core entity

Present each in-scope table with row counts. Ask which is the **primary focus** — the thing the user wants to count, sum, or track over time. Single-select.

The selected table becomes the **fact table**. Classify remaining tables as dimensions, bridges, or child tables (dlt `__` suffix) based on schema structure.

After the user picks, confirm briefly: "Got it — `orders` is the fact table. `users` and `products` look like dimensions. `orders__items` is a child table from dlt nesting."

### Step 3: Key metrics

From the fact table's numeric columns, present options. Use `multiSelect: true`. First selected becomes `primary_metric`.

### Step 4: Dimensions and grain

Batch two questions in one `AskUserQuestion` call:

**Question A — Primary dimension:**
Present grouping columns found in the schema (e.g., "by customer", "by category", "by region").

**Question B — Temporal grain** (only if temporal columns exist):
- Monthly (Recommended) — good default for dashboards
- Weekly — more detail, noisier
- Daily — high resolution, works for recent data
- All-time total — single number, no time axis

### Step 5: Relationships (show-and-opt-out)

Present detected foreign key and parent/child relationships with business verbs. Use `multiSelect: true` so the user can deselect irrelevant ones.

```
question: "These relationships were detected. Deselect any that aren't relevant."
multiSelect: true
options:
  - label: "orders → users (customer places order)"
    description: "Join via user_id"
  - label: "orders__items → orders (line items of order)"
    description: "dlt child table — nested line items"
```

Default: all selected. The user opts out of relationships they don't need.

### Final confirmation

Present a 3–6 bullet summary of the assembled ontology:

```
question: "Does this capture your data correctly?"
options:
  - label: "Yes, proceed (Recommended)"
    description: "Move on to chart planning with this ontology"
  - label: "Adjust something"
    description: "Go back and change a specific answer"
```

## Schema-to-concept mapping rules

Use these when generating interview options from evidence:

**Entity types:**
- **Event/fact tables**: timestamps, describe something that happened. Look for: created_at, event_type. Usually highest row count.
- **Entity/dimension tables**: describe things that exist. Look for: name, email, status. Low row count relative to facts.
- **Bridge/junction tables**: connect entities. Two foreign key columns, minimal attributes.
- **Child tables** (dlt `__` suffix): nested data from parent.

**Column classification:**
- **Metrics**: numeric columns you'd aggregate (sum, avg, count). Revenue, quantity, duration.
- **Dimensions**: categorical columns you'd group by. Status, category, region.
- **Temporal**: date/time columns. Created_at, updated_at, event_timestamp.
- **Identifiers**: primary/foreign keys. Critical for joins, not for direct analysis.

## Save ontology to file

After confirmation, write to `<pipeline_name>_ontology.md`:

```markdown
# Ontology: <label>

<summary — one sentence>

## Entities

### <table_name> (<role>)
- **Grain**: <what one row represents>
- **Metrics**: <comma-separated column names>
- **Dimensions**: <comma-separated column names>
- **Temporal column**: <column_name or "none">

## Relationships

- <from_table> → <to_table>: <verb> (via <join_column>)

## Primary focus

- **Primary metric**: <column_name>
- **Primary dimension**: <column_name>
- **Temporal grain**: <daily | weekly | monthly | all-time>
```

Rules:
- Use exact column names from the schema (not business aliases).
- Include only confirmed entities and relationships.
- This file is the source of truth for downstream skills.

Tell the user: "Ontology saved to `<pipeline_name>_ontology.md`."

## Chart planning

After the ontology is confirmed, plan charts. Hard cap: **10 charts total** (3 core + up to 7 supporting on request).

### Infer intent from ontology shape

<!-- TODO(human): implement intent-inference mapping

Replace this section with a mapping function that:
1. Takes ontology fields as input: entities (with roles, metrics, dimensions, temporal_column),
   primary_metric, primary_dimension, temporal_grain, relationships
2. Produces 1-2 intent types (primary + optional secondary) from:
   Trend, Comparison, Correlation, Composition, Distribution
3. Returns a rationale string explaining WHY these intents were chosen
4. Handles ambiguous cases where multiple signals are present
   (e.g., temporal + rich dimensions, or "all-time" grain with timestamps)

Available intent types:
- Trend: line chart over time (requires temporal column + metrics)
- Comparison: bar chart by category (requires dimensions)
- Correlation: scatter plot (requires 2+ metrics)
- Composition: stacked bar/treemap (requires metric + hierarchical dimensions)
- Distribution: histogram/box plot (requires numeric metrics with high cardinality)

See DESIGN.md "Open design decision: Intent inference" for trade-off analysis
of three approaches: priority cascade, multi-intent, ontology-weighted.
-->

Map the ontology's shape to chart intent types automatically. Produce a primary intent (and optionally a secondary intent) with a rationale string. Present the inferred intents for confirmation — do not ask the user to pick from abstract types.

### Chart spec format and sanity checks

See `references/chart-planning.md` for the full chart spec template and the 5-point sanity check table. Every chart must pass all sanity checks before finalizing.

### Chart confirmation

Present the chart list to the user:

```
[N] charts planned for [ontology label]:

1. [title] — [chart_type] showing [x] vs [y], colored by [color]
   [legend]
2. ...

Accept? (Yes / Adjust / Start over)
```

## Handoff to marimo-notebook

After the user confirms both the ontology and charts, assemble a **requirements summary** for the `marimo-notebook` skill:

**Data access:**
- Pipeline name, dataset name
- Connection method: `dlt.attach("<pipeline_name>")`
- Key tables and their roles

**Ontology reference:**
- Path to ontology file: `<pipeline_name>_ontology.md`
- Primary metric, primary dimension, temporal grain

**Chart specs:**
- Full list with id, type, title, axes, color, scale, source_table, legend

**Constraints:**
- Row cap: 1,000 rows active during build
- Libraries: marimo, altair, ibis-framework, pyarrow, dlt

Present this summary to the user.

**CRITICAL — hard stop**: Before presenting the summary, check whether the `marimo-notebook` skill is installed (look for `.claude/skills/marimo-notebook/SKILL.md` or `~/.claude/skills/marimo-notebook/SKILL.md`). If it is **not** installed:

1. Tell the user the "marimo-notebook" skill is required.
2. Show the install command:
   ```
   npx skills add marimo-team/skills
   ```
3. **STOP. Do not generate a notebook yourself. Do not write marimo code. Do not attempt to build the dashboard inline.** Wait for the user to install the skill and re-invoke.

You **MUST NOT** bypass this check by generating notebook code directly. The `marimo-notebook` skill contains patterns and constraints that cannot be reproduced ad-hoc.

## Next step

If `marimo-notebook` is installed: present the requirements summary, then **immediately invoke** the `marimo-notebook` skill via the Skill tool with the summary as arguments. Do not ask the user to invoke it — you launch it automatically.

If not installed: STOP and wait for the user to install it. After they confirm, invoke it yourself.
