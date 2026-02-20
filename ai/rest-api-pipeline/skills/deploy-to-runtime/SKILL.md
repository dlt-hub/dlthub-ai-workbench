---
name: deploy-to-runtime
description: Use when the user says "deploy to runtime", "launch on runtime", or "run on dlt Hub". Deploys dlt pipelines to dlt Hub Runtime — covers setup, authentication, profiles (prod/access), configuration sync, job scheduling, and monitoring.
---

# dlt Hub Runtime Deployment

## Prerequisites

- Workspace mode enabled:
  ```bash
  uv add "dlt[workspace]" dlt-runtime==0.21.1
  touch .dlt/.workspace   # enables `dlt runtime` CLI commands
  ```
- Always use `uv` — run all Python commands as `uv run python` and install packages with `uv add`
- GitHub account (OAuth login)
- **One workspace per GitHub account** — connecting a new repository replaces existing deployments.

## Workflow

1. Copy local credentials into `.dlt/prod.secrets.toml` — **IMPORTANT:** TOML does not allow duplicate section headers. If `[runtime]` already exists, merge keys into it rather than adding a second `[runtime]` block. Duplicate keys cause a silent parse error that fails at deploy time.
2. `dlt runtime login` — GitHub OAuth
3. `dlt runtime deploy` — syncs code + config to Runtime
4. `dlt runtime launch <script.py>` — test run
5. `dlt runtime schedule <script.py> "0 6 * * *"` — schedule (optional)
6. `dlt runtime logs <script.py>` — monitor

## Profiles

Runtime uses profiles to separate config for different contexts:

| Profile | Files | Use case |
|---------|-------|----------|
| `prod` | `prod.config.toml` / `prod.secrets.toml` | Batch jobs, scheduled pipelines |
| `access` | `access.config.toml` / `access.secrets.toml` | Interactive notebooks |
| *(default)* | `config.toml` / `secrets.toml` | Local dev only |

> All `*.secrets.toml` are gitignored. Use `dlt runtime configuration sync` to upload secrets without committing them.

## Commands

```bash
# Auth
dlt runtime login
dlt runtime logout

# Deploy
dlt runtime deploy                         # sync code + config
dlt runtime deployment sync               # code only
dlt runtime configuration sync           # secrets/config only

# Run
dlt runtime launch my_pipeline.py         # immediate batch run
dlt runtime serve my_notebook.py          # interactive session
dlt runtime schedule my_pipeline.py "0 6 * * *"
dlt runtime schedule my_pipeline.py cancel

# Monitor
dlt runtime logs my_pipeline.py           # latest run
dlt runtime logs my_pipeline.py 3         # specific run number
dlt runtime job-run logs my_pipeline.py --follow
dlt runtime cancel my_pipeline.py
dlt runtime dashboard
```

> Jobs are killed after 120 minutes. Split long pipelines into incremental loads.

> **`launch` requirement**: scripts run as `python <script.py>` — they must have an `if __name__ == "__main__":` entry point or the job will do nothing. Verify before launching.

> **Dependencies on Runtime**: Runtime installs from your project's `pyproject.toml`. If your pipeline script calls `.df()` (e.g., in quality checks), ensure `numpy` and `pandas` are in your dependencies (`uv add numpy pandas`).
