# Data exploration workflow

## Deterministic orchestration with bounded parallel agents

```
[Connect + Profile] -> [Path Selection]
      explore-data
                     -> [Evidence Pack Build]
                     -> [Parallel Inference Block]
                        Schema Agent
                        Data Profiling Agent
                        Ontology Hypothesis Agent A (Operational)
                        Ontology Hypothesis Agent B (Dimensional)
                        Ontology Hypothesis Agent C (Behavioral/Causal)
                     -> [Synthesis + Ontology Comparison Checkpoint]
                     -> [Overview or In-Depth Viz Planning]
                     -> [Notebook Architecture + Formatting + Mandatory marimo Verification]
```

## Model routing policy

### Model tiers
- `FAST`: low latency / low cost for formatting, listing, light summaries, deterministic restatements.
- `BALANCED`: structured reasoning for planning, synthesis, scoring, and constrained decision support.
- `DEEP`: ontology generation, conflict resolution, and notebook architecture decisions.

### Global escalation policy
- If output confidence is low, escalate in order: `FAST -> BALANCED -> DEEP`.
- If ontology conflict is unresolved, escalate to `DEEP`.
- If user requests deeper reasoning, escalate to `DEEP`.
- Escalation is bounded to one retry per step. No autonomous recursive loops.

### Context budget strategy definitions
- `minimal`: shortest required inputs only.
- `evidence_pack`: use only normalized Evidence Pack sections required by the step.
- `full`: include complete prior artifacts (reserved for hard conflict resolution only).

### Token budgets by phase
- Phase 0 Connect/Profile + Path Selection: `<= 1,600` output tokens total.
- Phase 0.5 Evidence Pack Build: `<= 1,200`.
- Phase 1 Parallel Inference Block (all branches combined): `<= 6,800`.
- Phase 2 Synthesis + Ontology Checkpoint: `<= 2,400`.
- Phase 3A Overview Viz Planning + Confirm: `<= 1,800`.
- Phase 3B In-Depth Viz Planning + Confirm: `<= 3,200`.
- Phase 4 Notebook Architecture + Formatting + Verification: `<= 4,000`.
- Fallback path: `<= 900`.

## Evidence pack standard

All `BALANCED` and `DEEP` steps operate primarily on a compact `evidence_pack` artifact, not raw schema dumps or raw samples.

Required fields only:
- `schema_excerpt`: relevant tables, keys, joins, parent/child references.
- `summary_stats`: key row counts, null/cardinality ranges, temporal coverage.
- `anomaly_flags`: data quality or join-risk flags.
- `user_responses_compressed`: concise user choices and constraints.
- `mode`: `overview | in-depth`.

## Phase definitions with routing

### Phase 0: Connect/profile + path selection

After `explore-data` produces profile inputs, present:

```
Your pipeline has [N] tables with [M] total rows.

How would you like to explore this data?

1. Overview (Recommended for first look)
   Quick schema summary, basic stats, 3-5 auto-recommended charts.
   Minimal questions. Notebook ready in one step.

2. In-Depth Analysis
   Full intent elicitation, up to 10 charts with interactive controls.
   More questions, richer output.

(default: 1)
```

Default: `overview`.

Routing:
- `model_tier`: `FAST`
- `max_output_tokens`: `800`
- `context_budget_strategy`: `minimal`
- `escalation_rule`: escalate to `BALANCED` only if mode request is ambiguous after one clarification.
- `caching_rule`: cache profile summary and selected mode keyed by pipeline + timestamp.

### Phase 0.5: Evidence Pack build

Build `evidence_pack` from profile outputs before parallel inference.

Routing:
- `model_tier`: `FAST`
- `max_output_tokens`: `700`
- `context_budget_strategy`: `minimal`
- `escalation_rule`: escalate to `BALANCED` if required fields cannot be populated deterministically.
- `caching_rule`: cache `evidence_pack` hash and reuse across Phase 1-4 unless pipeline/schema changes.

### Phase 1: Parallel inference block (bounded, exactly 5 branches)

1. **Schema Agent**
- `model_tier`: `FAST`
- `max_output_tokens`: `900`
- `context_budget_strategy`: `evidence_pack`
- `escalation_rule`: escalate to `BALANCED` if join graph confidence < 0.7.
- `caching_rule`: cache canonical schema graph keyed by `evidence_pack` hash.

2. **Data Profiling Agent**
- `model_tier`: `FAST`
- `max_output_tokens`: `900`
- `context_budget_strategy`: `evidence_pack`
- `escalation_rule`: escalate to `BALANCED` if anomaly rate exceeds threshold and explanation is under-specified.
- `caching_rule`: cache summary metrics and anomaly flags keyed by `evidence_pack` hash.

3. **Ontology Hypothesis Agent A (Operational)**
- `model_tier`: `DEEP`
- `max_output_tokens`: `1,500`
- `context_budget_strategy`: `evidence_pack`
- `escalation_rule`: retry in `DEEP` once with `full` context only if candidate invalid due to missing evidence links.
- `caching_rule`: cache candidate artifact + assumptions keyed by ontology pattern + `evidence_pack` hash.

4. **Ontology Hypothesis Agent B (Dimensional)**
- `model_tier`: `DEEP`
- `max_output_tokens`: `1,500`
- `context_budget_strategy`: `evidence_pack`
- `escalation_rule`: retry in `DEEP` once with `full` context only if candidate invalid due to missing evidence links.
- `caching_rule`: cache candidate artifact + assumptions keyed by ontology pattern + `evidence_pack` hash.

5. **Ontology Hypothesis Agent C (Behavioral/Causal)**
- `model_tier`: `DEEP`
- `max_output_tokens`: `1,500`
- `context_budget_strategy`: `evidence_pack`
- `escalation_rule`: retry in `DEEP` once with `full` context only if candidate invalid due to missing evidence links.
- `caching_rule`: cache candidate artifact + assumptions keyed by ontology pattern + `evidence_pack` hash.

Rules:
- No recursive spawning.
- No autonomous retry loops.
- Branches are isolated and emit structured artifacts with confidence + assumptions.
- Branch failures are isolated. Synthesis continues if at least one ontology branch succeeds.

### Phase 2: Synthesis + ontology selection checkpoint

Deterministic **Synthesis Agent** compares A/B/C using schema + profiling evidence from `evidence_pack`:
- `ontology_candidates` (0-3 valid)
- deterministic scorecard
- recommended default candidate
- explicit assumptions/uncertainties

Routing:
- `model_tier`: `BALANCED`
- `max_output_tokens`: `1,600`
- `context_budget_strategy`: `evidence_pack`
- `escalation_rule`: escalate to `DEEP` if candidate ordering ties, score conflict persists, or unresolved ontology conflict.
- `caching_rule`: cache scorecard + recommendation keyed by candidate hashes.

Then present one checkpoint:

```
ONTOLOGY CANDIDATES
---
A. Operational   [score]
B. Dimensional   [score]  (Recommended)
C. Behavioral    [score]

Select ontology for visualization planning.
(default: recommended)
```

If no candidates are valid, route to fallback summary.

### Phase 3A: Overview path

1. **Visualization Planning Agent** (`plan-visualizations --mode overview`) using selected ontology.
2. Auto-select 3-5 charts.
3. Single confirmation: accept / switch to in-depth / reject all.

Routing:
- `model_tier`: `BALANCED`
- `max_output_tokens`: `1,200`
- `context_budget_strategy`: `evidence_pack`
- `escalation_rule`: escalate to `DEEP` only if user explicitly requests deeper reasoning.
- `caching_rule`: cache chart candidate set keyed by selected ontology + mode.

### Phase 3B: In-depth path

1. **Visualization Planning Agent** (`plan-visualizations --mode in-depth`) using selected ontology.
2. Intent elicitation + chart proposal capped at 10.
3. User confirms viz plan.

Routing:
- `model_tier`: `BALANCED`
- `max_output_tokens`: `2,200`
- `context_budget_strategy`: `evidence_pack`
- `escalation_rule`: escalate to `DEEP` for unresolved multi-objective tradeoffs or explicit user request.
- `caching_rule`: cache confirmed viz plan keyed by selected ontology + intent + mode.

### Phase 4: Notebook generation + mandatory verification

1. **Notebook Architecture Agent** (`create-marimo-report`) builds cell architecture from ontology + viz plan.
2. **Notebook Formatting Agent** writes deterministic marimo-formatted output.
3. **Mandatory verification**: notebook must run cleanly before iteration handoff.

Routing:
- Notebook Architecture Agent:
  - `model_tier`: `DEEP`
  - `max_output_tokens`: `1,800`
  - `context_budget_strategy`: `evidence_pack`
  - `escalation_rule`: single retry in `DEEP` with `full` context if architecture conflicts with chart or ontology constraints.
  - `caching_rule`: cache notebook cell plan keyed by mode + ontology + viz plan hash.
- Notebook Formatting Agent:
  - `model_tier`: `FAST`
  - `max_output_tokens`: `1,000`
  - `context_budget_strategy`: `minimal`
  - `escalation_rule`: escalate to `BALANCED` only for unresolved formatting contract errors.
  - `caching_rule`: cache rendered notebook text keyed by architecture hash.

## State machine transitions

Shared front matter:
- `S0 -> S1`: connect/profile complete.
- `S1 -> S2`: mode selected.
- `S2 -> S3`: evidence pack built.
- `S3 -> S4`: parallel inference completed.
- `S4 -> S5`: synthesis completed; candidate set produced.
- `S5 -> S6`: ontology selected.

Overview path:
- `S6 -> O1`: overview viz proposed (`<=5`).
- `O1 -> O2`: user decision checkpoint.
- `O2(accept) -> O3`: overview notebook architecture.
- `O3 -> O4`: formatting.
- `O4 -> O5`: mandatory marimo verification.
- `O5 -> done`.

In-depth path:
- `S6 -> D1`: in-depth viz proposed (`<=10`).
- `D1 -> D2`: user confirmation.
- `D2(confirmed) -> D3`: in-depth notebook architecture.
- `D3 -> D4`: formatting.
- `D4 -> D5`: mandatory marimo verification.
- `D5 -> done`.

Escalation transitions:
- `O2(switch_to_in_depth) -> D1` using same selected ontology and cached evidence.
- `any_step(low_confidence) -> same_step_escalated` via `FAST -> BALANCED -> DEEP`.
- `Synthesis(unresolved_conflict) -> Synthesis_DEEP`.
- `Viz or Notebook(user_requests_deeper_reasoning) -> DEEP variant`.

Fallback transitions:
- `S5(candidate_count=0) -> F1`.
- `O2(reject_all) -> F1`.
- `D2(reject_all) -> F1`.
- `F1 -> fallback summary table + metric card -> done`.

## Rules

- Deterministic orchestrator remains the single state authority.
- Every phase emits an artifact that gates the next phase.
- Preserve choice architecture defaults and recommendation labels.
- Overview cap: `<=5` charts. In-depth cap: `<=10` charts.
- User may escalate overview -> in-depth at checkpoint. No in-depth -> overview downgrade mid-flow.
- marimo verification remains mandatory before completion.
- No autonomous recursive agent loops.
- Agent fan-out remains small, role-specific, and orchestrator-controlled per effective-agent guidance.
- Ontology remains grounded in https://dlthub.com/blog/ontology.

## Failure handling

- Connection failure -> re-prompt for pipeline name (once).
- Ontology branch failure -> isolate branch; continue synthesis with remaining candidates.
- All ontology candidates invalid -> fallback summary table + metric card.
- All charts rejected -> fallback summary table + metric card.
- marimo capability missing for custom widget -> drop that chart and disclose removal.
