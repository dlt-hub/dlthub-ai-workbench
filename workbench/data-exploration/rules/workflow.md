# Data exploration workflow

## Orchestration flow

```
[Entry Mode Detection]
  -> intent-driven -> [Intent Planning] -> [Scoped Data Narrowing]
  -> exploratory   -> [Overview/In-Depth Selection]
  -> [Evidence Gathering: schema + profiling + ontology hypotheses]
  -> [Synthesis + Ontology Selection]
  -> [Visualization Planning + Sanity Check]
  -> [Notebook Generation + Mandatory marimo Verification]
```

## Tone of voice

Be direct, specific, and practical. Talk about tables, columns, row counts, and chart types — not frameworks, paradigms, or abstractions.

Do:
- "This table has 12k rows with a `created_at` column — good candidate for a time series."
- "I'll group by `status` and count orders."
- "Pick which grouping makes sense for your use case."

Don't:
- "Let's explore the dimensional ontological framing of your data model."
- "This enables near-real-time actionability across process entities."
- "We'll synthesize evidence into a coherent analytical narrative."

Rules:
- Name specific tables, columns, and values when explaining choices.
- State what you'll do, then do it. Skip preamble.
- When presenting options, describe each in terms of what the user will see (e.g., "a bar chart of orders by status") not what it represents conceptually.
- If a technical term is needed (grain, cardinality, dimension), use it once and show a concrete example immediately.

## User interaction: always use toggle options

Every time the workflow requires user input, use `AskUserQuestion` with concrete selectable options. Never ask open-ended text questions when a set of choices can be offered. Users should toggle between options, not type free-form answers.

Rules:
- Present 2–4 options per question, each with a short label and description.
- Put the recommended option first and append "(Recommended)" to its label.
- Use `multiSelect: true` only when choices are not mutually exclusive.
- The user can always select "Other" (built-in) if none of the options fit.
- Batch related decisions into a single `AskUserQuestion` call (up to 4 questions).

## Entry mode detection

Classify the user's first message into one of:
- `intent_driven`: they have a specific goal — a dashboard, metric question, EDA target, hypothesis, or business question.
- `exploratory`: they want to look around and don't have a specific question yet.

Decision:
- `intent_driven` → skip the overview prompt, go straight to intent planning.
- `exploratory` → use `AskUserQuestion` to let the user toggle between "Overview" and "In-Depth" exploration modes.

## Intent planning (intent mode only)

When the user has a specific goal, plan before touching the data:
1. Say back what they want in one sentence.
2. List the tables, columns, and aggregations you'll need.
3. If clarifications are needed, use `AskUserQuestion` with toggle options (max 3 questions, each with 2–4 selectable choices). Do not ask open-ended questions.
4. List candidate dlt tables (use MCP tools).
5. Write a short plan (max 10 bullets) with specific table and column names. No code, no schema dumps.

Do not profile the full database before narrowing scope.

## Data narrowing

All downstream work follows the plan:
- List tables, pick only the ones relevant to the plan's entities/metrics/grain.
- Fetch schema only for selected tables.
- Profile only plan-relevant columns.
- Build a scoped evidence summary from these narrowed outputs.

## Evidence gathering

Collect these concrete facts for the next steps:
- Column names and types for selected tables
- Row counts, number of distinct values per key column, null percentages, date ranges
- Anything unexpected (e.g., a column that's 90% null, IDs that aren't unique)
- What the user chose in previous toggle questions

## Ontology grounding

Generate three ways to read the data, each focusing on different questions:
- **A. Operational**: What's happening right now? Track events, statuses, and pipeline runs. Example: "orders table as the main event stream, status column for funnel stages."
- **B. Analytical**: What are the numbers? Pick fact tables and group-by columns for rollups. Example: "`orders` as fact, `product_id` and `region` as dimensions, `amount` as the metric."
- **C. Behavioral**: What drives outcomes? Link actions to results. Example: "Do users who trigger event X convert at higher rates?"

Compare on: how many tables each covers, whether joins work cleanly, whether you can actually compute the metrics, and whether timestamps support the needed time ranges. Recommend one. Present the choice via `AskUserQuestion` with the three options as toggles (recommended first), so the user can select one rather than typing a response.

Reference: https://dlthub.com/blog/ontology — start from what the business cares about, then map tables to it.

## Visualization planning

When the user's intent is a dashboard:
1. Identify 3 core charts automatically.
2. Propose up to 5 optional charts.
3. Validate every candidate chart:
   - The group-by columns match the level of detail the user asked for
   - The aggregation (sum, count, avg) is correct for the column type
   - It answers the user's actual question
   - It doesn't show the same thing as another chart already in the list
4. Recommend top 3 only.

Caps:
- Overview: up to 5 charts
- In-depth: up to 10 charts

## EDA policy

If the user asks for EDA:
- Stay scoped to the intent (don't profile everything).
- Include: null rate, distribution, cardinality, time distribution (if applicable).
- Exclude irrelevant columns/tables.

## Notebook generation

- Deciding what goes in the notebook can take time; writing the cells should be fast.
- Mandatory marimo verification before presenting to user.
- If marimo-related issues block the flow, point user to: https://docs.marimo.io/guides/generate_with_ai/skills/

## Subagent parallelism and model routing

Use the Task tool to run independent work in parallel and route cheaper tasks to faster models. This saves time and cost across the workflow.

### Model routing principles

| Work type | Model | Why |
|---|---|---|
| Schema extraction, data profiling, code generation, formatting | `haiku` | Routine tasks with clear inputs and outputs |
| Picking charts, checking results, combining summaries | `sonnet` | Needs judgment but within a narrow scope |
| Understanding what the user wants, choosing how to read the data, notebook architecture | `opus` | Needs to weigh tradeoffs and make design calls |

### Where to parallelize

**Evidence gathering** (in `ground-ontology`): Spawn schema analysis and data profiling as two parallel haiku subagents. Both read the same scoped table list and return structured summaries.

**Data reading options** (in `ground-ontology`): Spawn three parallel opus subagents — one for Operational (A), one for Analytical (B), one for Behavioral (C). Each gets the same table/column summary and returns its proposed mapping. Biggest parallelism win in the workflow.

**Chart cell generation** (in `create-marimo-report`): After the notebook architecture is decided, spawn haiku subagents to generate individual chart cells in parallel. Each gets the chart spec from the viz plan.

### Rules for subagents

- Always launch independent subagents in the **same message** so they run concurrently.
- Each subagent gets a self-contained prompt with all context it needs — it has no access to conversation history.
- Never spawn recursive subagents (a subagent should not spawn its own subagents).
- If a subagent fails, its failure is isolated — use the remaining results and note the gap.

## Workflow routing

| Step | Skill |
|---|---|
| Data access and profiling | `explore-data` |
| Ontology mapping | `ground-ontology` |
| Chart planning | `plan-visualizations` |
| Notebook creation | `create-marimo-report` |

Paths:
- **Overview** → `explore-data` → `ground-ontology --mode overview` → `plan-visualizations --mode overview` → `create-marimo-report --mode overview`
- **In-Depth** → `explore-data` → `ground-ontology --mode in-depth` → `plan-visualizations --mode in-depth` → `create-marimo-report --mode in-depth`
- **Standalone** → `create-marimo-report` directly (skips ontology + viz planning)

## Conciseness constraints

- Planner output: max 10 bullets.
- Summaries: max 6 bullets per phase.
- Don't paste schemas or raw data into chat — summarize what matters.
- One decision at a time, with a recommended default, using `AskUserQuestion` toggle options.
