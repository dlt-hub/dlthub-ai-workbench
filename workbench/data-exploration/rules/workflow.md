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

## Entry mode detection

Classify the user's first message into one of:
- `intent_driven`: they have a specific goal — a dashboard, metric question, EDA target, hypothesis, or business question.
- `exploratory`: they want to look around and don't have a specific question yet.

Decision:
- `intent_driven` → skip the overview prompt, go straight to intent planning.
- `exploratory` → ask whether they want overview or in-depth exploration.

## Intent planning (intent mode only)

When the user has a specific goal, plan before touching the data:
1. Restate the intent concisely.
2. Identify implied entities, grain, metrics, and dimensions.
3. Ask at most 3 essential clarifications.
4. Identify candidate dlt tables (use MCP tools to list tables).
5. Produce a short plan (max 10 bullets). No code, no schema dumps.

Do not profile the full database before narrowing scope.

## Data narrowing

All downstream work follows the plan:
- List tables, pick only the ones relevant to the plan's entities/metrics/grain.
- Fetch schema only for selected tables.
- Profile only plan-relevant columns.
- Build a scoped evidence summary from these narrowed outputs.

## Evidence gathering

Collect and organize these inputs for ontology and visualization steps:
- Schema excerpts (selected tables only)
- Summary stats: row counts, cardinality, null rates, temporal ranges
- Anomaly flags
- User responses and selected exploration mode

## Ontology grounding

Generate exactly three ontology hypotheses, each mapping the schema to business concepts from a different angle:
- **A. Operational**: process/execution entities, near-real-time actionability
- **B. Dimensional**: fact/dimension framing for stable aggregation and reporting
- **C. Behavioral/Causal**: behavior patterns and plausible drivers

Compare them on coverage, join quality, metric usability, and temporal fitness. Recommend one. Present a single checkpoint for the user to confirm or override.

Ontology grounding follows https://dlthub.com/blog/ontology — model business reality first, then map schema to it.

## Visualization planning

When the user's intent is a dashboard:
1. Identify 3 core charts automatically.
2. Propose up to 5 optional charts.
3. Validate every candidate chart:
   - Matches declared grain
   - Uses valid aggregation
   - Answers the stated intent
   - Is not redundant with a higher-ranked chart
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

- Architecture decisions can take more thought; code generation should be fast.
- Mandatory marimo verification before presenting to user.
- If marimo-related issues block the flow, point user to: https://docs.marimo.io/guides/generate_with_ai/skills/

## Subagent parallelism and model routing

Use the Task tool to run independent work in parallel and route cheaper tasks to faster models. This saves time and cost across the workflow.

### Model routing principles

| Work type | Model | Why |
|---|---|---|
| Schema extraction, data profiling, code generation, formatting | `haiku` | Mechanical, well-scoped tasks that don't need deep reasoning |
| Synthesis, visualization selection, sanity validation | `sonnet` | Moderate reasoning with constrained output |
| Intent planning, ontology hypothesis generation, complex architecture | `opus` | Deep reasoning about business meaning and design tradeoffs |

### Where to parallelize

**Evidence gathering** (in `ground-ontology`): Spawn schema analysis and data profiling as two parallel haiku subagents. Both read the same scoped table list and return structured summaries.

**Ontology hypotheses** (in `ground-ontology`): Spawn three parallel opus subagents — one for Operational (A), one for Dimensional (B), one for Behavioral/Causal (C). Each receives the same evidence pack and returns an independent hypothesis. This is the biggest parallelism win in the workflow.

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
- No schema restatement or raw data dumps in conversational output.
- Present one decision point at a time, with a recommended default.
