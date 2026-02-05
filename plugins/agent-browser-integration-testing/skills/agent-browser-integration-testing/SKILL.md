---
name: agent-browser-integration-testing
description: |
  **网页自动化与端到端集成测试专家 (Web E2E Testing Expert)**

  本技能使具备专业的浏览器测试能力。你将通过 `agent-browser` CLI 进行由逻辑驱动的、原子级的网页功能验证。

  **适用场景**：
  - 验证用户旅程（如：注册、登录、购物车结算）。
  - 填写复杂表单并验证提交结果。
  - 检查页面跳转逻辑和关键元素状态。

  **核心作业流程 (SOP - 渐进式报告)**：
  1. **Init**: 参考 `references/REPORT_GUIDE.md` 的头部格式，**立即**创建报告文件，写入 Target URL 和 Date。
  2. **Open**: 打开目标 URL。
  3. **Loop (循环执行)**:
     - **Snapshot**: 获取 ref。
     - **Action**: 执行操作。
     - **Wait & Re-Snapshot**: 处理动态变化（严禁盲目连续操作）。
     - **Audit**: 运行 `network requests --json`。
     - **Record**: 依据 `REPORT_GUIDE.md` 要求：
       - 如有关键发现，及时记录到**"2. 关键发现"**
       - 将操作记录追加到 **"3. 执行日志"** 表格。
       - 将 API 数据追加到 **"4. 网络交互审计"** 表格。
       - 如有截图，**必须**使用 `![desc](path)` 语法嵌入到 **"5. 证据"** 部分。
  4. **Finalize**: 测试结束时，填充 **"1. 摘要"**、**"2. 关键发现"** 和 **"6. 建议"**，并最终核对格式。

  **交付标准**：必须严格遵循 `references/REPORT_GUIDE.md` 的格式要求。

compatibility: 需要安装 `agent-browser` CLI（vercel-labs/agent-browser），详细的安装步骤和故障排除请参考 [`references/AGENT_BROWSER_INSTALLATION.md`](references/AGENT_BROWSER_INSTALLATION.md) 安装指南。
---

# Agent Browser Integration Testing Skill

## 技能概述

本技能让Agent-browser通过精确的原子命令控制浏览器。它采用可访问性树快照机制，为交互元素分配稳定的临时ref，即使在动态页面上也能确保元素定位的可靠性，从而能够对页面所有功能进行准确且完善的集成测试。

## 命令列表

### 1. 打开页面

打开新的浏览器会话并导航到指定URL。

```Bash
agent-browser open "https://example.com/login"
```

### 2. 页面快照（相当于Inspect）

返回带有唯一ref的交互元素结构视图。

```Bash
agent-browser snapshot -i --json
```

**推荐参数**：

- -i：仅交互元素（输入框、按钮、链接等）
- --json：结构化JSON输出
- -c：紧凑模式（最小化输出）
- -d N：限制树深度

**示例输出（JSON）**：

```JSON
{
  "elements": [
    {
      "ref": "@e1",
      "role": "textbox",
      "name": "Username",
      "placeholder": "Enter username"
    },
    {
      "ref": "@e2",
      "role": "textbox",
      "name": "Password",
      "type": "password"
    },
    {
      "ref": "@e3",
      "role": "button",
      "name": "Login"
    }
  ]
}
```

### 3. 执行动作

所有动作均支持使用ref（@eX）以获得最高可靠性。

**使用ref的常见动作**：

```Bash
agent-browser fill @e1 "testuser"
agent-browser fill @e2 "P@ssw0rd123"
agent-browser click @e3
agent-browser wait --load networkidle
agent-browser screenshot after-login.png
```

**语义定位（无ref时的备选方案，**ref失败后强制尝试**）**：

```Bash
agent-browser find text "Login" click
agent-browser find label "Username" fill "testuser"
```

**其他实用动作**：

- agent-browser type @e1 "extra text"（不清除直接追加输入）
- agent-browser press Enter
- agent-browser wait 3000（毫秒）
- agent-browser wait --text "Welcome back"
- agent-browser get text @e4（提取文本用于验证）
- agent-browser get url
- agent-browser get title

### 3.5 网络监控（关键）

获取自页面加载以来捕获的所有网络请求数据。建议在关键操作后调用。

```bash
# 获取请求列表（推荐使用 JSON 以便解析）
agent-browser network requests --json
```

**用途**：用于填充测试报告中的"网络交互审计"部分，特别是检查 4xx/5xx 错误。

**输出示例**：

```json
[
  {
    "url": "https://example.com/api/login",
    "method": "POST",
    "type": "xhr",
    "status": 200,
    "duration": 350
  },
  {
    "url": "https://example.com/static/main.js",
    "method": "GET",
    "type": "script",
    "status": 200,
    "duration": 120
  }
]
```

### 4. 截图与验证

```Bash
agent-browser screenshot result.png --full
agent-browser get text body > page-content.txt
```

### 5. 关闭会话

```Bash
agent-browser close
```

## 最佳实践

- **始终先执行快照**：使用最新快照中的ref，绝不猜测选择器。
- **页面变化后必须重新快照**：导航、点击或表单提交会使之前的ref失效。
- **优先使用ref而非CSS/文本**：ref具有确定性和稳定性。
- **将复杂流程拆分为多个步骤**：便于调试和验证中间状态。
- **处理动态元素（如下拉框/弹窗）**：
    - ❌ **错误做法**：试图一次性完成（`click @e1 + click @e2`）。
    - ✅ **正确做法**：分步执行（点击 @e1 -> wait -> **snapshot** -> 点击新生成的 @ref）。
- **渐进式记录（Progressive Reporting）**：
    - ❌ **错误**：做完所有测试步骤后，凭记忆一次性写报告。
    - ✅ **正确**：每做完一步（如登录成功），立刻将截图和 API 结果写入报告文件，同时参考`references/REPORT_GUIDE.md`
      验证当前填充是否符合指导规范(**强制**)，这样即使中途崩溃，数据也不会丢失。
- **报告生成**：将快照、动作结果和截图汇总为可读的Markdown文件，保存到用户所在项目根目录的`/testing-report`目录下（**强制**
  务必遵循`references/REPORT_GUIDE.md` 中的格式和要求）。

**示例报告模板**：
***强制且必须参考`references/REPORT_GUIDE.md` 中的格式和要求为用户生成完善且符合要求的测试报告Markdown文件，方便用户归档和分享
***。