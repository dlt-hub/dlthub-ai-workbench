---
name: ground-ontology
description: Map a dlt pipeline schema to business-meaningful ontology concepts (entities, relationships, metrics, dimensions, grain). Use after exploring data with explore-data and before planning visualizations. Use when user wants to understand data semantically, map schema to business terms, or prepare for structured visualization planning. Supports overview mode (auto-infer, no confirmation) and in-depth mode (full mapping with user confirmation).
---

# Ground data in ontology

Map raw pipeline schema to business concepts using the dltHub ontology framework (https://dlthub.com/blog/ontology). Requires output from `explore-data` (schema, row counts, column stats). If not available, run `explore-data` first.

**Mode** is set by the workflow (see `rules/workflow.md`):
- `overview` — auto-infer ontology from schema heuristics. No user confirmation. Fast.
- `in-depth` — full mapping with user confirmation. Thorough.

Default: `in-depth` when invoked standalone.

---

## Overview mode

Auto-classify from schema without user interaction:

1. **Entities**: each non-child table (no `_dlt_parent_id`) = one entity. Grain = table name singular.
2. **Metrics**: all numeric columns except IDs and foreign keys.
3. **Dimensions**: all string/categorical columns with ≤50 distinct values.
4. **Temporal**: first date/timestamp column found per table.
5. **Relationships**: `_dlt_parent_id` joins and FK-pattern column names.

No user confirmation. Produce `ontology_map` with `confirmed: auto` and proceed.

Present a one-line summary: "Auto-detected [N] entities with [M] metrics across [K] dimensions."

---

## In-depth mode

### 1. Classify tables

For each table:
- **Entity** (noun): one row = one business object
- **Bridge/junction**: many-to-many relationship. Often has composite keys or `_dlt_parent_id` from nested data.

### 2. Map each entity

| Concept | Question | Source |
|---|---|---|
| **Grain** | What does one row represent? | Primary key + table name |
| **Metrics** | Which columns can be aggregated? | Numeric, high cardinality |
| **Dimensions** | Which columns group or filter? | Categorical, low-to-medium cardinality |
| **Temporal** | What is the time axis? | Date/timestamp columns |
| **Attributes** | What else describes this entity? | Remaining descriptive columns |

### 3. Map relationships

For each FK or `_dlt_parent_id` join: identify **from**/**to** entities, label with a **verb** (e.g., "Campaign *contains* Ad Groups"), note join column(s).

### 4. Present for confirmation

Present a pre-filled ontology — user confirms or edits, never builds from scratch.

```
ONTOLOGY MAP
---

Entities:
  - [Table A] — one row = one [grain]
    Metrics:    [col1], [col2]
    Dimensions: [col3], [col4]
    Temporal:   [date_col] (range: YYYY-MM-DD to YYYY-MM-DD)

  - [Table B] — one row = one [grain]
    ...

Relationships:
  - [Table A] → [Table B] via [column] ("[A] contains [B]")

Does this mapping accurately reflect your data?
```

**Rules:**
- Ask one question only: "Does this look right?"
- If >5 tables, group by relationship cluster and confirm per cluster
- Frame stakes: "This mapping guides all visualizations."

**If user rejects:** ask "Which table matters most?" and re-derive outward from it. One re-attempt only.

---

## Output artifact

```
ontology_map:
  mode: overview | in-depth
  entities:
    - table: str
      grain: str
      metrics: list[str]
      dimensions: list[str]
      temporal_col: str | null
  relationships:
    - from_entity: str
      to_entity: str
      join_col: str
      verb: str
  confirmed: true | auto
```

## Next steps

Use `plan-visualizations` to propose charts aligned to this ontology.
