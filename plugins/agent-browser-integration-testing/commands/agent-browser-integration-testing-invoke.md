---
name: agent-browser-integration-testing:invoke
description: Immediately call the agent-browser-integration-testing skill to perform browser automation testing (inspect, run custom steps, or auto smoke test).
argument-hint: "[mode] [url] [steps] 例如：inspect https://example.com 或 run https://example.com '[{\"action\":\"click\",\"target\":\"#btn\"}]' 或 auto https://example.com"
---

你现在必须**立即且强制**调用已安装的 **agent-browser-integration-testing** 这个 skill 来处理用户当前的需求。

用户提供的额外参数/需求（通过 $ARGUMENTS 传入）：
$ARGUMENTS

核心处理逻辑：

1. 解析 $ARGUMENTS 确定测试模式和参数：
   - `inspect <url>`: 分析页面 DOM 结构，返回可交互元素列表（inputs, buttons, links）
   - `run <url> <steps_json>`: 执行自定义测试步骤序列
   - `auto <url>`: 自动执行启发式冒烟测试

2. 支持的原子动作（用于 run 模式的 steps_json）：
   - `fill`: 填充输入框 `{"action": "fill", "target": "selector", "value": "text"}`
   - `click`: 点击元素 `{"action": "click", "target": "selector"}`
   - `wait`: 等待秒数 `{"action": "wait", "value": seconds}`
   - `screenshot`: 截图 `{"action": "screenshot"}`
   - `verify_text`: 验证文本 `{"action": "verify_text", "value": "expected text"}`

3. 测试工作流程（复杂测试场景）：
   - 首先使用 `inspect` 模式获取页面结构
   - 分析 JSON 输出，识别目标元素选择器
   - 构建 JSON 动作序列
   - 使用 `run` 模式执行动作序列
   - 根据 `references/REPORT_GUIDE.md` 生成 Markdown 测试报告

4. 如果 $ARGUMENTS 为空或格式不正确，询问用户：
   - 要测试的 URL
   - 测试模式（inspect/run/auto）
   - 如果是 run 模式，需要测试步骤 JSON 数组

5. 报告生成要求：
   - 使用 `references/REPORT_GUIDE.md` 中的报告模板
   - 包含测试摘要、关键发现、执行日志和证据（截图、页面标题）
   - 将 JSON 结果转换为用户可读的表格格式

现在开始：解析 $ARGUMENTS，调用 agent-browser-integration-testing skill，并基于输出生成完整的测试报告。
