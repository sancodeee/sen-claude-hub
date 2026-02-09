# Integration Test Report（集成测试报告）

**用户原始需求**：<<FILL: 用户需求原文>>
**目标 URL**：<<FILL: 完整测试目标 URL>>  
**日期与时间**：<<FILL: YYYY-MM-DD HH:MM:SS>>  
**总体状态**：<<FILL: PASS / FAIL / WARN>>  
**总耗时**：<<FILL: X.X 秒>>

### 1. 测试摘要（Test Summary）

- **工作流类型**：迭代快照 + 原子动作
- **执行的总命令数**：<<FILL: N>>
- **成功命令数**：<<FILL: N>>
- **失败命令数**：<<FILL: N>>
- **访问的关键页面数**：<<FILL: N>>
- **生成的截图数量**：<<FILL: N>>

### 2. 关键发现（Key Findings）

- <<FILL: 关键发现 1>>
- <<FILL: 关键发现 2>>
- <<FILL: 关键发现 3>>

### 3. 执行日志（Execution Log）

| 步骤 | 命令                 | 目标 / Ref      | 状态 | 耗时 (秒)        | 详情 / 错误信息    |
|----|--------------------|---------------|----|---------------|--------------|
| 1  | open               | <<FILL: URL>> | ✅  | <<FILL: 0.0>> | <<FILL: 结果>> |
| 2  | snapshot -i --json | -             | ✅  | <<FILL: 0.0>> | <<FILL: 结果>> |

### 4. 网络交互审计（Network Interaction Audit）

#### 4.1 后端API接口调用概览

| Method           | 接口路径 (Path Only)    | 状态码           | 耗时 (ms)     | 结果判定           | 业务说明         |
|------------------|---------------------|---------------|-------------|----------------|--------------|
| <<FILL: METHOD>> | <<FILL: /api/path>> | <<FILL: 200>> | <<FILL: 0>> | <<FILL: ✅ 成功>> | <<FILL: 说明>> |

**关键发现**：

- <<FILL: 关键发现 1>>

#### 4.2 异常/关键接口详情

<details>
<summary>❌ <b><<FILL: METHOD PATH (Status: CODE)>></b></summary>

**Request Payload:**

```json
<<FILL: JSON>>
```

**Response Body:**

```json
<<FILL: JSON>>
```

</details>

<details>
<summary>✅ <b><<FILL: METHOD PATH (Status: CODE)>></b></summary>

**Response Body (部分):**

```json
<<FILL: JSON>>
```

</details>

#### 4.3 前端资源加载记录（可选）

| 类型             | 数量           | 总耗时 (ms)    | 备注           |
|----------------|--------------|-------------|--------------|
| <<FILL: 资源类型>> | <<FILL: 数量>> | <<FILL: 0>> | <<FILL: 备注>> |

### 5. 举证（Evidence）

- **截图**：

  ![<<FILL: 简要描述>>](<<FILL: 相对路径>>)
  *图1：<<FILL: 详细描述>>*

  ![<<FILL: 简要描述>>](<<FILL: 相对路径>>)
  *图2：<<FILL: 详细描述>>*

- **最终页面标题**：<<FILL: 最终页面标题>>
- **最终 URL**：<<FILL: 最终页面 URL>>
- **关键快照摘录**（可选但强烈推荐）：<<FILL: 关键快照摘要>>

### 6. 建议（Recommendations）（新增必填部分）

- <<FILL: 建议 1>>
- <<FILL: 建议 2>>
- <<FILL: 建议 3>>
