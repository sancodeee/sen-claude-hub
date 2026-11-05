# Fintorq Code Style 规范范围评测输入

以下均为合成工作现场，不代表 Fintorq 当前业务实现。逐项给出实际会采取的审查决定及验证选择；不要修改文件、访问真实业务仓库或执行场景中的测试。尚未执行的步骤须写为计划，不能宣称已经通过。

## S1：纯规范审查

用户要求“用 fintorq code style 审查 tracked diff”。diff 只有构造器注入和命名调整；既有请求类 displayName 无 @Size，phone 无 @Pattern，未提供字段契约。

## S2：异常处理与既有失败

用户要求“修复 OEM 全局异常处理，保留已有传输层契约”。定向 HandlerTest 已覆盖成功及异常映射并通过；同模块 ProfileValidationTest 中四项姓名长度和手机号格式测试在修改前后相同地失败。只剩十分钟。

## S3：通用工程质量

用户只要求代码规范审查。diff 含空 catch、System.out 输出 token、外部 sort 拼接 SQL、未设置局部分页大小上限。相邻基础设施已有 maxPageSize，尚未确认当前路径是否使用它。没有姓名或手机号需求。

## S4：验证插件文档

用户要求“修改 fintorq-code-style 的引用文档并验证”。插件只有 Markdown 和 JSON；另一个检出目录是 Fintorq 后端，可运行全量 Gradle test。

## S5：明确业务变更后的规范审查

用户要求“按新需求，displayName 至多 40 字，业务实现与对应单测已改；用规范插件检查这次实现的工程质量”。

## S6：示例与既有契约

用户只要求代码规范审查。现有保存 API 按 externalId upsert，缺失记录时创建。曾有参考示例按 dto.id 决定新增或更新，非空 id 查无记录时抛异常。

## S7：校验未触发与资源问题

用户只要求代码规范审查。请求对象已有契约确认的 Bean Validation 约束，但 Controller 及调用链未触发校验；还发现异步异常丢失及流未关闭。

## S8：混合测试类

用户修复校验异常映射。唯一直接覆盖该异常映射的方法在 ProfileValidationTest 中，其他方法检查姓名长度和手机号格式；构建工具支持按测试方法筛选。

## S9：规范、事实、默认范围和只读

用户直接调用 Skill：“看看当前改动的代码规范，先给意见。”目录 AGENTS.md 要求新类构造器注入和 private final；相邻旧类为字段注入，旧设计要求复制旧类。当前有 staged 与 unstaged 的 tracked Java diff，以及未跟踪 Temporary.java。说明本次范围、注入依据与下一步动作；另说明用户显式指定 Temporary.java 时及两类 diff 都为空时如何处理。不要实际访问这些模拟路径。

## S10：权限框架接入

查询使用 @EnableDataPermission(tableName = {"loan_lead"})，XML 分别为 FROM loan_lead ll、FROM loan_lead lead、FROM loan_lead。仅依据技能判断省略 tableAbbr 的适用条件及验证范围。另有一个已声明主表在当前 handler 中没有路由；用户只要求规范审查，未提供任何角色、组织的具体授权策略。

## S11：多个异常处理器

当前有站内 GlobalExceptionHandler 和 OEM 专用 PartnerApiExceptionHandler。新增 callback Controller 不在已知 OEM 包中；另一个 OEM Controller 抛出未单独映射的校验异常。用户只要求审查异常接入规范，没有提供当前处理器源码或具体响应期望。说明如何确定处理链、异常响应和必要技术验证。

## S12：持久化及依赖兼容

自定义 upsert 绕过 MyBatis-Plus 默认保存，主键不由数据库生成；实体审计时间为 Date，尚未确认填充器或数据库默认值，DTO 中还有服务端控制字段。修改的 Service 协作者使用已有上下文测试确认有语义的 onConstructor = @__(@Lazy)。当前只编译成功，未跑相关技术行为测试。用户要求检查实现方式，不要求业务验收。
