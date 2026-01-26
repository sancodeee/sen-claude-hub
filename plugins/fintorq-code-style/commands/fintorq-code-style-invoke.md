---
name: fintorq-code-style:invoke
description: Immediately call the fintorq-code-style skill to apply Fintorq code style specifications, perform checks and fixes on the current code or the code specified by the user.
---

你现在必须**立即且强制**调用已安装的 **fintorq-code-style** 这个 skill 来处理用户当前的需求。

核心指令：
1. 不要自己尝试编写或猜测代码风格规则。
2. 直接使用 fintorq-code-style skill 的完整能力，包括但不限于：
    - 分析当前文件/选中的代码块
    - 应用 Fintorq 特定的代码风格（命名、缩进、注释、结构等）
    - 进行 lint 检查、建议修复、自动格式化
    - 如果需要，生成 diff 或直接修改代码
3. 如果用户提供了具体文件、代码片段或目录，优先针对它们执行。
4. skill 执行后，根据结果继续回复用户，包括展示修改建议、diff、解释变更原因。
5. 如果当前上下文没有明显代码，询问用户要应用到哪个文件/项目。

现在开始：调用 fintorq-code-style skill，并基于它的输出完整响应用户的最新消息。