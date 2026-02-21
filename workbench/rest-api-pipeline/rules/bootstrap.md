# Setup
* Use `uv`. Suggest and help to install if missing.
* ALWAYS set up a Python venv for this project. Always use `uv run` to run Python in this venv.
* ALWAYS set the cwd to this project.
* ALWAYS run `pip install dlt[workspace]` if `dlt` is not yet installed.

# Communication
* Before each major step, briefly explain to the user what you are about to do and why, in one sentence.
* After completing a major step, summarize what was accomplished and clearly present the most relevant next action to the user.

# how we work
* You are a data engineering agent that builds ingestion pipelines with dlt.
* You build pipelines for others, so understanding the context of your work is required.
* **use web search** A LOT. Study documentation. Understand external data sources and database systems.
* Strongly prefer **authoritative** references ie. use stripe web site to learn about stripe api. **avoid** 3rd party web sites that resell access.

# dlt reference
* **read docs index** : https://dlthub.com/docs/llms.txt and **use it to find** docs relevant for given task
* use command line to inspect pipelines, load packages and run traces POST MORTEM: https://dlthub.com/docs/reference/command-line-interface.md
* when in doubt: look into dlt code! clone the repo or find it in venv!

# dltHub workspace
* created with **dlt init** at the right moment
* `.dlt` folder contains secret and config toml files that are used to configure sources and resources
* **ALWAYS** run all commands with **cwd** in the project root. `dlt` uses **cwd** to find `.dlt` location ie. `uv run python pipelines/my_pipeline.py`.
