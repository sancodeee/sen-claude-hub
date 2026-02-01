# 浏览器集成测试报告模板

使用此模板在执行浏览器集成测试后生成完整的 Markdown 测试报告。

**版本 4.1.0** - 支持自动遍历测试、API 覆盖率、所有表单元素类型和智能并行测试

---

# 浏览器集成测试报告

## 测试元数据

| 字段 | 值 |
|-------|-------|
| **URL** | {{TEST_URL}} |
| **操作类型** | {{TEST_OPERATION}} |
| **时间戳** | {{TEST_TIMESTAMP}} |
| **测试 ID** | {{TEST_ID}} |
| **脚本版本** | 4.1.0 (Python Enhanced) |
| **浏览器** | Chrome (via agent-browser) |
| **测试执行者** | Claude (agent-browser-integration-test) |

## 执行摘要

{{TEST_SUMMARY}}

### 测试概览

| 指标 | 值 |
|--------|-------|
| 总测试数 | {{TOTAL_TESTS}} |
| 通过 | {{PASSED_TESTS}} |
| 失败 | {{FAILED_TESTS}} |
| 跳过 | {{SKIPPED_TESTS}} |
| 通过率 | {{PASS_RATE}}% |
| 持续时间 | {{TEST_DURATION}} |

---

## 详细测试结果

### 1. 可访问性测试

验证页面可访问性和基本功能。

| 测试用例 | 状态 | 详情 |
|-----------|--------|---------|
| 页面成功加载 | {{PAGE_LOAD_STATUS}} | {{PAGE_LOAD_DETAILS}} |
| 加载时无控制台错误 | {{CONSOLE_ERROR_STATUS}} | {{CONSOLE_ERROR_DETAILS}} |
| 页面标题存在 | {{TITLE_STATUS}} | 标题："{{PAGE_TITLE}}" |
| Meta 描述存在 | {{META_DESC_STATUS}} | {{META_DESC_DETAILS}} |
| 视口已配置 | {{VIEWPORT_STATUS}} | {{VIEWPORT_DETAILS}} |

**证据：**
- 初始加载时间：{{LOAD_TIME_MS}}ms
- 截图：`{{INITIAL_SCREENSHOT}}`

---

### 2. 导航测试

验证所有导航元素正常工作。

| 测试用例 | 状态 | 详情 |
|-----------|--------|---------|
| 发现的链接总数 | {{LINK_COUNT}} | {{LINK_BREAKDOWN}} |
| 内部链接有效 | {{INTERNAL_LINK_STATUS}} | 测试了 {{INTERNAL_LINK_COUNT}} 个链接 |
| 外部链接有效 | {{EXTERNAL_LINK_STATUS}} | 测试了 {{EXTERNAL_LINK_COUNT}} 个链接 |
| 无损坏链接 (404) | {{BROKEN_LINK_STATUS}} | {{BROKEN_LINK_DETAILS}} |

**证据：**
{{NAVIGATION_DETAILS}}

---

### 3. 表单测试

验证表单功能（用于 CREATE/UPDATE 操作）。

| 测试用例 | 状态 | 详情 |
|-----------|--------|---------|
| 检测到表单 | {{FORM_DETECTED_STATUS}} | 发现 {{FORM_COUNT}} 个表单 |
| 输入字段可访问 | {{INPUT_STATUS}} | {{INPUT_COUNT}} 个输入框 |
| 验证功能正常 | {{VALIDATION_STATUS}} | {{VALIDATION_DETAILS}} |
| 提交按钮功能正常 | {{SUBMIT_STATUS}} | {{SUBMIT_DETAILS}} |
| 成功/错误消息 | {{MESSAGE_STATUS}} | {{MESSAGE_DETAILS}} |

**证据：**
- 提交前截图：`{{PRE_SUBMIT_SCREENSHOT}}`
- 提交后截图：`{{POST_SUBMIT_SCREENSHOT}}`
- 表单数据：{{FORM_DATA}}

---

### 4. 内容测试

验证页面内容和媒体（用于 READ 操作）。

| 测试用例 | 状态 | 详情 |
|-----------|--------|---------|
| 关键内容存在 | {{CONTENT_STATUS}} | {{CONTENT_DETAILS}} |
| 图片正确加载 | {{IMAGE_STATUS}} | {{IMAGE_COUNT}} 张图片，{{BROKEN_IMAGE_COUNT}} 张损坏 |
| 无损坏媒体 | {{MEDIA_STATUS}} | {{MEDIA_DETAILS}} |
| 响应式布局 | {{RESPONSIVE_STATUS}} | {{RESPONSIVE_DETAILS}} |

**证据：**
- 页面文本长度：{{PAGE_TEXT_LENGTH}} 个字符
- 标题结构：{{HEADING_STRUCTURE}}
{{CONTENT_EVIDENCE}}

---

### 5. 交互测试

验证用户交互（用于 DELETE/UPDATE 操作）。

| 测试用例 | 状态 | 详情 |
|-----------|--------|---------|
| 按钮可点击 | {{BUTTON_STATUS}} | {{BUTTON_COUNT}} 个按钮 |
| 确认对话框正常 | {{CONFIRM_STATUS}} | {{CONFIRM_DETAILS}} |
| 状态变化持久化 | {{STATE_STATUS}} | {{STATE_DETAILS}} |
| 操作可撤销 | {{REVERSIBLE_STATUS}} | {{REVERSIBLE_DETAILS}} |

**证据：**
{{INTERACTION_EVIDENCE}}

---

## API 测试覆盖 (新增 - 用于 ALL 操作)

此章节仅在执行 `all` 操作时生成，展示测试过程中捕获的所有 API 调用。

### API 端点覆盖

| 方法 | 端点 | 状态 | 响应时间 |
|---|---|---|---|
| {{API_METHOD}} | {{API_ENDPOINT}} | {{API_STATUS_ICON}} {{API_STATUS}} | {{API_TIMING}}ms |

**总计**: {{TOTAL_API_CALLS}} 个 API 调用

### 按方法分类

| 方法 | 数量 |
|---|---|
| GET | {{GET_COUNT}} |
| POST | {{POST_COUNT}} |
| PUT | {{PUT_COUNT}} |
| DELETE | {{DELETE_COUNT}} |
| PATCH | {{PATCH_COUNT}} |
| OTHER | {{OTHER_COUNT}} |

### API 响应状态分布

| 状态码 | 数量 | 百分比 |
|--------|------|--------|
| 2xx (成功) | {{SUCCESS_COUNT}} | {{SUCCESS_PERCENT}}% |
| 3xx (重定向) | {{REDIRECT_COUNT}} | {{REDIRECT_PERCENT}}% |
| 4xx (客户端错误) | {{CLIENT_ERROR_COUNT}} | {{CLIENT_ERROR_PERCENT}}% |
| 5xx (服务器错误) | {{SERVER_ERROR_COUNT}} | {{SERVER_ERROR_PERCENT}}% |

---

## 交互元素测试结果 (新增 - 用于 ALL 操作)

此章节展示每个交互元素的测试结果。

### 元素测试矩阵

| 元素类型 | 文本 | 操作 | 状态 | API调用 |
|---|---|---|---|---|
| {{ELEMENT_TYPE}} | {{ELEMENT_TEXT}} | {{ELEMENT_ACTION}} | {{ELEMENT_STATUS}} | {{ELEMENT_APIS}} |

### 按类型统计

| 元素类型 | 已测试 | 成功 | 失败 | 跳过 |
|---|---|---|---|---|
| button | {{BUTTON_TESTED}} | {{BUTTON_PASSED}} | {{BUTTON_FAILED}} | {{BUTTON_SKIPPED}} |
| link | {{LINK_TESTED}} | {{LINK_PASSED}} | {{LINK_FAILED}} | {{LINK_SKIPPED}} |
| input | {{INPUT_TESTED}} | {{INPUT_PASSED}} | {{INPUT_FAILED}} | {{INPUT_SKIPPED}} |
| select | {{SELECT_TESTED}} | {{SELECT_PASSED}} | {{SELECT_FAILED}} | {{SELECT_SKIPPED}} |
| checkbox | {{CHECKBOX_TESTED}} | {{CHECKBOX_PASSED}} | {{CHECKBOX_FAILED}} | {{CHECKBOX_SKIPPED}} |
| radio | {{RADIO_TESTED}} | {{RADIO_PASSED}} | {{RADIO_FAILED}} | {{RADIO_SKIPPED}} |

---

## 测试覆盖率摘要 (新增 - 用于 ALL 操作)

| 维度 | 已测试 | 总数 | 覆盖率 |
|---|---|---|---|
| 交互元素 | {{TESTED_ELEMENTS}} | {{TOTAL_ELEMENTS}} | {{ELEMENT_COVERAGE}}% |
| API 调用 | {{TESTED_APIS}} | {{TOTAL_APIS}} | {{API_COVERAGE}}% |
| 导航链接 | {{TESTED_LINKS}} | {{TOTAL_LINKS}} | {{LINK_COVERAGE}}% |

---

## 风险评估 (新增 - 用于 ALL 操作)

此章节展示危险操作的测试情况。

### 危险操作汇总

| 风险级别 | 检测到 | 已确认执行 | 已跳过 |
|---|---|---|---|
| CRITICAL | {{CRITICAL_DETECTED}} | {{CRITICAL_CONFIRMED}} | {{CRITICAL_SKIPPED}} |
| HIGH | {{HIGH_DETECTED}} | {{HIGH_CONFIRMED}} | {{HIGH_SKIPPED}} |
| MEDIUM | {{MEDIUM_DETECTED}} | {{MEDIUM_CONFIRMED}} | {{MEDIUM_SKIPPED}} |

### 跳过的操作详情

- ⏭️ **{{SKIPPED_TYPE}}**: {{SKIPPED_TEXT}} ({{SKIPPED_RISK}})
- ⏭️ **{{SKIPPED_TYPE}}**: {{SKIPPED_TEXT}} ({{SKIPPED_RISK}})

### 确认执行的操作详情

- ✅ **{{CONFIRMED_TYPE}}**: {{CONFIRMED_TEXT}} ({{CONFIRMED_RISK}})
- ✅ **{{CONFIRMED_TYPE}}**: {{CONFIRMED_TEXT}} ({{CONFIRMED_RISK}})

---

## 控制台输出

### 错误
{{CONSOLE_ERRORS}}

### 警告
{{CONSOLE_WARNINGS}}

### 信息消息
{{CONSOLE_INFO}}

---

## 网络分析

### 请求摘要

| 指标 | 值 |
|--------|-------|
| 总请求数 | {{TOTAL_REQUESTS}} |
| 成功 | {{SUCCESS_REQUESTS}} |
| 失败 | {{FAILED_REQUESTS}} |
| 平均响应时间 | {{AVG_RESPONSE_TIME}}ms |

### 失败的请求
{{FAILED_REQUESTS_DETAILS}}

### 慢请求 (>1000ms)
{{SLOW_REQUESTS_DETAILS}}

---

## 性能指标

| 指标 | 值 | 阈值 | 状态 |
|--------|-------|-----------|--------|
| 页面加载时间 | {{PAGE_LOAD_TIME}}ms | <3000ms | {{LOAD_TIME_STATUS}} |
| 可交互时间 | {{TTI}}ms | <5000ms | {{TTI_STATUS}} |
| 总资源数 | {{TOTAL_RESOURCES}} | <100 | {{RESOURCES_STATUS}} |
| 页面大小 | {{PAGE_SIZE}}MB | <5MB | {{SIZE_STATUS}} |

---

## 截图

### 初始页面加载
![初始加载]({{INITIAL_SCREENSHOT_PATH}})

### 表单填充后
{{FORM_FILLED_SCREENSHOT}}

### 关键操作后
{{ACTION_SCREENSHOTS}}

### 最终状态
{{FINAL_SCREENSHOT}}

---

## 测试建议

### 严重问题
{{CRITICAL_ISSUES}}

### 改进建议
{{IMPROVEMENTS}}

### 优化建议
{{SUGGESTIONS}}

---

## 测试执行日志

```
{{TEST_LOG}}
```

---

## 结论

{{CONCLUSION}}

### 测试完成时间
{{COMPLETION_TIMESTAMP}}

### 报告生成时间
{{REPORT_GENERATION_TIMESTAMP}}

---

## 附录

### 风险级别定义

| 风险级别 | 描述 | 示例关键词 |
|---|---|---|
| CRITICAL | 数据丢失操作 | delete, destroy, remove, 删除, 移除 |
| HIGH | 会话结束、财务操作 | pay, checkout, logout, 支付, 登出 |
| MEDIUM | 数据导出、批量操作 | export, download, reset, 导出, 重置 |
| LOW | 普通操作 | 其他所有交互 |

### 测试数据生成规则

| 字段类型/名称 | 生成值 |
|---|---|
| email | test_{timestamp}@example.com |
| password | TestPass123! |
| phone/tel/mobile | 138{随机8位数字} |
| url/website | https://example.com |
| date | 今日日期 (ISO格式) |
| number | 1-100 随机数 |
| text/default | Test Data {timestamp} |

### 测试限制

- 导航链接最多测试 10 个
- 安全操作最多测试 20 个按钮
- 危险操作需要用户确认
- 危险操作可以跳过或中止测试
