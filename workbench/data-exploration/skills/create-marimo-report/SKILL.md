---
name: create-marimo-report
description: Create an interactive marimo notebook to visualize and report on pipeline data. Works standalone or as final step after ground-ontology and plan-visualizations.
---

# Create a data report

Create an interactive marimo notebook to visualize data loaded by a dlt pipeline.

Parse `$ARGUMENTS`:
- `pipeline-name` (optional): dlt pipeline name
- `report-description` (optional, after `--`): custom report intent

## Model routing and token policy

Use a two-agent deterministic handoff:

1. Notebook Architecture Agent
- `model_tier`: `DEEP`
- `max_output_tokens`: `1800`
- `context_budget_strategy`: `evidence_pack`
- `escalation_rule`: one DEEP retry with `full` context if architecture conflicts with ontology/chart constraints.
- `caching_rule`: cache notebook cell architecture by `(mode, selected_ontology_id, viz_plan_hash)`.

2. Notebook Formatting Agent
- `model_tier`: `FAST`
- `max_output_tokens`: `1000`
- `context_budget_strategy`: `minimal`
- `escalation_rule`: escalate to `BALANCED` for unresolved formatting/contract violations.
- `caching_rule`: cache rendered notebook text by architecture hash.

Global:
- confidence-triggered escalation follows `FAST -> BALANCED -> DEEP`
- no autonomous recursive loops

## When coming from workflow (overview or in-depth)

If upstream steps are complete, required inputs are:
- `selected_ontology` (A/B/C)
- `viz_plan`
- `mode`
- `evidence_pack` (for compressed context reuse)

Restate commitment before generation:

"Generating [overview/in-depth] notebook from ontology [A|B|C] for [intent] with [N] charts."

### Mode differences

| Aspect | Overview | In-Depth |
|---|---|---|
| Max charts | 5 | 10 |
| Interactive controls | No (static altair) | Yes (`mo.ui.altair_chart`) |
| Ontology header | One-line selected ontology summary | Full selected ontology map |
| Stat cards | Basic | Detailed |
| Filename | `<pipeline>_overview.py` | `<pipeline>_analysis.py` |
| Cell count | 6-10 | 8-20 |

## 1. Standalone mode

If `selected_ontology` and `viz_plan` are absent:
1. inspect schema
2. summarize business context
3. ask user goal
4. continue with report generation

## 2. Create marimo notebook

Create `<pipeline_name>_explore.py` in marimo Python format (`@app.cell`).

Install if needed:
```
pip install "dlt[workspace]"
```

## 3. Data access contract

Use:
- `dlt.attach()`
- `pipeline.dataset()`
- ibis expressions for queries

Do not use destination-specific connectors, raw SQL as primary path, or pandas transformations as query layer.

## 4. Chart + marimo contract

- Use `mo.ui.altair_chart()` for interactive charts in in-depth mode.
- Use static altair charts in overview mode.
- Enforce chart cap from `viz_plan`.
- Keep unique variable names across cells (`_` prefix for local vars).

## 5. Capability verification

When chart plan includes custom widget, verify `anywidget-generator` availability.
If unavailable, remove that chart and disclose removal.

## 6. Notebook generation contract

Generated notebook MUST satisfy:
- single `.py` marimo notebook
- PEP 723 metadata
- ontology-aware markdown header reflecting selected ontology
- one chart per chart cell
- deterministic chart order (core before supporting)
- no conditional control flow outside allowed connection cell checks
- architecture is generated before formatting and both artifacts are cached

## 7. Mandatory run verification

Before launch, verify notebook executes without errors:

```
uv run python <filename>.py
```

Fix errors before proceeding.

Only after verification, launch:

```
marimo edit --watch --no-token <filename>.py
```

## 8. Final checkpoint

Present outline before writing:

```
NOTEBOOK READY ([overview/in-depth])
---
File: [filename].py
Ontology: [A|B|C]
Cells: [N]
Charts: [chart count]
```

## 9. Iterate with the user

After first version:
- incorporate feedback
- revise/add cells
- keep ontology and chart cap constraints intact
