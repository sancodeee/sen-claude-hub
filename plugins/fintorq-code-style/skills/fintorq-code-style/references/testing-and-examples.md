# 测试、文档与实现模式

## Javadoc 与注释

- Service 接口、Mapper 方法、Controller 对外方法应说明业务契约、参数、返回值和重要异常。
- 实现类的普通 `@Override` 方法不重复接口 Javadoc；新增 public/protected 方法及非显然的 private 方法按相邻代码补充说明。
- 注释解释原因、约束和兼容背景，不逐句翻译代码。
- TODO 必须写清待解决问题和触发条件，不能作为缺失实现的长期替代。

## 单元测试

使用当前项目的 JUnit 5、Mockito 和既有测试基建：

```java
@ExtendWith(MockitoExtension.class)
class LoanLeadServiceImplTest {

    @Mock
    private LoanLeadMapper loanLeadMapper;

    @InjectMocks
    private LoanLeadServiceImpl loanLeadService;

    @Test
    @DisplayName("保存贷款线索 - 记录不存在时抛业务异常")
    void saveLoanLead_notFound_throwsDataNotExist() {
        BusinessException exception = assertThrows(BusinessException.class,
                () -> loanLeadService.saveLoanLead(dto));
        assertEquals("Data does not exist", exception.getMessage());
    }
}
```

- 测试类默认命名 `*Test`，测试方法优先使用 `method_scenario_expectedResult`。
- 测试可观察行为，不只验证 mock 调用次数；静态 mock 使用 try-with-resources。
- 覆盖成功、边界、空值、权限、异常和兼容路径；修复缺陷时先写能够复现问题的测试。
- 不为了让测试容易通过而在生产代码中增加测试专用分支。

## 常用实现模式

### 保存或更新

```java
Date now = Date.from(Instant.now());
LoanLead entity;
if (dto.getId() == null) {
    entity = new LoanLead();
    BeanUtil.copyProperties(dto, entity,
            "id", "deleteFlag", "createBy", "createTime", "updateBy", "updateTime");
    entity.setCreateTime(now);
    entity.setUpdateTime(now);
    if (!save(entity)) {
        throw new BusinessException(ExceptionCodeEnum.SERVER_ERROR);
    }
} else {
    entity = getById(dto.getId());
    if (entity == null) {
        throw new BusinessException(ExceptionCodeEnum.DATA_NOT_EXIST);
    }
    BeanUtil.copyProperties(dto, entity,
            "id", "deleteFlag", "createBy", "createTime", "updateBy", "updateTime");
    entity.setUpdateTime(now);
    if (!updateById(entity)) {
        throw new BusinessException(ExceptionCodeEnum.SERVER_ERROR);
    }
}
return convertToVO(entity);
```

该示例仅适用于当前字段为 `Date` 且没有可靠自动填充的实体。复制属性时应排除主键、删除标志和审计字段；具体字段以实体为准，不能让外部 DTO 覆盖服务端控制字段。若 `createBy`、`updateBy` 为必填，应按项目现有方式从可信身份上下文设置。若对应表、Mapper 或 `MetaObjectHandler` 已提供审计字段，遵循实际机制，避免重复覆盖。主键生成与回填同样以当前持久化路径为准；异常码应优先替换为语义准确的现有领域错误码。

### 分页转换

优先使用 `IPage.convert` 保留页码、页大小和总数：

```java
IPage<LoanLeadDbVO> dbPage = mapper.getLoanLeadPage(page, queryDTO);
return dbPage.convert(this::convertToVO);
```

### 异步任务

使用项目管理的线程池，不直接创建不可控线程。异步失败必须记录足够上下文或传播给调用方；如果异步操作参与业务一致性，明确重试、幂等和补偿策略。

## 验证

按最小充分原则选择验证：

1. 文档或清单：如果仓库或插件提供对应校验器则运行，并执行 `git diff --check`。
2. 单模块 Java 修改：至少运行受影响模块的 `compileJava` 或定向单元测试。
3. 公共模块或跨模块修改：补充消费者模块编译/测试。
4. Spring 配置、构造器或 Bean 依赖变化：运行能够创建相关 ApplicationContext 的测试；必要时验证启动链路。
5. API 契约变化：运行 MVC/契约测试，并确认调用方兼容。
6. 数据权限变化：覆盖授权、拒绝、别名和不支持主表的 fail-closed 行为。

未经用户在当前任务中明确同意，不运行 Testcontainers、Docker 依赖测试、全量 `tc*` 任务或 `--rerun-tasks`。无法运行必要校验时，明确说明原因和剩余风险。
