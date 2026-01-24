# MCP 别名参考文档

本文档提供完整的 MCP 别名映射表和使用说明，配合 `scripts/call_mcp.py` 中的 `MCP_MAP` 字典使用。

**版本**: v2.2

## 完整别名映射表

### 代码仓库 (GitHub & 代码仓库)

| 别名 | MCP Server | 典型命令 |
|------|------------|----------|
| `gh` | github | list-repos, search-code, prs, issues |
| `github` | github | list-repos, search-code, prs, issues |
| `gitlab` | zread | read_file, get_repo_structure |
| `gitee` | zread | read_file, get_repo_structure |
| `repo` | zread | read_file, get_repo_structure |
| `repository` | zread | read_file, get_repo_structure |
| `开源仓库` | zread | read_file, get_repo_structure |
| `代码仓库` | zread | read_file, get_repo_structure |

**示例：**
```
gh list-repos owner=username
gh search-code query="function_name" language=python
gh prs state=open sort=updated
gh issues labels=bug state=open
```

### 数据库 (Database)

| 别名 | MCP Server | 典型命令 |
|------|------------|----------|
| `db` | mysql | query, execute, schema |
| `database` | mysql | query, execute, schema |
| `sql` | mysql | query, execute, schema |
| `mysql` | mysql | query, execute, schema |
| `查库` | mysql | query, execute, schema |
| `查询数据库` | mysql | query, execute, schema |
| `数据库` | mysql | query, execute, schema |

**示例：**
```
db query "SELECT * FROM users LIMIT 10"
db schema users
db execute "CREATE TABLE test (id INT)"
```

### 浏览器自动化 (Browser)

| 别名 | MCP Server | 典型命令 |
|------|------------|----------|
| `browser` | playwright | goto, screenshot, click, type |
| `web` | playwright | goto, screenshot, click, type |
| `web page` | playwright | goto, screenshot, click, type |
| `chrome` | chrome-devtools | navigate, screenshot, click |
| `firefox` | playwright | goto, screenshot, click, type |
| `edge` | playwright | goto, screenshot, click, type |
| `safari` | playwright | goto, screenshot, click, type |
| `浏览器` | playwright | goto, screenshot, click, type |
| `浏览器测试` | playwright | goto, screenshot, click, type |
| `谷歌浏览器` | chrome-devtools | navigate, screenshot, click |
| `谷歌浏览器测试` | chrome-devtools | navigate, screenshot, click |

**示例：**
```
browser goto https://example.com
browser screenshot
browser click #submit-btn
browser type #search "keyword"
```

### 搜索工具 (Search)

| 别名 | MCP Server | 典型命令 |
|------|------------|----------|
| `search` | web-search-prime | query (with num, location params) |
| `搜索` | web-search-prime | query (with num, location params) |

**示例：**
```
search "latest AI news" num=10
search "Claude Code docs" location=us
```

### 网页读取 (Web Reader)

| 别名 | MCP Server | 典型命令 |
|------|------------|----------|
| `read web` | web-reader | url (with timeout, format params) |
| `web-reader` | web-reader | url (with timeout, format params) |
| `web reader` | web-reader | url (with timeout, format params) |
| `网页读取` | web-reader | url (with timeout, format params) |
| `读取网页` | web-reader | url (with timeout, format params) |

**示例：**
```
read web https://example.com timeout=30 return_format=markdown
web-reader https://docs.claude.com no_cache=true
```

### 图像分析 (Image Analysis)

| 别名 | MCP Server | 典型命令 |
|------|------------|----------|
| `picture` | zai-mcp-server | analyze_image, ui_to_artifact |
| `image` | zai-mcp-server | analyze_image, ui_to_artifact |
| `photo` | zai-mcp-server | analyze_image, ui_to_artifact |
| `illustration` | zai-mcp-server | analyze_image, ui_to_artifact |
| `查看图片` | zai-mcp-server | analyze_image, ui_to_artifact |
| `图片` | zai-mcp-server | analyze_image, ui_to_artifact |
| `图像` | zai-mcp-server | analyze_image, ui_to_artifact |
| `视觉` | zai-mcp-server | analyze_image, ui_to_artifact |

**示例：**
```
image analyze image_source=/path/to/image.png prompt="Describe this"
picture ui_to_artifact output_type=code
```

### API 文档 (API Documentation)

| 别名 | MCP Server | 典型命令 |
|------|------------|----------|
| `API docs` | context7 | resolve-library-id, query-docs |
| `API documentation` | context7 | resolve-library-id, query-docs |
| `API` | context7 | resolve-library-id, query-docs |
| `API文档` | context7 | resolve-library-id, query-docs |

**示例：**
```
API docs react "How to use useEffect"
API resolve-library-id "express"
```

### PDF 读取 (PDF Reader)

| 别名 | MCP Server | 典型命令 |
|------|------------|----------|
| `pdf` | pdf-reader | read_pdf |
| `pdf-reader` | pdf-reader | read_pdf |
| `pdf reader` | pdf-reader | read_pdf |
| `读取pdf` | pdf-reader | read_pdf |
| `pdf读取` | pdf-reader | read_pdf |
| `pdf解析` | pdf-reader | read_pdf |
| `解析pdf` | pdf-reader | read_pdf |

**示例：**
```
pdf read_pdf sources=[{"path": "/path/to/document.pdf"}] include_full_text=true
pdf read_pdf sources=[{"url": "https://example.com/document.pdf", "pages": "1-5"}] include_images=true
```

## 添加新别名

### 步骤

1. **更新 Python 映射字典**

   编辑 `scripts/call_mcp.py`，在 `MCP_MAP` 字典中添加：

   ```python
   MCP_MAP: Dict[str, str] = {
       # ... 现有映射 ...
       "your-alias": "your-mcp-server-name",
   }
   ```

2. **更新本文档**

   在上述表格对应分类中添加新行，或创建新的分类表格。

3. **重新加载 Skill**

   - 方式一：在 Claude Code 中输入 `/reload`
   - 方式二：重启 Claude Code

### 命名规范

- 使用小写字母
- 多词别名用连字符分隔：`web-reader`
- 保持简洁但具描述性
- 考虑添加常用同义词作为额外别名
- 支持中文别名（v2.2+）

## MCP Server 名称参考

以下是一些常见的 MCP Server 名称，供配置时参考：

| Server Name | 描述 |
|-------------|------|
| `github` | GitHub API |
| `gitlab` | GitLab 集成 |
| `gitee` | Gitee 集成 |
| `mysql` | MySQL 数据库 |
| `postgres` | PostgreSQL 数据库 |
| `sqlite` | SQLite 数据库 |
| `playwright` | 浏览器自动化 (Playwright) |
| `chrome-devtools` | Chrome DevTools Protocol |
| `web-search-prime` | 网页搜索 |
| `web-reader` | 网页内容提取 |
| `zai-mcp-server` | 图像/视频分析 |
| `zread` | Git 仓库文件读取 |
| `context7` | API 文档查询 |
| `supabase` | Supabase 集成 |

## 调试技巧

### 测试别名解析

```bash
# 测试单个别名
python3 ~/.claude/skills/mcp-faster-caller/scripts/call_mcp.py "gh list-repos owner=username"

# 查看所有可用别名
python3 -c "import sys; sys.path.insert(0, '~/.claude/skills/mcp-faster-caller/scripts'); from call_mcp import MCP_MAP; print('\\n'.join(sorted(MCP_MAP.keys())))"
```

### 验证 MCP Server 连接

在 Claude Code 中运行：
```
/请问当前配置了哪些 MCP servers？
```

或检查 MCP 配置文件（通常在 `~/.claude/mcp_config.json` 或类似位置）。

## 常见问题

**Q: 为什么某个别名不工作？**

A: 检查以下几点：
1. 别名是否在 `MCP_MAP` 中定义
2. 对应的 MCP Server 是否已安装并配置
3. Server 名称是否拼写正确

**Q: 如何查看某个 MCP Server 支持哪些命令？**

A: 在 Claude Code 中询问：
```
/mcp-faster-caller [server-name] help
```

或查阅该 MCP Server 的官方文档。

**Q: 可以使用中文别名吗？**

A: 是的！v2.2 版本开始全面支持中文别名，为中文用户提供更好的体验。所有重要功能都提供了中英文双语映射。
