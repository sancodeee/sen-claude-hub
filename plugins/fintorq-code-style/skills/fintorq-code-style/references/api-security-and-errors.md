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

- 使用 `@Valid`/`@Validated` 触发 Bean Validation，并为分页大小、格式和必填字段设置合理边界。
- 使用当前 `PermissionCodeEnum` 与相邻接口约定配置 `@PreAuthorize`；禁止发明权限码。
- 使用 `@Tag`、`@Operation`、`@Parameter` 描述对外契约，但不要复制实现细节。
- Controller 只转换 Req/DTO/VO/Resp，不直接编排持久化或复杂业务。

## 安全

- 所有外部输入均按使用场景校验；SQL 使用参数绑定，不拼接用户输入。
- 输出编码应在正确边界完成，不对所有输入做会改变合法业务值的盲目“清洗”。
- 密码、Token、密钥、完整证件号、手机号、邮箱及其他敏感字段不得明文记录。
- 敏感字段是否返回必须结合权限、数据状态和当前脱敏策略判断。

## 异常与响应

先核对 Controller 所在包、实际匹配的 `@RestControllerAdvice` 范围、Advice 优先级及调用方契约，再选择异常和响应方式。站内默认规则与 OEM S2S 的专用契约分别适用，不能只看到“第三方接口”就假定由某个处理器接管。

### 站内默认接口

由 `GlobalExceptionHandler` 处理的普通站内业务，使用项目 `BusinessException` 和当前 `ExceptionCodeEnum`。选择规则：

- 优先复用已有、语义准确的标准 HTTP 状态码或扩展业务码。
- 扩展码采用当前枚举约定：前三位表达 HTTP 类别，后三位表达业务细分。
- 特殊前端处理必须在枚举或契约附近说明，例如“不弹提示、仅刷新快照”。
- 不为单次场景随意新增近义错误码；新增前搜索调用方与前端处理。
- 错误信息应具体但不能泄漏敏感数据、内部 SQL 或第三方凭证。

成功响应使用当前 `Result.success(...)` 和分页转换工具；下载、流式输出等直接写响应的接口保持现有异常处理方式。

当前 `GlobalExceptionHandler` 的传输层契约需要保持兼容：多数校验失败、访问拒绝和业务异常使用 HTTP 200 承载 `Result` 中的业务错误码，认证失败使用 HTTP 401，限流使用 HTTP 429。不能仅为 REST 风格统一改变站内 HTTP 状态，也不能将该兼容规则套到 OEM S2S 接口。

### OEM S2S 接口

当前 `app-partner` 的 `PartnerApiExceptionHandler` 通过 `@RestControllerAdvice(basePackages = "com.fintorq.ptcenter.controller.oem")` 限定作用域，优先级高于 `GlobalExceptionHandler`。实现前核验当前处理器、Controller 包和异常类型；以下是当前契约快照：

| 异常路径 | HTTP 与响应契约 |
|---|---|
| `PartnerApiException` | 保留异常携带的 `httpStatus` 和 `errorCode`，包括既有冲突路径的 HTTP 409。 |
| `BusinessException`、`MethodArgumentNotValidException`、`HttpMessageNotReadableException`、`MissingRequestHeaderException` | HTTP 400，`metadata.error_code = "INVALID_REQUEST"`。 |
| `NovatedProviderNotReadyException` | HTTP 503，`metadata.error_code = "PROVIDER_NOT_READY"`。 |
| 未预期异常 | HTTP 500，`metadata.error_code = "INTERNAL_ERROR"`，响应不泄漏内部细节。 |

该处理器使用真实 HTTP 错误状态，`Result.code` 与该状态值一致，并在 `Result.metadata.error_code` 保留外部协议错误标识。新增场景复用当前外部契约，不将站内业务码或 HTTP 200 包装规则直接搬入，也不随意发明新的外部错误码。

不能把所有“校验异常”都推断为 HTTP 400。当前未单独映射的 `ConstraintViolationException` 若进入该 Advice，会走通用异常分支，返回 HTTP 500 / `INTERNAL_ERROR`；新增映射属于接口契约变更，应先核对实际需求和调用方，再补对应路由测试。

其他包的第三方接口、下载和流式响应需核对各自实际处理链；不能为了套用上述约定擅自移动 Controller 包或扩大 Advice 作用域。修改异常路由时，优先复用当前 `PartnerApiExceptionRoutingTest`，覆盖两类 Advice 同时注册时的 OEM 校验/冲突响应，以及站内历史响应不变；断言 HTTP 状态、`Result.code` 和适用的 `metadata.error_code`。

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
