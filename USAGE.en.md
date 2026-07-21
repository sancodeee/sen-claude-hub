# Usage Guide (English)

This guide explains how to install the **sen-claude-hub** plugin marketplace and its plugins into **Claude Code** and **Codex**.

> 中文版本: [USAGE.zh.md](./USAGE.zh.md)

## A. Overview

`sen-claude-hub` is a plugin marketplace recognized by both Claude Code and Codex. Installation on either platform is a two-step process:

1. **Add the marketplace** so the platform knows it exists.
2. **Install the plugins** you want from the registered marketplace.

Repository: `https://github.com/sancodeee/sen-claude-hub`

---

## B. Install into Claude Code

### Prerequisites

- A working installation of the Claude Code CLI.

### Step 1: Add the marketplace

**Option 1 · Remote repository (recommended)**

```text
/plugin marketplace add sancodeee/sen-claude-hub
```

**Option 2 · Local repository (already cloned)**

```text
/plugin marketplace add /path/to/sen-claude-hub
```

Once added, inspect the plugins in the marketplace:

```text
/plugin marketplace info sen-claude-hub
```

### Step 2: Install plugins

Install plugins one by one using `/plugin install <name>@sen-claude-hub`:

```text
/plugin install mcp-faster-caller@sen-claude-hub
/plugin install global-java-code-style@sen-claude-hub
/plugin install fintorq-code-style@sen-claude-hub
/plugin install agent-browser-integration-testing@sen-claude-hub
/plugin install byd-vehicle-scrape@sen-claude-hub
/plugin install jenkins-cli@sen-claude-hub
/plugin install git-worktree-helper@sen-claude-hub
/plugin install trip-forge@sen-claude-hub
/plugin install obsidian-solution-designer@sen-claude-hub
```

> You can also run `/plugin` to open the interactive panel and browse/select plugins to install.

### Step 3: Verify and use

- List registered commands:

  ```text
  /help
  ```

- Invoke a plugin command, e.g. generate a travel plan:

  ```text
  /trip-forge:invoke Yantai 3 days, two people, departing from Beijing
  ```

- Invoke the detailed-design command:

  ```text
  /obsidian-solution-designer:design Create a backend detailed design for order cancellation using the current repository and target Obsidian knowledge base as sources.
  ```

### Manage the marketplace and plugins

```text
/plugin marketplace update sen-claude-hub     # Update the marketplace
/plugin marketplace remove sen-claude-hub     # Remove the marketplace
```

To uninstall an individual plugin, run `/plugin` and disable/uninstall it from the panel.

---

## C. Install into Codex

Codex discovers the marketplace through `.agents/plugins/marketplace.json` in the repository and loads each plugin's skills via its `.codex-plugin/plugin.json` (the `skills` field points to `./skills/`). Each plugin uses the policy `installation: AVAILABLE` and `authentication: ON_INSTALL`.

### Step 1: Get the repository

```bash
git clone https://github.com/sancodeee/sen-claude-hub.git
cd sen-claude-hub
```

### Step 2: Add the local marketplace and install plugins

The Codex marketplace manifest lives at `.agents/plugins/marketplace.json`. In Codex, add this repository directory as a **local marketplace**, then install the plugins you need from it. The installable plugin names match the [per-plugin reference](#d-per-plugin-reference) below.

> Note: plugins are loaded as skills. After installation, Codex triggers the matching skill on demand in relevant situations, and you can also invoke it explicitly with the example prompts below.

### Step 3: Invoke in a session

After installation, trigger a plugin with natural language in a Codex session, for example:

- Generate a travel plan: `Create a complete HTML travel plan for my next trip.`
- Run an end-to-end test: `Run an end-to-end test for this web application.`
- Create a full-stack detailed design: `Create a full-stack detailed design from these requirements and repository facts.`

See the "Codex example prompt" column below for more per-plugin examples.

---

## D. Per-plugin reference

| Plugin | Claude Code command | Codex example prompt | Typical use |
|--------|---------------------|----------------------|-------------|
| `mcp-faster-caller` | `/mcp-faster-caller:invoke` | `Use the GitHub MCP tools for this request.` | Route concise aliases to MCP tools |
| `global-java-code-style` | `/global-java-code-style:invoke` | `Review this Java code for style and quality issues.` | General Java coding standards |
| `fintorq-code-style` | `/fintorq-code-style:invoke` | `Review this code against Fintorq standards.` | Fintorq project code standards |
| `agent-browser-integration-testing` | `/agent-browser-integration-testing:invoke` | `Run an end-to-end test for this web application.` | Browser automation and E2E testing |
| `byd-vehicle-scrape` | `/byd-vehicle-scrape:invoke` | `Scrape the latest data for BYD Atto 2.` | BYD vehicle data scraping and SQL generation |
| `jenkins-cli` | `/jenkins-cli:invoke` | `List the Jenkins jobs available to me.` | Jenkins CLI usage and diagnostics |
| `git-worktree-helper` | `/git-worktree-helper:create`, `/git-worktree-helper:cleanup` | `Create a worktree for this task.` | Create / clean up Git worktrees |
| `trip-forge` | `/trip-forge:invoke` | `Create a complete HTML travel plan for my next trip.` | Generate HTML travel plan reports |
| `obsidian-solution-designer` | `/obsidian-solution-designer:design` | `Create a full-stack detailed design from these requirements and repository facts.` | Produces an implementation-ready backend or full-stack detailed design when information is sufficient; otherwise asks only blocking questions and creates no partial document |

---

## E. Troubleshooting

| Symptom | What to check |
|---------|---------------|
| Marketplace not found | Confirm the marketplace name is `sen-claude-hub`; use `sancodeee/sen-claude-hub` for remote, or an **absolute path** for local. |
| Command missing after install | Run `/help` in Claude Code to confirm the command is registered; restart the session if needed. |
| Stale marketplace contents | Run `/plugin marketplace update sen-claude-hub` (on Codex, run `git pull` to update the local repository). |
| Codex does not trigger a plugin | Confirm `.agents/plugins/marketplace.json` exists at the repo root and the plugin directory contains `.codex-plugin/plugin.json`; invoke explicitly with the example prompt from the reference table. |
