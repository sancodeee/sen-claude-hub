---
name: mcp-faster-caller
description: MCP 调用技能，支持中英文双语指令！支持 GitHub 操作、数据库查询、浏览器自动化、网页搜索、图像分析等。使用简单别名快速调用，如：gh（GitHub）、db（数据库）、browser（浏览器）、search（搜索）、image（图像分析）。触发关键词：MCP、mcp、gh、github、git、repo、repository、开源仓库、代码仓库、db、database、sql、mysql、postgres、sqlite、查询数据库、数据库、查库、query、select、browser、浏览器、web、网页、chrome、firefox、edge、safari、谷歌浏览器、浏览器测试、search、搜索、web-reader、网页读取、读取网页、image、picture、photo、illustration、图片、图像、视觉、查看图片、API、API文档、automation、testing、screenshot、navigate、goto、click、type、fast、quick、快捷、快速、call、调用、别名、alias、pdf、pdf-reader、pdf reader、读取pdf、pdf读取、pdf解析、解析pdf
argument-hint: "[别名] [命令] [参数] 例如：gh list-repos owner=用户名 或 数据库 query 'SELECT * FROM table'"
disable-model-invocation: false
user-invocable: true
allowed-tools:
  - Bash
model: inherit
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
   python3 ~/.claude/plugins/cache/sen-claude-hub/mcp-faster-caller/1.0.0/skills/mcp-faster-caller/sc
    +ripts/call_mcp.py "$ARGUMENTS"
   ```
3. 根据返回结果，调用对应的 MCP 工具

### 快速开始

```bash
# GitHub 操作
gh list-repos owner=username

# 数据库操作
db query "SELECT * FROM users LIMIT 5"

# 浏览器自动化
browser goto https://example.com
```

## 更多信息

- 📖 **[完整别名参考](references/mcp_aliases.md)** - 所有可用别名和使用示例
- 🔧 **[故障排除](references/troubleshooting.md)** - 常见问题和解决方案
- ⚙️ **[自定义配置](references/configuration.md)** - 如何添加新别名（代码修改方式）以及安装当前缺失的MCP
