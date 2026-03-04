# Data exploration workflow

## Flow

```
connect-and-profile → [dashboard type selection] → (dlt dashboard | analyze-questions → marimo-notebook → launch notebook)
```

The user has dlt pipeline data and business questions. This toolkit connects to the data, then offers a choice between the built-in dlt Workspace Dashboard and a custom Marimo notebook.

## Dashboard type selection (MANDATORY before chart planning)

After `connect-and-profile` completes, **always** present this choice using `AskUserQuestion`:

```
question: "What kind of dashboard do you want?"
options:
  - label: "Quick dashboard (Recommended for first look)"
    description: "Opens the built-in dlt Workspace Dashboard in the browser — table schemas, row counts, sample data. Ready instantly."
  - label: "Custom notebook"
    description: "Full interview → ontology → chart planning → Marimo notebook. More powerful, takes longer."
```

- **Quick dashboard**: run `dlt pipeline <pipeline_name> show` and stop. Do not proceed to `analyze-questions`.
- **Custom notebook**: continue with `analyze-questions` → `marimo-notebook` → launch.

This routing applies whenever the user asks for a "dashboard", "visualization", "report", or wants to "see the data" — not only when they say "dlt dashboard" by exact phrase.

## User interaction: always use toggle options

Every time the workflow requires user input, use `AskUserQuestion` with concrete selectable options. Never ask open-ended text questions when a set of choices can be offered.

Rules:
- Present 2–4 options per question, each with a short label and description.
- Put the recommended option first and append "(Recommended)" to its label.
- Use `multiSelect: true` only when choices are not mutually exclusive.
- The user can always select "Other" (built-in) if none of the options fit.
- Batch related decisions into a single `AskUserQuestion` call (up to 4 questions).

## Pipeline discovery

Before any analysis, use dlt MCP tools as the primary discovery path:
1. `list_pipelines` — discover available pipelines.
2. `list_tables` — enumerate tables and row counts.
3. `get_table_schemas` — fetch column info for relevant tables.

If MCP tools are unavailable, fall back to Python: `dlt.attach()` first, then `dlt.pipeline(..., destination=dlt.destinations.duckdb(path))`. Verify with `dataset.row_counts().df()`.

Do not skip this step when the pipeline target is unclear.

## Build/test row-cap policy

Default to **1,000 rows per query output** during development and notebook iteration:
- Prefer deterministic ordering before capping (`order_by` on timestamp or stable key), then `limit(1000)`.
- Keep cap active through notebook generation.
- Only remove when the user explicitly requests full-load results.

At notebook delivery, ask one toggle:
- `Remove 1,000-row cap (Recommended for final output)` — regenerate without cap
- `Keep 1,000-row cap` — keep development-safe limits

## Data access priority

1. **Relation methods first** — simpler, destination-agnostic
2. **Escalate to ibis** for joins, group-by, computed columns
3. **Raw SQL** as a last resort
4. **Never** import destination libraries directly
5. **Never** use pandas as the query layer — materialize to pandas only at the display boundary

Full API reference: `dlt-relation-api` rule.

## Skill routing

| Step | Skill | What happens |
|---|---|---|
| Connect + profile | `connect-and-profile` | Pipeline discovery, schema/stats gathering, anomaly flags |
| Dashboard routing | (workflow step) | Offer quick dlt dashboard vs custom Marimo notebook |
| *Quick path* | (workflow step) | `dlt pipeline <name> show` — done |
| *Custom path:* Ontology + charts | `analyze-questions` | 5-step interview, ontology file, chart specs, sanity checks |
| *Custom path:* Notebook generation | `marimo-notebook` (external) | Generates marimo notebook from requirements summary |
| *Custom path:* Launch notebook | (workflow step) | Offer to launch the generated notebook in browser |

Routing is mandatory: invoke the corresponding skill via the Skill tool at each step.

### marimo-notebook dependency check (HARD GATE)

Before handing off to notebook generation, verify the `marimo-notebook` skill is installed. Check for `.claude/skills/marimo-notebook/SKILL.md` or `~/.claude/skills/marimo-notebook/SKILL.md`.

**If not installed: STOP.** Do not generate notebook code. Do not write marimo cells inline. Tell the user:

```
The "marimo-notebook" skill is required for notebook generation.
Install it:

npx skills add marimo-team/skills
```

Then wait. Only proceed after the user confirms the skill is installed.

### Launch notebook after generation

After the `marimo-notebook` skill completes and a notebook file exists, present a toggle:

```
question: "Notebook generated. Launch it now?"
options:
  - label: "Launch now (Recommended)"
    description: "Opens the notebook in the browser at localhost:2718"
  - label: "Skip — launch manually later"
    description: "Notebook saved to <file>.py, launch later with: uv run marimo edit <file>.py"
```

If "Launch now": run `uv run marimo edit <notebook_file>.py --headless --no-token` in background. Tell the user the URL.

## Self-check

After each skill completes, verify its documented output requirements are met before proceeding. If any requirement is unmet, fix it before moving on.

Critical invariants across all steps:
- Connection uses `dlt.attach()` or explicit destination — never raw `duckdb` imports
- Row cap (1,000) is active on all queries unless the user opted out
- All user decisions use `AskUserQuestion` with toggle options — no open-ended text questions
- The `marimo-notebook` skill existence is verified before any notebook generation
- No notebook code is generated without the `marimo-notebook` skill installed
- After notebook generation, the launch prompt was presented

## Conciseness constraints

- Planner output: max 10 bullets.
- Summaries: max 6 bullets per phase.
- Summarize schemas and data — do not paste raw output into chat.
- One decision at a time, with a recommended default, using `AskUserQuestion` toggle options.
