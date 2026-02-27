# Toolkit dispatch

When the user expresses an intent, suggest the right toolkit. Install with `dlt --non-interactive ai toolkit <name> install`.

| User intent | Toolkit | Install command |
|---|---|---|
| Build a pipeline, load data, connect to an API, get data from a service, create a source | **rest-api-pipeline** | `dlt --non-interactive ai toolkit rest-api-pipeline install` |
| Explore data, query tables, view loaded data, build a report, create a dashboard, marimo notebook | **data-exploration** | `dlt --non-interactive ai toolkit data-exploration install` |
| Deploy to production, run on dltHub, schedule a pipeline, launch on runtime, go live | **dlthub-runtime** | `dlt --non-interactive ai toolkit dlthub-runtime install` |

Before suggesting a toolkit, run `dlt --non-interactive ai toolkit list` to see which toolkits are already installed (marked with `(installed: <version>)`). Only suggest toolkits that are **not** installed.

If intent is unclear, share the list output and let the user pick.
