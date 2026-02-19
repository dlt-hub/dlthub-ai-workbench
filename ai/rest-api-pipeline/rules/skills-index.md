# Skills index

Match the user's intent to a skill and invoke it. Say "I'll use the `<skill>` skill." then execute it.
If multiple skills apply, state the order and do them in sequence.

| Skill | Invoke when the user... |
|---|---|
| `find-source` | asks what connector or source to use, mentions a data provider by name |
| `create-pipeline` | wants to build a new pipeline, has a `dlt init` command ready |
| `debug-pipeline` | has an error, pipeline is failing, wants to run the pipeline for the first time |
| `validate-data` | wants to check loaded data, inspect schema, fix types or nested structures |
| `add-endpoint` | wants more data from the same API, mentions a new endpoint or resource |
| `adjust-endpoint` | wants to remove limits, load more data, fix pagination, set up incremental loading |
| `view-data` | asks to query data, explore tables, check row counts, "show me the data", "how many X", "what are the Y", "which Z", or any question about the contents of loaded data — **always use this skill, never write inline queries** |
| `create-report` | wants a dashboard, charts, visualizations, or a marimo notebook |