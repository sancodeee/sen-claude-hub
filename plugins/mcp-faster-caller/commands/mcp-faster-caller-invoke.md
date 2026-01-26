---
name: mcp-faster-caller:invoke
description: Immediately call the mcp-faster-caller skill to handle the user's current needs.
argument-hint: "[alias] [command] [arguments] 例如：gh list-repos owner=用户名 或 数据库 query 'SELECT * FROM table'"
---

你现在必须**立即且强制**调用已安装的 **mcp-faster-caller** 这个 skill 来处理用户当前的需求。

用户提供的额外参数/需求（通过 $ARGUMENTS 传入到 mcp-faster-caller skill）：
$ARGUMENTS

现在开始：调用 fintorq-code-style skill，并基于它的输出完整响应用户的最新消息。