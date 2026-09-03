# 持久化与数据权限

## PO 与表结构

- 使用 MyBatis-Plus；基础 CRUD 优先复用 `IService`、`ServiceImpl` 和 `BaseMapper`，复杂查询使用自定义 Mapper/XML。
- 常规 PO 继承 `BaseCommonPO`，不要重复声明基类已经提供的 `id`、逻辑删除和审计字段。
- 当前 `BaseCommonPO.id` 使用 `IdType.ASSIGN_ID`。标准 MyBatis-Plus `save`/insert 路径通常无需手工赋值；自定义 SQL、upsert 或绕开 MyBatis-Plus 的路径必须核对主键生成方式。若表非自增且 SQL 不生成主键，调用前显式使用项目既有的 ID 生成机制（如 `IdWorker.getId()`）；若由数据库或 SQL 生成，必须验证生成键能否回填到内存实体，否则返回响应前重新查询。
- `@TableName` 必须对应当前 migration/DDL 中的真实表名。表名通常使用小写下划线并带业务域前缀，如 `loan_`、`auth_`、`comm_`；禁止根据类名臆造表名或统一移除前缀。
- `@TableField`、逻辑删除字段和版本字段沿用现有实体及 MyBatis-Plus 配置，不擅自改变字段语义。

当前 `BaseCommonPO.deleteFlag` 只有 `@TableField`，项目也未配置 MyBatis-Plus 全局逻辑删除，因此不能假设查询会自动追加 `delete_flag` 条件；必须检查现有 Wrapper、Mapper/XML，并按业务语义显式过滤。实体上的 `@Version` 也不等于乐观锁已经生效：先检查 `MybatisPlusInterceptor` 是否注册 `OptimisticLockerInnerInterceptor`。当前配置未注册该拦截器，需要沿用相关业务的条件更新和版本递增机制。

## 审计字段与时间类型

不要假设 `BaseCommonPO` 会自动填充 `createTime`、`updateTime`、`createBy` 或 `updateBy`。实现保存逻辑前必须检查：

1. 当前实体字段类型和 `FieldFill` 配置。
2. 是否存在 `MetaObjectHandler` 或 Mapper/XML 显式赋值。
3. 对应表是否配置数据库默认值和 `ON UPDATE`。
4. 保存后是否立即从内存实体构造响应。

如果没有自动填充或数据库默认值，按相邻实现显式设置所有必需字段，包括需要时从可信身份上下文取得的 `createBy`、`updateBy`。当前基类时间字段仍为 `java.util.Date` 时，可在边界使用 `Date.from(Instant.now())`，也可保留当前模块已经采用的 `new Date()`；同一次写入复用一个 `now`，不要为了形式强行把 setter 改传 `Instant` 或 `LocalDateTime`。

新业务时间优先使用 `java.time`，但迁移公共审计字段属于跨模块变更，必须单独设计和验证。依赖数据库默认时间时，如果响应需要最新审计值，应重新查询或使用能够回填的既有机制，避免返回 `null` 或旧值。

## Mapper 与分页

复杂分页查询采用 `Page<DbVO>`/`IPage<DbVO>`，在 Service 转换为 `VO`：

```java
Page<LoanLeadDbVO> page = new Page<>(req.getCurrent(), req.getSize());
IPage<LoanLeadDbVO> dbPage = baseMapper.getLoanLeadPage(page, queryDTO);
return dbPage.convert(this::convertToVO);
```

自定义 Mapper 对象参数需与 XML 名称一致：

```java
IPage<LoanLeadDbVO> getLoanLeadPage(
        Page<LoanLeadDbVO> page,
        @Param("dto") LoanLeadListDTO dto);
```

查询必须考虑现有逻辑删除、版本控制、组织隔离和索引条件；是否由框架自动处理必须以实际注解和拦截器配置为准。不要使用字符串拼接构造外部输入 SQL。

## `@EnableDataPermission`

注解位于 `com.fintorq.common.rest.annotation.dataPermission.EnableDataPermission`，标注在 Mapper 方法上。

```java
@EnableDataPermission(tableName = {"loan_lead"}, tableAbbr = {"ll"})
IPage<LoanLeadDbVO> getLoanLeadPage(
        Page<LoanLeadDbVO> page,
        @Param("dto") LoanLeadListDTO dto);
```

强制规则：

- `tableName` 必须恰好声明一个权限主表；禁止裸写 `@EnableDataPermission`。
- `tableAbbr` 可省略，声明时最多一个，并且必须与 SQL 中的真实别名一致。
- 注解格式合法不等于运行时支持。添加或审查时必须读取当前 `CustomDataPermissionHandler` 及相关 SQL provider，确认主表已有路由。
- 本 Skill 核验时的实现支持 `loan_lead`、`loan_application` 和 `loan_quotation`；该列表只是快照，当前分支的 handler 才是事实来源。其他表需要先实现并测试对应权限策略，不能直接套用注解。
- 数据权限拦截器由 `common-rest` 的 MyBatis-Plus 配置注册，不在配置类上添加 `@EnableDataPermission`。
- 查询 DTO 中的组织条件不能替代数据权限注解，两者按当前业务规则组合。

数据权限的目标是 fail-closed，但不能把注解存在等同于已经强制执行。当前 handler 遇到 SQL 中不是所声明主表的表节点时会返回 `null`；因此必须确认实际 SQL 包含且命中了声明的权限主表，并测试主表缺失时拒绝执行。变更后至少覆盖：授权范围、无权限、别名、缺失/不支持主表，以及分页/联表 SQL 场景。
