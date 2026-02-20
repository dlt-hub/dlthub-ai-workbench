# dlt Hub Runtime — Command Reference

| Command | Description |
|---------|-------------|
| `dlt runtime login` | Authenticate via GitHub OAuth |
| `dlt runtime logout` | Clear local credentials |
| `dlt runtime info` | Show workspace overview |
| `dlt runtime dashboard` | Open web dashboard |
| `dlt runtime deploy` | Sync code and config (no execution) |
| `dlt runtime launch <script>` | Deploy and run batch job immediately |
| `dlt runtime serve <script>` | Deploy and start interactive notebook |
| `dlt runtime schedule <script> "<cron>"` | Schedule job with cron expression |
| `dlt runtime schedule <script> cancel` | Remove schedule |
| `dlt runtime logs <script> [run_number]` | View execution logs |
| `dlt runtime cancel <script> [run_number]` | Stop a running job |
| `dlt runtime job list` | List all jobs |
| `dlt runtime job create <script>` | Register job without running |
| `dlt runtime job-run list` | List all runs |
| `dlt runtime job-run create <script>` | Execute a new run |
| `dlt runtime job-run logs <script> [-f]` | Tail logs (optionally follow) |
| `dlt runtime job-run cancel <script>` | Cancel a run |
| `dlt runtime deployment sync` | Sync code files only |
| `dlt runtime deployment list` | List all deployments |
| `dlt runtime deployment info` | Show deployment details |
| `dlt runtime configuration sync` | Upload secrets/config to Runtime |
| `dlt runtime configuration list` | List configuration versions |
| `dlt runtime configuration info` | Show configuration details |
