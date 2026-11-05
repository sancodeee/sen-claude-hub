# 测试、文档与实现模式

## Javadoc 与注释

- Service 接口、Mapper 方法、Controller 对外方法应说明业务契约、参数、返回值和重要异常。
- 实现类的普通 `@Override` 方法不重复接口 Javadoc；新增 public/protected 方法及非显然的 private 方法按相邻代码补充说明。
- 注释解释原因、约束和兼容背景，不逐句翻译代码。
- TODO 必须写清待解决问题和触发条件，不能作为缺失实现的长期替代。

## 单元测试

使用当前项目的 JUnit 5、Mockito 和既有测试基建。下面以现有纯策略类 `LeadStatusTransitionPolicy` 为例，完整准备非法状态输入并断言业务错误码；它没有协作者，因此不需要 mock。使用前核对当前分支的生产签名与枚举：

- `app-loan/src/main/java/com/fintorq/loancenter/service/LeadStatusTransitionPolicy.java`
- `common-core/src/main/java/com/fintorq/common/core/enums/ExceptionCodeEnum.java`

```java
package com.fintorq.loancenter.service;

import com.fintorq.common.core.enums.loan.quotelead.LeadTypeEnum;
import com.fintorq.common.core.exception.BusinessException;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static com.fintorq.common.core.enums.ExceptionCodeEnum.PARAM_ERROR;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class LeadStatusTransitionPolicyExampleTest {

    private final LeadStatusTransitionPolicy policy = new LeadStatusTransitionPolicy();

    @Test
    @DisplayName("Finance 线索的非法状态应返回参数错误")
    void requireBusinessLineStatus_invalidStatus_throwsParameterError() {
        Integer leadType = LeadTypeEnum.QUOTE.getId();
        Integer invalidStatus = Integer.MIN_VALUE;

        BusinessException exception = assertThrows(BusinessException.class,
                () -> policy.requireBusinessLineStatus(leadType, invalidStatus));

        assertEquals(PARAM_ERROR.code, exception.getCode());
    }
}
```

- 测试类默认命名 `*Test`，测试方法优先使用 `method_scenario_expectedResult`。
- 测试可观察行为，不只验证 mock 调用次数；静态 mock 使用 try-with-resources。
- 测试“记录不存在”等协作分支时，显式准备有效输入、ID 和实际查询方法的 mock 返回值，正确初始化生产依赖；断言当前业务错误码和必要的未写入行为，不依赖未定义变量、偶然的默认 mock 返回值或仅比较错误文案。
- 覆盖成功、边界、空值、权限、异常和兼容路径；修复缺陷时先写能够复现问题的测试。
- 不为了让测试容易通过而在生产代码中增加测试专用分支。

## 常用实现模式

### 保存或更新

依据 [`persistence-and-permissions.md`](persistence-and-permissions.md) 核验实体、权限机制和 Mapper 后，再选择当前业务的保存路径。通用流程如下，不将 `getById` + `updateById` 当作适用于所有实体的安全模板：

1. 按接口契约区分新增与更新，校验输入；整理**允许修改字段白名单**，只显式映射这些字段。组织归属、所有者、删除标志、主键和审计值等受控字段由服务端处理，客户端传入的版本仅作为并发校验依据，不直接覆盖实体版本。
2. 新增时，从可信上下文确定归属和审计身份，按当前表及业务设置有效状态、初始版本和必填审计字段；核对 ID 生成与回填机制。不能让客户端借“保存”选择任意组织，也不能把更新失败转成新增。
3. 更新前确认当前用户对目标记录的权限与状态。逻辑删除未自动生效时显式过滤删除记录；只读查询上的数据权限注解不代表写入也已受保护。
4. 沿用当前业务的条件更新机制，在**同一条写入**中约束目标 ID，以及该实体实际要求的有效状态和可信授权范围。存在版本控制时，同次写入还需约束预期版本并完成版本递增；按实际生效的拦截器或 SQL 实现，不能仅因存在 `@Version` 就省略并发条件。不能只在写入前检查一次而随后按 ID 无条件更新，也不为套用本流程给原表新增删除或版本字段。
5. 只更新白名单字段和服务端维护的更新审计值；创建审计值保持原样。没有可靠自动填充且字段为 `Date` 时，同次写入复用一个 `Date now`；已有填充或数据库默认值时遵循实际机制，不重复覆盖。
6. 核对写入结果；针对单记录条件更新，未命中、版本冲突或其他写入失败按现有错误契约处理，不返回成功，也不泄漏范围外记录是否存在。响应需要数据库生成/维护的字段时，使用当前可回填或重新查询的受限读取路径。

保存相关回归至少覆盖本次改动涉及的成功路径，以及删除记录、越权记录、恶意受控字段、版本冲突和写入失败等拒绝路径。字段名、状态值、权限 API、错误码及并发机制均以当前业务实现为准。

### 分页转换

优先使用 `IPage.convert` 保留页码、页大小和总数：

```java
IPage<LoanLeadDbVO> dbPage = mapper.getLoanLeadPage(page, queryDTO);
return dbPage.convert(this::convertToVO);
```

### 异步任务

使用项目管理的线程池，不直接创建不可控线程。异步失败必须记录足够上下文或传播给调用方；如果异步操作参与业务一致性，明确重试、幂等和补偿策略。

## 验证

按改动性质选择最小充分验证；编译验证类型与依赖，行为测试验证业务结果，两者不能混为一谈：

1. 文档或清单：如果仓库或插件提供对应校验器则运行，并执行 `git diff --check`。
2. 仅类型、签名或依赖调整且不改变业务行为：至少运行受影响模块的 `compileJava`；签名影响调用方时同时编译消费者。
3. 业务逻辑、校验、权限或缺陷修复：运行能够覆盖变化的定向行为测试；缺陷修复先复现，再确认修复后通过。已有测试未覆盖变化时补充必要回归，不能仅凭编译成功宣称修复已验证。
4. 公共模块或跨模块修改：在上述验证基础上，补充受影响消费者的编译和相关行为测试。
5. Spring 配置、构造器或 Bean 依赖变化：运行能够创建相关 ApplicationContext 的测试；必要时验证启动链路。
6. API 契约变化：运行 MVC/契约测试，并确认调用方兼容；异常路由变化按 [`api-security-and-errors.md`](api-security-and-errors.md) 区分站内与 OEM 等实际处理范围，断言 HTTP 状态、业务码和适用的外部错误标识。
7. 数据权限变化：覆盖授权、拒绝、别名和不支持主表的 fail-closed 行为；持久化条件变化需验证实际 SQL/Mapper 行为，不能只检查 mock 调用次数。

未经用户在当前任务中明确同意，不运行 Testcontainers、Docker 依赖测试、全量 `tc*` 任务或 `--rerun-tasks`。优先选择不依赖 Docker 的定向测试；无法运行必要校验时，分别报告已执行结果、未验证项及原因，不能把编译成功当作行为验证的替代。
