# dltHub AI Workbench

**dlt** (data load tool) is an open-source Python library for loading data from APIs and databases into a warehouse or lakehouse. **dltHub** (paid platform) extends dlt with enterprise-grade features: transformations, data quality validation, managed runtime infrastructure, managed data apps, and an AI-powered workspace environment.

The **dltHub AI Workbench** is a collection of toolkits that give AI coding assistants the knowledge and step-by-step workflows to build data pipelines with dlt. Each toolkit covers a specific phase of the data engineering lifecycle — ingesting from a REST API, exploring loaded data, or deploying to dltHub — and guides the assistant through it in a fixed sequence rather than leaving it to improvise. You can use the workbench as-is or fork and customize it for your own stack.

The dltHub AI Workbench is tested with **Claude Code**, **Cursor**, **Codex**, and **Copilot** and may work with other AI coding assistants. We recommend starting in accept edits mode to review the scaffolded pipeline code when getting started with the dlthub AI workbench.

---

## The dlthub AI workbench supports the iterative data engineering workflow

Building a data pipeline is iterative. You start by developing and debugging a pipeline locally, explore the loaded data to validate it, then loop back to refine — and when it's ready, you deploy it and build data apps on top. The workbench toolkits map directly onto these phases.

![Data Development Lifecycle](images/data_development_lifecycle.png)

---

## The AI Workbench

The workbench gives your coding assistant **toolkits** — each one a structured, guided workflow for a specific phase. Instead of generating ad-hoc code, the assistant follows a fixed sequence of steps from start to finish. 

A **Toolkit** contains skills, commands, rules, and an MCP server — tied together by a **workflow** that tells the assistant which skill to run at each step. All toolkits depend on **`init`** for shared rules, secrets handling, and the MCP server. When using the `dlt ai` CLI, `init` is installed automatically as a dependency. When using the Claude marketplace, install the `init` plugin separately.

![AI Workbench](images/ai_workbench.png)

### Workbench components

| Component | What it is | When it runs |
|-----------|-----------|-------------|
| **Skill** | Step-by-step procedure the assistant follows | Triggered by user intent or explicitly with `/skill-name` |
| **Command** | A slash command for a specific action | User invokes with `/toolkit:command` |
| **Rule** | Always-on context (conventions, constraints) | Every session, automatically |
| **Workflow** | Ordered sequence of skills with a fixed entry point | Loaded as a rule — always active |
| **MCP server** | Exposes pipelines, tables, and secrets as tools | During a session, via MCP protocol |

---

### Available toolkits

| Toolkit | Phase | Workflow entry | What it does | Example prompts |
|---------|-------|---------------|-------------|---------------|
| `bootstrap` | Setup | `/init-workspace` | Cold-start when you have no Python environment yet | *"Set up a Python environment with dlt"* |
| `rest-api-pipeline` | Build | `find-source` | Scaffold, debug, and validate REST API ingestion pipelines | *"Load data from the Stripe API into DuckDB"* |
| `dlthub-runtime` | Run | `setup-runtime` | Deploy pipelines to the dltHub platform | *"Deploy my pipeline to dltHub"*, *"Launch my notebook to the dltHub runtime"* |
| `data-exploration` | Explore | `explore-data` | Query loaded data and create marimo dashboards | *"Show me what's in the orders table"*, *"Visualize revenue by month as a bar chart"* |

> `init` is a shared dependency that provides rules, secrets handling, and the MCP server. It is installed automatically by `dlt ai init` or as a separate plugin via the Claude marketplace.

---

## Getting started

> **No Python environment yet?** Install `bootstrap` first and run `/init-workspace` — the assistant sets up `uv`, Python, and `dlt` for you.

### Claude Code

Add the workbench via the Claude marketplace — no terminal setup required:

1. Start a Claude Code session in your terminal:
   ```bash
   claude
   ```

2. Inside the Claude session, add the marketplace:
   ```
   /plugin marketplace add dlt-hub/dlthub-ai-workbench
   ```

3. Install the **`init`** plugin first — it provides shared rules, secrets handling, and the MCP server config:
   ```
   /plugin install init@dlthub-ai-workbench --scope project
   ```

4. Install the toolkits you want to use (if you are not sure which one to install we recommend installing all of them):
   ```
   /plugin install bootstrap@dlthub-ai-workbench --scope project
   /plugin install rest-api-pipeline@dlthub-ai-workbench --scope project
   /plugin install dlthub-runtime@dlthub-ai-workbench --scope project
   /plugin install data-exploration@dlthub-ai-workbench --scope project
   ```

5. Start a new session — plugins take effect only after restarting Claude Code:
   ```bash
   claude
   ```

For the MCP server to run, `uv` and `dlt` must be installed on your machine. If you don't have them yet, install `bootstrap` first and run `/init-workspace` before starting a new session.

> **Resuming a session?** Plugins installed mid-session are not active until you start a new one. Previous sessions can be resumed, but the new toolkit skills will only be available in sessions started after installation.


### Cursor, Codex, Copilot — via `dlt ai` CLI

```bash
# Install uv (fast Python package manager) if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dlt with workspace support
uv pip install --upgrade "dlt[workspace]"

# Set up your workspace (auto-detects your coding assistant)
dlt ai init

`dlt ai init` detects your coding assistant from environment variables and config files, then installs skills, rules, and the MCP server in the correct locations for that tool.

# Browse and install toolkits (if you are not sure which toolkits to install we recommend installing all of them):
dlt ai toolkit list

dlt ai toolkit rest-api-pipeline install
dlt ai toolkit rest-api-pipeline install
dlt ai toolkit dlthub-runtime install
dlt ai toolkit data-exploration install
```

---

## The `dlt ai` CLI

The `dlt ai` subcommand is the bridge between the workbench and your coding assistant. It handles two things: installing toolkit components into the right locations for your assistant, and running the MCP server that the assistant uses during a session.

**Toolkit management** — copies skills, rules, commands, and MCP config from the workbench into your project's agent config directory (`.claude/`, `.cursor/`, `.agents/`, etc.):

```bash
dlt ai status                        # show installed agent, dlt version, active toolkits
dlt ai toolkit list                  # list available toolkits from the workbench
dlt ai toolkit <name> info           # show a toolkit's skills, commands, and workflow
dlt ai toolkit <name> install        # install a toolkit for the detected agent
dlt ai toolkit <name> install --agent cursor   # override agent detection
```

**Secrets management** — dlt stores credentials in TOML files; these commands let the assistant inspect and update them without reading raw secret values:

```bash
dlt ai secrets list                  # show which secret files exist and where
dlt ai secrets view-redacted         # print secrets with values masked
dlt ai secrets update-fragment --path <file> '<toml>'  # merge a TOML snippet into a secrets file
```

**MCP server** — starts a local server that exposes your dlt workspace (pipelines, schemas, tables, secrets) as tools the assistant can call:

```bash
dlt ai mcp run                       # run in SSE mode (default)
dlt ai mcp run --stdio               # run in stdio mode (for assistants that require it)
dlt ai mcp install                   # register the MCP server in the agent's config
```

The MCP server is what allows the assistant to answer questions like "what tables were loaded?" or "show me the last pipeline trace" without you having to copy-paste output into the chat.

---

## License

TO BE UPDATED
