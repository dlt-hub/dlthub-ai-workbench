# dlt AI Dev Kit

When the user asks to create, build, or write a data pipeline for any source or API,
follow the `/write-pipeline` skill defined in `.claude/commands/write-pipeline.md`.

When the source requires authentication, follow the `/setup-auth` skill defined in `.claude/commands/setup-auth.md`.

When the user asks to view, explore, or inspect loaded pipeline data,
follow the `/view-data` skill defined in `.claude/commands/view-data.md`.

**NEVER ask the user to paste or type an API key, token, or any credential into the chat. Ever.**
Always write a placeholder to `.dlt/secrets.toml` and tell the user to fill it in themselves.