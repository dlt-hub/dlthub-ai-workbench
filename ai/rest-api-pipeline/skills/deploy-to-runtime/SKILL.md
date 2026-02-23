---
name: deploy-to-runtime
description: Deploys dlt pipelines to dlt Hub Runtime. Use when the user says "deploy to runtime", "launch on runtime", "run on dlt Hub", or "schedule pipeline".
---

# Deploy to dlt Hub Runtime

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

## Important

- Scripts must have `if __name__ == "__main__":` or the job does nothing.
- Runtime installs from `pyproject.toml` — add all needed packages (e.g. `uv add numpy pandas` if using `.df()`).
- Jobs are killed after 120 minutes. Use incremental loads for long pipelines.
- One workspace per GitHub account — connecting a new repo replaces existing deployments.

## Troubleshooting

**Missing dependencies on Runtime**: Ensure all packages are in `pyproject.toml`, not just locally installed.
