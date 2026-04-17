---
name: jenkins-cli
description: 本机 Jenkins CLI 使用指南。适用于 Jenkins 查询、权限诊断、控制台日志查看、Job XML 导入导出、构建命令说明和高风险操作边界控制。涉及 Jenkins 命令时优先使用本技能。
argument-hint: "[动作] [目标] 例如：who-am-i、list-jobs、console my-job 123、get-job my-job"
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash
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
- 请求会影响 Jenkins 状态，如 `build`、`create-job`、`update-job`
- 请求属于高风险操作，如 `delete-job`、`safe-restart`、`restart`
- 无法确认目标 Jenkins、目标 Job 或影响范围

## 默认工作顺序

1. 先读取 [environment-and-discovery.md](references/environment-and-discovery.md) 确认入口命令、环境变量和帮助查看方式。
2. 如果是查询或诊断场景，读取 [safe-operations.md](references/safe-operations.md)。
3. 如果用户要修改 Job 配置，读取 [change-operations.md](references/change-operations.md)。
4. 如果请求涉及删除、重启或其他影响平台状态的动作，读取 [dangerous-operations.md](references/dangerous-operations.md)。
5. 如果命令报错或环境缺失，读取 [troubleshooting.md](references/troubleshooting.md)。

## 风险分级

- `Safe/Read-only`：`version`、`who-am-i`、`list-jobs`、`list-plugins`、`get-job`、`console`
- `Change`：`build`、`create-job`、`update-job`
- `Dangerous`：`delete-job`、`safe-restart`、`restart`

## 执行原则

- 默认优先查询类命令。
- 未经明确授权，不执行 `build`。
- 未经明确授权，不执行任何创建、更新、删除、重启相关命令。
- 不输出 `JENKINS_API_TOKEN`、`-auth` 字符串或其他敏感信息。
- 需要示例时，只给已验证命令和已验证参数，不猜测长参数或别名。
