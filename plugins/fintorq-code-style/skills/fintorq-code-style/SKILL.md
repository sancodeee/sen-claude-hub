---
name: fintorq-code-style
description: Use when writing, reviewing, or refactoring Java code in a Fintorq backend repository.
---

# Fintorq Code Style

为 Fintorq 后端 Java 代码提供代码规范与工程质量要求。规则只适用于 Fintorq 仓库，不覆盖用户要求，也不替代对当前代码、配置、相关技术测试和数据库脚本的核验。

## 指令约束与事实核验

指令与实现事实分别判断：

- **操作与规范**：遵循用户要求和当前作用域的 `AGENTS.md`；更深目录的规则优先。本 Skill 补充项目默认规范，不覆盖这些要求。
- **实现事实**：以当前分支的代码、构建配置、相关技术测试、SQL migration 和可复现运行结果为准；本 Skill 中的实现快照及历史 `docs/` 只作核验线索。

代码与规范不一致时，说明实际行为和规范要求的差异；存量代码能够运行不代表新代码可以忽略明确规范，也不构成批量重构的理由。不要根据示例猜业务逻辑、表名、权限码或接口契约。

## 操作边界

- 用户只要求审查、评估或检查时，保持只读，按严重程度输出问题和依据。
- 只有用户明确要求修复、实现或应用规范时才修改文件；修改后运行与风险匹配的校验。
- 保留现有架构、兼容契约和模块风格，优先最小必要改动。

## 审查范围

直接调用 Skill 与通过命令调用使用同一规则：

- 用户指定文件、代码片段、目录、提交或比较基线时，以显式范围为准；可以包含未跟踪文件。
- 未指定范围且当前位于 Git 仓库时，默认审查 tracked diff：分别读取 `git diff --cached` 和 `git diff`，覆盖 staged 与 unstaged 的变更及必要上下文；不自动纳入未跟踪文件或扫描全仓。
- 两类 diff 均为空，或不在 Git 仓库且没有可定位的目标时，说明当前没有默认审查范围，再询问目标；不能据此宣称代码没有问题。

## 规范范围

- 检查命名、分层、依赖注入、持久化用法、输入安全、权限框架接入、异常、日志、资源管理和测试质量是否遵循项目已有代码约定。通用安全和异常处理检查也只限实现方式，不据此审查业务语义。
- 姓名长度、手机号合法性、业务字段必填、额度阈值、状态流转和业务准入条件等具体业务校验，不作为本 Skill 的检查项。即使代码或业务测试中已有这些规则，也不能据此将其列为代码规范要求。
- 输入校验关注既有校验是否被正确触发，以及分页、请求大小等技术边界是否按当前配置生效；具体字段取值规则由业务需求和接口契约定义。规范审查不自行新增、删除或调整这些规则。
- 不判断既有业务规则、业务内容、角色或组织的具体授权范围，以及业务测试断言的期望是否正确，不把业务测试成败列为代码规范通过条件。
- 用户另外明确要求实现或验收业务变更时，按该任务处理，并将业务验收与本 Skill 的规范结论分开；本 Skill 只约束代码质量。

## 核心规则

- 使用当前项目的 Gradle 多模块与 MyBatis-Plus 方案，不引入 JPA/Hibernate 或新的大型架构模式。
- 外部输入按既有契约启用校验和技术边界防护，不自行制定字段业务约束；只捕获能够处理的异常；可关闭资源使用 try-with-resources。
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

1. 先读取当前作用域的 `AGENTS.md`，再定位相关代码；需要理解兼容契约时检查对应 `docs/`，但回到代码和相关测试确认，不扩展为业务规则验收。
2. 对照最近的同类实现，确认模块、包名、数据类型、注解、异常类型及调用方式。
3. 审查时给出文件与行号、实际风险和最小修复建议；不要把历史风格差异自动判成必须重构。
4. 修改时保持职责清晰、命名明确，不做无关抽象，不添加未使用依赖。
5. 先区分插件文档验证与 Java 实现验证，再按 [`references/testing-and-examples.md`](references/testing-and-examples.md) 选择与改动直接相关的检查。业务字段测试失败不等于插件规范检查失败。未经用户明确同意，不运行 Testcontainers 或依赖 Docker 的测试。
