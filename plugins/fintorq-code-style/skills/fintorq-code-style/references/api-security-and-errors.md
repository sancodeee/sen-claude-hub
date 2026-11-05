# API、安全、异常与日志

## API 契约

新 Controller 的类级路径优先引用 `api-contract` 中现有的 `*ApiPaths` 常量。新增常量前检查相邻路径的模块根、版本段、复数形式和 kebab-case 约定；不要把示例常量当成已经存在的代码。

普通业务操作默认沿用项目的 POST + lowerCamelCase 动作路径风格，例如 `/getList`、`/saveOrUpdate`。以下场景可以按协议语义和既有契约使用 GET：

- 下载、预览、Range 请求。
- SSE/EventSource 流式订阅。
- 重定向或短链接访问。
- 无副作用的能力、状态或公开资源查询。

不得仅为“统一风格”改变已有 HTTP 方法、路径或响应结构。修改公开契约前必须确认前端、第三方调用方、缓存、安全、OpenAPI 和兼容性影响。

请求体通常使用 `Req`，但路径参数、查询参数、Header、无请求体或流式协议按实际契约选择。响应通常使用 `Result<Resp>` 或 `Result<CommonPageResp<Resp>>`；文件、重定向和流式接口遵循现有响应类型。

## Controller 基线

```java
@Slf4j
@Tag(name = "贷款线索")
@RestController
@RequestMapping(LoanApiPaths.LEADS)
@RequiredArgsConstructor
public class LoanLeadController {
    private final ILoanLeadService loanLeadService;
}
```

- 已有 Bean Validation 约束应通过适用的 `@Valid`/`@Validated` 正确触发；分页大小、请求大小等技术边界按当前配置或基础设施契约校验。
- 字段必填、长度和格式等具体业务规则由需求与接口契约决定，不因代码规范审查自行添加或修改。检查校验触发、异常映射和敏感信息保护，不判断姓名、手机号等字段应接受哪些业务值。
- 权限框架接入沿用项目既有 `PermissionCodeEnum` 引用、`@PreAuthorize` 注解和拦截链；核对技术接入是否生效，不发明权限码或决定角色的具体授权范围。
- 使用 `@Tag`、`@Operation`、`@Parameter` 描述对外契约，但不要复制实现细节。
- Controller 只转换 Req/DTO/VO/Resp，不直接编排持久化或复杂业务。

## 安全

- 外部输入沿用项目既有校验入口与技术边界防护；SQL 值使用参数绑定，排序列等不能绑定的标识符通过项目既有受控映射处理，不拼接外部输入。
- 输出编码应在正确边界完成，不对所有输入做会改变合法业务值的盲目“清洗”。
- 密码、Token、密钥、完整证件号、手机号、邮箱及其他敏感字段不得明文记录。
- 敏感字段处理复用项目已有脱敏与访问控制实现；本 Skill 不决定具体业务响应应返回哪些字段、何种业务状态可见或哪些角色应获授权。

## 异常与响应

先核对 Controller 所在包、实际匹配的 `@RestControllerAdvice` 范围、Advice 优先级和调用链，再选择项目既有异常类型与处理方式。站内接口和 OEM S2S 等专用处理链分别核验；不能只因接口面向第三方就套用某个处理器，也不能为套用规则移动 Controller 包或扩大 Advice 作用域。

由 `GlobalExceptionHandler` 处理的接口沿用项目 `BusinessException`、当前 `ExceptionCodeEnum` 等既有类型与调用方式：

- 引用已有错误码，遵循当前枚举的编码与声明方式，不硬编码或发明错误码。
- 扩展码采用当前枚举约定：前三位表达 HTTP 类别，后三位表达业务细分。
- 新增错误码沿用项目统一枚举的声明与引用方式，避免在调用处散落字面量。
- 错误输出沿用统一异常处理方式，不能泄漏敏感数据、内部 SQL 或第三方凭证。

本 Skill 不判断某种业务状态是否应报错、应选择哪个业务错误码、提示文案是否符合业务要求或前端应执行哪种业务动作；这些由需求与既有业务契约决定。

成功响应使用当前 `Result.success(...)` 和分页转换工具；下载、流式输出等直接写响应的接口保持现有异常处理方式。

异常到 HTTP 状态及 `Result` 的映射，以当前匹配的处理器和调用方技术契约为准，不在 Skill 中维护响应结果快照。`app-partner` 中 OEM 接口的 `PartnerApiExceptionHandler` 与站内 `GlobalExceptionHandler` 可能具有不同作用域和优先级，应先读取当前实现。不能仅因异常属于“校验异常”就推定某个 HTTP 状态或错误标识。

新增或调整异常处理时，定向验证相关 Advice 同时注册后的实际路由、异常类型与原因链、HTTP 状态及响应结构中既有错误标识的传递，确认受影响调用方的技术兼容性。测试期望依据当前代码和明确的技术契约取得，不在规范审查中重新选择业务错误或改变既有传输方式。

## 日志与资源

```java
log.info("Query loan leads, operatorId={}, page={}", operatorId, req.getCurrent());
log.warn("Loan lead not found, id={}", leadId);
log.error("Failed to save loan lead, id={}", leadId, exception);
```

- 使用 SLF4J `{}` 占位符，不使用字符串拼接或 `System.out/err`。
- 请求日志优先复用项目现有的脱敏和 MDC/追踪上下文能力，不另写一套可能遗漏敏感字段的序列化日志。
- Info 记录关键业务结果，Warn 记录可恢复异常，Error 记录失败及必要上下文。
- 不重复记录同一异常；只有当前层能够补充有价值上下文时才记录。
- 仅捕获能处理、转换或补充上下文的异常，禁止空 `catch`。
- 文件、连接和流使用 try-with-resources；异步任务必须记录失败或把失败传播到可观测边界。
