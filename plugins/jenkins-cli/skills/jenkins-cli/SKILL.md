---
name: jenkins-cli
description: 本机 Jenkins CLI 使用指南。适用于 Jenkins 查询、权限诊断、控制台日志查看、Job XML 导入导出、构建命令说明和高风险操作边界控制。涉及 Jenkins 命令时优先使用本技能。
argument-hint: "[动作] [目标] 例如：who-am-i、list-jobs、console my-job 123、get-job my-job"
user-invocable: true
allowed-tools: Read, Grep, Glob
---

# Jenkins CLI

本技能用于指导如何安全使用本机 `jenkins-cli`，重点是：

- 判断什么时候该用 Jenkins CLI
- 先做环境与权限检查
- 按风险等级选择命令
- 避免误触发 Job、误改配置或误重启 Jenkins

## 何时使用

- 用户要查询 Jenkins 身份、权限、任务、插件或控制台日志
- 用户要导出 Job XML，或了解如何通过 XML 创建/更新 Job
- 用户要了解如何触发构建，但未明确要求立即执行
- 用户提到 `jenkins-cli`、Jenkins 命令行、Jenkins Job 管理、Jenkins 控制台日志

## 何时不要直接执行

- 用户只是询问“怎么做”，没有授权执行真实命令
- 尚未获得明确授权的变更请求，如 `build`、`create-job`、`update-job`
- 尚未完成风险告知和明确授权的高风险请求，如 `delete-job`、`safe-restart`、`restart`
- 无法确认目标 Jenkins、目标 Job 或影响范围

## 默认工作顺序

1. 先读取 [environment-and-discovery.md](references/environment-and-discovery.md)，解析插件根目录、发现入口并完成本地依赖自检；缺依赖时按文档准备。
2. 如果是查询或诊断场景，读取 [safe-operations.md](references/safe-operations.md)。
3. 如果用户要触发构建、创建或修改 Job，读取 [change-operations.md](references/change-operations.md)。
4. 如果请求涉及删除、重启或其他影响平台状态的动作，读取 [dangerous-operations.md](references/dangerous-operations.md)。
5. 如果命令报错或环境缺失，读取 [troubleshooting.md](references/troubleshooting.md)。

## 风险分级

- `Safe/Read-only`：`version`、`who-am-i`、`list-jobs`、`list-plugins`、`get-job`、`console`
- `Change`：`build`、`create-job`、`update-job`
- `Dangerous`：`delete-job`、`safe-restart`、`restart`

## 执行原则

- 默认优先查询类命令。
- 本技能不预授权 Shell 工具；执行命令仍遵循宿主权限规则。业务授权与工具审批分别判断，文档中的风险分级不是可执行的命令白名单。
- 使用随插件分发的 wrapper，或已经核对过行为的现有 `jenkins-cli`；不依赖特定用户名和机器路径。
- 未经明确授权，不执行 `build`。
- 未经明确授权，不执行任何创建、更新、删除、重启相关命令。
- 用户已有有效授权且操作、目标、参数和影响范围齐备时沿用授权；仅在信息缺失、范围变化或授权撤回时补充确认对应部分，不重复索要相同授权。
- 不输出 `JENKINS_API_TOKEN`、`-auth` 字符串或其他敏感信息。
- 需要示例时，只给已验证命令和已验证参数，不猜测长参数或别名。
