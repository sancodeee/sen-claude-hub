---
name: agent-browser-integration-testing
description: |
  **AI-Driven Browser Testing Toolset**
  
  This skill provides a suite of atomic browser automation tools powered by `agent-browser` (CLI). It is designed to be the "hands" and "eyes" for the Agent to perform logic-driven web testing.

  **Modes**:
  1.  **Inspect** (`inspect`): Returns page structure (inputs, buttons, links) as JSON. Use this first to "see" the page.
  2.  **Execute** (`run`): Executes a sequence of atomic actions (fill, click, wait, verify) defined by the Agent.
  3.  **Auto** (`auto`): Runs a heuristic smoke test (best for quick checks).

  **Workflow for Complex Tests**:
  1.  Call `inspect` on the URL.
  2.  Analyze the JSON output to identify target element IDs or names.
  3.  Construct a JSON action sequence.
  4.  Call `run` with the action sequence.
  5.  **Report**: Parse the JSON result and generate a Markdown report for the user (see `references/REPORT_GUIDE.md`).

compatibility: Requires `agent-browser` CLI and Python 3+.
---

# Agent Browser Integration Testing Skill

## Overview
This skill transforms the `agent-browser` CLI into a programmable testing agent. Unlike rigid scripts, it exposes atomic capabilities (`inspect`, `run`) that allow the AI to orchestrate complex, logic-dependent testing scenarios while maintaining execution stability.

## Commands

### 1. Inspect Page
Analyzes the DOM and returns interactive elements.
```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/agent-browser-integration-testing/scripts/run_test.py inspect --url "https://example.com/login"
```
**Output (JSON)**:
```json
{
  "inputs": ["[text] id=username name=user", "[password] id=pwd"],
  "buttons": ["[Button] text='Login' id=submit-btn"]
}
```

### 2. Run Custom Steps
Executes a specific sequence of actions.
```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/agent-browser-integration-testing/scripts/run_test.py run --url "https://example.com/login" --steps '[
  {"action": "fill", "target": "#username", "value": "testuser"},
  {"action": "fill", "target": "#pwd", "value": "123456"},
  {"action": "click", "target": "#submit-btn"},
  {"action": "wait", "value": 2},
  {"action": "verify_text", "value": "Welcome"}
]'
```
**Supported Actions**:
*   `fill`: `{"action": "fill", "target": "selector", "value": "text"}`
*   `click`: `{"action": "click", "target": "selector OR text=ButtonName"}`
*   `wait`: `{"action": "wait", "value": seconds}`
*   `screenshot`: `{"action": "screenshot"}`
*   `verify_text`: `{"action": "verify_text", "value": "expected text"}`

### 3. Auto Smoke Test
Quickly scans and pokes the page (heuristic).
```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/agent-browser-integration-testing/scripts/run_test.py auto --url "https://example.com"
```

## Best Practices
*   **Always Inspect First**: Don't guess selectors. Use `inspect` to get ground truth.
*   **Use `text=` for Buttons**: If IDs are missing/complex, use `text=Submit` for robust clicking.
*   **Step-by-Step**: For long flows, break them into multiple `run` calls if needed.
*   **Reporting**: Always summarize the JSON results into a readable table for the user using the format in `references/REPORT_GUIDE.md`.
