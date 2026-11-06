# 持久化与数据权限

## PO 与表结构

- 使用 MyBatis-Plus；基础 CRUD 优先复用 `IService`、`ServiceImpl` 和 `BaseMapper`，复杂查询使用自定义 Mapper/XML。
- 常规 PO 继承 `BaseCommonPO`，不要重复声明基类已经提供的 `id`、逻辑删除和审计字段。
- 当前 `BaseCommonPO.id` 使用 `IdType.ASSIGN_ID`。标准 MyBatis-Plus `save`/insert 路径通常无需手工赋值；自定义 SQL、upsert 或绕开 MyBatis-Plus 的路径必须核对主键生成方式。若表非自增且 SQL 不生成主键，调用前显式使用项目既有的 ID 生成机制（如 `IdWorker.getId()`）；若由数据库或 SQL 生成，必须验证生成键能否回填到内存实体，否则返回响应前重新查询。
- `@TableName` 必须对应当前 migration/DDL 中的真实表名。表名通常使用小写下划线并带业务域前缀，如 `loan_`、`auth_`、`comm_`；禁止根据类名臆造表名或统一移除前缀。
- `@TableField`、逻辑删除字段和版本字段沿用现有实体及 MyBatis-Plus 配置，不擅自改变字段语义。

逻辑删除和乐观锁沿用当前项目的注解、拦截器及 Mapper 实现方式，不假定存在未配置的自动行为，也不由本 Skill 决定业务记录的过滤或状态更新条件。

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

查询复用项目既有 Wrapper、Mapper/XML 和拦截器用法；不通过字符串拼接将外部输入构造为 SQL。

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
- `tableAbbr` 声明时最多一个；显式值或省略后生成的限定名，都必须与 SQL 主表实际使用的限定名一致。
- 省略 `tableAbbr` 不表示运行时从 SQL 自动识别别名。当前 `EnableDataPermissionHandler.generateAbbreviation` 按表名的下划线分段取首字母，例如 `loan_lead -> ll`；仅当 SQL 为 `FROM loan_lead ll` 等匹配写法时可以省略。SQL 使用 `lead` 等其他别名时，应显式声明 `tableAbbr = {"lead"}`；主表没有别名时，不能直接套用省略写法，应显式使用与 SQL 匹配的表限定名，或为 SQL 与注解配置一致的别名。
- 默认生成规则以当前 `EnableDataPermissionHandler` 为准；规则不明确时再定位别名生成方法或相关测试。注解能解析不代表最终权限 SQL 正确。
- 仅在权限注解、SQL 主表/别名/作用域、权限路由发生变化，或有具体接入疑点时，核对主表路由及相关 handler/provider。优先复用本任务已确认且未变化的依据，不为普通命名或格式审查重复读取基础设施。
- 可用主表以当前分支的 handler 路由为准，不在 Skill 中维护业务表支持清单，也不根据示例为其他业务表制定权限策略。
- 数据权限拦截器由 `common-rest` 的 MyBatis-Plus 配置注册，不在配置类上添加 `@EnableDataPermission`。
- 查询 DTO 中的组织条件不能替代项目要求的数据权限注解；遵循既有接入方式，不由本 Skill 判断组织条件的业务取值。

涉及权限框架接入的修改，定向验证注解参数、SQL 主表及别名匹配、路由和既有 fail-closed 机制；不把注解存在等同于接入正确。不检查或验收各角色、组织应能访问哪些具体业务记录，不制定业务权限矩阵。
