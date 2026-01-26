---
name: code-style
description: Official code style and development standards for the Fintorq project. MUST be followed for all Java code generation.
user-invocable: true
---

# Fintorq Code Style & Standards

This skill provides the official coding standards and development guidelines for the Fintorq project. All generated code must adhere to these rules.

## 1. Tech Stack & Environment

| Component | Specification |
|-----------|---------------|
| **Java Version** | Java 17 |
| **Framework** | Spring Boot 3.x |
| **ORM** | MyBatis-Plus (NOT JPA/Hibernate) |
| **Build Tool** | Gradle (Multi-module) |
| **Utils** | Lombok (Heavy usage), Hutool |
| **Logging** | SLF4J |
| **API Doc** | Knife4j/OpenAPI 3 |
| **Security** | Spring Security + JWT |

## 2. Project Structure & Package Organization

### Module Organization
```
com.fintorq.*
├── {module}center/        # 模块名 (loancenter, usercenter, cmcenter 等)
│   ├── controller/        # 控制器
│   ├── service/           # 服务接口
│   ├── service/impl/      # 服务实现
│   ├── mapper/            # 数据访问
│   ├── entity/            # 实体类 (PO)
│   │   ├── po/            # 持久化对象
│   │   ├── dto/           # 数据传输对象
│   │   ├── vo/            # 视图对象
│   │   ├── req/           # 请求对象
│   │   └── resp/          # 响应对象
│   └── constants/         # 常量定义
```

### Module Name Conventions
| 模块 | Package Name |
|------|--------------|
| 贷款模块 | `loancenter` |
| 用户模块 | `usercenter` |
| 通用模块 | `cmcenter` |
| 合作伙伴模块 | `partnercenter` |

## 3. Naming Conventions

### Class Naming
| 类型 | 命名规范 | 示例 |
|------|----------|------|
| Controller | `{Name}Controller` | `LoanQuoteLeadController` |
| Service Interface | `I{Name}Service` | `ILoanQuoteLeadService` |
| Service Implementation | `{Name}ServiceImpl` | `LoanQuoteLeadServiceImpl` |
| Mapper | `{Name}Mapper` | `LoanQuoteLeadMapper` |
| Entity/PO | `{Name}` | `LoanQuoteLead` |
| DTO | `{Name}DTO` | `DashboardDTO` |
| VO | `{Name}VO` | `LoanQuoteLeadVO` |
| Req | `{Name}Req` | `LoanQuoteLeadListReq` |
| Resp | `{Name}Resp` | `DashboardResp` |
| Config | `{Name}Config` | `ThreadPoolConfig` |
| Enum | `{Name}Enum` | `LoanQuoteLeadStatusEnum` |

### Method/Variable Naming
| 类型 | 规范 | 示例 |
|------|------|------|
| Methods | lowerCamelCase | `getUserById`, `saveLoanQuoteLead` |
| Variables | lowerCamelCase | `userId`, `loanQuoteLead` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `DEFAULT_PAGE_SIZE` |
| Boolean Methods | Prefix with `is`, `has`, `can` | `isValid()`, `hasPermission()` |

## 4. Architectural Layers & Class Types

### 4.1 Controller Layer

**职责**: 处理 HTTP 请求，参数验证，调用 Service 层，返回响应

**必需注解**:
```java
@Slf4j
@Tag(name = "模块名称", description = "模块描述")
@RestController
@RequestMapping("/path")  // lowerCamelCase
@RequiredArgsConstructor(onConstructor = @__(@Autowired))
public class ExampleController {

    private final IExampleService exampleService;
}
```

**权限控制**:
```java
@PreAuthorize("hasAuthority('permission.code')")
```

**返回类型**:
- 有数据: `Result<T>`
- 无数据: `void` (直接写入 response)
- 分页: `Result<CommonPageResp<T>>`

**完整示例**:
```java
@Slf4j
@Tag(name = "贷款报价线索管理模块", description = "贷款报价前端信息管理相关接口")
@RestController
@RequestMapping("/loanQuoteLead")
@RequiredArgsConstructor(onConstructor = @__(@Autowired))
public class LoanQuoteLeadController {

    private final ILoanQuoteLeadService loanQuoteLeadService;

    /**
     * 分页查询贷款报价线索列表
     *
     * @param req 查询条件
     * @return 分页结果
     */
    @PostMapping("/getLoanQuoteLeadList")
    @Operation(summary = "分页查询贷款报价线索列表")
    @PreAuthorize("hasAuthority('worklist.read')")
    public Result<CommonPageResp<LoanQuoteLeadListResp>> getLoanQuoteLeadList(
            @Parameter(description = "查询条件", required = true)
            @Valid @RequestBody LoanQuoteLeadListReq req) {

        log.info("查询贷款报价线索列表，操作人：{}，查询条件：{}",
                RequestContext.getUserId(), req);

        IPage<LoanQuoteLeadVO> voPage = loanQuoteLeadService.getLoanQuoteLeadList(req);
        IPage<LoanQuoteLeadListResp> respPage = voPage.convert(LoanQuoteLeadListResp::toResp);
        CommonPageResp<LoanQuoteLeadListResp> result = CommonPageResp.toCommonPageResp(respPage);

        return Result.success(result);
    }
}
```

### 4.2 Service Layer

**接口定义**:
```java
public interface ILoanQuoteLeadService extends IService<LoanQuoteLead> {
    SaveOrUpdateLoanQuoteLeadVO saveOrUpdateLoanQuoteLead(SaveOrUpdateLoanQuoteLeadDTO dto);
    IPage<LoanQuoteLeadVO> getLoanQuoteLeadList(LoanQuoteLeadListReq req);
}
```

**实现类**:
```java
@Slf4j
@Service
@RequiredArgsConstructor
public class LoanQuoteLeadServiceImpl extends ServiceImpl<LoanQuoteLeadMapper, LoanQuoteLead>
        implements ILoanQuoteLeadService {

    private final ILoanQuoteLeadNoteService loanQuoteLeadNoteService;

    @Value("${sla.default}")
    private int slaHours;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public SaveOrUpdateLoanQuoteLeadVO saveOrUpdateLoanQuoteLead(
            @NotNull SaveOrUpdateLoanQuoteLeadDTO dto) {
        // 业务逻辑
    }
}
```

**依赖注入规范**:
- 使用 `@RequiredArgsConstructor` (Lombok)
- 不使用 `onConstructor = @__(@Autowired)` (Service 层可省略)
- 注入字段使用 `private final`

### 4.3 Mapper Layer

**接口定义**:
```java
@Mapper
public interface LoanQuoteLeadMapper extends BaseMapper<LoanQuoteLead> {

    IPage<LoanQuoteLeadDbVO> getLoanQuoteLeadPage(Page<LoanQuoteLeadDbVO> page,
                                                     @Param("dto") LoanQuoteLeadListDBDTO dto);
}
```

**XML 映射文件位置**: `src/main/resources/mapper/{module}/`

### 4.4 Entity/PO Layer

**实体类规范**:
```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_loan_quote_lead")
public class LoanQuoteLead extends BaseCommonPO {

    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("mobile")
    private String mobile;

    @TableField("organization_code")
    private String organizationCode;

    // BaseCommonPO 包含: createTime, updateTime, createBy, updateBy, deleteFlag
}
```

**字段规范**:
- 使用 `@TableName` 指定表名
- 使用 `@TableId(type = IdType.AUTO)` 主键
- 使用 `@TableField` 映射数据库字段
- 继承 `BaseCommonPO` 获取通用字段

### 4.5 Data Transfer Objects (Req/DTO/VO/Resp)

**对象职责划分**:

| 类型 | 职责 | 示例 |
|------|------|------|
| **Req** | 接收前端请求参数 | `LoanQuoteLeadListReq` |
| **DTO** | Service 层内部数据传输 | `DashboardDTO` |
| **VO** | Service 层返回给 Controller | `LoanQuoteLeadVO` |
| **Resp** | 返回给前端 | `DashboardResp` |

**示例**:
```java
// Req - 接收请求参数
@Data
public class LoanQuoteLeadListReq {
    @NotNull(message = "页码不能为空")
    private Integer current;

    @NotNull(message = "页大小不能为空")
    private Integer size;

    private String searchText;
    private Integer timeRangeFilter;
}

// DTO - 内部数据传输
@Data
public class DashboardDTO {
    private String timePeriod;
}

// VO - Service 层返回
@Data
public class LoanQuoteLeadVO {
    private Long id;
    private String mobile;
    private Integer status;
}

// Resp - 返回给前端
@Data
public class DashboardResp {
    private Integer naf;
    private BigDecimal potentialSales;
}
```

### 4.6 【强制】分层架构数据类型约束

**严格遵循各层的数据类型规范，确保清晰的职责边界和数据流向**。

#### 4.6.1 Controller 层约束

**方法入参类型**：
- ✅ 允许：基本类型参数（`Long id`, `String code` 等）
- ✅ 允许：**Req** 对象
- ❌ 禁止：DTO、VO、DbVO、Resp 对象

**方法返回值类型**：
- ✅ 允许：基本类型参数
- ✅ 允许：**Resp** 对象（通过 `Result<Resp>` 包装）
- ❌ 禁止：DTO、VO、DbVO、Req 对象

**示例**：
```java
// ✅ 正确 - 使用 Req 入参，Resp 返回值
@PostMapping("/getLoanQuoteLeadList")
public Result<CommonPageResp<LoanQuoteLeadListResp>> getLoanQuoteLeadList(
        @Valid @RequestBody LoanQuoteLeadListReq req) {
    IPage<LoanQuoteLeadVO> voPage = loanQuoteLeadService.getLoanQuoteLeadList(req);
    IPage<LoanQuoteLeadListResp> respPage = voPage.convert(LoanQuoteLeadListResp::toResp);
    return Result.success(CommonPageResp.toCommonPageResp(respPage));
}

// ❌ 错误 - Controller 不应直接返回 VO
public Result<IPage<LoanQuoteLeadVO>> getLoanQuoteLeadList(LoanQuoteLeadListReq req) {
    return Result.success(loanQuoteLeadService.getLoanQuoteLeadList(req));
}

// ❌ 错误 - Controller 不应接收 DTO
public Result<Resp> method(Dto dto) {
    // ...
}
```

#### 4.6.2 Service 层约束

**方法入参类型**：
- ✅ 允许：基本类型参数
- ✅ 允许：**DTO** 对象、**Req** 对象
- ❌ 禁止：VO、DbVO、Resp 对象

**方法返回值类型**：
- ✅ 允许：基本类型参数
- ✅ 允许：**VO** 对象
- ❌ 禁止：DTO、DbVO、Resp、Req 对象

**示例**：
```java
// ✅ 正确 - 使用 DTO 入参，VO 返回值
public interface ILoanQuoteLeadService extends IService<LoanQuoteLead> {
    SaveOrUpdateLoanQuoteLeadVO saveOrUpdateLoanQuoteLead(SaveOrUpdateLoanQuoteLeadDTO dto);
    IPage<LoanQuoteLeadVO> getLoanQuoteLeadList(LoanQuoteLeadListReq req);
}

// ❌ 错误 - Service 不应返回 DTO
public SaveOrUpdateLoanQuoteLeadDTO saveOrUpdateLoanQuoteLead(SaveOrUpdateLoanQuoteLeadDTO dto) {
    // ...
}

// ❌ 错误 - Service 不应直接返回 DbVO
public IPage<LoanQuoteLeadDbVO> getLoanQuoteLeadPage(LoanQuoteLeadListReq req) {
    // ...
}
```

#### 4.6.3 Mapper 层约束

**方法入参类型**：
- ✅ 允许：基本类型参数
- ✅ 允许：**DTO** 对象（需加 `@Param("dto")` 注解）
- ❌ 禁止：Req、VO、DbVO、Resp 对象

**方法返回值类型**：
- ✅ 允许：基本类型参数
- ✅ 允许：**DbVO** 对象
- ❌ 禁止：DTO、VO、Resp、Req 对象

**示例**：
```java
// ✅ 正确 - 使用 DTO 入参，DbVO 返回值
@Mapper
public interface LoanQuoteLeadMapper extends BaseMapper<LoanQuoteLead> {
    IPage<LoanQuoteLeadDbVO> getLoanQuoteLeadPage(Page<LoanQuoteLeadDbVO> page,
                                                   @Param("dto") LoanQuoteLeadListDBDTO dto);
}

// ❌ 错误 - Mapper 不应返回 VO
IPage<LoanQuoteLeadVO> getLoanQuoteLeadPage(Page<LoanQuoteLeadVO> page,
                                            @Param("dto") LoanQuoteLeadListDBDTO dto);

// ❌ 错误 - Mapper 不应接收 Req
IPage<LoanQuoteLeadDbVO> getLoanQuoteLeadPage(Page<LoanQuoteLeadDbVO> page,
                                              @Param("req") LoanQuoteLeadListReq req);
```

#### 4.6.4 数据流向图

```
┌─────────────────────────────────────────────────────────────────┐
│                        数据流向                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Frontend                                                       │
│     │                                                           │
│     │ ① Req                                                     │
│     ▼                                                           │
│  ┌─────────────┐                                               │
│  │ Controller  │                                               │
│  │  ─────────  │   ② DTO/Req                                   │
│  │     │       │ ───────────────────────┐                       │
│  └─────────────┘                       │                       │
│       │                                 │                       │
│       │ ③ VO                            ▼                       │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│  │   (convert) │   │   Service   │   │   Mapper    │          │
│  │  ─────────  │   │  ─────────  │   │  ─────────  │          │
│  │      │      │   │     │       │   │     │       │          │
│  │      │      │   └─────────────┘   └─────────────┘          │
│  │      │      │         │                 │                   │
│  │      │      │         │ ④ DTO           │ ⑤ DbVO            │
│  │      │      │         │ ─────────────── │ ───────────────┐  │
│  │      ▼      │         │                 │                │  │
│  │  ┌───────┐  │         │                 ▼                ▼  │
│  │  │ Resp  │  │         │           ┌─────────────┐   ┌─────────────┐
│  │  └───────┘  │         │           │  Database   │   │  Database   │
│  │             │         │           └─────────────┘   └─────────────┘
│  └─────────────┘         │
│       │                 │
│       │ ⑥ Resp                                                     │
│       ▼                                                           │
│  Frontend                                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**数据类型用途说明**：

| 类型 | 使用场景 | 可出现层次 |
|------|----------|-----------|
| **Req** | 接收前端请求参数 | Controller → Service |
| **Resp** | 返回数据给前端 | Controller |
| **DTO** | Service 层内部数据传输 | Service ↔ Mapper |
| **VO** | Service 层业务数据封装 | Service → Controller |
| **DbVO** | 数据库查询结果封装 | Mapper → Service |

## 5. Dependency Injection & Configuration

### 5.1 依赖注入方式

**推荐方式**: `@RequiredArgsConstructor`
```java
@Service
@RequiredArgsConstructor
public class ExampleServiceImpl {

    private final IExampleService exampleService;
    private final IOrgFacadeService orgFacadeService;
}
```

**Controller 层**: 可添加 `onConstructor = @__(@Autowired)`
```java
@RequiredArgsConstructor(onConstructor = @__(@Autowired))
```

### 5.2 配置类规范

**命名**: `{Name}Config`

**示例**:
```java
@Configuration
@EnableDataPermission
public class MybatisPlusConfig {

    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        // 配置
    }
}
```

## 6. API Design Standards

### 6.1 REST API 路径设计

**规范**:
- 使用 lowerCamelCase (小驼峰)
- 名词复数表示资源集合
- 使用 HTTP 方法语义

**示例**:
```
POST   /api/loanQuoteLead/getLoanQuoteLeadList
POST   /api/loanQuoteLead/saveOrUpdate
POST   /api/loanQuoteLead/addNote
POST   /api/loanQuoteLead/export
```

### 6.2 输入验证与安全

**对所有外部输入进行严格验证和清洗**:

```java
@Data
public class LoanQuoteLeadListReq {
    @NotNull(message = "页码不能为空")
    @Min(value = 1, message = "页码必须大于0")
    private Integer current;

    @NotNull(message = "页大小不能为空")
    @Min(value = 1, message = "页大小必须大于0")
    @Max(value = 100, message = "页大小不能超过100")
    private Integer size;

    @Pattern(regexp = "^$|^[A-Za-z0-9]+$", message = "搜索文本只能包含字母和数字")
    private String searchText;
}
```

**安全原则**:
- 使用 `@Valid` 或 `@Validated` 触发验证
- 使用 `@PreAuthorize` 进行权限控制
- 防止 SQL 注入：使用 MyBatis-Plus 参数绑定
- 防止 XSS：对用户输入进行编码
- 敏感数据（密码、密钥）不在日志中明文输出

**敏感数据日志安全**:
```java
// ❌ 错误 - 密码明文输出
log.info("User login: username={}, password={}", username, password);

// ✅ 正确 - 不记录敏感信息
log.info("User login attempt: username={}", username);

// ✅ 正确 - 脱敏处理
log.info("User login: username={}, password=****", username);
```

### 6.3 权限控制

**使用 `@PreAuthorize` 注解**:
```java
@PreAuthorize("hasAuthority('worklist.read')")
@PreAuthorize("hasAuthority('worklist.write')")
@PreAuthorize("hasAuthority('dashboard')")
@PreAuthorize("hasAuthority('report')")
```

**权限码位置**: `com.fintorq.common.core.enums.auth.PermissionCodeEnum`

### 6.4 Swagger 文档注解

```java
@Tag(name = "模块名称", description = "模块描述")
@Operation(summary = "接口摘要", description = "详细描述")
@Parameter(description = "参数描述", required = true)
```

## 7. Data Access Standards

### 7.1 MyBatis-Plus 使用规范

**基础 CRUD**: 使用 `IService` 和 `ServiceImpl` 提供的方法
```java
// 查询单个
LoanQuoteLead lead = this.getById(leadId);

// 查询列表
List<LoanQuoteLead> leads = this.list();

// 保存
boolean success = this.save(loanQuoteLead);

// 更新
boolean success = this.updateById(loanQuoteLead);

// 删除
boolean success = this.removeById(leadId);
```

**复杂查询**: 自定义 Mapper 方法
```java
// Mapper
IPage<LoanQuoteLeadDbVO> getLoanQuoteLeadPage(Page<LoanQuoteLeadDbVO> page,
                                               @Param("dto") LoanQuoteLeadListDBDTO dto);

// Service
Page<LoanQuoteLeadDbVO> page = new Page<>(req.getCurrent(), req.getSize());
IPage<LoanQuoteLeadDbVO> result = baseMapper.getLoanQuoteLeadPage(page, dbDto);
```

### 7.2 枚举规范

**实现 `IEnum<T>` 接口**:
```java
public enum LoanQuoteLeadStatusEnum implements IEnum<Integer> {

    NEW(1, "New"),
    CONTACTED(2, "Contacted"),
    IN_PROGRESS(3, "In Progress"),
    COMPLETED(4, "Completed"),
    LOST(5, "Lost");

    private final Integer id;
    private final String name;

    LoanQuoteLeadStatusEnum(Integer id, String name) {
        this.id = id;
        this.name = name;
    }

    @Override
    public Integer getId() {
        return this.id;
    }

    @Override
    public String getName() {
        return this.name;
    }

    public static LoanQuoteLeadStatusEnum toEnum(int id) {
        return Arrays.stream(values())
                .filter(e -> e.getId().equals(id))
                .findFirst()
                .orElse(null);
    }

    public static String getNameById(Integer id) {
        if (id == null) {
            return null;
        }
        LoanQuoteLeadStatusEnum statusEnum = toEnum(id);
        return statusEnum != null ? statusEnum.getName() : null;
    }
}
```

### 7.3 数据权限

**使用 `@EnableDataPermission` 注解启用数据权限**:
```java
@EnableDataPermission
IPage<LoanQuoteLeadDbVO> getLoanQuoteLeadPage(Page<LoanQuoteLeadDbVO> page,
                                               @Param("dto") LoanQuoteLeadListDBDTO dto);
```

**组织权限隔离**: 在查询 DTO 中设置 `organizationCode`
```java
dbDto.setOrganizationCode(RequestContext.getCurrentUserOrgCode());
```

## 8. Exception Handling & Response Format

### 8.1 异常码体系

**位置**: `com.fintorq.common.core.enums.ExceptionCodeEnum`

**分类**:
- **2xx**: 成功状态码
- **3xx**: 重定向状态码
- **4xx**: 客户端错误状态码
- **5xx**: 服务器错误状态码
  - `5001xx`: 通用请求参数、业务数据异常
  - `5003xx`: common service error
  - `5005xx`: loan service error

**常用异常码**:
```java
SUCCESS(200, "OK")
PARAM_MISS(500101, "Request param is missing")
PARAM_ERROR(500102, "Request param error")
DATA_NOT_EXIST(500103, "Data does not exist")
DATA_ALREADY_EXISTS(500104, "Data already exists")
SERVER_ERROR(500, "Internal server error")
```

### 8.2 异常抛出

**使用 `BusinessException`**:
```java
throw new BusinessException(ExceptionCodeEnum.PARAM_MISS, "Organization code cannot be empty!");
throw new BusinessException(ExceptionCodeEnum.DATA_NOT_EXIST,
        String.format("Organization not found for code: %s", orgCode));
```

### 8.3 统一响应格式

**成功响应**:
```java
return Result.success(data);
```

**分页响应**:
```java
CommonPageResp<T> result = CommonPageResp.toCommonPageResp(page);
return Result.success(result);
```

**无返回值**:
```java
public void exportData(@Valid @RequestBody ExportReq req, HttpServletResponse response) {
    // 直接写入 response
}
```

## 9. Coding Standards

### 9.1 空值处理

**尽量避免返回 `null`**:
- 对于可能为空的返回值，使用 `Optional<T>` 明确表达（Java 8+）
- 方法参数若不允许 `null`，使用 `Objects.requireNonNull` 检查

```java
// ✅ 推荐 - 使用 Optional
public Optional<User> findUserById(Long id) {
    User user = userMapper.selectById(id);
    return Optional.ofNullable(user);
}

// ✅ 推荐 - 参数非空检查
public void setName(String name) {
    this.name = Objects.requireNonNull(name, "name 不能为空");
}

// ✅ 推荐 - 集合返回空集合而非 null
public List<LoanQuoteLead> getLeadsByStatus(Integer status) {
    List<LoanQuoteLead> leads = baseMapper.selectList(
        new QueryWrapper<LoanQuoteLead>().eq("status", status)
    );
    return CollUtil.isEmpty(leads) ? Collections.emptyList() : leads;
}

// ❌ 避免 - 返回 null
public List<LoanQuoteLead> getLeadsByStatus(Integer status) {
    List<LoanQuoteLead> leads = baseMapper.selectList(...);
    return leads.isEmpty() ? null : leads;  // 不推荐
}
```

### 9.2 线程安全

**优先设计无状态或不可变的类**，这样可天然支持并发。

**对于共享可变状态，必须使用合适的并发控制**:

```java
// ✅ 推荐 - 无状态 Service（天然线程安全）
@Service
@RequiredArgsConstructor
public class LoanQuoteLeadServiceImpl {
    // 只有 final 字段，无共享可变状态
    private final LoanQuoteLeadMapper mapper;
}

// ✅ 推荐 - 使用线程安全集合
@Component
public class CacheManager {
    private final ConcurrentHashMap<String, Object> cache = new ConcurrentHashMap<>();
}

// ✅ 推荐 - 使用原子类
@Component
public class CounterService {
    private final AtomicLong counter = new AtomicLong(0);

    public long increment() {
        return counter.incrementAndGet();
    }
}

// ✅ 推荐 - 使用 volatile 保证可见性
@Component
public class ConfigHolder {
    private volatile String configValue;

    public void updateConfig(String value) {
        this.configValue = value;
    }
}

// ⚠️ 谨慎使用 - synchronized 方法
@Component
public class LegacySyncService {
    private final Object lock = new Object();

    public void criticalSection() {
        synchronized (lock) {
            // 临界区代码
        }
    }
}
```

### 9.3 异常安全与资源管理

**使用 try-with-resources 管理可关闭资源**:

```java
// ✅ 推荐 - try-with-resources
public void processFile(String path) {
    try (BufferedReader reader = new BufferedReader(new FileReader(path))) {
        // 处理文件
    } catch (IOException e) {
        log.error("Failed to process file: {}", path, e);
        throw new BusinessException(ExceptionCodeEnum.SERVER_ERROR, "文件处理失败");
    }
}

// ❌ 避免 - 手动关闭资源
public void processFile(String path) {
    BufferedReader reader = null;
    try {
        reader = new BufferedReader(new FileReader(path));
        // 处理文件
    } catch (IOException e) {
        // ...
    } finally {
        if (reader != null) {
            try {
                reader.close();  // 容易遗漏
            } catch (IOException e) {
                // ...
            }
        }
    }
}
```

**确保异常时资源不会泄露**:

```java
// ✅ 正确 - 异常时资源自动释放
@Transactional(rollbackFor = Exception.class)
public void processWithJdbc(DataSource dataSource) {
    try (Connection conn = dataSource.getConnection();
         PreparedStatement stmt = conn.prepareStatement("SELECT * FROM t_table")) {
        // 处理数据库操作
    } catch (SQLException e) {
        log.error("Database error", e);
        throw new BusinessException(ExceptionCodeEnum.SERVER_ERROR, "数据库操作失败");
    }
}
```

### 9.4 注释规范

**类级别 Javadoc**:
```java
/**
 * 贷款报价线索服务实现类
 *
 * @author ratio
 * @since 2025/11/26
 */
```

**方法级别 Javadoc**:
```java
/**
 * 发送已提交的邮件
 *
 * @param dto 包含贷款报价线索数据的 DTO对象
 */
private void sendSubmittedEmail(SaveOrUpdateLoanQuoteLeadDTO dto, LoanQuoteLead loanQuoteLead) {
    // 实现
}
```

**字段注释**:
```java
/**
 * SLA超时时间（小时）
 * 从配置文件读取，支持动态调整
 */
@Value("${sla.default}")
private int slaHours;
```

### 9.5 健壮原则

**编写健壮的代码**，对边界值和异常输入要有明确处理逻辑：

```java
// ✅ 推荐 - 边界值检查
public void setPageSize(int pageSize) {
    if (pageSize < 1 || pageSize > 1000) {
        throw new IllegalArgumentException(
            String.format("页大小必须在 1-1000 之间，当前值: %d", pageSize)
        );
    }
    this.pageSize = pageSize;
}

// ✅ 推荐 - 对外部数据进行验证
public void processExternalData(ExternalDataDto dto) {
    if (dto == null) {
        throw new BusinessException(ExceptionCodeEnum.PARAM_MISS, "外部数据不能为空");
    }

    // 验证关键字段
    if (StrUtil.isBlank(dto.getId())) {
        throw new BusinessException(ExceptionCodeEnum.PARAM_ERROR, "ID 不能为空");
    }

    // 安全处理集合
    List<String> items = dto.getItems() != null ? dto.getItems() : Collections.emptyList();

    // 继续处理...
}

// ✅ 推荐 - 使用默认值而非 null
public String getConfigValue(String key) {
    String value = configService.get(key);
    return StrUtil.blankToDefault(value, "default");
}
```

### 9.6 注释规范

| 类型 | 是否必须写 Javadoc | 说明 |
|------|-------------------|------|
| **IService 接口** | ✅ 必须 | 所有 public 方法必须写 Javadoc |
| **Mapper 接口** | ✅ 必须 | 所有方法必须写 Javadoc |
| **ServiceImpl 实现类** | ⚠️ 条件必须 | 见下方详细规则 |
| **Controller 类** | ✅ 必须 | 所有 public 方法必须写 Javadoc |
| **私有方法** | ✅ 必须 | 实现类中的私有方法必须写 Javadoc |

**ServiceImpl Javadoc 规则**:
```java
public class LoanQuoteLeadServiceImpl implements ILoanQuoteLeadService {

    // ✅ 不需要写 Javadoc - 接口已有定义
    @Override
    public SaveOrUpdateLoanQuoteLeadVO saveOrUpdateLoanQuoteLead(SaveOrUpdateLoanQuoteLeadDTO dto) {
        // 实现
    }

    // ✅ 必须写 Javadoc - 这是私有方法，接口中没有定义
    /**
     * 发送已提交的邮件
     *
     * @param dto 包含贷款报价线索数据的 DTO对象
     * @param loanQuoteLead 贷款报价线索实体
     */
    private void sendSubmittedEmail(SaveOrUpdateLoanQuoteLeadDTO dto, LoanQuoteLead loanQuoteLead) {
        // 实现
    }

    // ✅ 必须写 Javadoc - 这是 protected 方法，接口中没有定义
    /**
     * 构建经销商邮件模板变量
     *
     * @param dto 贷款报价线索 DTO
     * @param orgFacadeVO 组织信息
     * @return 模板变量 Map
     */
    protected Map<String, String> buildDealerEmailTemplateVariables(
            SaveOrUpdateLoanQuoteLeadDTO dto, OrgFacadeVO orgFacadeVO) {
        // 实现
    }
}
```

**IService/Mapper 接口示例**:
```java
/**
 * 贷款报价线索服务接口
 *
 * @author ratio
 * @since 2025/11/26
 */
public interface ILoanQuoteLeadService extends IService<LoanQuoteLead> {

    /**
     * 保存或更新贷款报价线索
     *
     * @param dto 贷款报价线索数据传输对象
     * @return 保存或更新后的视图对象
     */
    SaveOrUpdateLoanQuoteLeadVO saveOrUpdateLoanQuoteLead(SaveOrUpdateLoanQuoteLeadDTO dto);

    /**
     * 分页查询贷款报价线索列表
     *
     * @param req 查询请求参数
     * @return 分页结果
     */
    IPage<LoanQuoteLeadVO> getLoanQuoteLeadList(LoanQuoteLeadListReq req);
}
```

### 9.7 日志规范

**使用 `@Slf4j` 注解**:
```java
@Slf4j
public class ExampleService {
    // 使用 log
}
```

**日志格式**:
```java
// Info 级别 - 记录关键操作
log.info("查询贷款报价线索列表，操作人：{}，查询条件：{}",
        RequestContext.getUserId(), req);

log.info("查询贷款报价线索列表完成，返回{}条记录，当前页：{}，每页大小：{}，总记录数：{}",
        result.getList().size(), result.getPageNum(), result.getPageSize(), result.getTotal());

// Warn 级别 - 记录警告
log.warn("Loan quote lead not found for update: id={}", dto.getId());

// Error 级别 - 记录错误
log.error("Failed to save loan quote lead: id={}", dto.getId());
log.error("Failed to send dealer notice email for lead id {} and organization {}: {}",
        dto.getId(), organizationCode, e.getMessage(), e);
```

**日志占位符**: 使用 `{}` 而非字符串拼接

### 9.8 工具类使用

**Hutool 工具类**:
```java
// 字符串工具
StrUtil.isEmpty(str)
StrUtil.isNotBlank(str)
StrUtil.blankToDefault(str, defaultValue)

// Bean 工具
BeanUtil.copyProperties(source, target)

// 集合工具
CollUtil.isNotEmpty(list)
```

**时间处理**:
```java
// 使用 java.time API
Instant.now()
LocalDateTime.now()
Date.from(instant)
```

## 11. Testing Standards

### 11.1 测试类命名

**命名规范**: `{ClassName}Test`

**示例**:
```java
class QuotationServiceImplSimpleTest {
    // 测试方法
}
```

### 11.2 测试注解

```java
@ExtendWith(MockitoExtension.class)  // JUnit 5 + Mockito
@DisplayName("测试描述")
```

### 11.3 Mock 规范

```java
@Mock
private QuotationMapper quotationMapper;

@Mock
private IApplicationService applicationService;

@InjectMocks
@Spy
private QuotationServiceImpl quotationService;
```

**静态方法 Mock**:
```java
try (MockedStatic<RequestContext> mockedRequestContext = mockStatic(RequestContext.class)) {
    mockedRequestContext.when(RequestContext::getUserId).thenReturn(1001L);
    // 测试逻辑
}
```

### 11.4 测试方法命名

**推荐格式**: `{methodName}_{scenario}_{expectedResult}`

**示例**:
```java
@Test
@DisplayName("批量创建quotation - 基本功能测试")
void testBatchCreateQuotations_BasicFunctionality() {
    // Given
    // When
    // Then
}

@Test
@DisplayName("批量创建quotation - 空列表测试")
void testBatchCreateQuotations_EmptyList() {
    // 测试
}

@Test
@DisplayName("批量创建quotation - null列表测试")
void testBatchCreateQuotations_NullList() {
    // 测试
}
```

### 11.5 断言规范

```java
// 使用 JUnit 5 Assertions
assertNotNull(result);
assertEquals(1, result.size());
assertTrue(result.containsKey("PEPPER"));

// 异常断言
BusinessException exception = assertThrows(BusinessException.class, () -> {
    quotationService.selectQuotation(applicationId, quotationId);
});
assertEquals("Application does not exist or has been deleted", exception.getMessage());
```

## 12. Common Patterns

### 12.1 分页查询模式

```java
@Override
public IPage<LoanQuoteLeadVO> getLoanQuoteLeadList(LoanQuoteLeadListReq req) {
    // 1. 转换查询条件
    LoanQuoteLeadListDBDTO dbDto = convertToDBDTO(req);

    // 2. 创建分页对象
    Page<LoanQuoteLeadDbVO> page = new Page<>(req.getCurrent(), req.getSize());

    // 3. 执行查询
    IPage<LoanQuoteLeadDbVO> dbResult = baseMapper.getLoanQuoteLeadPage(page, dbDto);

    // 4. 转换为 VO
    return new Page<>(req.getCurrent(), req.getSize(), dbResult.getTotal()) {
        {
            setRecords(dbResult.getRecords().stream()
                    .map(this::convertToVO)
                    .collect(Collectors.toList()));
        }
    };
}
```

### 12.2 保存/更新模式

```java
@Override
public SaveOrUpdateLoanQuoteLeadVO saveOrUpdateLoanQuoteLead(SaveOrUpdateLoanQuoteLeadDTO dto) {
    if (dto.getId() != null) {
        // 更新现有记录
        LoanQuoteLead entity = this.getById(dto.getId());
        if (entity == null) {
            throw new BusinessException(ExceptionCodeEnum.DATA_NOT_EXIST);
        }
        BeanUtil.copyProperties(dto, entity);
        this.updateById(entity);
        return new SaveOrUpdateLoanQuoteLeadVO(entity);
    } else {
        // 创建新记录
        LoanQuoteLead entity = new LoanQuoteLead();
        BeanUtil.copyProperties(dto, entity);
        entity.setCreateTime(new Date());
        this.save(entity);
        return new SaveOrUpdateLoanQuoteLeadVO(entity);
    }
}
```

### 12.3 异步操作模式

```java
// 异步发送邮件
CompletableFuture.runAsync(() -> sendThankNoticeEmailToCUser(dto),
        threadPoolManager.getEmailSendThreadPoolExecutor()
).exceptionally(throwable -> {
    log.error("Failed to send email for mobile: {}", dto.getMobile(), throwable);
    return null;
});
```

## 13. Important Notes

### 13.1 禁止事项

- **NO JPA Annotations**: 不使用 `javax.persistence` 或 `jakarta.persistence` 注解
- **NO `@Autowired` on fields**: 不使用字段注入
- **NO `System.out/err`**: 使用日志框架
- **NO raw types**: 使用泛型
- **NO deprecated Date**: 使用 `java.time` API

### 13.2 时区处理

- 数据库时间存储: UTC
- 客户端时区: 通过 `RequestContext.getTimeZone()` 获取
- 时间转换: 使用 `ZoneOffset.UTC`

### 13.3 敏感数据过滤

根据用户权限和数据状态动态过滤敏感字段（如 overdue 订单的姓名、邮箱、电话）。

```java
private boolean hasViewOverdueSensitiveDataPermission() {
    return RequestContext.hasAuthority(PermissionCodeEnum.VIEW_OVERDUE_LEAD.getName());
}
```

## 14. AI 代码生成指引

本章节为 AI 代码生成提供指导原则，确保生成的代码具有高质量、可维护性和可扩展性。

### 14.1 可读性与清晰性

**优先考虑代码的清晰和可读性**：

```java
// ✅ 推荐 - 清晰直观
public List<LoanQuoteLead> getActiveLeads() {
    return baseMapper.selectList(
        new QueryWrapper<LoanQuoteLead>().eq("status", Status.ACTIVE)
    );
}

// ❌ 避免 - 过度"巧妙"但晦涩
public List<LoanQuoteLead> getActiveLeads() {
    return Stream.of(baseMapper.selectList(null))
        .filter(l -> Status.ACTIVE.equals(l.getStatus()))
        .collect(Collectors.toList());
}
```

**生成的代码要自解释**：
- 使用有意义的变量名和方法名
- 避免单字母变量名（除循环变量 i、j 等）
- 命名要准确反映其用途

### 14.2 单一职责原则

**函数、方法和类应尽量职责单一，功能内聚**：

```java
// ✅ 推荐 - 单一职责
@Service
@RequiredArgsConstructor
public class LoanQuoteLeadServiceImpl {

    public SaveOrUpdateLoanQuoteLeadVO saveOrUpdate(SaveOrUpdateLoanQuoteLeadDTO dto) {
        validateDto(dto);           // 验证
        LoanQuoteLead entity = convertToEntity(dto);  // 转换
        saveEntity(entity);          // 保存
        sendNotification(entity);    // 通知
        return convertToVO(entity);
    }

    private void validateDto(SaveOrUpdateLoanQuoteLeadDTO dto) {
        // 验证逻辑
    }

    private LoanQuoteLead convertToEntity(SaveOrUpdateLoanQuoteLeadDTO dto) {
        // 转换逻辑
    }

    private void sendNotification(LoanQuoteLead entity) {
        // 通知逻辑
    }
}

// ❌ 避免 - 一个方法做太多事情
public SaveOrUpdateLoanQuoteLeadVO saveOrUpdate(SaveOrUpdateLoanQuoteLeadDTO dto) {
    // 100+ 行代码，包含验证、转换、保存、通知等多种职责
}
```

### 14.3 避免重复与简单优先

**遵循 DRY（Don't Repeat Yourself）原则**：

```java
// ✅ 推荐 - 提取公共方法
private void applyCommonFilters(QueryWrapper<LoanQuoteLead> wrapper, SearchReq req) {
    if (StrUtil.isNotBlank(req.getMobile())) {
        wrapper.like("mobile", req.getMobile());
    }
    if (StrUtil.isNotBlank(req.getOrganizationCode())) {
        wrapper.eq("organization_code", req.getOrganizationCode());
    }
}

// ❌ 避免 - 重复代码
public List<LoanQuoteLead> search1(SearchReq req) {
    QueryWrapper<LoanQuoteLead> wrapper = new QueryWrapper<>();
    if (StrUtil.isNotBlank(req.getMobile())) {
        wrapper.like("mobile", req.getMobile());
    }
    // ...
}

public List<LoanQuoteLead> search2(SearchReq req) {
    QueryWrapper<LoanQuoteLead> wrapper = new QueryWrapper<>();
    if (StrUtil.isNotBlank(req.getMobile())) {
        wrapper.like("mobile", req.getMobile());
    }
    // ...
}
```

**保持代码简单直接（KISS 原则）**：
- 满足需求的前提下选用简单可维护的方案
- 不必追求过度抽象或极致优化，除非明确必要

### 14.4 可维护性和扩展性

**鼓励使用接口和抽象来解耦模块**：

```java
// ✅ 推荐 - 面向接口编程
@Service
@RequiredArgsConstructor
public class LoanQuoteLeadServiceImpl implements ILoanQuoteLeadService {

    private final LoanQuoteLeadMapper mapper;          // 接口注入
    private final INotificationService notificationService;  // 接口注入
}

// ❌ 避免 - 紧耦合设计
@Service
public class LoanQuoteLeadServiceImpl {

    private LoanQuoteLeadMapper mapper = new LoanQuoteLeadMapper();  // 硬编码创建
}
```

**遵循 SOLID 等设计原则**：
- **S**ingle Responsibility：单一职责
- **O**pen/Closed：对扩展开放，对修改封闭
- **L**iskov Substitution：里氏替换
- **I**nterface Segregation：接口隔离
- **D**ependency Inversion：依赖倒置

### 14.5 错误处理与日志

**生成具有意义的错误信息**：

```java
// ✅ 推荐 - 具体的错误信息
if (StrUtil.isBlank(dto.getMobile())) {
    throw new BusinessException(
        ExceptionCodeEnum.PARAM_ERROR,
        "手机号不能为空"
    );
}

if (!isValidMobile(dto.getMobile())) {
    throw new BusinessException(
        ExceptionCodeEnum.PARAM_ERROR,
        String.format("手机号格式不正确: %s", dto.getMobile())
    );
}

// ❌ 避免 - 模糊的错误信息
if (StrUtil.isBlank(dto.getMobile())) {
    throw new BusinessException(ExceptionCodeEnum.PARAM_ERROR, "参数错误");
}
```

**避免吞掉异常**：

```java
// ✅ 推荐 - 记录并重新抛出
try {
    sendEmail(dto);
} catch (EmailException e) {
    log.error("Failed to send email for mobile: {}", dto.getMobile(), e);
    throw new BusinessException(ExceptionCodeEnum.SERVER_ERROR, "邮件发送失败", e);
}

// ❌ 避免 - 吞掉异常
try {
    sendEmail(dto);
} catch (Exception e) {
    // 静默忽略
}
```

### 14.6 注释与文档

**为生成的代码添加适当注释**：

```java
/**
 * 分页查询贷款报价线索列表
 *
 * <p>支持按手机号、状态、时间范围等条件过滤</p>
 *
 * @param req 查询请求参数，包含分页信息和过滤条件
 * @return 分页结果，包含符合条件的线索列表
 * @throws BusinessException 当查询参数无效时抛出
 */
@Override
public IPage<LoanQuoteLeadVO> getLoanQuoteLeadList(LoanQuoteLeadListReq req) {
    // 实现逻辑
}
```

**TODO 注释使用**：
- 标记需要后续检查或优化的代码
- 说明 TODO 的具体原因和期望的改进方向

```java
// TODO: 考虑使用缓存优化频繁查询的性能
// TODO: 当前的同步邮件发送可能影响响应时间，后续改为异步
public SaveOrUpdateLoanQuoteLeadVO saveOrUpdate(SaveOrUpdateLoanQuoteLeadDTO dto) {
    // 实现
}
```

**注释应解释"为什么"而非"是什么"**：

```java
// ✅ 推荐 - 解释原因
// 使用索引查询而非模糊搜索，因为 mobile 字段建立了索引
List<LoanQuoteLead> leads = baseMapper.selectList(
    new QueryWrapper<LoanQuoteLead>().eq("mobile", mobile)
);

// ❌ 避免 - 重复代码逻辑
// 查询 mobile 等于传入参数的记录
List<LoanQuoteLead> leads = baseMapper.selectList(
    new QueryWrapper<LoanQuoteLead>().eq("mobile", mobile)
);
```

---

*Last Updated: 2026-01-26 | Version: 3.1*
