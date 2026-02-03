---
name: agent-browser-integration-testing:invoke
description: Immediately call the agent-browser-integration-testing skill to perform browser automation testing (inspect, run custom steps, or auto smoke test).
argument-hint: "[mode] [url] [steps] 例如：inspect https://example.com 或 run https://example.com '[{\"action\":\"click\",\"target\":\"#btn\"}]' 或 auto https://example.com"
---

你现在必须**立即且强制**调用已安装的 **agent-browser-integration-testing** 这个 skill 来处理用户当前的需求。

用户提供的额外参数/需求（通过 $ARGUMENTS 传入 agent-browser-integration-testing skill）：
$ARGUMENTS

现在开始：解析 $ARGUMENTS，调用 agent-browser-integration-testing skill，并基于输出生成完整的**Markdown**测试报告。
