# Skill Building Learnings — dlt AI Dev Kit

## What we built
Three Claude Code skills for building dlt data pipelines:
- `/write-pipeline` — end-to-end pipeline creation
- `/setup-auth` — credentials setup
- `/view-data` — schema and data inspection

---

## Experiments & Learnings

### 1. Skill discoverability
**Problem:** SKILL.md files in `ai/dlt-pipeline/skills/` are not natively picked up by Claude Code as slash commands.
**Why:** Claude Code looks for slash commands in `.claude/commands/`, not in custom plugin directories.
**Solution:** Two layers — keep SKILL.md files in the plugin directory for documentation/portability, and mirror them into `.claude/commands/` for native slash command support.

### 2. CLAUDE.md as a router
**Learning:** CLAUDE.md is read automatically by Claude on every session. It works best as a **router** — pointing to skills rather than duplicating instructions. Putting the full workflow summary in CLAUDE.md caused Claude to run steps in parallel instead of following the skill's sequential logic.
**Fix:** CLAUDE.md should say "follow skill X" not "do steps 1, 2, 3..."

### 3. Ambiguous conditionals cause parallel execution
**Problem:** Writing "use dlthub result if found, otherwise use official docs" caused Claude to search both simultaneously.
**Fix:** Use explicit stop language: "If found, use that page and **stop**. Only if not found, then search for..."

### 4. Never ask for credentials in chat
**Problem:** The setup-auth skill initially asked the user to provide their API key in the chat — a serious security risk.
**Root cause:** The skill said "ask the user for credentials" without specifying how.
**Fix:** The skill now writes placeholder values to `.dlt/secrets.toml` and tells the user to fill it in themselves. This rule is also enforced globally in CLAUDE.md with a hard prohibition.

### 5. Separating concerns across skills
**Learning:** Cramming pipeline writing + data viewing into one skill made it hard to invoke data viewing independently. Splitting into `/write-pipeline` and `/view-data` means:
- Each skill has a single clear purpose
- Users can invoke viewing without re-running the pipeline
- The write-pipeline skill delegates to view-data at the end, keeping the flow intact

### 6. dlt package extras
- `dlt[rest_api]` — does not exist as a pip extra (caused a warning)
- `dlt[duckdb]` — installs DuckDB destination only
- `dlt[workspace]` — installs full workspace tooling including marimo, MCP, ibis, and pandas/pyarrow

### 7. dlt CLI for inspection
Prefer the dlt CLI over ad-hoc Python scripts for data inspection — it's cleaner and doesn't require writing throwaway code:
```bash
uv run dlt pipeline <name> schema   # table schema
uv run dlt pipeline <name> info     # row counts, state
uv run dlt pipeline <name> show     # data preview
```

### 8. dlt REST API pagination
The Rick and Morty API uses `info.next` for pagination. dlt handles this with:
```python
"paginator": {
    "type": "json_link",
    "next_url_path": "info.next",
}
```

### 9. Child tables
dlt automatically normalises nested arrays into child tables (e.g. `characters__episode`, `episodes__characters`). These are linked to their parent via `_dlt_parent_id`.

### 10. .claude file conflict
The repo had a `.claude` file (a plugin pointer) that conflicted with Claude Code's `.claude/commands/` directory convention. Renamed `.claude` → `.claude-plugin` to resolve.

---

## Skill structure that works

```
.claude/
  commands/
    write-pipeline.md   ← native slash command
    setup-auth.md
    view-data.md
ai/dlt-pipeline/
  skills/
    write-pipeline/SKILL.md   ← plugin format (portable)
    setup-auth/SKILL.md
    view-data/SKILL.md
CLAUDE.md               ← global router, hard rules
```