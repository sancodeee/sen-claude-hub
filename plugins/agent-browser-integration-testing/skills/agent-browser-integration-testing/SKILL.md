---
name: agent-browser-integration-testing
description: |
  **URL页面集成测试技能**

  本技能提供由 `agent-browser` CLI 驱动的原子级浏览器自动化工具。它作为AI Agent的“眼睛”和“双手”，通过快照 + ref 工作流进行逻辑驱动的网页功能集成测试，具有高可靠性和效率。

  **核心工作流简介**：
  1. 打开目标URL
  2. 执行快照以获取带有唯一ref（@e1、@e2 等）的交互元素
  3. 使用ref执行动作（填写、点击等）
  4. 页面发生变化后重新快照（之前的ref会失效）
  5. 根据结果生成Markdown报告（参考 `references/REPORT_GUIDE.md`）

compatibility: 需要安装 `agent-browser` CLI（vercel-labs/agent-browser），详细的安装步骤和故障排除请参考 [`references/AGENT_BROWSER_INSTALLATION.md`](references/AGENT_BROWSER_INSTALLATION.md) 安装指南。
---

# Agent Browser Integration Testing Skill

## 技能概述

本技能让Agent-browser通过精确的原子命令控制浏览器。它采用可访问性树快照机制，为交互元素分配稳定的临时ref，即使在动态页面上也能确保元素定位的可靠性。

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

**语义定位（无ref时的备选方案）**：

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
- **报告生成**：将快照、动作结果和截图汇总为可读的Markdown文件，保存到用户所在项目根目录的`/testing-report`目录下（**强制**务必遵循
  `references/REPORT_GUIDE.md` 中的格式和要求）。

**示例报告模板**：
***强制且必须参考`references/REPORT_GUIDE.md` 中的格式和要求为用户生成完善且符合要求的测试报告Markdown文件，方便用户归档和分享
***。