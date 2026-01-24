# MCP Faster Caller - 参考文档

这个目录包含 MCP Faster Caller 技能的所有参考文档和配置指南。

**版本**: v2.2

## 📚 文档列表

### [mcp_aliases.md](mcp_aliases.md)
完整的 MCP 别名映射表和使用示例，涵盖所有支持的服务器类型：
- GitHub 操作
- 数据库查询
- 浏览器自动化
- 网页搜索和读取
- 图像分析
- API 文档查询

### [troubleshooting.md](troubleshooting.md)
故障排除指南，包含：
- 常见问题及解决方案
- 调试技巧
- 性能优化建议
- 获取帮助的途径

### [configuration.md](configuration.md)
自定义配置指南，包括：
- 如何添加新别名
- MCP Server 集成方法
- 权限配置
- 高级配置选项

## 🚀 快速开始

1. **查看可用别名**: 参考 [mcp_aliases.md](mcp_aliases.md)
2. **使用技能**: 在 Claude Code 中输入 `/mcp-faster-caller alias command [args]`
3. **遇到问题**: 查看 [troubleshooting.md](troubleshooting.md)
4. **自定义配置**: 参考 [configuration.md](configuration.md)

## 📖 使用示例

```bash
# GitHub 操作
/mcp-faster-caller gh list-repos owner=username

# 数据库查询
/mcp-faster-caller db query "SELECT * FROM users LIMIT 5"

# 浏览器自动化
/mcp-faster-caller browser goto https://example.com
```

## 🔧 维护说明

- `mcp_aliases.md`: 与 `scripts/call_mcp.py` 中的 `MCP_MAP` 保持同步
- `configuration.md`: 更新以反映新的服务器集成
- `troubleshooting.md`: 根据用户反馈添加常见问题

## 📞 获取帮助

如果文档中没有找到答案，请查看主目录的 `SKILL.md` 或在 Claude Code 中寻求帮助。
