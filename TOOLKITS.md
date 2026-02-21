# Component compatibility matrix

How `dlt ai` installs workbench components across AI platforms.

## Component types

| Component | Source dir | Description |
|-----------|-----------|-------------|
| skill | `skills/<name>/` | Directory with `SKILL.md` + supporting files, copied as a tree |
| command | `commands/<name>.md` | Single markdown file, slash-command or prompt template |
| rule | `rules/<name>.md` | Single markdown file, always-on context injected by the IDE |

## Platform support

| Component | Claude Code | Cursor | Codex |
|-----------|------------|--------|-------|
| skill | native | native | native |
| command | native | native | converted to skill |
| rule | native | native | converted to skill |

## Install paths

| Component | Claude Code | Cursor | Codex |
|-----------|------------|--------|-------|
| skill | `.claude/skills/<name>/` | `.cursor/skills/<name>/` | `.agents/skills/<name>/` |
| command | `.claude/commands/<name>.md` | `.cursor/commands/<name>.md` | `.agents/skills/<name>/SKILL.md` |
| rule | `.claude/rules/<plugin>-<name>.md` | `.cursor/rules/<plugin>-<name>.mdc` | `.agents/skills/<plugin>-<name>/SKILL.md` |

## Transforms applied during install

| Component | Claude Code | Cursor | Codex |
|-----------|------------|--------|-------|
| skill | passthrough | passthrough | passthrough |
| command | passthrough | passthrough | wrapped with `name`/`description` frontmatter |
| rule | non-Claude frontmatter stripped (keeps `name`, `description`) | `alwaysApply: true` added, `description` derived from first heading if missing | wrapped with `name`/`description` frontmatter |

## Conflict handling

When a destination path already exists, the component is skipped with a warning. Existing files are never overwritten.

## Auto-detection priority

When `--variant` is omitted, the platform is detected in this order:

1. **Runtime env vars** (set by the IDE when it spawns the CLI): Claude Code > Codex > Cursor
2. **Project-local file probes** (checked in priority order):
   - Claude Code: `.claude/`, `CLAUDE.md`
   - Codex: `.agents/`, `AGENTS.md`
   - Cursor: `.cursor/`, `.cursorignore`, `.cursorrules`
3. **Global (home dir) probes**: `~/.claude/`, `~/.codex/`, `~/.cursor/`
