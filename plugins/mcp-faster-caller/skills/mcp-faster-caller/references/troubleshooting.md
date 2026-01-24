# 故障排除指南

## 常见问题

### Skill 未触发
**问题**: Skill 未被 Claude 调用或无法通过 `/mcp-faster-caller` 命令触发

**解决方案**:
- 确认路径：`~/.claude/skills/mcp-faster-caller/SKILL.md`
- 检查文件权限和目录结构
- 运行 `/reload` 重新加载技能
- 重启 Claude Code

### 脚本报错
**问题**: 执行 Python 脚本时出现错误

**解决方案**:
- 检查 `python3` 是否可用: `python3 --version`
- 确认脚本有执行权限: `chmod +x scripts/call_mcp.py`
- 验证脚本路径是否正确

### 未知 alias
**问题**: 使用别名时提示"未知 alias"

**解决方案**:
- 查看 `MCP_MAP` 字典中的可用别名
- 检查别名拼写是否正确（大小写敏感）
- 添加新的别名映射（见[自定义配置](configuration.md)）

### MCP Server 未配置
**问题**: 提示找不到对应的 MCP Server

**解决方案**:
- 检查 MCP 配置文件（通常在 `~/.claude/mcp_config.json`）
- 确认服务器已正确安装和配置
- 验证服务器名称是否与 `MCP_MAP` 中的匹配

## 调试方式

### 测试别名解析
```bash
# 直接测试解析脚本
python3 ~/.claude/skills/mcp-faster-caller/scripts/call_mcp.py "gh list-repos owner=username"

# 查看所有可用别名
python3 -c "import sys; sys.path.insert(0, '~/.claude/skills/mcp-faster-caller/scripts'); from call_mcp import MCP_MAP; print('\n'.join(sorted(MCP_MAP.keys())))"
```

### 验证 MCP Server 连接
在 Claude Code 中运行：
```
/mcp-faster-caller gh help
```

或检查 MCP 配置文件。

### 日志查看
如果仍有问题，可以查看 Claude Code 的日志输出获取更多调试信息。

## 性能优化

- **Token 节省**: 本技能将典型 MCP 调用从 80-300 token 压缩到 10-25 token
- **响应速度**: 通过预解析减少 Claude 的推理时间
- **内存使用**: 脚本轻量化，不占用过多资源

## 获取帮助

如果问题仍然存在：
1. 提供完整的错误信息
2. 说明使用的指令和期望结果
3. 提及您的操作系统和 Python 版本