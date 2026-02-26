---
name: plan-visualizations
description: Propose visualizations for a marimo notebook grounded in a confirmed ontology. Use after ground-ontology and before create-marimo-report. Use when user wants to plan charts, pick visualizations, decide what analysis to do, or choose between trend/comparison/composition views. Supports overview mode (auto-recommend 3–5, one confirmation) and in-depth mode (intent elicitation, up to 10 charts).
---

# Plan visualizations

Propose a bounded set of charts aligned to the user's ontology and business intent.

Requires an **ontology map** from `ground-ontology`. If not available, run `ground-ontology` first.

**Mode** is set by the workflow (see `rules/workflow.md`):
- `overview` — auto-recommend 3–5 charts. No intent elicitation. Single confirmation.
- `in-depth` — elicit business intent, propose up to 10 charts in two tiers.

Default: `in-depth` when invoked standalone.

---

## Overview mode

Skip intent elicitation. Auto-select charts from the ontology:

1. **Pick intent from data shape:**
   - Has temporal column → Trend
   - Has dimension but no temporal → Comparison
   - Has 2+ metrics, no temporal → Correlation
   - Fallback → Comparison

2. **Auto-select 3–5 charts** using the core palette for the detected intent (see chart matrix below). Pick only charts whose required columns exist in the ontology.

3. **Present for confirmation:**

```
OVERVIEW — [N] charts recommended

Based on your data shape ([intent] analysis):

  1. [Chart Type]: [Title]
     X: [column]  Y: [column]
  2. ...
  3. ...

Accept? (Yes / Switch to In-Depth Analysis)
```

User can accept (→ notebook generation) or escalate to in-depth (→ restart at in-depth ontology confirmation).

**If user rejects all:** fall back to one summary table + one metric card.

---

## In-depth mode

### 1. Elicit business intent

Generate 3-4 intent options from the ontology. Only include intents the data supports:

| Intent | Requires | Pattern |
|---|---|---|
| **Trend** | metric + temporal column | "How does [metric] change over [time]?" |
| **Comparison** | metric + dimension | "How does [metric] differ across [dimension]?" |
| **Composition** | metric + dimension | "What makes up [metric] by [dimension]?" |
| **Correlation** | 2+ metrics | "How do [metric A] and [metric B] relate?" |

Present with commitment reinforcement: "You confirmed [entity] with [metric] over [time]. Based on this..."

```
Based on your [Entity] data with [N metrics] over [date range]:

1. Trend Analysis (Recommended)
   "How does [metric] change over [time]?"

2. Comparison
   "How does [metric] differ across [dimension]?"

3. Composition
   "What makes up [metric] by [dimension]?"

Which direction? (default: 1)
```

**Rules:** Mark the most data-rich intent as "(Recommended)". Ask one question only — don't combine intent and filters. If user rejects all, ask "In one sentence, what do you want to learn?" and map to the closest intent.

After selection, optionally ask: "Any specific scope or filter? (Enter for all data)"

### 2. Propose charts

Map intent to a deterministic palette — recommend 3 core, offer up to 7 supporting:

| Intent | Core (top 3) | Supporting (up to 7) |
|---|---|---|
| **Trend** | Line (metric x time), Stat cards, Stacked area | YoY table, Moving average, Dimension bar, Min/max |
| **Comparison** | Bar (metric x dim), Grouped bar, Rank table | Histogram, Box plot, Diff table, Top-N |
| **Composition** | Stacked bar, Treemap, Proportion table | Stacked area over time, Waterfall, Sunburst, % bar |
| **Correlation** | Scatter, Heatmap, Stat summary | Regression overlay, Residuals, Binned scatter, Matrix |

Present core first with concrete column mappings:

```
Goal: "[intent summary]"

CORE (directly answer your question):
  1. [Chart Type]: [Title]
     X: [column]  Y: [column]  Group: [column]
  2. ...
  3. ...

Accept these 3? (Yes / Show more / Edit)
```

Show supporting only on request. Cap at 10 total. Don't ask about colors/fonts — use Altair defaults.

**If user rejects all:** fall back to one summary table + one metric card.

---

## Output artifact

```
viz_plan:
  mode: overview | in-depth
  intent_type: trend | comparison | composition | correlation
  primary_question: str
  primary_metric: str
  primary_dimension: str
  temporal_scope: str | null
  filters: list[{column, operator, value}] | null
  charts:
    - id: int
      tier: core | supporting
      chart_type: str
      title: str
      x: str
      y: str
      color: str | null
      source_table: str
  total_count: int  # overview: ≤5, in-depth: ≤10
  confirmed: true
```

## Next steps

Use `create-marimo-report` to generate the notebook from this plan.
