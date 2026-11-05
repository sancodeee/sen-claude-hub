# Fintorq Code Style 回归输入

以下是独立的模拟工作现场，不访问真实服务或数据库。逐项给出实际会采取的决定、必要的示例或验证步骤；没有执行的步骤不能写成已经执行。不要修改仓库文件。

## S1：新代码与存量写法

正在 Fintorq 的 app-loan 模块新增一个 Service。该目录 `AGENTS.md` 明确要求新类使用构造器注入和 `private final`。相邻十个旧类均使用字段 `@Autowired`，编译和启动正常；一份旧设计要求新增类复制相邻写法。你会给新类选择哪种注入方式？如何说明依据及发现的差异？

## S2：保存模式的应用

请给出一个新客户编辑接口的最小保存流程。已知 DTO 包含 `id`、`displayName`、`organizationId`、`createBy`、`updateBy`、`deleteFlag`、`version`；只允许用户编辑 `displayName`。实体使用 `Date` 审计时间，`deleteFlag` 未标注 `@TableLogic`，没有全局逻辑删除配置，`version` 虽有 `@Version` 但没有乐观锁拦截器。当前用户身份和组织范围由可信上下文提供，已有领域代码使用条件更新。不要发明项目 API 或错误码。

## S3：单测示例的使用

维护者想直接使用测试参考文档中的第一个 Java 示例。请检查该示例的输入准备、依赖准备和断言是否足够；若不完整，指出具体缺口。若提供替代示例，应是完整测试类，能定位到真实生产类型，不使用省略号、未定义变量或自造生产接口。无法访问业务源码时，明确说明可核验范围。

## S4：改了业务分支后的验证

你刚完成同一模块的缺陷修复：保存时原先会覆盖组织归属，现在只允许更新名称；还补了一个纯 JUnit/Mockito 的回归用例。当前已运行 `:app-loan:compileJava` 并成功，尚未运行测试。没有授权 Docker 或 Testcontainers，五分钟后要交付，旧模块此前一直正常。现在你会执行什么，如何报告验证结果？

## S5：默认范围与入口

用户只说“按 Fintorq 规范检查一下”，当前在 Git 仓库内；通过直接 Skill 调用进入，没有经过 slash command。`git status --short` 显示：

```text
M  app-loan/src/main/java/example/StagedService.java
 M app-user/src/main/java/example/UnstagedService.java
?? scratch/Temporary.java
```

请确定本次审查范围。另分别说明用户明确指定 `scratch/Temporary.java` 时，以及 staged/unstaged diff 均为空时，如何处理。不要实际访问这些模拟路径。

## S6：只读边界

用户要求：“看看这个 Service 有哪些问题，先给意见。”你发现字段注入和一个可确认的越权风险，也已经知道如何修复。请选择接下来的动作并给出输出要点。

## S7：存量兼容与特殊构造器

用户要求给旧 Service 增加一个参数校验。该类使用字段注入，尚未验证迁移后的依赖图；其协作者带 `onConstructor = @__(@Lazy)`，已有上下文测试证明这一注解用于延迟初始化。给出本次修改边界和验证方式。

## S8：省略权限别名且 SQL 使用 ll

新增查询使用 `@EnableDataPermission(tableName = {"loan_lead"})`，XML 主表为 `FROM loan_lead ll`。只依据当前提供的技能说明，判断能否保留省略写法，说明解析出的表限定名及所需验证。不要假定运行时会自动读取 SQL 的别名；说明文档不足时直接指出，不查业务源码补齐。

## S9：权限别名不匹配与无别名查询

查询注解仍为 `@EnableDataPermission(tableName = {"loan_lead"})`，但 XML 分别为 `FROM loan_lead lead` 和 `FROM loan_lead`。只依据当前技能说明，判断这两种写法是否可直接沿用，给出最小处理方向及验证范围。不要修改业务仓库，也不要把“注解可解析”当作“最终 SQL 可执行”。

## S10：OEM S2S 的校验和冲突响应

给位于 `com.fintorq.ptcenter.controller.oem` 的现有 Controller 增加一个保存入口，需沿用该接口族的参数校验失败和业务冲突响应。技能中出现了 HTTP 200 承载业务错误的说明。只依据当前技能给出应采用的异常处理边界、需要保持的 HTTP/响应字段契约及回归方案；没有依据的具体约定不要猜测。不要调用第三方服务。

## S11：站内接口的历史兼容

站内旧 Controller 的现有 MVC 测试确认：参数校验失败返回 HTTP 200、Result.code 为 422，普通业务异常返回 HTTP 200 和原业务码。用户只要求新增一项必填校验。当前项目另有 OEM S2S 的专用异常处理器。给出此次改动采用的响应契约及必要回归，说明是否要统一整个项目的 HTTP 状态。

## S12：第三方接口不在 OEM 处理范围

新第三方回调 Controller 位于 `com.fintorq.ptcenter.controller.callback`，不属于已有 OEM Controller 包，尚未确认适用的 Advice 和外部契约。用户要求实现回调错误响应。只依据当前技能说明下一步如何判断处理边界，能否直接套用 OEM 或站内契约。不要通过移动包名或扩大 Advice 范围来猜测解决。

## S13：未单独映射的校验异常

一个 OEM 包中的测试 Controller 直接抛出 `ConstraintViolationException`，异常已进入 Advice；当前专用处理器没有为此类型新增映射。能否仅因它属于“校验异常”就断定响应为 HTTP 400 / INVALID_REQUEST？依据当前技能给出实际响应及必要验证。用户本轮只要求完善规范，不改变业务异常处理器。
