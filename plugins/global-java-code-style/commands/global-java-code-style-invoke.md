---
name: global-java-code-style:invoke
description: Immediately call the global-java-code-style skill to apply the global-java-code-style specifications to the current code or the code specified by the user.
argument-hint: "[issue description]"
---

你现在必须**立即且强制**调用已安装的 **global-java-code-style** 这个 skill 来处理用户当前的需求。

用户提供的"[issue description]"额外参数/需求（通过 $ARGUMENTS 传入 global-java-code-style skill）：
$ARGUMENTS

核心处理逻辑：

1. 如果 $ARGUMENTS 为空（用户只输入 /global-java-code-style:invoke），默认针对当前活跃文件、选中的代码块或整个项目应用全局
   Java 代码风格规范检查，包括但不限于：
    - 命名规范（类、方法、变量、常量等）
    - 缩进、换行、空格规则
    - 注释风格（Javadoc 要求等）
    - 代码结构优化（方法长度、类组织）
    - 常见 Java 最佳实践和 lint 规则检查

2. 如果 $ARGUMENTS 不为空，解析并优先使用其中的信息：
    - 如果包含文件路径（如 src/main/java/com/example/UserService.java、**/*.java），针对指定文件/目录/包执行
    - 如果提到 --fix 或 修复/自动修改/格式化，则启用修复模式并生成 diff 或直接应用变更
    - 如果提到 --check 或 检查/验证/报告，则只报告问题不修改代码
    - 其他文本视为具体用户需求（如“重点检查异常处理和日志规范”或“针对 Spring Boot 项目应用”），注入到 skill 调用中作为额外指导

3. 不要自己猜测或编写 Java 风格规则，必须完全依赖 global-java-code-style skill 的能力。
4. skill 执行完成后：
    - 展示结果（问题列表、建议、diff、变更预览等）
    - 解释变更原因（引用全局 Java 规范依据）
    - 如果有修改，询问用户是否应用或进一步调整

现在开始：解析 $ARGUMENTS（如果有），然后调用 global-java-code-style skill，并基于它的输出完整响应用户的最新消息。