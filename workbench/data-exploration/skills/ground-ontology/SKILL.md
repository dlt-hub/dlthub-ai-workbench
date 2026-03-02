---
name: ground-ontology
description: Map a dlt pipeline schema to business-meaningful ontology concepts (entities, relationships, metrics, dimensions, grain) by interviewing the user about their domain. Use after exploring data with explore-data and before planning visualizations. Use this skill whenever the user wants to understand what their data means in business terms, map tables to real-world concepts, decide what metrics and dimensions to track, or prepare for building dashboards and reports — even if they don't use the word "ontology".
---

# Ground data in ontology

Build a business ontology by interviewing the user about their domain, then mapping the schema to their mental model. Reference: https://dlthub.com/blog/ontology

## Core principle

The user knows their business better than any schema inference. Ask them what their data means, then formalize their answers into a structured ontology. Model business reality first, then map the schema to it — not the other way around.

## Prerequisites

Requires output from `explore-data`:
- Schema excerpts for relevant tables
- Summary stats (row counts, cardinality, null rates, temporal ranges)
- Anomaly flags
- User's chosen mode and any constraints
- Plan artifact (for intent-driven requests)

If these are missing, run `explore-data` first.

**Mode** is set by the workflow:
- `overview` — shorter interview, fewer questions, aim for speed
- `in-depth` — thorough interview with more detail

Default: `in-depth` when invoked standalone.

## Interview flow

The interview uses `AskUserQuestion` at every step. Present concrete options inferred from the schema evidence — never ask open-ended questions when toggles can be offered. The user can always pick "Other" to provide custom input.

Before starting, summarize the schema evidence in 3–5 bullets: table names, row counts, key columns. This gives the user context for answering.

### Step 1: Business domain

Infer 2–4 domain labels from table names, column names, and data patterns. Present them as options.

Example:
```
question: "What does this data represent?"
options:
  - label: "E-commerce / Orders"
    description: "Tables suggest order transactions, products, and customers"
  - label: "Developer Activity"
    description: "Tables suggest repositories, commits, and contributors"
  - label: "Customer Support"
    description: "Tables suggest tickets, agents, and resolution tracking"
```

The answer sets the business vocabulary for the rest of the interview.

### Step 2: Core entities and roles

Present each in-scope table and ask the user to identify which is their **primary focus** (the main thing they want to analyze). Use a single-select question.

Example:
```
question: "Which table is your main focus — the thing you want to count, sum, or track over time?"
options:
  - label: "orders (45k rows)"
    description: "Transaction records with amounts, dates, and customer references"
  - label: "support_tickets (12k rows)"
    description: "Ticket events with status, priority, and timestamps"
  - label: "users (3k rows)"
    description: "User profiles with attributes and signup dates"
```

The selected table becomes the **fact table**. Remaining tables are classified as dimensions (entity lookups), bridges (many-to-many joins), or child tables (dlt nested data) based on schema structure.

After the user picks, confirm the classification briefly:
- "Got it — `orders` is the fact table. `users` and `products` look like dimensions (you'd group by them). `orders__items` is a child table from dlt nesting."

### Step 3: Key metrics

From the fact table's numeric columns, present options for which metrics matter. Use `multiSelect: true`.

Example:
```
question: "Which numbers do you care about most?"
multiSelect: true
options:
  - label: "amount (revenue per order)"
    description: "Sum or average this to see revenue trends"
  - label: "quantity (items per order)"
    description: "Count of items — useful for volume analysis"
  - label: "discount (discount applied)"
    description: "Track discount impact on revenue"
```

The first selected metric becomes `primary_metric`.

### Step 4: Primary dimensions and temporal grain

Batch two questions in one `AskUserQuestion` call:

**Question A — Primary dimension:**
```
question: "How do you want to slice the data?"
options:
  - label: "By customer"
    description: "Group by customer to see per-customer patterns"
  - label: "By product category"
    description: "Group by category to compare segments"
  - label: "By region"
    description: "Group by geographic region"
```

**Question B — Temporal grain** (only if temporal columns exist):
```
question: "What time granularity?"
options:
  - label: "Monthly (Recommended)"
    description: "Good default for trends — smooths out daily noise"
  - label: "Weekly"
    description: "More granular — shows week-over-week changes"
  - label: "Daily"
    description: "Most detailed — best for short time ranges"
  - label: "All-time"
    description: "No time breakdown — just totals"
```

### Step 5: Relationship confirmation

Present the detected foreign key and parent/child relationships. Ask the user to confirm and label them with business verbs. Use `multiSelect: true` to let them deselect irrelevant relationships.

Example:
```
question: "These relationships were detected. Which are relevant for your analysis?"
multiSelect: true
options:
  - label: "orders → users (customer places order)"
    description: "Join orders to user profiles via user_id"
  - label: "orders → products (order contains product)"
    description: "Join orders to product catalog via product_id"
  - label: "orders__items → orders (line items of order)"
    description: "dlt child table — nested line items"
```

### Overview mode shortcut

In `overview` mode, compress the interview:
- Combine Steps 1–2 into one question: present the most likely fact table with a domain label pre-filled.
- Auto-select all numeric columns as metrics and all categorical columns as dimensions.
- Ask only one question: confirm the fact table + primary metric + temporal grain.
- Skip relationship confirmation (use detected relationships as-is).

## Building the ontology from answers

After the interview, assemble the `selected_ontology` artifact:

1. **Entities**: Map each table to its role (fact/dimension/bridge/child) based on Step 2 answers.
2. **Grain**: Set from the fact table's row-level meaning + Step 4 temporal grain.
3. **Metrics**: From Step 3 selections. First selected = `primary_metric`.
4. **Dimensions**: From Step 4A selections. First selected = `primary_dimension`.
5. **Relationships**: From Step 5 confirmations, with user-provided verbs.
6. **Label**: From Step 1 domain selection.

Present a brief summary (max 6 bullets) of the assembled ontology for final confirmation:

```
question: "Does this capture your data correctly?"
options:
  - label: "Yes, proceed (Recommended)"
    description: "Move on to visualization planning with this ontology"
  - label: "Adjust something"
    description: "Go back and change a specific answer"
```

If the user picks "Adjust something", ask which step to revisit (present steps as options).

## Save ontology to file

After the user confirms, write the ontology to a markdown file in the project root:

**Filename**: `<pipeline_name>_ontology.md`

**Format**:

```markdown
# Ontology: <label>

<summary — one sentence>

## Entities

### <table_name> (<role>)
- **Grain**: <what one row represents>
- **Metrics**: <comma-separated column names>
- **Dimensions**: <comma-separated column names>
- **Temporal column**: <column_name or "none">

### <table_name> (<role>)
...

## Relationships

- <from_table> → <to_table>: <verb> (via <join_column>)
- ...

## Primary focus

- **Primary metric**: <column_name>
- **Primary dimension**: <column_name>
- **Temporal grain**: <daily | weekly | monthly | all-time>
```

Rules:
- One `###` section per entity, one `- ...` line per relationship.
- Use the exact column names from the schema (not business aliases).
- Include only the entities and relationships the user confirmed — don't add extras.
- This file is the **source of truth** for downstream skills. `plan-visualizations` and `create-marimo-report` should read it to verify alignment.

Tell the user where the file was saved: "Ontology saved to `<pipeline_name>_ontology.md`."

## How to map schema to business concepts

This is the analytical foundation. Use these rules when interpreting schema evidence to generate interview options:

### Identifying entity types

- **Event/fact tables** have timestamps and describe something that happened (a purchase, a commit, a page view). Look for: created_at, timestamp, event_type columns. Usually highest row count.
- **Entity/dimension tables** describe things that exist (users, products, repositories). Look for: name, email, status columns, low row count relative to event tables.
- **Bridge/junction tables** connect entities (team memberships, tag assignments). Look for: two foreign key columns, minimal additional attributes.
- **Child tables** (dlt `__` suffix) are nested data extracted by dlt — they inherit meaning from their parent.

### Classifying columns

- **Metrics**: numeric columns you'd aggregate (sum, avg, count). Revenue, quantity, duration, score.
- **Dimensions**: categorical columns you'd group by or filter on. Status, category, region, user_type.
- **Temporal**: date/time columns that define when. Created_at, updated_at, event_timestamp.
- **Identifiers**: primary/foreign keys. Not directly useful for analysis but critical for joins.

### Mapping relationships

Look at foreign keys and dlt parent/child edges. For each relationship, describe it with a verb:
- `orders.user_id → users.id` → "user **places** order"
- `commits.repo_id → repositories.id` → "repository **contains** commit"

These verbs help downstream visualization make sense ("orders by user" rather than "join on user_id").

## Parallel execution strategy

Evidence preparation can still be parallelized. Hypothesis generation is replaced by the interview (which is sequential and interactive).

### Phase 1: Evidence preparation (two haiku subagents in parallel)

**Skip for simple schemas** (≤3 tables) — do it inline instead.

Spawn both in the **same message** so they run concurrently:

**Schema Agent** (model: `haiku`):
```
Analyze the following dlt table schemas and produce a canonical schema graph.
For each table: classify as event/entity/bridge/child, identify grain, list foreign key
and parent/child relationships with verbs.

Tables and schemas:
[paste scoped schema excerpts]

Return a structured summary — no prose, just the graph.
```

**Data Profiling Agent** (model: `haiku`):
```
Profile these columns from a dlt pipeline and return data-shape constraints.
For each column: cardinality, null rate, min/max (for temporal/numeric), distinct count.
Flag anomalies (>50% null, single-value columns, suspicious distributions).

Tables and sample data:
[paste scoped stats and sample rows]

Return a structured summary — no prose, just the profile.
```

### Phase 2: Interview (sequential, interactive)

Run the interview steps above. Use Phase 1 outputs to generate smart options for each question.

## Scope discipline

- Stay within the tables/entities identified by the plan. Don't expand scope unless the user asks.
- Don't trigger full-database profiling from this skill.
- Keep summaries concise — max 6 bullets.
- Present business concepts first, schema mechanics second.

## Handoff contract: `selected_ontology`

The output passed to `plan-visualizations` must include these fields. If any are missing, the downstream skill should flag the gap rather than guessing.

```
selected_ontology:
  label: <business domain label from Step 1>
  summary: <one-sentence description of the ontology>
  entities:
    - table: <table_name>
      role: "fact" | "dimension" | "bridge" | "child"
      grain: <what one row represents>
      metrics: [<column_name>, ...]
      dimensions: [<column_name>, ...]
      temporal_column: <column_name> | null
  relationships:
    - from: <table_name>
      to: <table_name>
      join_column: <column_name>
      verb: <business verb>
  primary_metric: <the main number the user cares about>
  primary_dimension: <the main grouping column>
  temporal_grain: "daily" | "weekly" | "monthly" | "all-time"
```

## Next steps

Pass the `selected_ontology` to `plan-visualizations`. The ontology file (`<pipeline_name>_ontology.md`) is also available for downstream skills to read and cross-reference.
