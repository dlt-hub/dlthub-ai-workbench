---
name: setup-secrets
description: Use to access and modify *.secrets.toml in SAFE way. Use when need to set up, check, verify, debug, or read dlt secrets (API keys, database credentials). Also use when writing Python code that needs credentials.
argument-hint: "[source-name]"
---

# Set up dlt secrets

**Essential Reading** Credentials & config resolution: `https://dlthub.com/docs/general-usage/credentials/setup.md` `https://dlthub.com/docs/general-usage/credentials/advanced`

Configure credentials in `.dlt/secrets.toml`. **Never read secrets files directly** — use only `dlt ai secrets` CLI commands.

**Read additional docs as needed:**
- Connection string credentials (databases, warehouses): `https://dlthub.com/docs/general-usage/credentials/complex_types.md`
- Built-in credential types (`GcpServiceAccountCredentials`, `AwsCredentials`, etc.): `https://dlthub.com/docs/general-usage/credentials/complex_types.md#built-in-credentials`
- Destination-specific credentials: `https://dlthub.com/docs/dlt-ecosystem/destinations/`

Parse `$ARGUMENTS`:
- `source_name` or description of what credentials are needed (e.g. "stripe api key", "postgres credentials")

## 1. Figure out what to configure

If called from another skill, you already know the source, destination, and which fields are needed — skip to step 3.

If called standalone (e.g. user says "set up secrets" or hit `ConfigFieldMissingException`):
- Read the exception message — it tells you the exact field name and TOML path
- Read the pipeline script to find `dlt.secrets.value` parameters on `@dlt.source`/`@dlt.resource` functions
- Identify the destination type for required credentials

## 2. Find the right secrets file and inspect its shape

```
dlt ai secrets list
```

Lists workspace-scoped secrets files. Profile-scoped files (e.g. `.dlt/dev.secrets.toml`) appear first — **use those when present**, fall back to `.dlt/secrets.toml` otherwise.

**Pick the target file** from the list — you will pass it as `--path` to `update-fragment` in step 4.

Then inspect the current content:

```
dlt ai secrets view-redacted
```

Shows the **unified merged** view of all workspace secret files with values replaced by `***`. Use it to see:
- Which sections already exist (`[sources.<name>]`, `[destination.<name>]`)
- Which fields have real values (stars) vs placeholders (`<configure me>`)
- Whether the layout matches what the pipeline expects

To inspect a specific file instead (profile and workspace scoped):
```
dlt ai secrets view-redacted --path .dlt/<profile>.secrets.toml
dlt ai secrets view-redacted --path .dlt/secrets.toml
```

Skip this step if you already know the secrets file is empty or doesn't exist.

## 3. Research credentials

Before asking the user for values:
- **Web search** the data source for how credentials are obtained (API docs, developer portal)
- Tell the user exactly what they need and where to get it (e.g. "Go to https://dashboard.stripe.com/apikeys")
- Explain what each credential field is for

## 4. Write secrets with `update-fragment`

`dlt ai secrets update-fragment --path <file>` merges a TOML fragment into the given secrets file. It creates the file if needed, deep-merges without overwriting other sections, and prints the redacted result.

**`--path` is required** — use the target file you picked in step 2.

### Layout rules

**Always** scope secrets under the source or destination name:

```toml
[sources.<source_name>]
api_key = "<paste-your-api-key-here>"

[destination.<destination_name>.credentials]
host = "localhost"
port = 5432
database = "analytics"
username = "loader"
password = "<paste-your-password-here>"
```

`<source_name>` = `name=` arg on `@dlt.source`, or the function name if not set.

### Placeholders

Use **meaningful placeholders** that hint at the format:
- API keys: `"sk-*****-your-key"` or `"ak-xxxx-xxxx-xxxx"`
- Tokens: `"ghp_xxxxxxxxxxxxxxxxxxxx"` (GitHub), `"xoxb-xxxx"` (Slack)
- Passwords: `"<paste-your-password-here>"`
- URLs: `"https://your-instance.example.com"`

**Never** use the generic `"<configure me>"`.

### Examples (Linux / macOS)

Use multiline single-quoted strings — all POSIX shells (bash, zsh, sh, dash, fish) pass real newlines:

```sh
dlt ai secrets update-fragment --path .dlt/secrets.toml '[sources.stripe]
api_key = "sk-test-xxxxxxxxxxxx"
'
```

```sh
dlt ai secrets update-fragment --path .dlt/secrets.toml '[destination.postgres.credentials]
host = "localhost"
port = 5432
database = "analytics"
username = "loader"
password = "<paste-your-password-here>"
'
```

Profile-scoped:
```sh
dlt ai secrets update-fragment --path .dlt/<profile>.secrets.toml '[sources.my_api]
api_key = "sk-xxxxxxxxxxxx"
'
```

### Examples (Windows)

Use `\n` for newlines in a single-line string. The CLI converts literal `\n` to real newlines before parsing:

```
dlt ai secrets update-fragment --path .dlt/secrets.toml "[sources.stripe]\napi_key = \"sk-test-xxxxxxxxxxxx\""
```

```
dlt ai secrets update-fragment --path .dlt/secrets.toml "[destination.postgres.credentials]\nhost = \"localhost\"\nport = 5432\ndatabase = \"analytics\"\nusername = \"loader\"\npassword = \"<paste-your-password-here>\""
```

## 5. Verify

```
dlt ai secrets view-redacted
```

Shows the unified merged view across all workspace secret files. Tell the user which fields still have placeholders and how to obtain real values.


## 6. Use secrets in Python
You can write Python scripts that read and use secrets without ever revealing them. `dlt.secrets` and `dlt.config` work as dictionaries using the same TOML paths shown by `view-redacted`.

Example: you need to call the GitHub REST API and `view-redacted` shows `[sources.github] api_key = "***"`:
```py
import dlt
import requests

# reads from secrets.toml [sources.github] api_key — never prints the value
api_key = dlt.secrets["sources.github.api_key"]
resp = requests.get(
    "https://api.github.com/user",
    headers={"Authorization": f"Bearer {api_key}"},
)
print(resp.json()["login"])
```

You can also retrieve typed credentials:
```py
from dlt.sources.credentials import GcpServiceAccountCredentials

creds = dlt.secrets.get("destination.bigquery.credentials", GcpServiceAccountCredentials)
```

**Reference**: https://dlthub.com/docs/general-usage/credentials/advanced.md#access-configs-and-secrets-in-code
