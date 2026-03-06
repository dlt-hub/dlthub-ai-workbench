---
name: analyze-questions
description: Generate charts from dlt pipeline data to answer the user's business questions — interview, plan one chart per selected question, generate all at once, then iterate. Use when the user wants to visualize their data, make charts, or explore what their pipeline shows. Runs after connect-and-profile. Do NOT use for connecting to pipelines or inspecting schemas (use connect-and-profile), or for generating the notebook itself (use marimo-notebook).
---

# Analyze questions and plan charts

Interview the user to surface all their questions, then **build one chart per selected question**. All confirmed charts land in the notebook at once. Add more questions iteratively from there.

Lead with business questions, not schema details.

## Prerequisites

Requires profiling evidence from `connect-and-profile`: table names, row counts, key columns. If missing, run `connect-and-profile` first.

Plan charts for ibis queries and altair rendering — not pandas or raw SQL.

## Adding more charts

If `<pipeline_name>_analysis_plan.md` already exists, skip the interview. Ask the user what new question they want to add, then jump to **Plan charts**.

## Interview

Use `AskUserQuestion` at every step — present concrete options inferred from the schema, never open-ended questions.

Summarize the profiling evidence in 2–3 bullets first (tables, row counts, key columns), then infer 3–5 plain-language business questions the data can answer. Present as multi-select:

```
question: "What questions do you want to answer? (Pick all that interest you — I'll create a chart for each)"
multiSelect: true
options:
  - label: "How has order revenue changed over time?"
    description: "orders table — monthly/weekly trends"
  - label: "Which customers spend the most?"
    description: "orders + users — rank by total spend"
  - label: "Other"
    description: "Describe your own question"
```

Avoid PII columns (emails, names, addresses) as chart dimensions unless the user explicitly asks.

## Plan charts

For each selected question, silently decide: which table(s), which metric and grouping columns, the appropriate time grain (if temporal), and the right chart type:

- Trend over time → **line chart**
- Comparison across categories → **bar chart**
- Relationship between two metrics → **scatter plot**
- Parts of a whole → **stacked bar or treemap**
- Distribution of a metric → **histogram or box plot**

If a question has both temporal and categorical aspects, pick the primary one first — the secondary becomes the next chart.

Before presenting, sanity-check each spec: does it actually answer the question? If not, rethink before showing it.

Then present each spec in sequence for quick confirmation:

```
question: "Here's the chart for question 1. Look good?"
options:
  - label: "Yes (Recommended)"
  - label: "Adjust"
    description: "Change the chart type, metric, or grouping"
```

Show the spec above the toggle:

```
Chart: Monthly Revenue Trend
Type: line chart
X: orders.created_at (monthly)
Y: sum(orders.amount)
Source: orders table (50k rows)
"Total order revenue over time, aggregated monthly"
```

If "Adjust", ask one targeted follow-up — don't re-run the full interview. Confirm all specs before proceeding to code generation.

## Save analysis plan

After all specs are confirmed, append each to `<pipeline_name>_analysis_plan.md`: the question and chart spec (type, axes, source table). Use exact column names from the schema.

## Handoff

Before invoking `marimo-notebook`, generate chart code for all confirmed specs:
- Write an ibis query that produces the data for the chart (use `dlt.attach()` to connect — see `rules/dlt-relation-api.md`)
- Write an altair chart from the query result. Sanity-check: does it aggregate at the right grain, is the metric summable, and does it directly answer the question?
- Wrap both in a marimo notebook file (`<pipeline_name>_dashboard.py`) using proper marimo cell structure

Then pass the notebook file path to the `marimo-notebook` skill. The workflow rule handles the dependency check, launch, and iteration loop — don't duplicate it here.
