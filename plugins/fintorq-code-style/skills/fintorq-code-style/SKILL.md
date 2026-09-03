---
name: fintorq-code-style
description: Use when writing, reviewing, or refactoring Java code in a Fintorq backend repository.
---

# Fintorq Code Style

为 Fintorq 后端 Java 代码提供项目级规范。规则只适用于 Fintorq 仓库，不覆盖用户要求，也不替代对当前代码、配置、测试和数据库脚本的核验。

## 事实优先级

发生冲突时按以下顺序判断：

1. 当前分支的代码、构建配置、测试、SQL migration 和可复现运行结果。
2. 当前目录及更深目录的 `AGENTS.md`。
3. 本 Skill 的核心规则与相关参考文件。
4. 历史设计、报告和其他 `docs/` 内容。

不要根据示例猜业务逻辑、表名、权限码或接口契约。易变事实必须回到当前仓库确认。

## 操作边界

- 用户只要求审查、评估或检查时，保持只读，按严重程度输出问题和依据。
- 只有用户明确要求修复、实现或应用规范时才修改文件；修改后运行与风险匹配的校验。
- 保留现有架构、兼容契约和模块风格，优先最小必要改动。

## 核心规则

- 使用当前项目的 Gradle 多模块与 MyBatis-Plus 方案，不引入 JPA/Hibernate 或新的大型架构模式。
- 外部输入必须校验；只捕获能够处理的异常；可关闭资源使用 try-with-resources。
- 使用 SLF4J 与 `{}` 占位符；禁止 `System.out`、`System.err`、空 `catch` 和敏感数据明文日志。
- 依赖默认使用构造器注入和 `private final` 字段，禁止字段注入。保留有实际语义的 `@Lazy`、构造器 `@Autowired` 或其他构造器注解，移除前先验证依赖图和启动行为。
- 分层对象、数据库表、审计字段、数据权限、异常码和 API 路径必须依据当前实现，不把本文示例当作事实来源。

## 按需读取

只读取当前任务需要的参考文件；跨多个层次的修改应读取所有相关文件：

- 包结构、命名、分层对象、依赖注入：[`references/architecture-and-layering.md`](references/architecture-and-layering.md)
- MyBatis-Plus、PO、审计字段、Mapper、数据权限：[`references/persistence-and-permissions.md`](references/persistence-and-permissions.md)
- Controller、API、校验、安全、异常与日志：[`references/api-security-and-errors.md`](references/api-security-and-errors.md)
- Javadoc、单元测试、验证与常用实现模式：[`references/testing-and-examples.md`](references/testing-and-examples.md)

## 工作方式

1. 先读取当前作用域的 `AGENTS.md`，再定位相关代码；涉及业务逻辑时检查对应 `docs/`，但回到代码和测试确认。
2. 对照最近的同类实现，确认模块、包名、数据类型、注解和错误语义。
3. 审查时给出文件与行号、实际风险和最小修复建议；不要把历史风格差异自动判成必须重构。
4. 修改时保持职责清晰、命名明确，不做无关抽象，不添加未使用依赖。
5. 完成前运行定向编译或测试。未经用户明确同意，不运行 Testcontainers 或依赖 Docker 的测试。
