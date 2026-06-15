# sen-claude-hub

> 一个同时面向 **Claude Code** 与 **Codex** 的个人插件市场（Plugin Marketplace）。

`sen-claude-hub` 把一组日常开发中高频使用的能力打包成可一键安装的插件，并通过统一的市场清单分发。每个插件都同时提供 Claude Code（`.claude-plugin/`）与 Codex（`.codex-plugin/`）两套清单，因此无论你使用哪个平台，都能用同一个仓库完成安装与调用。

## ✨ 特性

- **双平台支持**：同一仓库同时被 Claude Code 与 Codex 识别。
- **开箱即用**：内置 8 个插件，覆盖代码规范、自动化测试、数据爬取、运维、旅行规划等场景。
- **命令 + 技能形态**：每个插件提供 slash 命令（`commands/`）与技能（`skills/`），可显式调用，也可由模型按需触发。

## 📦 插件清单

| 插件 | 版本 | 分类 | 作用 |
|------|------|------|------|
| `mcp-faster-caller` | 1.0.0 | Productivity | 将简洁别名路由到 MCP 工具（GitHub / 数据库 / 浏览器 / 搜索 / 文档 / 图像 / PDF） |
| `global-java-code-style` | 1.0.0 | Developer Tools | 通用 Java 编码、架构、异常处理、测试与安全规范 |
| `fintorq-code-style` | 1.0.0 | Developer Tools | Fintorq 项目官方代码风格与开发规范 |
| `agent-browser-integration-testing` | 1.0.0 | Productivity | 基于 agent-browser CLI 的浏览器自动化与端到端集成测试 |
| `byd-vehicle-scrape` | 1.0.0 | Data | 爬取比亚迪车型配置与价格数据并生成 MySQL SQL |
| `jenkins-cli` | 1.0.0 | Productivity | 本机 Jenkins CLI 使用指南与高风险操作边界控制 |
| `git-worktree-helper` | 2.1.0 | Productivity | 创建 / 清理 Git worktree 并同步本地代理与项目配置 |
| `trip-forge` | 1.1.0 | Productivity | 调研并生成自包含、移动端优先的 HTML 旅行攻略报告 |

## 🚀 快速开始

**Claude Code**（添加市场后即可安装插件）：

```text
/plugin marketplace add sancodeee/sen-claude-hub
/plugin install trip-forge@sen-claude-hub
```

**Codex**（克隆仓库后从本地市场添加）：

```bash
git clone https://github.com/sancodeee/sen-claude-hub.git
```

完整步骤、逐插件调用示例与故障排查，请阅读使用指南。

## 📖 使用指南

- 🇬🇧 English: [USAGE.en.md](./USAGE.en.md)
- 🇨🇳 中文: [USAGE.zh.md](./USAGE.zh.md)

## 🗂️ 目录结构

```text
sen-claude-hub/
├── .claude-plugin/
│   └── marketplace.json        # Claude Code 市场清单
├── .agents/
│   └── plugins/
│       └── marketplace.json    # Codex 市场清单
└── plugins/                    # 所有插件源码
    └── <plugin-name>/
        ├── .claude-plugin/plugin.json   # Claude Code 插件清单
        ├── .codex-plugin/plugin.json    # Codex 插件清单（含 interface 元数据）
        ├── commands/                    # slash 命令
        └── skills/                      # 技能（SKILL.md / assets / references）
```

- `.claude-plugin/marketplace.json`：供 Claude Code 解析的市场与插件索引。
- `.agents/plugins/marketplace.json`：供 Codex 解析的市场与插件索引。
- `plugins/*`：每个插件的实际内容，两个平台共享同一份命令与技能。

## 👤 作者与许可

- 作者：sen（<https://github.com/sancodeee>）
- 仓库：<https://github.com/sancodeee/sen-claude-hub>
