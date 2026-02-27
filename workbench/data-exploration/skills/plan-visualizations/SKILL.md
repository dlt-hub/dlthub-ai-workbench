---
name: plan-visualizations
description: Propose visualizations for a marimo notebook grounded in a selected ontology. Use after ground-ontology and before create-marimo-report. Supports overview mode (auto-recommend 3-5, one confirmation) and in-depth mode (intent elicitation, up to 10 charts). Use this skill whenever the user wants to plan charts, decide what to visualize, pick chart types for their data, or figure out how to present metrics — even if they don't mention "visualization planning" explicitly.
---

# Plan visualizations

Propose a bounded set of charts aligned to the selected ontology and user intent.

## Library contract

All visualization plans must target this stack only:
- `dlt` (pipeline/dataset access)
- `ibis` (query/expression layer) — https://ibis-project.org/reference/expression-tables
- `marimo` (notebook/UI runtime)
- `altair` (chart layer)
- `pyarrow` (interchange/materialization)

Do not plan around pandas-first, raw SQL-first, or destination-specific query paths.

## Prerequisites

Requires from `ground-ontology`:
- `selected_ontology` (A, B, or C — the confirmed ontology hypothesis)
- `ontology_comparison` (the scorecard, for context)
- Evidence gathered during exploration

If unavailable, run `ground-ontology` first.

**Mode** is set by workflow:
- `overview` — auto-recommend 3-5 charts; single confirmation
- `in-depth` — intent elicitation + up to 10 charts

Default: `in-depth` when invoked standalone.

---

## Overview mode

Skip intent elicitation. Auto-select charts based on what the data supports:

1. Pick intent from data shape:
   - Temporal columns present → **Trend** (line chart over time)
   - Dimensions without temporal → **Comparison** (bar chart by category)
   - 2+ metrics without temporal → **Correlation** (scatter plot)
   - Fallback → **Comparison**

2. Auto-select 3-5 valid charts.

3. Present one checkpoint:

```
OVERVIEW — [N] charts from ontology [A|B|C]

[List each chart: type, title, what it shows, legend]

Accept? (Yes / Switch to In-Depth Analysis / Reject all)
```

If reject all: produce a fallback summary table + metric card instead.

---

## In-depth mode

### 1. Elicit business intent

Offer supported intents:
- **Trend**: how something changes over time
- **Comparison**: how categories or groups differ
- **Composition**: what makes up a whole
- **Correlation**: how two measures relate

Ask one question at a time. Recommend a default based on the ontology.

### 2. Propose charts

Hard cap of 10 total:
- 3 core charts first (these are mandatory for dashboard intent)
- Up to 7 supporting charts only on request

For each chart, specify:
- Chart type (line, bar, scatter, heatmap, etc.)
- Title (clear, business-meaningful)
- X axis, Y axis, color encoding
- **Scale type** per axis: `linear` (default) or `log`
- **Legend**: one sentence explaining what the colors/marks represent and how to read the chart. Example: "Each bar is a product category; height is total revenue in USD." Rendered as a subtitle or caption in the notebook.
- Source table
- Whether it's core or supporting
- Brief justification (one sentence)

### When to use log scales

Flag an axis for log scale when:
- Values span **2+ orders of magnitude** (e.g., star counts range 1–100k, revenue $10–$1M)
- The distribution is **power-law or exponential** (most values clustered near zero, long tail)
- A **scatter plot** has both axes with skewed distributions — log-log often reveals structure hidden by outliers
- Comparing **growth rates** rather than absolute values over time

Do **not** use log scale when:
- Values include zero or negatives (log of zero is undefined)
- The range is narrow (< 10x) — linear is more intuitive
- The audience is non-technical and may misread log axes

During evidence gathering, check `max / min` ratio for metric columns. If > 100, recommend log scale in the chart spec.

---

## Parallel sanity validation

When there are 5+ charts to validate, spawn a single haiku subagent to run all sanity checks at once rather than validating inline. This keeps the main conversation moving:

```
Validate each chart against these criteria and return pass/fail per chart.

Charts:
[paste chart specs: id, type, title, x, y, source_table, grain, legend]

Ontology context:
[paste selected ontology summary: entities, grain, metrics]

Criteria per chart:
1. Matches grain — aggregates at the right level for its source table
2. Valid aggregation — metric is actually summable/averageable at this grain
3. Answers intent — directly addresses the stated question
4. Non-redundant — shows something different from higher-ranked charts
5. Expressible in ibis — query can be written with ibis table/generic expressions
6. Scale appropriate — log scale flagged when max/min > 100; no log scale on zero-inclusive axes

Return: chart_id, pass/fail per criterion, drop recommendation (yes/no).
```

Use model: `haiku` — this is mechanical validation, not creative reasoning.

## Visualization sanity check

Before finalizing, validate every proposed chart against these criteria:

| Check | Question |
|---|---|
| Matches grain | Does the chart aggregate at the right level for its source table? |
| Valid aggregation | Is the metric actually summable/averageable at this grain? |
| Answers intent | Does this chart directly answer the stated question? |
| Non-redundant | Does it show something meaningfully different from higher-ranked charts? |
| Expressible in ibis | Can the underlying query be written with ibis table/generic expressions? |
| Scale appropriate | Should any axis use log scale (max/min > 100)? Are zero-inclusive axes kept linear? |

Drop charts that fail any check. Refill from the optional set without exceeding caps.

---

## Output

For each chart in the plan, record:
- `id`, `tier` (core/supporting), `chart_type`, `title`
- `x`, `y`, `color` (column names), `x_scale`, `y_scale` (`linear` or `log`), `source_table`
- `legend` — one sentence: what the colors/marks mean and how to read the chart
- Sanity check results (pass/fail per criterion)

Also record:
- Mode (overview/in-depth)
- Selected ontology ID
- Intent type
- Primary question, metric, dimension, temporal scope
- Any filters the user requested
- Top 3 recommended chart IDs

## Next steps

Pass the `selected_ontology` + `viz_plan` to `create-marimo-report`.
