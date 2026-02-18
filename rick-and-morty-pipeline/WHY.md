# WHY

Load all Rick and Morty universe data (characters, locations, episodes) into a local DuckDB for analysis and exploration. This is a reference pipeline demonstrating the full dlt recipe on a public, auth-free API.

**Goals:**
- Demonstrate dlt REST API source with pagination and incremental loading
- Provide a queryable local dataset for exploration
- Show dlt's built-in flattening of nested objects and child tables for arrays
