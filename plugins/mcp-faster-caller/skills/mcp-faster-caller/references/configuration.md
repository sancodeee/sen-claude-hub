# 自定义配置指南

**版本**: v2.2

## 添加新别名

### 步骤

1. **编辑 Python 映射字典**

   打开 `scripts/call_mcp.py`，在 `MCP_MAP` 字典中添加新的映射：

   ```python
   MCP_MAP: Dict[str, str] = {
       # ... 现有映射 ...
       "your-alias": "your-mcp-server-name",
       "your-chinese-alias": "your-mcp-server-name",  # 支持中文别名
   }
   ```

2. **更新别名文档**

   编辑 `references/mcp_aliases.md`，在对应分类中添加新行：

   ```markdown
   | your-alias | your-mcp-server-name | 描述命令 |
   | your-chinese-alias | your-mcp-server-name | 描述命令 |
   ```

3. **重新加载 Skill**

    - 方法一：在 Claude Code 中输入 `/reload`
    - 方法二：重启 Claude Code

### 命名规范

- 使用小写字母
- 多词别名用连字符分隔：`web-reader`
- 保持简洁但具描述性
- 考虑添加常用同义词作为额外别名
- 支持中文别名，提供更好的本地化体验

## MCP Server 集成

### 常用 Server 类型

| Server 类型   | 描述            | 配置要点                   |
|-------------|---------------|------------------------|
| GitHub      | GitHub API 集成 | 需要 GitHub Token        |
| Database    | 数据库连接         | 需要连接字符串                |
| Browser     | 浏览器自动化        | 需要 Playwright/Chromium |
| Search      | 网页搜索          | 需要搜索 API 密钥            |
| File System | 文件系统操作        | 本地文件权限                 |

### MCP Server 配置示例

#### GitHub Server

```bash
claude mcp add --transport http github --scope user https://api.githubcopilot.com/mcp -H "Authorization: Bearer YOUR_API_KEY"
```

##### Github API_KEY获取

- 从官网获取API_KEY: https://github.com/settings/personal-access-tokens/new

#### MySQL Database

```bash
claude mcp add mysql_blog_db \
-e MYSQL_HOST="$YOUR_MYSQL_HOST" \
-e MYSQL_PORT="$YOUR_MYSQL_PORT" \
-e MYSQL_USER="$YOUR_MYSQL_USER" \
-e MYSQL_PASS="$YOUR_MYSQL_PASS" \
-e MYSQL_DB="$DB_NAME" \
-e MYSQL_ENABLE_LOGGING="true" \
-e ALLOW_INSERT_OPERATION="false" \
-e ALLOW_UPDATE_OPERATION="false" \
-e ALLOW_DELETE_OPERATION="false" \
-- node $(npm root -g)/@benborla29/mcp-server-mysql/dist/index.js
```

#### Chrome devtools MCP

```bash
claude mcp add chrome-devtools -- npx chrome-devtools-mcp@latest
```

#### Playwright MCP

```bash
claude mcp add playwright npx @playwright/mcp@latest
```

#### Context7 MCP

```bash
claude mcp add context7 -- npx -y @upstash/context7-mcp --api-key YOUR_API_KEY
```

##### Context7 API Keys获取方式

- 从官网获取API_KEY: https://context7.com/dashboard

#### Pdf-reader MCP

```bash
claude mcp add pdf-reader -- npx @sylphx/pdf-reader-mcp
```

#### Web-reader MCP

```bash
claude mcp add -s user -t http web-reader https://open.bigmodel.cn/api/mcp/web_reader/mcp --header "Authorization: Bearer your_api_key"
```

##### 获取Web-search-prime API_KEY方式

- 从官网获取API_KEY: https://bigmodel.cn/usercenter/proj-mgmt/apikeys

#### Web-search-prime MCP

```bash
claude mcp add -s user -t http web-search-prime https://open.bigmodel.cn/api/mcp/web_search_prime/mcp --header "Authorization: Bearer your_api_key"
```

##### 获取Zread API_KEY方式

- 从官网获取API_KEY: https://bigmodel.cn/usercenter/proj-mgmt/apikeys

#### Zai-mcp-server MCP

```bash
claude mcp add -s user zai-mcp-server --env Z_AI_API_KEY=your_api_key -- npx -y "@z_ai/mcp-server"
```

##### 获取Zread API_KEY方式

- 从官网获取API_KEY: https://bigmodel.cn/usercenter/proj-mgmt/apikeys

#### Zread MCP

```bash
claude mcp add -s user -t http zread https://open.bigmodel.cn/api/mcp/zread/mcp --header "Authorization: Bearer your_api_key"
```

##### 获取Zread API_KEY方式

- 从官网获取API_KEY: https://bigmodel.cn/usercenter/proj-mgmt/apikeys

## 权限配置

### 技能权限

编辑 `.claude/settings.local.json` 来控制技能的工具权限：

```json
{
  "permissions": {
    "allow": [
      "Bash(tree:*)",
      "Bash(python3 scripts/call_mcp.py:*)",
      "Bash(chmod:*)"
    ]
  }
}
```

### MCP Server 权限

某些 MCP Server 可能需要额外的权限配置，请参考各 Server 的文档。

## 环境变量配置

可以通过环境变量自定义行为：

- `MCP_FAST_CALLER_DEBUG=1`: 启用调试模式

## 最佳实践

1. **测试新别名**: 添加新别名后，先在命令行测试解析脚本
2. **文档同步**: 确保 `MCP_MAP` 字典和文档始终同步
3. **权限最小化**: 只授予必要的工具权限
4. **错误处理**: 为新集成添加适当的错误处理
5. **性能监控**: 监控 token 使用量和响应时间
6. **双语支持**: 为重要功能同时提供中文和英文别名

## 扩展开发

### 添加新的 Server 类型

1. 实现 Server 适配器
2. 在 `MCP_MAP` 中注册别名
3. 更新文档
4. 添加测试用例

### 自定义解析逻辑

修改 `parse_mcp_call()` 函数来支持更复杂的指令格式。

## 版本升级说明

### v2.2 更新内容

- **高性能优化**: 移除配置文件加载，提升启动速度
- **双语别名映射**: 支持中英文双语别名，提供更好的用户体验
- **代码化配置**: 通过直接修改 `MCP_MAP` 字典进行配置
- **简化架构**: 移除不必要的文件系统操作

### 从旧版本升级

如果您之前使用过配置文件，请：

1. 将配置文件中的别名手动添加到 `scripts/call_mcp.py` 的 `MCP_MAP` 字典中
2. 更新相关文档
3. 删除不再使用的配置文件
