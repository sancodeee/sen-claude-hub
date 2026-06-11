# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

`sen-claude-hub` is a **Claude Code plugin marketplace**. It is not an application — it is a collection of installable plugins (skills + slash commands) published through two marketplace manifests. Each plugin packages domain knowledge and/or automation scripts that Claude (or Codex) loads on demand.

There is no top-level build, test, or dependency manifest. Each plugin is self-contained, and only some plugins ship executable code with their own tooling.

## Repository structure

- `.claude-plugin/marketplace.json` — the **Claude Code** marketplace manifest (plugin name, description, `source` path, `version`).
- `.agents/plugins/marketplace.json` — the parallel **Codex / agents** marketplace manifest (per-plugin `category` and install `policy`).
- `plugins/<name>/` — one directory per plugin, each with the same internal shape:
  - `.claude-plugin/plugin.json` — Claude-facing metadata.
  - `.codex-plugin/plugin.json` — Codex-facing metadata, including a richer `interface` block (displayName, capabilities, defaultPrompt) and a `skills` path.
  - `commands/<name>-invoke.md` (or task-specific commands) — slash command(s) whose body forces an immediate call to the plugin's skill, passing `$ARGUMENTS` through.
  - `skills/<name>/SKILL.md` — the skill itself: YAML frontmatter + Markdown instructions.
  - `skills/<name>/references/*.md` — progressive-disclosure docs the skill tells Claude to read only when a specific scenario applies.
  - `skills/<name>/scripts/*` — optional executable helpers (Python or Node).

## How a plugin is wired together

Adding or editing a plugin means keeping several files consistent:

1. **Both marketplace manifests** (`.claude-plugin/` and `.agents/plugins/`) must list the plugin with the same `name` and `source`/`path`. The Claude manifest carries `version` and `description`; the Codex manifest carries `category` and `policy`.
2. **Both `plugin.json` files** (`.claude-plugin/` and `.codex-plugin/`) must agree on `name` and `version`. Versions are also duplicated in the Claude marketplace manifest — bump all three together when releasing.
3. **The command file** is a thin dispatcher. Its frontmatter declares `name: <plugin>:<verb>`, `description`, and `argument-hint`; its body is an imperative instruction (often in Chinese) telling Claude to *immediately and mandatorily* invoke the skill and respond based on the skill's output. User input flows in via the `$ARGUMENTS` placeholder.
4. **The `SKILL.md` frontmatter** controls activation: `description` (the trigger text Claude matches against — keep it keyword-rich, bilingual where relevant), `user-invocable: true`, and `allowed-tools` (commonly `Read, Grep, Glob, Bash`). The body defines when to use / when *not* to use the skill, the working order, and references to read.

### Plugin-root resolution (important for script-bearing skills)

Skills that run scripts never hardcode paths. They resolve a `PLUGIN_ROOT` first, differently per host:

- **Claude Code:** `PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:?CLAUDE_PLUGIN_ROOT is not set}"`.
- **Codex:** derive the absolute directory of the loaded `SKILL.md` and walk up two levels — do **not** use the Claude assignment.

Scripts are then invoked as `"${PLUGIN_ROOT:?PLUGIN_ROOT must be set}/skills/<name>/scripts/<script>"`. Preserve this pattern when adding script-based skills; an unset root must abort rather than run with an empty path.

## Plugins in this repo

- **mcp-faster-caller** — compresses verbose MCP calls into short aliases (`gh`, `db`, `browser`, `search`, …) via `scripts/call_mcp.py`.
- **global-java-code-style** / **fintorq-code-style** — reference-only skills (no scripts) providing Java coding standards; `fintorq-code-style` is project-specific and marked MUST-follow.
- **agent-browser-integration-testing** — browser E2E testing driven by the external `agent-browser` CLI; includes `scripts/validate-report.js` and report templates.
- **byd-vehicle-scrape** — Node + Playwright scraper that produces JSON then SQL.
- **jenkins-cli** — guidance + risk-tiered operating rules for the local `jenkins-cli`; reference-only, splits safe / change / dangerous operations across `references/`.
- **git-worktree-helper** — Python scripts to create worktrees, sync local agent/project config, and safely reclaim config before cleanup. The only plugin with automated tests.

## Commands & tooling

There is no repo-wide command runner. Tooling is per-plugin:

**git-worktree-helper** (Python, `unittest`):
```bash
# Run the worktree sync tests
python3 plugins/git-worktree-helper/skills/git-worktree-helper/tests/test_worktree_sync.py
# or
cd plugins/git-worktree-helper/skills/git-worktree-helper && python3 -m unittest tests.test_worktree_sync
```
The test boots throwaway git repos in temp dirs and shells out to `create_worktree.py` / `remove_worktree.py`. Scripts use only the Python standard library (no third-party deps).

**byd-vehicle-scrape** (Node + Playwright):
```bash
cd plugins/byd-vehicle-scrape/skills/byd-vehicle-scrape
npm install          # installs playwright
npm run scrape       # node scripts/scrape-byd-variant-details.js
npm run sql          # node scripts/generate_sql.mjs
```

**agent-browser-integration-testing** (Node):
```bash
node plugins/agent-browser-integration-testing/skills/agent-browser-integration-testing/scripts/validate-report.js
```

## Conventions

- **Skill content is written primarily in Chinese**, with English used in some `plugin.json` `interface`/`description` fields. Match the existing language of the file you edit. Commit messages follow Conventional Commits with a Chinese subject (e.g. `feat(git-worktree-helper): 添加配置同步功能支持安全清理工作树`).
- **Safety tiering**: skills that touch real systems (jenkins-cli, git-worktree-helper) separate read-only/safe operations from state-changing and high-risk ones, and instruct Claude to confirm before destructive actions rather than execute by default. Preserve this gating when extending them.
- **Progressive disclosure**: keep `SKILL.md` lean and push detail into `references/*.md` that the skill loads conditionally, rather than inlining everything.
- **Secrets**: skills explicitly forbid echoing tokens like `JENKINS_API_TOKEN` — keep auth strings out of any command output or examples.
- `__pycache__/` and `*.py[cod]` are gitignored within script-bearing plugins.
