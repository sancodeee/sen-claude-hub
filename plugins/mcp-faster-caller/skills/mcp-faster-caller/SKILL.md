---
name: mcp-faster-caller
description: 使用MCP前务必调用的技能，支持 GitHub (gh/repo)、数据库查询 (db/sql)、浏览器自动化 (browser/web)、网页搜索 (search/read)、API文档搜索、图像/PDF 分析 (image/pdf)。中英文皆可，涉及到关键词或别名也可快速触发。
argument-hint: "[alias] [command] [arguments] 例如：gh list-repos owner=用户名 或 数据库 query 'SELECT * FROM table'"
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash
---

# MCP Faster Caller

极简封装 MCP 调用，将原本需要 80-300 token 的 MCP 调用压缩到 10-25 token。

## 使用方式

解析用户的 MCP 调用指令：**$ARGUMENTS**

指令格式：`<alias> <command> [arguments]`

### 调用步骤

1. 解析用户输入的指令，提取 alias、command 和 arguments
2. 使用 Python 脚本 `scripts/call_mcp.py` 解析指令：
   ```bash
   # python3 ~/.claude/skills/mcp-faster-caller/scripts/call_mcp.py "$ARGUMENTS"
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/mcp-faster-caller/scripts/call_mcp.py "$ARGUMENTS"
   ```
3. 根据返回结果，调用对应的 MCP 工具

### 快速开始

```bash
# GitHub 操作
gh list-repos owner=username

# 数据库操作
db query "SELECT * FROM users LIMIT 5"

# 浏览器自动化测试
browser goto https://example.com
```

## 更多信息参考
- 📖 **[参考文档和配置指南](references/README.md)** - 参考文档和配置指南
- 📖 **[完整别名参考](references/mcp_aliases.md)** - 所有可用别名和使用示例
- 🔧 **[故障排除](references/troubleshooting.md)** - 常见问题和解决方案
- ⚙️ **[自定义配置](references/configuration.md)** - 如何添加新别名（代码修改方式）
- ⚙️ **[自定义配置](references/configuration.md)** - 如何安装缺失的 ***MCP SERVER***

