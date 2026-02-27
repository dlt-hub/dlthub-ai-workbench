---
name: ground-ontology
description: Map a dlt pipeline schema to business-meaningful ontology concepts (entities, relationships, metrics, dimensions, grain). Use after exploring data with explore-data and before planning visualizations. Use this skill whenever the user wants to understand what their data means in business terms, map tables to real-world concepts, decide what metrics and dimensions to track, or prepare for building dashboards and reports — even if they don't use the word "ontology".
---

# Ground data in ontology

Map raw pipeline schema to business concepts using the dltHub ontology framework (https://dlthub.com/blog/ontology).

## Core principle

Model business reality first, then map the schema to it — not the other way around. A table called `events` might represent user actions, system logs, or financial transactions. The schema tells you the shape; the ontology tells you the meaning.

## Prerequisites

Requires output from `explore-data`:
- Schema excerpts for relevant tables
- Summary stats (row counts, cardinality, null rates, temporal ranges)
- Anomaly flags
- User's chosen mode and any constraints
- Plan artifact (for intent-driven requests)

If these are missing, run `explore-data` first.

**Mode** is set by the workflow:
- `overview` — lighter analysis, aim for speed
- `in-depth` — thorough analysis with more detail

Default: `in-depth` when invoked standalone.

## How to map schema to business concepts

This is the intellectual core of the skill. For each table in scope:

### 1. Identify what the table *represents* in the real world

Ask yourself: what business event, entity, or relationship does each row capture?

- **Event tables** have timestamps and describe something that happened (a purchase, a commit, a page view). Look for: created_at, timestamp, event_type columns.
- **Entity tables** describe things that exist (users, products, repositories). Look for: name, email, status columns, low row count relative to event tables.
- **Bridge/junction tables** connect entities (team memberships, tag assignments). Look for: two foreign key columns, minimal additional attributes.
- **Child tables** (dlt `__` suffix) are nested data extracted by dlt — they inherit meaning from their parent.

### 2. Determine the grain

The grain is the level of detail each row represents. For example:
- `orders` table: one row = one order (order grain)
- `order_items` table: one row = one line item (line-item grain)
- `daily_metrics` table: one row = one day (daily grain)

The grain determines what aggregations are valid. You can roll up from fine to coarse (line items → orders → daily totals) but not the reverse.

### 3. Classify columns as metrics, dimensions, or temporal

- **Metrics**: numeric columns you'd aggregate (sum, avg, count). Revenue, quantity, duration, score.
- **Dimensions**: categorical columns you'd group by or filter on. Status, category, region, user_type.
- **Temporal**: date/time columns that define when. Created_at, updated_at, event_timestamp.
- **Identifiers**: primary/foreign keys. Not directly useful for analysis but critical for joins.

### 4. Map relationships

Look at foreign keys and dlt parent/child edges. For each relationship, describe it with a verb:
- `orders.user_id → users.id` → "user **places** order"
- `commits.repo_id → repositories.id` → "repository **contains** commit"

These verbs help downstream visualization make sense ("orders by user" rather than "join on user_id").

## Schema complexity gate

Before spawning subagents, check the schema size:

- **Simple schema** (≤5 data tables AND ≤1 obvious fact/event table): Skip Phase 2 parallel agents. Generate all three ontology hypotheses in a single pass — write them yourself inline. The overhead of 3 opus subagents isn't justified when the schema has one fact table and a couple of dimension tables (the hypotheses will look nearly identical). Phase 1 evidence prep can also be done inline for ≤3 tables.
- **Complex schema** (>5 tables OR multiple fact tables): Use the full parallel strategy below.

How to identify a "fact table": it has timestamps, high row count relative to other tables, and foreign keys pointing to entity tables. If there's exactly one table like that, the schema is simple.

## Parallel execution strategy

This skill has two parallelizable phases. Use the Task tool to run them concurrently. **Skip this section for simple schemas** (see complexity gate above).

### Phase 1: Evidence preparation (two haiku subagents in parallel)

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

### Phase 2: Ontology hypotheses (three opus subagents in parallel)

After Phase 1 completes, spawn all three in the **same message**:

Each subagent gets the same prompt template with a different lens:

```
You are generating ONE ontology hypothesis for a dlt pipeline dataset.
Your lens: [Operational | Dimensional | Behavioral/Causal]

[Lens-specific instructions — see sections A/B/C below]

Schema graph:
[paste Phase 1 schema agent output]

Data profile:
[paste Phase 1 profiling agent output]

User context:
[paste mode, intent, constraints]

For each table produce: role, grain, metrics, dimensions, temporal column.
For each relationship: from, to, join column, verb.
List supporting evidence and explicit assumptions.
Keep to max 6 bullets of summary.
```

Use model: `opus` for all three — ontology mapping requires deep reasoning about business meaning.

### Phase 3: Synthesis (sequential)

After all three hypotheses return, synthesize them yourself (no subagent needed). Compare on the criteria in the synthesis checkpoint below.

## Three ontology hypotheses

Generate exactly three hypotheses, each interpreting the same schema through a different business lens. The same table might play different roles in each hypothesis.

### A. Operational

Focus on **processes and execution**. Treat event tables as process steps, entity tables as actors/resources. Emphasize recency, throughput, bottlenecks, and operational health.

Example: For a GitHub dataset, the operational view might center on "contribution pipeline" — commits flow through repos, PRs go through review cycles, issues track work items.

### B. Dimensional

Focus on **stable aggregation and reporting**. Identify clear fact tables (events with metrics) and dimension tables (entities with attributes). This is the classic analytics framing — star/snowflake schema thinking.

Example: Same GitHub dataset — commits are the fact table, with metrics like additions/deletions. Dimensions: repository, author, time. Designed for "show me commits per author per month" queries.

### C. Behavioral/Causal

Focus on **patterns and drivers**. Look for sequences, cohorts, and plausible cause-effect relationships. Label uncertainty explicitly — correlation is not causation, but hypotheses are valuable.

Example: Same GitHub dataset — look at contributor behavior patterns, commit frequency trends, whether PR review time correlates with merge rate. These are hypotheses to explore, not established facts.

## What each hypothesis must include

For each hypothesis (A, B, C), produce:
- **Entities**: each table's role, its grain, metrics, dimensions, and temporal column
- **Relationships**: from-entity, to-entity, join column, verb
- **Attributes**: business-meaningful column descriptions per entity
- **Evidence**: what in the schema/data supports this interpretation
- **Assumptions**: what you're assuming that isn't proven by the data

## Synthesis checkpoint

Score each hypothesis 1–5 on each criterion. This removes subjectivity and makes the recommendation reproducible.

| Criterion | 1 (Poor) | 3 (Adequate) | 5 (Excellent) |
|---|---|---|---|
| **Coverage** | Covers <50% of relevant tables | Covers most tables, misses some columns | All relevant tables and columns mapped |
| **Join quality** | Many:many hacks or missing joins | Mostly clean 1:many, one workaround | All relationships are clean 1:many with clear keys |
| **Metric usability** | Proposed metrics aren't aggregable at grain | Metrics work but some need derived columns | All metrics directly aggregable at declared grain |
| **Temporal fitness** | No temporal column identified | Timestamps exist but grain doesn't match user intent | Temporal column matches requested grain exactly |
| **Semantic coherence** | Mirrors schema structure, no business meaning | Business concepts present but forced | Natural mapping from schema to business reality |

**Scoring process:**
1. Score each hypothesis (A, B, C) on all 5 criteria (1–5 each).
2. Sum the scores (max 25).
3. Recommend the highest-scoring hypothesis. If tied, prefer the one that better matches the user's stated intent.
4. Include the scorecard in the output so the user can see why.

Produce the scorecard and recommendation, then present one question:

```
Select ontology for downstream visualization planning:
A. Operational — [one-line summary]
B. Dimensional — [one-line summary] (Recommended)
C. Behavioral/Causal — [one-line summary]
```

If the user rejects all candidates and no valid alternative emerges, route to a fallback summary (basic table + metric card with no ontology framing).

## Scope discipline

- Stay within the tables/entities identified by the plan. Don't expand scope unless the user asks.
- Don't trigger full-database profiling from this skill.
- Keep summaries concise — max 6 bullets per hypothesis.
- Present business concepts first, schema mechanics second.

## Handoff contract: `selected_ontology`

The output passed to `plan-visualizations` must include these fields. If any are missing, the downstream skill should flag the gap rather than guessing.

```
selected_ontology:
  id: "A" | "B" | "C"
  label: "Operational" | "Dimensional" | "Behavioral"
  summary: <one-sentence description>
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
  scores:
    coverage: 1-5
    join_quality: 1-5
    metric_usability: 1-5
    temporal_fitness: 1-5
    semantic_coherence: 1-5
    total: <sum>
```

## Next steps

Pass the `selected_ontology` to `plan-visualizations`.
