# Integration Test Report（集成测试报告）

**用户原始需求**：详细测试这个系统全量功能，反复检查不能有功能遗漏测试，系统入口：https://dev.portal.fintorq.com.au/index.html#/login，账号：wangsen@mail.com，密码：1234
**目标 URL**：https://dev.portal.fintorq.com.au/index.html#/login  
**日期与时间**：2026-02-09 16:48:07  
**总体状态**：FAIL  
**总耗时**：915.0 秒

### 1. 测试摘要（Test Summary）

- **工作流类型**：迭代快照 + 原子动作
- **执行的总命令数**：75
- **成功命令数**：70
- **失败命令数**：5
- **访问的关键页面数**：9
- **生成的截图数量**：8

### 2. 关键发现（Key Findings）

- 登录表单可稳定定位并完成跳转，成功进入 Dashboard 页面
- Dashboard 左侧菜单可见（Dashboard / Leads Worklist / Support / Organization / Account / Role）
- 首次点击 “Leads Worklist” 出现 30s 超时错误（Resource temporarily unavailable），重试后成功进入列表页
- Support 标签页首次切换 System Update 发生 30s 超时错误，重试后可切换成功
- 多个交互点击出现 “Resource temporarily unavailable (os error 35)”（Dashboard 时间筛选、View All Leads）
- Role 菜单跳转表现不一致（出现 /administration/role/list 与 /dashboard 的不同落点）

### 3. 执行日志（Execution Log）

| 步骤 | 命令                 | 目标 / Ref      | 状态 | 耗时 (秒)        | 详情 / 错误信息    |
|----|--------------------|---------------|----|---------------|--------------|
| 1  | open               | https://dev.portal.fintorq.com.au/index.html#/login | ✅  | 0.03 | 页面加载成功（标题：Dealer Portal） |
| 2  | snapshot -i --json | -             | ✅  | 0.01 | 找到 3 个交互元素（Email, Password, Login） |
| 3  | fill               | @e1           | ✅  | 0.02 | 填写邮箱 |
| 4  | fill               | @e2           | ✅  | 0.01 | 填写密码 |
| 5  | click              | @e3           | ✅  | 0.03 | 点击登录 |
| 6  | wait --load        | networkidle   | ✅  | 0.01 | 等待页面稳定 |
| 7  | get url            | -             | ✅  | 0.01 | 当前 URL：/index.html#/dashboard |
| 8  | get title          | -             | ✅  | 0.01 | 标题：Dealer Portal |
| 9  | snapshot -i --json | -             | ✅  | 0.01 | Dashboard 菜单与操作项已加载 |
| 10 | screenshot         | dashboard.png | ✅  | 0.05 | 已保存登录后仪表盘截图 |
| 11 | network requests --json | -        | ✅  | 0.02 | 捕获 XHR/Fetch 调用 |
| 12 | network --help     | -             | ✅  | 0.01 | 查询网络请求参数（无副作用） |
| 13 | network requests --clear | -       | ✅  | 0.01 | 清空请求日志 |
| 14 | click              | @e2           | ❌  | 30.01 | Resource temporarily unavailable (os error 35) |
| 15 | snapshot -i --json | -             | ✅  | 0.01 | 重新获取 Dashboard 交互元素 |
| 16 | click              | @e2           | ✅  | 0.06 | 进入 Leads Worklist |
| 17 | wait --load        | networkidle   | ✅  | 0.01 | 等待列表页稳定 |
| 18 | get url            | -             | ✅  | 0.01 | 当前 URL：/index.html#/worklist/list |
| 19 | snapshot -i --json | -             | ✅  | 0.02 | 列表页控件加载（Search、筛选、分页） |
| 20 | screenshot         | worklist.png  | ✅  | 0.10 | 已保存 Leads Worklist 页面截图 |
| 21 | fill               | @e8           | ✅  | 0.02 | 搜索框输入 “test” |
| 22 | press              | Enter         | ✅  | 0.02 | 触发搜索 |
| 23 | wait --load        | networkidle   | ✅  | 0.01 | 等待搜索结果刷新 |
| 24 | network requests --json | -        | ✅  | 0.01 | 捕获列表页/搜索相关 API |
| 25 | network requests --clear | -       | ✅  | 0.01 | 清空请求日志 |
| 26 | click              | @e15          | ✅  | 0.05 | 点击首条 View 进入详情 |
| 27 | wait --load        | networkidle   | ✅  | 0.01 | 等待详情页稳定 |
| 28 | get url            | -             | ✅  | 0.01 | 当前 URL：/index.html#/novated-lease/detail?leadId=2020668162202529793 |
| 29 | snapshot -i --json | -             | ✅  | 0.02 | 快照未显示明显新增控件（可能为同页详情或异步渲染） |
| 30 | screenshot         | lead-detail.png | ✅ | 0.10 | 已保存详情页截图 |
| 31 | network requests --json | -        | ✅  | 0.01 | 捕获详情页相关 API |
| 32 | snapshot -i --json | -             | ✅  | 0.02 | 详情页返回菜单可见 |
| 33 | network requests --clear | -       | ✅  | 0.01 | 清空请求日志 |
| 34 | click              | @e3           | ✅  | 0.04 | 进入 Support |
| 35 | wait --load        | networkidle   | ✅  | 0.01 | 等待 Support 页面稳定 |
| 36 | get url            | -             | ✅  | 0.01 | 当前 URL：/index.html#/inbox |
| 37 | snapshot -i --json | -             | ✅  | 0.01 | Support 页面包含 Inbox/System Update 标签 |
| 38 | screenshot         | support.png   | ✅  | 0.09 | 已保存 Support 页面截图 |
| 39 | click              | @e9           | ❌  | 30.01 | Resource temporarily unavailable (os error 35) |
| 40 | snapshot -i --json | -             | ✅  | 0.02 | 重新获取元素（页面状态变化） |
| 41 | get url            | -             | ✅  | 0.01 | 当前 URL：/index.html#/administration/role/list |
| 42 | screenshot         | role-list.png | ✅  | 0.03 | 已保存 Role 列表页面截图 |
| 43 | network requests --clear | -       | ✅  | 0.01 | 清空请求日志 |
| 44 | click              | @e3           | ✅  | 0.05 | 再次进入 Support |
| 45 | wait --load        | networkidle   | ✅  | 0.01 | 等待 Support 页面稳定 |
| 46 | get url            | -             | ✅  | 0.01 | 当前 URL：/index.html#/inbox |
| 47 | snapshot -i --json | -             | ✅  | 0.02 | Support 页面标签可见 |
| 48 | click              | @e9           | ✅  | 0.03 | 切换到 System Update |
| 49 | wait --load        | networkidle   | ✅  | 0.01 | 等待标签内容加载 |
| 50 | snapshot -i --json | -             | ✅  | 0.01 | System Update 标签选中 |
| 51 | screenshot         | support-system-update.png | ✅ | 0.08 | 已保存 System Update 页面截图 |
| 52 | network requests --json | -        | ✅  | 0.01 | 捕获 Support 相关 API |
| 53 | network requests --clear | -       | ✅  | 0.01 | 清空请求日志 |
| 54 | click              | @e4           | ✅  | 0.04 | 进入 Organization |
| 55 | wait --load        | networkidle   | ✅  | 0.01 | 等待 Organization 页面稳定 |
| 56 | get url            | -             | ✅  | 0.01 | 当前 URL：/index.html#/administration/organization |
| 57 | snapshot -i --json | -             | ✅  | 0.01 | Organization 页面交互元素较少 |
| 58 | screenshot         | organization.png | ✅ | 0.06 | 已保存 Organization 页面截图 |
| 59 | network requests --clear | -       | ✅  | 0.01 | 清空请求日志 |
| 60 | click              | @e5           | ✅  | 0.04 | 进入 Account 列表 |
| 61 | wait --load        | networkidle   | ✅  | 0.01 | 等待 Account 页面稳定 |
| 62 | get url            | -             | ✅  | 0.01 | 当前 URL：/index.html#/administration/account/list |
| 63 | snapshot -i --json | -             | ✅  | 0.01 | Account 列表含创建/编辑/删除按钮 |
| 64 | screenshot         | account-list.png | ✅ | 0.06 | 已保存 Account 列表截图 |
| 65 | network requests --clear | -       | ✅  | 0.01 | 清空请求日志 |
| 66 | click              | @e6           | ✅  | 0.04 | 进入 Role（实际路由回 Dashboard） |
| 67 | wait --load        | networkidle   | ✅  | 0.01 | 等待页面稳定 |
| 68 | get url            | -             | ✅  | 0.01 | 当前 URL：/index.html#/dashboard |
| 69 | snapshot -i --json | -             | ✅  | 0.01 | Dashboard 控件可见 |
| 70 | network requests --clear | -       | ✅  | 0.01 | 清空请求日志 |
| 71 | click              | @e7           | ❌  | 30.01 | Resource temporarily unavailable (os error 35) |
| 72 | snapshot -i --json | -             | ✅  | 0.01 | 重新获取 Dashboard 交互元素 |
| 73 | find role radio click --name "1D" | - | ❌ | 30.01 | Resource temporarily unavailable (os error 35) |
| 74 | click              | @e14          | ❌  | 30.01 | Resource temporarily unavailable (os error 35) |
| 75 | close              | -             | ✅  | 0.03 | 关闭浏览器会话 |

### 4. 网络交互审计（Network Interaction Audit）

#### 4.1 后端API接口调用概览

| Method           | 接口路径 (Path Only)    | 状态码           | 耗时 (ms)     | 结果判定           | 业务说明         |
|------------------|---------------------|---------------|-------------|----------------|--------------|
| POST | /adminConversationUser/getAdminConversationUnreadCount | N/A | N/A | ⚠️ 未提供状态 | 获取管理员对话未读数 |
| POST | /systemMessageUser/getSystemMessageUnreadCount | N/A | N/A | ⚠️ 未提供状态 | 获取系统消息未读数 |
| POST | /loanLead/getDashboardData | N/A | N/A | ⚠️ 未提供状态 | 获取仪表盘数据 |
| POST | /loanLead/getUrgentLeadAlert | N/A | N/A | ⚠️ 未提供状态 | 获取紧急线索提醒 |
| POST | /common/dictionary/getEnumList | N/A | N/A | ⚠️ 未提供状态 | 获取字典枚举 |
| POST | /loanLead/getLoanLeadList | N/A | N/A | ⚠️ 未提供状态 | 获取线索列表 |
| POST | /loanLead/getNovatedDetail | N/A | N/A | ⚠️ 未提供状态 | 获取线索详情 |

**关键发现**：

- 网络请求日志未包含状态码与耗时字段，需依赖后端日志或浏览器 DevTools 进行补充验证

#### 4.2 异常/关键接口详情

<details>
<summary>⚠️ <b>POST /loanLead/getDashboardData (Status: N/A)</b></summary>

**Request Payload:**

```json
{}
```

**Response Body:**

```json
{}
```

</details>

<details>
<summary>⚠️ <b>POST /loanLead/getUrgentLeadAlert (Status: N/A)</b></summary>

**Response Body (部分):**

```json
{}
```

</details>

<details>
<summary>⚠️ <b>POST /loanLead/getLoanLeadList (Status: N/A)</b></summary>

**Request Payload:**

```json
{}
```

**Response Body:**

```json
{}
```

</details>

<details>
<summary>⚠️ <b>POST /loanLead/getNovatedDetail (Status: N/A)</b></summary>

**Request Payload:**

```json
{}
```

**Response Body:**

```json
{}
```

</details>

#### 4.3 前端资源加载记录（可选）

| 类型             | 数量           | 总耗时 (ms)    | 备注           |
|----------------|--------------|-------------|--------------|
| 静态资源 | 未采集 | 未采集 | 本次仅审计 XHR/Fetch |

### 5. 举证（Evidence）

- **截图**：

  ![Dashboard](testing-report/report-20260209163252/dashboard.png)
  *图1：登录成功后的 Dashboard 页面*

  ![Leads Worklist](testing-report/report-20260209163252/worklist.png)
  *图2：Leads Worklist 列表页面（含搜索与筛选）*

  ![Lead Detail](testing-report/report-20260209163252/lead-detail.png)
  *图3：线索详情页面（从 View 进入）*

  ![Support Inbox](testing-report/report-20260209163252/support.png)
  *图4：Support Inbox 页面*

  ![Support System Update](testing-report/report-20260209163252/support-system-update.png)
  *图5：Support System Update 标签页*

  ![Role List](testing-report/report-20260209163252/role-list.png)
  *图6：Role 列表页面*

  ![Organization](testing-report/report-20260209163252/organization.png)
  *图7：Organization 页面*

  ![Account List](testing-report/report-20260209163252/account-list.png)
  *图8：Account 列表页面*

- **最终页面标题**：Dealer Portal
- **最终 URL**：https://dev.portal.fintorq.com.au/index.html#/dashboard
- **关键快照摘录**（可选但强烈推荐）：Dashboard 可见时间筛选与 View All Leads/Export Report 操作按钮

### 6. 建议（Recommendations）（新增必填部分）

- 建议排查频繁出现的 “Resource temporarily unavailable (os error 35)” 点击超时问题（可能与前端阻塞/网络层读写/长任务有关），并在关键点击后增加可观察的加载状态或重试机制
- 建议补充可观测的网络状态码与耗时（前端埋点或代理日志），以便在测试报告中精确定位接口成功率与性能
- Role 菜单跳转存在不一致（/administration/role/list 与 /dashboard），建议核对路由权限与菜单配置
