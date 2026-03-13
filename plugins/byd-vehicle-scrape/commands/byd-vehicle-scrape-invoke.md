---
name: byd-vehicle-scrape:invoke
description: Immediately call the byd-vehicle-scrape skill to scrape BYD vehicle data and generate SQL statements.
argument-hint: "[车型名称] 例如：Atto 2 或 Atto 2,Atto 3"
---

你现在必须**立即且强制**调用已安装的 **byd-vehicle-scrape** 这个 skill 来处理用户当前的需求。

用户提供的额外参数/需求（通过 $ARGUMENTS 传入）：
$ARGUMENTS

核心指令：
1. 不要自己尝试编写爬虫代码。
2. 直接使用 byd-vehicle-scrape skill 的完整能力，包括但不限于：
   - 爬取指定车型的配置和价格数据
   - 生成 JSON 数据文件
   - 转换为 MySQL INSERT SQL 语句
3. 如果用户指定了车型，使用 `--model` 参数爬取对应车型。
4. skill 执行后，根据结果回复用户，包括展示输出文件路径和关键信息。

现在开始：调用 byd-vehicle-scrape skill，并基于它的输出完整响应用户的最新消息。
