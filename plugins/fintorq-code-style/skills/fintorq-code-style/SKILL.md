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
- 字段长度、格式、必填、额度、状态、业务准入和角色/组织授权范围由需求与既有契约决定，本 Skill 不制定或验收，也不把业务测试成败作为规范门槛。
- 校验检查聚焦既有约束是否触发、技术边界是否生效，不自行调整业务规则。用户明确要求业务实现或验收时照常完成该任务，分别报告业务与规范结论。

## 核心规则

- 使用当前项目的 Gradle 多模块与 MyBatis-Plus 方案，不引入 JPA/Hibernate 或新的大型架构模式。
- 外部输入按既有契约启用校验和技术边界防护，不自行制定字段业务约束；只捕获能够处理的异常；可关闭资源使用 try-with-resources。
- 使用 SLF4J 与 `{}` 占位符；禁止 `System.out`、`System.err`、空 `catch` 和敏感数据明文日志。
- 依赖默认使用构造器注入和 `private final` 字段，禁止字段注入。保留有实际语义的 `@Lazy`、构造器 `@Autowired` 或其他构造器注解，移除前先验证依赖图和启动行为。
- 分层对象、数据库表、审计字段、数据权限、异常码和 API 路径必须依据当前实现，不把本文示例当作事实来源。

## 按需读取

只读取与本次改动或具体问题直接相关的参考段落；已有上下文足够时不扩读，已确认且未变化的依据直接复用：

- 包结构、命名、分层对象、依赖注入：[`references/architecture-and-layering.md`](references/architecture-and-layering.md)
- MyBatis-Plus、PO、审计字段、Mapper、数据权限：[`references/persistence-and-permissions.md`](references/persistence-and-permissions.md)
- Controller、API、校验、安全、异常与日志：[`references/api-security-and-errors.md`](references/api-security-and-errors.md)
- Javadoc、单元测试、验证与常用实现模式：[`references/testing-and-examples.md`](references/testing-and-examples.md)

## 工作方式

1. 读取适用的 `AGENTS.md`，以指定范围或 diff 和必要上下文为起点；现有信息不足时，才补查相关同类实现、配置或契约文档。
2. 只读规范审查默认静态检查，不编译、不跑测试、不派发子代理；仅当用户明确要求，或存在必须运行才能确认的具体问题时，才做对应的最小验证。结论给出文件行号、风险和最小建议，不把历史风格差异变成重构任务。
3. 修改保持职责清晰、命名明确，不做无关抽象、不添加未使用依赖；按 [`references/testing-and-examples.md`](references/testing-and-examples.md) 选择与实际变化对应的必要检查。

**停止条件**：必要检查完成、结论已有依据即结束。没有新改动、新失败或与本次改动有关的未解决安全/兼容性风险，不重复读取、重跑检查或扩大测试范围。失败先定位，修复后仅复验受影响项；必要校验无法执行时如实报告限制，不以无关检查代替，也不将未解决的回归视为完成。
