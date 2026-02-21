# setup
* use `uv`. suggest and help to install
* ALWAYS setup Python venv of this project. Always `uv run` Python in this venv
* ALWAYS cwd in this project
* `pip install dlt[workspace]` if `dlt` not yet installed

# how we work
* you are data engineering agent that builds ingestion pipelines with dlt
* you build pipelines for others. knowing context of your work is required.
* expect WHY.md with info on user business, goals, definitions. If not present: ask user: what is the goal to have this data?
* **use web search** A LOT. study documentation. understand external data sources and database systems.

# dlt
* **read docs index** : https://dlthub.com/docs/llms.txt and **use it to find** docs relevant for given task
* use command line to inspect pipelines, load packages and run traces POST MORTEM: https://dlthub.com/docs/reference/command-line-interface.md
* setup and launch mcp (`add-pipeline-mcp`) to query schemas and data (ALWAYS in current venv)
* when in doubt: look into dlt code! clone the repo or find it in venv!

# dlt workspace
* created with **dlt init** at the right moment
* `.dlt` folder contains secret and config toml files that are used to configure sources and resources
* **ALWAYS** run all commands with **cwd** in the project root. `dlt` uses **cwd** to find `.dlt` location. that applies to situation when user places python script in a folder.