# 架构、命名与分层

## 技术与模块基线

Fintorq 后端当前以 Java 17、Spring Boot 3、Gradle 多模块、MyBatis-Plus、Lombok、SLF4J、Spring Security/JWT 和 OpenAPI 为主。实现前仍应核对当前分支的构建文件与依赖，不能仅凭本页升级或替换框架。

常见模块与包根：

| 模块 | 主要包根 |
|---|---|
| `app-main` | `com.fintorq.app.main` |
| `app-common` | `com.fintorq.cmcenter` |
| `app-user` | `com.fintorq.usercenter` |
| `app-loan` | `com.fintorq.loancenter` |
| `app-lender` | `com.fintorq.lendercenter` |
| `app-partner` | `com.fintorq.ptcenter` |
| `api-contract` | `com.fintorq.api.contract` |
| `client-api` | `com.fintorq.client.api` |
| `common-core` | `com.fintorq.common.core` |
| `common-rest` | `com.fintorq.common.rest` |
| `common-test` | `com.fintorq.common.test` |

业务模块通常包含 `controller`、`service`、`service.impl`、`facade`、`mapper`、`entity`、`config`、`enums` 等目录；按职责还可包含 `audit`、`externalapi`、`job`、`security`、`strategy`、`event` 等目录，不创建无实际内容的占位目录。新增工具类统一放入 `utils`；现有 `util` 作为历史目录保留，不为统一目录名做无关迁移。`constant`/`constants` 等其他历史差异跟随当前模块。

## 命名约定

新代码优先沿用相邻实现：

| 类型 | 默认命名 |
|---|---|
| Controller | `*Controller` |
| Service 接口 | `I*Service` |
| Service 实现 | `*ServiceImpl` |
| Facade | `I*FacadeService` / `*FacadeServiceImpl` |
| Mapper | `*Mapper` |
| 请求/响应 | `*Req` / `*Resp` |
| 内部传输/视图/查询结果 | `*DTO` / `*VO` / `*DbVO` |
| 配置/枚举 | `*Config` / `*Enum` |

方法和变量使用 lowerCamelCase，常量使用 UPPER_SNAKE_CASE，布尔查询方法优先使用 `is`、`has`、`can`。已有公共类型若未遵循后缀约定，保持兼容，不为改名破坏调用方。

`facade` 包中的跨模块契约不强制使用单一后缀。除 `I*FacadeService` / `*FacadeServiceImpl` 外，表达实际职责的 `*Resolver`、`*Client` 或领域 `*Service` 也可以使用；优先保持调用契约和同一接口族的一致性。

枚举是否实现 `com.fintorq.common.core.enums.IEnum`，以同一枚举族和消费者要求为准；不要假设所有枚举都必须实现。

## 分层对象

新接口的默认数据流：

```text
Frontend -> Req -> Controller -> Req/DTO -> Service -> DTO -> Mapper -> Database
Frontend <- Resp <- Controller <- VO      <- Service <- DbVO <- Mapper <- Database
```

- Controller 接收基础参数或 `Req`，对外顶层响应优先为 `Result<Resp>`；分页响应使用项目现有 `CommonPageResp`。
- Service 接收基础参数、`Req` 或 `DTO`，向 Controller 返回业务 `VO`。
- Mapper 接收基础参数或查询 `DTO`，复杂查询通常返回 `DbVO`；聚合投影、跨模块契约或既有 read model 可以使用语义明确的 `DTO`、`VO`、`FacadeDTO`、`FacadeVO` 等类型。自定义对象参数按 XML 名称添加 `@Param`。
- `Resp` 嵌套已有 `VO` 仅在字段语义、脱敏规则和前端契约完全一致时使用；需要裁剪、改名或脱敏时创建专用 `Resp`。

这是新代码的默认边界，不是重写兼容接口的理由。审查旧接口时先判断是否存在真实泄漏、安全或维护风险，再决定是否迁移。

## 依赖注入

默认写法：

```java
@Service
@RequiredArgsConstructor
public class ExampleServiceImpl {
    private final IExampleService exampleService;
}
```

- 新代码禁止在字段上直接使用 `@Autowired`；存量字段注入只在实际修改相关类且能够验证构造关系时迁移，不做全仓机械替换。
- 单构造器通常不需要显式 `@Autowired`。
- `onConstructor = @__(@Lazy)`、显式构造器 `@Autowired`、参数级 `@Lazy` 可能用于循环依赖、多个构造器选择或其他运行时语义。审查时先检查构造器数量、依赖图和测试，不能机械删除。
- 相邻类只用于确认模块契约和特殊运行时语义，不能用历史字段注入或冗余构造器注解覆盖上述新代码默认规则。若不得不引入 `@Lazy`，说明原因并通过 Spring 上下文或相关测试验证。

## 职责与文档

- Controller 只做协议适配、校验、权限和响应转换；业务逻辑放在 Service。
- Service 方法保持单一职责，但不要为了形式拆出大量无意义私有方法。
- Mapper 负责持久化，不承载业务决策。
- 公共接口和非显然行为使用 Javadoc 解释契约与原因；实现接口的普通覆盖方法不重复接口文档。
