# Data exploration workflow

## Dual-path architecture

```
                          ┌─ OVERVIEW ──→ [Auto-Ontology] → [Auto-Viz (≤5)] → [Lightweight Notebook]
[Connect + Profile] → [Path Selection]
   explore-data           │
                          └─ IN-DEPTH ──→ [Ground Ontology] → [Plan Viz (≤10)] → [Full Notebook]
                                          ground-ontology     plan-visualizations  create-marimo-report
```

## Phase 0: Path selection

After `explore-data` produces a data profile, present:

```
Your pipeline has [N] tables with [M] total rows.

How would you like to explore this data?

1. Overview (Recommended for first look)
   Quick schema summary, basic stats, 3–5 auto-recommended charts.
   Minimal questions. Notebook ready in one step.

2. In-Depth Analysis
   Full ontology mapping, business intent elicitation, up to 10 charts
   with interactive controls. More questions, richer output.

(default: 1)
```

**Default:** Overview. Apply when user doesn't choose, says "just show me the data," or intent is unclear.

**In-Depth triggers:** User explicitly asks for deep analysis, mentions specific business questions, says "in-depth," or the data has >10 tables (suggest in-depth but don't force).

The selected path is passed as `mode: overview | in-depth` to all downstream skills.

## Overview path

1. **Explore data** (`explore-data`) — connect, profile
2. **Ground ontology** (`ground-ontology --mode overview`) — auto-infer entities/metrics/dimensions from schema. No user confirmation. Lightweight ontology.
3. **Plan visualizations** (`plan-visualizations --mode overview`) — auto-select 3–5 charts from data shape. Single confirmation: "Here are 3 charts. Accept? (Yes / Switch to In-Depth)"
4. **Create notebook** (`create-marimo-report --mode overview`) — lightweight notebook: data connection + charts + summary. No interactive filter controls.

**Checkpoints:** 1 (chart confirmation in step 3). User can escalate to in-depth at this checkpoint.

## In-depth path

1. **Explore data** (`explore-data`) — connect, profile
2. **Ground ontology** (`ground-ontology --mode in-depth`) — full ontology mapping with user confirmation
3. **Plan visualizations** (`plan-visualizations --mode in-depth`) — intent elicitation + up to 10 charts in two tiers (3 core + 7 supporting)
4. **Create notebook** (`create-marimo-report --mode in-depth`) — full notebook with interactive controls, ontology header, all confirmed charts

**Checkpoints:** 3 (ontology, charts, final notebook).

## Rules

- Each phase produces an artifact that gates the next. No autonomous retry loops.
- Every choice has a recommended default. Overview users make 2 decisions (path + charts). In-depth users make 4–6.
- Each phase restates prior confirmed decisions before the next question.
- User can escalate overview → in-depth at any checkpoint. Cannot downgrade in-depth → overview mid-flow.

## Transitions

**Overview:**
- 0 → O1: path selected as overview
- O1 → O2: data profile produced → auto-ontology (no gate)
- O2 → O3: auto-viz proposed → user confirms (or escalates to in-depth)
- O3 → done: notebook written

**In-depth:**
- 0 → D1: path selected as in-depth
- D1 → D2: data profile produced → ontology confirmed by user
- D2 → D3: viz plan confirmed and chart count ≤ 10
- D3 → done: notebook written and validated

**Escalation:**
- Any overview checkpoint → D2 (in-depth ontology), carrying forward the data profile

## Failure handling

- Connection failure → re-prompt for pipeline name (once)
- Ontology rejected (in-depth only) → ask "which table matters most?" and re-derive (once)
- All charts rejected → fall back to summary table + one metric card
- marimo capability missing → remove chart, surface to user
