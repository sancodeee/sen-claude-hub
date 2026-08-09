# 使用指南（中文）

本指南介绍如何把 **sen-claude-hub** 插件市场及其中的插件安装到 **Claude Code** 和 **Codex**。

> English version: [USAGE.en.md](./USAGE.en.md)

## A. 概述

`sen-claude-hub` 是一个同时被 Claude Code 与 Codex 识别的插件市场。两个平台的安装都分为两步：

1. **添加市场**：让平台知道这个市场的存在。
2. **安装插件**：从已添加的市场中选择具体插件启用。

仓库地址：`https://github.com/sancodeee/sen-claude-hub`

---

## B. 安装到 Claude Code

### 前置条件

- 已安装并能正常运行 Claude Code CLI。

### 步骤 1：添加市场

**方式一 · 远程仓库（推荐）**

```text
/plugin marketplace add sancodeee/sen-claude-hub
```

**方式二 · 本地仓库（已克隆到本地）**

```text
/plugin marketplace add /path/to/sen-claude-hub
```

添加成功后，可用以下命令查看市场内的插件：

```text
/plugin marketplace info sen-claude-hub
```

### 步骤 2：安装插件

逐个安装，格式为 `/plugin install <插件名>@sen-claude-hub`：

```text
/plugin install global-java-code-style@sen-claude-hub
/plugin install fintorq-code-style@sen-claude-hub
/plugin install agent-browser-integration-testing@sen-claude-hub
/plugin install byd-vehicle-scrape@sen-claude-hub
/plugin install jenkins-cli@sen-claude-hub
/plugin install git-worktree-helper@sen-claude-hub
/plugin install trip-forge@sen-claude-hub
/plugin install obsidian-solution-designer@sen-claude-hub
/plugin install resume-forge@sen-claude-hub
```

> 也可以直接运行 `/plugin` 打开交互式面板，在其中浏览并勾选要安装的插件。

### 步骤 3：验证与使用

- 查看已注册的命令：

  ```text
  /help
  ```

- 调用某个插件的命令，例如生成旅行攻略：

  ```text
  /trip-forge:invoke 烟台 3天 两人 从北京出发
  ```

- 调用详细方案设计命令：

  ```text
  /obsidian-solution-designer:design 为订单取消能力编写后端详细设计；资料位于当前仓库和目标 Obsidian 知识库。
  ```

- 基于真实材料撰写中文 Markdown 简历，并可选按 JD 定制：

  ```text
  /resume-forge:write <真实材料与可选 JD>
  ```

### 管理市场与插件

```text
/plugin marketplace update sen-claude-hub     # 更新市场到最新版本
/plugin marketplace remove sen-claude-hub     # 移除市场
```

如需卸载单个插件，运行 `/plugin` 进入面板进行禁用 / 卸载。

---

## C. 安装到 Codex

Codex 通过仓库内的 `.agents/plugins/marketplace.json` 识别市场，并通过每个插件的 `.codex-plugin/plugin.json` 加载其技能（`skills` 指向 `./skills/`）。插件策略为 `installation: AVAILABLE`、`authentication: ON_INSTALL`。

### 步骤 1：获取仓库

```bash
git clone https://github.com/sancodeee/sen-claude-hub.git
cd sen-claude-hub
```

### 步骤 2：添加本地市场并安装插件

仓库的 Codex 市场清单位于 `.agents/plugins/marketplace.json`。在 Codex 中以**本地市场**的方式添加该仓库目录，然后从市场中选择安装所需插件。可安装的插件名与下方[逐插件速查表](#d-逐插件速查表)一致。

安装 ResumeForge：

```text
codex plugin add resume-forge@sen-claude-hub
```

> 提示：插件以技能（skill）形态加载。安装后，Codex 会在合适的场景按需触发对应技能，你也可以用下方的示例 prompt 显式调用。

### 步骤 3：在会话中调用

安装后，在 Codex 会话中用自然语言触发对应插件，例如：

- 生成旅行攻略：`Create a complete HTML travel plan for my next trip.`
- 运行端到端测试：`Run an end-to-end test for this web application.`
- 生成全栈详细设计：`Create a full-stack detailed design from these requirements and repository facts.`
- 基于真实材料撰写中文 Markdown 简历，并可选按 JD 定制：`$resume-forge 基于以下真实材料撰写中文 Markdown 简历，可选按目标 JD 定制：...`

更多逐插件示例见下表的「Codex 示例 prompt」列。

---

## D. 逐插件速查表

| 插件 | Claude Code 命令 | Codex 示例 prompt | 典型用途 |
|------|------------------|-------------------|----------|
| `global-java-code-style` | `/global-java-code-style:invoke` | `Review this Java code for style and quality issues.` | 通用 Java 编码规范 |
| `fintorq-code-style` | `/fintorq-code-style:invoke` | `Review this code against Fintorq standards.` | Fintorq 项目代码规范 |
| `agent-browser-integration-testing` | `/agent-browser-integration-testing:invoke` | `Run an end-to-end test for this web application.` | 浏览器自动化与 E2E 测试 |
| `byd-vehicle-scrape` | `/byd-vehicle-scrape:invoke` | `Scrape the latest data for BYD Atto 2.` | 比亚迪车型数据爬取与 SQL 生成 |
| `jenkins-cli` | `/jenkins-cli:invoke` | `List the Jenkins jobs available to me.` | Jenkins CLI 使用与诊断 |
| `git-worktree-helper` | `/git-worktree-helper:create`、`/git-worktree-helper:cleanup` | `Create a worktree for this task.` | 创建 / 清理 Git worktree |
| `trip-forge` | `/trip-forge:invoke` | `Create a complete HTML travel plan for my next trip.` | 生成 HTML 旅行攻略报告 |
| `obsidian-solution-designer` | `/obsidian-solution-designer:design` | `Create a full-stack detailed design from these requirements and repository facts.` | 资料充分时生成成熟的后端或全栈详细设计；关键信息不足时只询问阻塞问题，不创建半成品文档 |
| `resume-forge` | `/resume-forge:write` | `$resume-forge 基于以下真实材料撰写中文 Markdown 简历，可选按目标 JD 定制：...` | 基于真实材料撰写中文 Markdown 简历，并可选按 JD 定制 |

---

## E. 故障排查

| 现象 | 排查动作 |
|------|----------|
| 提示找不到市场 | 确认市场名为 `sen-claude-hub`；远程添加用 `sancodeee/sen-claude-hub`，本地添加需提供仓库**绝对路径**。 |
| 插件安装后命令不出现 | 在 Claude Code 中运行 `/help` 确认命令已注册；必要时重启会话。 |
| 市场内容过旧 | 运行 `/plugin marketplace update sen-claude-hub`（Codex 侧执行 `git pull` 更新本地仓库）。 |
| Codex 未触发插件 | 确认仓库根目录存在 `.agents/plugins/marketplace.json`，且对应插件目录含 `.codex-plugin/plugin.json`；用速查表中的示例 prompt 显式调用。 |
