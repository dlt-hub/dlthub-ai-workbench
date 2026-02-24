---
name: deploy-to-runtime
description: Deploys dlt pipelines to dlt Hub Runtime. Use when the user says "deploy to runtime", "launch on runtime", "run on dlt Hub", or "schedule pipeline".
---

# Deploy to dlt Hub Runtime

Deploy a dlt pipeline to [dlt Hub Runtime](https://dlthub.com/docs/walkthroughs/deploy-a-pipeline/deploy-with-dlt-runtime) for remote execution and scheduling.

## Step 1: Install dependencies

Verify `pyproject.toml` exists in the project root. If not, run `uv init` first. Runtime uses it to install dependencies remotely.

```bash
uv add "dlt[workspace]" dlt-runtime==0.21.1
touch .dlt/.workspace
```

## Step 2: Verify `.dlt/` config structure

Run `ls .dlt/*.toml` and ensure these files exist:

```
.dlt/
├── config.toml           # Local dev config
├── secrets.toml          # Local dev secrets (gitignored)
├── prod.config.toml      # Production config
├── prod.secrets.toml     # Production secrets (gitignored)
├── access.config.toml    # Interactive notebook config
└── access.secrets.toml   # Interactive notebook secrets (gitignored)
```

Create missing profile files by copying from defaults:
- `cp .dlt/config.toml .dlt/prod.config.toml`
- `cp .dlt/secrets.toml .dlt/prod.secrets.toml`

## Step 3: Set up production credentials

Copy credentials into `.dlt/prod.secrets.toml`.

Ask the user to fill in the secrets file with production credentials.

## Step 4: Login, deploy, launch

```bash
dlt runtime login                              # GitHub OAuth
dlt runtime deploy                             # sync code + config
dlt runtime launch my_pipeline.py              # test run
dlt runtime schedule my_pipeline.py "0 6 * * *"  # optional cron
dlt runtime logs my_pipeline.py                # check output
```

Replace `my_pipeline.py` with the actual pipeline script name found in the project.

## Important

- Scripts must have `if __name__ == "__main__":` or the job does nothing.
- Runtime installs from `pyproject.toml` — add all needed packages (e.g. `uv add numpy pandas` if using `.df()`).
- Jobs are killed after 120 minutes. Use incremental loads for long pipelines.
- One workspace per GitHub account — connecting a new repo replaces existing deployments.

## Troubleshooting

**Missing dependencies on Runtime**: Ensure all packages are in `pyproject.toml`, not just locally installed.

**Job does nothing**: Check that the script has `if __name__ == "__main__":` guard.

**Logs show errors**: Run `dlt runtime logs <script>` to inspect. Common issues: missing secrets in `prod.secrets.toml`, missing packages in `pyproject.toml`.

## Command reference

For the full CLI reference with all arguments and options, run:
```bash
dlt render-docs runtime-cli.md --commands runtime
```

This generates an authoritative markdown reference from the installed `dlt` + `dlt-runtime` argparse definitions. Use it when you need exact flag names, positional argument order, or subcommand details beyond the quick-reference below.

### Quick reference

| Command | Description |
|---------|-------------|
| `dlt runtime login` | Authenticate via GitHub OAuth |
| `dlt runtime logout` | Clear local credentials |
| `dlt runtime info` | Show workspace overview |
| `dlt runtime dashboard` | Open web dashboard |
| `dlt runtime deploy` | Sync code and config (no execution) |
| `dlt runtime launch <script> [-d]` | Deploy and run batch job (`-d` to detach) |
| `dlt runtime serve <script> [--app-type {marimo,mcp,streamlit}]` | Deploy and start interactive notebook/app |
| `dlt runtime publish <script> [--cancel]` | Generate or revoke a public link for a notebook/app |
| `dlt runtime schedule <script> <cron\|cancel> [--current]` | Schedule job with cron or cancel it |
| `dlt runtime logs <script> [run_number]` | View execution logs |
| `dlt runtime cancel <script> [run_number]` | Stop a running job |
| `dlt runtime job list` | List all jobs |
| `dlt runtime job create <script>` | Register job without running |
| `dlt runtime job-run list` | List all runs |
| `dlt runtime job-run create <script>` | Execute a new run |
| `dlt runtime job-run logs <script> [run_number]` | Show logs (follows if still running) |
| `dlt runtime job-run cancel <script> [run_number]` | Cancel a run |
| `dlt runtime deployment sync` | Sync code files only |
| `dlt runtime deployment list` | List all deployments |
| `dlt runtime deployment info` | Show deployment details |
| `dlt runtime configuration sync` | Upload secrets/config to Runtime |
| `dlt runtime configuration list` | List configuration versions |
| `dlt runtime configuration info` | Show configuration details |
