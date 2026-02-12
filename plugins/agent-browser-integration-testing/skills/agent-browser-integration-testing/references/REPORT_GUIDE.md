# 测试报告生成指南

## 报告文件路径格式
---
测试报告将保存在以下路径结构中：
- 目录：`testing-report/report-{timestamp}/`
- 文件名：`yyyyMMddHHmmss-{business name}-report.md`

其中：
- `{timestamp}`：测试开始时间戳
- `yyyyMMddHHmmss`：格式化的时间戳（如：20250209143022）
- `{business name}`：根据测试业务主题自定义的名称
---

**角色要求**：当你使用 `agent-browser-integration-testing` 技能完成测试后，你**必须**为用户生成一份最终报告。报告必须严格遵循以下结构和要求，使用清晰、专业、结构化的 Markdown 格式。报告的目标是让用户一目了然地了解测试全貌、关键结果、问题点及证据。

## Integration Test Report（集成测试报告）

**用户原始需求**：[用户需求原文]（用户使用agent-browser-integration-testing skill时提出的需求原文）
**目标 URL**： [完整测试目标 URL]  
**日期与时间**： [YYYY-MM-DD HH:MM:SS]（使用测试完成时的实际时间）  
**总体状态**： [PASS / FAIL / WARN]  
**总耗时**： [X.X 秒]（从 open 到最后一次操作的累计耗时，如有多个会话则汇总）

### 1. 测试摘要（Test Summary）

- **工作流类型**： [迭代快照 + 原子动作]（固定描述当前技能的标准工作流）
- **执行的总命令数**： [N]（包括 open、snapshot、fill、click、wait、screenshot 等所有命令）
- **成功命令数**： [N]
- **失败命令数**： [N]
- **访问的关键页面数**： [N]（统计发生导航的次数或列出主要页面 URL）
- **生成的截图数量**： [N]

### 2. 关键发现（Key Findings）

- [成功点描述，例如：登录表单填写正常，点击登录按钮后成功导航至仪表盘页面]
- [成功点描述，例如：页面关键交互元素（如用户名、密码、登录按钮）均可通过 ref 稳定定位]
- [问题点描述，例如：点击“提交”后出现超时，页面未跳转]
- [问题点描述，例如：某些动态加载元素在首次 snapshot 中未出现，需要额外 wait]
- [其他观察，例如：检测到页面包含以下导航链接：/dashboard、/profile、/logout]
- [性能观察，例如：页面平均加载时间约 X 秒，首次 snapshot 耗时 Y ms]
- **如果有失败**：必须在此明确列出错误信息（如 timeout、element not found、JS error 等）并说明可能原因

### 3. 执行日志（Execution Log）

使用 Markdown 表格格式，记录每一步的关键操作。表格必须包含以下列：

| 步骤 | 命令                  | 目标 / Ref                    | 状态 | 耗时 (秒) | 详情 / 错误信息                          |
|------|-----------------------|-------------------------------|------|-----------|------------------------------------------|
| 1    | open                  | https://example.com/login     | ✅   | 2.1       | 页面加载成功                             |
| 2    | snapshot -i --json    | -                             | ✅   | 0.4       | 找到 3 个交互元素 (@e1–@e3)               |
| 3    | fill                  | @e1                           | ✅   | 0.3       | 填写用户名                               |
| 4    | fill                  | @e2                           | ✅   | 0.3       | 填写密码                                 |
| 5    | click                 | @e3                           | ✅   | 1.8       | 导航至仪表盘                             |
| 6    | wait --text           | "Welcome back"                | ✅   | 0.9       | 文案出现                                 |
| 7    | screenshot            | after-login.png               | ✅   | 0.5       | 截图已保存                               |

- 每行对应一次主要工具调用
- 状态使用 ✅（成功）或 ❌（失败）
- 详情列中包含关键结果或完整错误信息

### 4. 网络交互审计（Network Interaction Audit）

> **重要说明**：此部分**仅**列出测试过程中触发的后端 API 接口调用（XHR/Fetch）。
> - ✅ **包含**：POST /api/xxx、GET /api/xxx 等 XHR/Fetch 请求
> - ❌ **排除**：HTML页面导航、JS/CSS静态资源、图片、字体等

**分类规则**：
1. **后端API接口**（type="xhr" 或 type="fetch"）→ 记录到 **4.1 节**
2. **异常/关键API接口详情**（type="xhr" 或 type="fetch"）→ 记录到 **4.2 节**
3. **静态资源**（type="script", "stylesheet", "image", "font" 等）→ 记录到 **4.3 节（可选）**
4. **页面导航**（type="document"）→ 记录到"**执行日志**"而非API审计

#### 4.1 后端API接口调用概览

| Method | 接口路径 (Path Only) | 状态码 | 耗时 (ms) | 结果判定 | 业务说明 |
|--------|---------------------|--------|-----------|----------|----------|
| POST   | /api/v1/auth/login  | 200    | 450       | ✅ 成功   | 用户登录 |
| GET    | /api/v1/user/profile | 200   | 120       | ✅ 成功   | 获取用户信息 |
| POST   | /api/v1/orders/create | 400   | 85        | ❌ 失败   | 创建订单 |
| GET    | /api/v1/notifications | 500   | 1200      | ❌ 异常   | 获取通知列表 |

**关键发现**：（根据实际测试情况填写）
- 系统使用 JWT Token 认证
- 所有 API 请求携带自定义请求头
- 发现 X 个接口响应异常

#### 4.2 异常/关键接口详情

对于**所有失败的接口**（非 2xx）以及**关键业务接口**（如登录、提交订单），必须在下方提供详细的请求与响应信息（使用折叠块）：

<details>
<summary>❌ <b>POST /api/v1/orders/create (Status: 400)</b></summary>

**Request Payload:**
```json
{
  "productId": 123,
  "quantity": -1
}
```

**Response Body:**
```json
{
  "error": "Bad Request",
  "message": "Quantity must be positive"
}
```

**关键请求头（可选）:**
```
Content-Type: application/json
Authorization: Bearer xxx
```
</details>

<details>
<summary>✅ <b>POST /api/v1/auth/login (Status: 200)</b></summary>

**Request Payload:**
```json
{
  "username": "testuser",
  "password": "******"
}
```

**Response Body:**
```json
{
  "token": "eyJhbG...",
  "user": { "id": 101, "role": "admin" }
}
```

**关键请求头（可选）:**
```
Content-Type: application/json
```
</details>

#### 4.3 前端资源加载记录（可选）

> 仅在需要性能分析或资源问题时添加此小节

| 类型 | 数量 | 总耗时 (ms) | 备注 |
|------|------|------------|------|
| JS资源 | 5 | ~800 | 动态chunk加载策略 |
| CSS资源 | 2 | ~150 | 样式文件 |
| 其他资源 | 3 | ~200 | 第三方服务（如验证码） |

### 5. 举证（Evidence）

- **截图**：
  > **重要**：必须使用 Markdown 图片语法 (`![alt text](path)`) 直接嵌入截图，**严禁**只列出文件名或路径。确保图片能在报告中直接渲染展示。

  ![[简要描述]]([文件相对路径])
  *图1：[详细描述，例如：登录页面初始状态]*

  ![[简要描述]]([文件相对路径])
  *图2：[详细描述，例如：登录成功后的仪表盘页面]*

  （如果生成多个截图，必须按此格式全部展示）
- **最终页面标题**： [捕获的最终页面标题]
- **最终 URL**： [测试结束时的当前 URL]
- **关键快照摘录**（可选但强烈推荐）：列出最后一次 snapshot 中最重要的几个 ref 及其描述

### 6. 建议（Recommendations）（新增必填部分）

- [如果通过]：建议下一步功能测试点或生产环境监控建议
- [如果失败]：明确的重现步骤、可能的根本原因（如网络问题、动态加载、反爬虫机制）、修复建议
- [通用优化建议]：是否需要增加 wait 时间、调整定位策略、使用 headless 模式等
- [安全性/兼容性观察]：如发现敏感字段未脱敏、移动端适配问题等

**Agent 注意事项**：

- 【**必须**】你必须从多次工具调用（open、snapshot、fill、click、screenshot、get text 等）的输出中汇总信息来填充报告。
- 【**必须**】所有字段必须真实填充，不能留空或使用占位符。
- 【**必须**】报告必须客观、详尽、易读；优先使用表格和列表提升可读性。
- 【**必须**】如果测试涉及多个页面或长流程，建议在“关键发现”中增加小节分段。
- 【**必须**】最终报告必须独立成文，直接回复给用户，无需额外解释。