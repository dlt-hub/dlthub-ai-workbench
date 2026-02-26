---
name: ground-ontology
description: Map a dlt pipeline schema to business-meaningful ontology concepts (entities, relationships, metrics, dimensions, grain). Use after exploring data with explore-data and before planning visualizations. Supports deterministic multi-ontology inference with bounded parallel hypotheses and a synthesis checkpoint.
---

# Ground data in ontology

Map raw pipeline schema to business concepts using the dltHub ontology framework (https://dlthub.com/blog/ontology).

Requires output from `explore-data`:
- `evidence_pack` (preferred)
- or legacy profile fields: schema, row counts, column stats, temporal ranges

If missing, run `explore-data` first.

**Mode** is set by workflow:
- `overview`
- `in-depth`

Default: `in-depth` when invoked standalone.

## Model routing and token policy

Global route defaults for this skill:
- `context_budget_strategy`: `evidence_pack`
- `escalation_chain`: `FAST -> BALANCED -> DEEP` (this skill starts at BALANCED/DEEP)
- `global_escalation_rule`:
  - low confidence output -> escalate once
  - unresolved ontology conflict -> escalate to `DEEP`
  - explicit user request for deeper reasoning -> escalate to `DEEP`

Per-agent routing:

1. Schema Agent
- `model_tier`: `FAST`
- `max_output_tokens`: `900`
- `context_budget_strategy`: `evidence_pack`
- `escalation_rule`: escalate to `BALANCED` for low join confidence.
- `caching_rule`: cache canonical schema graph by `evidence_pack_hash`.

2. Data Profiling Agent
- `model_tier`: `FAST`
- `max_output_tokens`: `900`
- `context_budget_strategy`: `evidence_pack`
- `escalation_rule`: escalate to `BALANCED` for unresolved anomaly diagnostics.
- `caching_rule`: cache profile summary by `evidence_pack_hash`.

3. Ontology Hypothesis Agent A (Operational)
- `model_tier`: `DEEP`
- `max_output_tokens`: `1500`
- `context_budget_strategy`: `evidence_pack`
- `escalation_rule`: single retry in `DEEP` with `full` context when evidence linkage is insufficient.
- `caching_rule`: cache candidate + assumptions by `(pattern, evidence_pack_hash)`.

4. Ontology Hypothesis Agent B (Dimensional)
- `model_tier`: `DEEP`
- `max_output_tokens`: `1500`
- `context_budget_strategy`: `evidence_pack`
- `escalation_rule`: single retry in `DEEP` with `full` context when evidence linkage is insufficient.
- `caching_rule`: cache candidate + assumptions by `(pattern, evidence_pack_hash)`.

5. Ontology Hypothesis Agent C (Behavioral/Causal)
- `model_tier`: `DEEP`
- `max_output_tokens`: `1500`
- `context_budget_strategy`: `evidence_pack`
- `escalation_rule`: single retry in `DEEP` with `full` context when evidence linkage is insufficient.
- `caching_rule`: cache candidate + assumptions by `(pattern, evidence_pack_hash)`.

6. Synthesis Agent
- `model_tier`: `BALANCED` (`DEEP` if conflicts)
- `max_output_tokens`: `1600`
- `context_budget_strategy`: `evidence_pack`
- `escalation_rule`: escalate to `DEEP` for unresolved score ties or ontology conflict.
- `caching_rule`: cache scorecard and recommendation by candidate hashes.

---

## Deterministic bounded inference

When run from workflow, execute a fixed non-recursive fan-out:

1. **Schema Agent**: canonical schema graph
2. **Data Profiling Agent**: data-shape constraints
3. **Ontology Hypothesis Agent A**: Operational ontology
4. **Ontology Hypothesis Agent B**: Dimensional ontology
5. **Ontology Hypothesis Agent C**: Behavioral/Causal ontology

Rules:
- Exactly three ontology hypotheses (A/B/C), never more.
- No autonomous retry loops.
- Failures are branch-local.
- Each candidate must include explicit evidence and assumptions.
- All BALANCED/DEEP reasoning uses compressed `evidence_pack` inputs, not raw schema dumps.

---

## Ontology hypotheses

All candidates must use the same ontology structure:
- entities (grain, metrics, dimensions, temporal)
- relationships (from, to, join, verb)

### A. Operational

Prefer process/execution entities and near-real-time actionability.

### B. Dimensional

Prefer fact/dimension framing for stable aggregation and reporting.

### C. Behavioral/Causal

Prefer behavior patterns and plausible drivers while labeling uncertainty.

---

## Synthesis checkpoint (required)

Compare A/B/C deterministically and produce:
- candidate validity flags
- scorecard (coverage, join quality, metric usability, temporal fitness)
- recommended candidate
- unresolved assumptions

Then ask one question only:

```
Select ontology for downstream visualization planning:
A. Operational
B. Dimensional (Recommended)
C. Behavioral/Causal
```

If user rejects all and no valid candidate remains, route to fallback summary path.

---

## Evidence pack requirements

The skill expects `evidence_pack` with only:
- relevant schema excerpts
- key summary statistics
- anomaly flags
- compressed user responses
- selected path (`overview` or `in-depth`)

If only legacy profile fields are available, build and cache a normalized `evidence_pack` first.

---

## Output artifacts

```
ontology_candidates:
  - id: A | B | C
    pattern: operational | dimensional | behavioral_causal
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
    evidence:
      - source: schema | profile
        note: str
    assumptions: list[str]
    valid: true | false

ontology_comparison:
  scores:
    A: number
    B: number
    C: number
  recommended: A | B | C | null
  candidate_count: int

selected_ontology:
  id: A | B | C
  confirmed: true
```

## Next steps

Use `plan-visualizations` with `selected_ontology`.
