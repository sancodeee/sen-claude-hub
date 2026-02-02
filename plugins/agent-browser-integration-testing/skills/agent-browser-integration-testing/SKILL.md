---
name: agent-browser-integration-testing
description: |
  Browser integration testing skill using agent-browser.

  Force trigger with exact command format:
    test <url> [create|read|update|delete|all]
  Examples:
    - test https://example.com create
    - test https://demo.app all

  Also supports natural language (English & Chinese):
    - "run integration tests on example.com"
    - "test login flow and buttons"
    - “测试 https://xxx.com 创建功能”
    - “帮我对这个页面做集成测试，url是xxx”
    - “浏览器集成测试，重点测新增、删除操作”

  Prioritizes lightweight agent-browser calls; generates structured reports by modules.
compatibility: Requires agent-browser CLI installed and Python 3+ environment. Prioritizes agent-browser for testing; avoids heavy tools like Playwright or Chrome DevTools unless necessary.
metadata:
  author: sancodeee
  version: 1.0.0
---

# Agent Browser Integration Testing Skill

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