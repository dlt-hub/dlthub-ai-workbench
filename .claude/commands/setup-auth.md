---
name: setup-auth
description: Set up authentication credentials for a dlt pipeline source. Writes secrets to .dlt/secrets.toml once and never touches that file again.
argument-hint: <source-name>
---

# Set up authentication for a dlt pipeline

Parse `$ARGUMENTS`:
- `source-name` (required): the source or API to configure auth for (e.g., "stripe", "github")

## Steps

### 1. Determine the required credentials

Based on the source docs found during pipeline setup, identify what credential fields are needed (e.g. `api_key`, `token`, `client_secret`). Do not ask the user to provide values.

### 2. Write a placeholder to .dlt/secrets.toml

Write `.dlt/secrets.toml` with dummy placeholder values and instruct the user to fill them in:

```toml
[sources.<source_name>]
api_key = "your_api_key_here"   # Replace with your actual key
```

If `.dlt/secrets.toml` already exists, append the new section without overwriting existing entries.

Never ask the user to paste credentials into the chat. Never read or log the contents of `.dlt/secrets.toml`.

**Important:** `.dlt/secrets.toml` must be in `.gitignore`. If it isn't, add it before writing the file.

Tell the user: "Please open `.dlt/secrets.toml` and replace the placeholder value(s) with your actual credentials."

### 3. Stop — never touch secrets.toml again

Once credentials are written, do not read, modify, or reference `.dlt/secrets.toml` in any future step.
The pipeline will pick up credentials automatically from this file at runtime via `dlt.secrets.value`.