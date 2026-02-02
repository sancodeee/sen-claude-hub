---
name: agent-browser-integration-testing
description: |
  **THIS SKILL IS STRICTLY LIMITED TO AGENT-BROWSER CLI ONLY.**

  **MANDATORY RULE #1**: For **EVERY SINGLE** browser action — including but not limited to: opening URL, navigation, clicking elements, filling forms, submitting, extracting text, taking screenshots, inspecting network, finding buttons/links/forms, verifying results — **YOU MUST ONLY USE subprocess to call the 'agent-browser' command-line tool**. 
  **NEVER** call, suggest, fallback to, or even consider using Playwright MCP, chrome-devtools MCP, browserbase, puppeteer, selenium, or ANY other browser automation MCP/tool unless agent-browser binary literally does not exist in PATH (and you must clearly say "agent-browser command not found" in that case).

  **MANDATORY RULE #2**: If agent-browser returns an error, log the exact command and error message, do NOT switch to any MCP.

  **MANDATORY RULE #3**: Do NOT generate any browser-related code yourself (js/python/etc). Do NOT write Playwright/Puppeteer code. Do NOT use MCP function calls for browser tasks.

  Trigger formats (use these exact patterns to invoke):
  • test <url> [create|read|update|delete|all]
  • test https://example.com create
  • test https://demo.app all

  Natural language support (English & Chinese):
  • run integration tests on https://...
  • 测试 https://... 的创建功能
  • 帮我对这个页面做完整集成测试
  • 浏览器页面集成测试 url是xxx 测 CRUD

  This skill executes python scripts/run_test.py --url=... --operation=... and relies 100% on agent-browser CLI inside the script.
compatibility: Requires agent-browser CLI installed in PATH and Python 3+. **agent-browser is the ONLY allowed browser automation method**. No Playwright, no chrome-devtools-mcp, no other MCPs.
metadata:
  author: sancodeee
  version: 1.1.0
---

# Agent Browser Integration Testing Skill – STRICT AGENT-BROWSER ONLY

## 最高优先级强制规则（Claude 必须遵守）
1. **只能使用 agent-browser CLI** 执行所有浏览器相关操作。
2. **严禁** 在任何情况下直接或间接调用 Playwright、chrome-devtools、browserbase 或其他任何浏览器 MCP。
3. 如果 agent-browser 命令不存在或报错，必须在回复中明确写出：
```doctest
   【错误】agent-browser 命令未找到或执行失败。
   命令：agent-browser <实际命令>
   错误：{完整错误信息}
   请安装 agent-browser：npm install -g @vercel-labs/agent-browser （或参考官方文档）
```
并**停止后续浏览器操作**，不要尝试用其他工具补救。
4. 所有测试步骤的 agent-browser 调用必须通过 `scripts/run_test.py` 中的 subprocess 执行。
5. 报告中必须列出**每一步实际执行的 agent-browser 命令**。

## Overview
This skill automates integration testing in a browser environment for web pages and APIs. It supports:
- Command-line style invocation: e.g., "test https://example.com create" to test creation functionalities.
- Natural language: e.g., "Perform full integration tests on https://example.com, focusing on user management APIs."
- Testing scopes: create (add/new), read (query/view), update (edit/modify), delete (remove), or all.
- Comprehensive coverage: APIs, buttons, forms, and links. Follows jumps/links and prompts user for continuation.
- Output: Fixed-format test report in Markdown, structured by business modules (e.g., User Module, Payment Module).

## Usage Guidelines
- **Trigger Conditions**: Load this skill when the user mentions browser testing, integration tests, URLs with operations (CRUD), or commands starting with "test".
- **Input Parsing**:
- Extract URL from query.
- Identify operation: create, read, update, delete, all (default to all if unspecified).
- For natural language, interpret custom requirements (e.g., "focus on login flow").
- **Dependencies**:
- agent-browser: Use for all browser interactions (navigation, clicks, API calls simulation).
- Python: Execute scripts/run_test.py for orchestration and report generation.
- Avoid heavy tools: Only fall back if agent-browser insufficient (rare).
- **Testing Process**:
1. Open browser to URL using agent-browser.
2. Identify elements: Buttons, forms, links, API endpoints (via network inspection if needed).
3. Perform tests per operation:
- Create: Simulate additions (e.g., form submits).
- Read: Query/view data.
- Update: Modify existing entries.
- Delete: Remove items.
4. Handle jumps: If links/buttons lead to new pages, note them and prompt user: "Do you want to test the jumped page at [new_url]? Yes/No."
5. Group by modules: Infer business modules from page structure (e.g., via headings/sections).
6. Validate: Check for success/failure, errors, expected responses.
- **Report Generation**:
- Use the fixed template in references/test_report_template.md.
- Fill in sections dynamically: Overview, Module-wise results (API/Function, Test Case, Result, Notes).
- Output as Markdown for consistency.
- Save to project root's testing-report directory with timestamped filename.

## 使用方式（中文支持）
- 命令触发：test ${url} [create/read/update/delete/all]
- 中文自然语言示例：
- “测试 https://example.com 的创建功能”
- “帮我对这个网址做完整集成测试，包括新增、查询、更新、删除”
- “浏览器自动化测试这个页面，所有按钮和 API 都要测”

## Script Integration
- Invoke scripts/run_test.py with arguments: python scripts/run_test.py --url=${url} --operation=${op}
- The script handles agent-browser calls, test execution, and template filling.

## Error Handling
- If agent-browser not installed: Instruct user to install.
- Failures: Log in report with details.
- User Interaction: Use Claude's messaging to ask for confirmations (e.g., jumps).

## References
- Load references/test_report_template.md when generating reports.
- Additional docs can be added here for advanced usage.
