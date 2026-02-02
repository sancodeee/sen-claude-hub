# Testing Report Generation Guide

**Role**: When you finish testing using the `agent-browser-integration-testing` skill, you MUST generate a final report for the user. Use the following structure as a guideline.

---

# Integration Test Report

**Target**: [URL]
**Date**: [YYYY-MM-DD HH:MM]
**Status**: [PASS / FAIL / WARN]

## 1. Test Summary
*   **Mode Used**: [Auto / Custom Steps]
*   **Total Steps**: [N]
*   **Successful**: [N]
*   **Failed**: [N]

## 2. Key Findings
*   [Describe what worked, e.g., "Login form submitted successfully"]
*   [Describe any issues, e.g., "Submit button was not clickable"]
*   [Note any detected navigation links]

## 3. Execution Log
| Step | Action | Target | Status |
| :--- | :--- | :--- | :--- |
| 1 | fill | #username | ✅ Success |
| 2 | click | Login | ❌ Failed (Timeout) |

## 4. Evidence
*   **Screenshots**: [Link to screenshot files if generated]
*   **Page Title**: [Captured page title]

---

**Note to Agent**:
*   Parse the JSON output from `run_test.py` to fill this table.
*   If `status` is "failed", provide the `error` message in the Findings section.
