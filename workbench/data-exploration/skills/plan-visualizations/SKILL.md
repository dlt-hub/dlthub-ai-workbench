---
name: plan-visualizations
description: Propose visualizations for a marimo notebook grounded in a selected ontology. Use after ground-ontology and before create-marimo-report. Supports overview mode (auto-recommend 3-5, one confirmation) and in-depth mode (intent elicitation, up to 10 charts).
---

# Plan visualizations

Propose a bounded set of charts aligned to selected ontology and user intent.

Requires from `ground-ontology`:
- `selected_ontology`
- `ontology_comparison` (for commitment restatement)
- `evidence_pack` (preferred for BALANCED/DEEP reasoning)

If unavailable, run `ground-ontology` first.

**Mode** is set by workflow:
- `overview` — auto-recommend 3-5 charts; single confirmation
- `in-depth` — intent elicitation + up to 10 charts

Default: `in-depth` when invoked standalone.

## Model routing and token policy

Overview route defaults:
- `model_tier`: `BALANCED`
- `max_output_tokens`: `1200`
- `context_budget_strategy`: `evidence_pack`
- `escalation_rule`: escalate to `DEEP` only for explicit user request for deeper reasoning.
- `caching_rule`: cache overview chart proposal by `(selected_ontology_id, mode, evidence_pack_hash)`.

In-depth route defaults:
- `model_tier`: `BALANCED`
- `max_output_tokens`: `2200`
- `context_budget_strategy`: `evidence_pack`
- `escalation_rule`: escalate to `DEEP` when tradeoffs cannot be resolved deterministically or user asks for deeper reasoning.
- `caching_rule`: cache confirmed viz plan by `(selected_ontology_id, intent_type, mode, evidence_pack_hash)`.

Global:
- Confidence-triggered escalation follows `FAST -> BALANCED -> DEEP`.
- No autonomous recursive retries.

---

## Overview mode

Skip intent elicitation. Auto-select charts from `selected_ontology`.

1. Pick intent from data shape:
- temporal present -> Trend
- dimension without temporal -> Comparison
- 2+ metrics without temporal -> Correlation
- fallback -> Comparison

2. Auto-select 3-5 valid charts.

3. Present one checkpoint:

```
OVERVIEW - [N] charts from selected ontology [A|B|C]

Accept? (Yes / Switch to In-Depth Analysis / Reject all)
```

If reject all: fallback summary table + metric card.

Token discipline:
- keep rationale concise and capped
- reuse cached ontology commitment summary

---

## In-depth mode

### 1. Elicit business intent

Offer supported intents only:
- Trend
- Comparison
- Composition
- Correlation

Ask one question at a time. Keep recommended default.

### 2. Propose charts

Use deterministic palette with hard cap of 10 total:
- 3 core charts first
- up to 7 supporting only on request

Do not exceed cap.

If reject all: fallback summary table + metric card.

Token discipline:
- ask one intent question per turn
- avoid repeating ontology evidence already in `evidence_pack`
- cap supporting-chart narrative to concise justifications

---

## Output artifact

```
viz_plan:
  mode: overview | in-depth
  selected_ontology_id: A | B | C
  intent_type: trend | comparison | composition | correlation
  primary_question: str
  primary_metric: str
  primary_dimension: str | null
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
  total_count: int  # overview: <=5, in-depth: <=10
  confirmed: true
```

## Next steps

Use `create-marimo-report` with `selected_ontology` + `viz_plan`.
