# Testing Report Generation Guide

**Role**: 当你使用 `agent-browser-integration-testing` skill 完成测试后，你**必须**为用户生成一份最终报告。报告必须严格遵循以下结构和要求，使用清晰、专业、结构化的 Markdown 格式。报告目标是让用户一目了然地了解测试全貌、关键结果、问题点及证据。

## Integration Test Report

**Target URL**: [完整测试目标 URL]  
**Date & Time**: [YYYY-MM-DD HH:MM:SS]（使用测试完成时的实际时间）  
**Overall Status**: [PASS / FAIL / WARN]  
**Total Duration**: [X.X seconds]（从 open 到最后一次操作的累计耗时，如有多个会话则汇总）

### 1. Test Summary

- **Workflow Type**: [Iterative Snapshot + Atomic Actions]（固定描述当前 skill 的标准工作流）
- **Total Commands Executed**: [N]（包括 open、snapshot、fill、click、wait、screenshot 等所有命令）
- **Successful Commands**: [N]
- **Failed Commands**: [N]
- **Key Pages Visited**: [N]（统计发生导航的次数或列出主要页面 URL）
- **Screenshots Taken**: [N]

### 2. Key Findings

- [成功点描述，例如：登录表单填写正常，点击登录按钮后成功导航至仪表盘页面]
- [成功点描述，例如：页面关键交互元素（如用户名、密码、登录按钮）均可通过 ref 稳定定位]
- [问题点描述，例如：点击“提交”后出现超时，页面未跳转]
- [问题点描述，例如：某些动态加载元素在首次 snapshot 中未出现，需要额外 wait]
- [其他观察，例如：检测到页面包含以下导航链接：/dashboard、/profile、/logout]
- [性能观察，例如：页面平均加载时间约 X 秒，首次 snapshot 耗时 Y ms]
- **如果有失败**：必须在此明确列出错误信息（如 timeout、element not found、JS error 等）并说明可能原因

### 3. Execution Log

使用 Markdown 表格格式，记录每一步的关键操作。表格必须包含以下列：

| Step | Command              | Target / Ref                  | Status | Duration (s) | Details / Error                  |
|------|----------------------|-------------------------------|--------|--------------|----------------------------------|
| 1    | open                 | https://example.com/login     | ✅     | 2.1         | Page loaded successfully        |
| 2    | snapshot -i --json   | -                             | ✅     | 0.4         | Found 3 interactive elements (@e1–@e3) |
| 3    | fill                 | @e1                           | ✅     | 0.3         | Filled username                 |
| 4    | fill                 | @e2                           | ✅     | 0.3         | Filled password                 |
| 5    | click                | @e3                           | ✅     | 1.8         | Navigation to dashboard         |
| 6    | wait --text          | "Welcome back"                | ✅     | 0.9         | Text appeared                   |
| 7    | screenshot           | after-login.png               | ✅     | 0.5         | Screenshot saved                |

- 每行对应一次主要工具调用
- Status 使用 ✅（成功）或 ❌（失败）
- Details 中包含关键结果或完整错误信息

### 4. Evidence

- **Screenshots**：
  - [文件名1]: [简要描述，例如：登录页面初始状态]
  - [文件名2]: [简要描述，例如：登录成功后的仪表盘页面]
  - （如果生成多个截图，必须全部列出并描述）
- **Final Page Title**: [捕获的最终页面标题]
- **Final URL**: [测试结束时的当前 URL]
- **Key Snapshot Excerpt**（可选但推荐）：列出最后一次 snapshot 中最重要的几个 ref 及其描述

### 5. Recommendations（新增必填部分）

- [如果通过]：建议下一步功能测试点或生产监控建议
- [如果失败]：明确的重现步骤、可能的根本原因（如网络、动态加载、反爬虫）、修复建议
- [通用建议]：是否需要增加 wait、调整定位策略、使用 headless 模式等优化点
- [安全性/兼容性观察]：如发现敏感字段未脱敏、移动端适配问题等

**Note to Agent**:

- 你必须从多次工具调用（open、snapshot、fill、click、screenshot、get text 等）的输出中汇总信息填充报告。
- 所有字段必须真实填充，不能留空或使用占位符。
- 报告必须客观、详尽、易读；优先使用表格和列表提升可读性。
- 如果测试涉及多个页面或长流程，建议在 Key Findings 中增加小节分段。
- 最终报告必须独立成文，直接回复给用户，无需额外解释。