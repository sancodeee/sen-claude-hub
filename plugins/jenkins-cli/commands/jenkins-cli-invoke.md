---
name: jenkins-cli:invoke
description: Immediately call the jenkins-cli skill to handle Jenkins CLI usage, diagnostics, and guarded operation guidance.
argument-hint: "[动作] [目标] 例如：list-jobs、console my-job 123、build my-job、get-job my-job"
---

你现在必须**立即且强制**调用已安装的 **jenkins-cli** 这个 skill 来处理用户当前的需求。

用户提供的额外参数/需求（通过 $ARGUMENTS 传入 jenkins-cli skill）：
$ARGUMENTS

核心指令：
1. 先根据 skill 中的安全分级判断当前请求是查询类、变更类还是高风险类操作。
2. 查询类请求可以直接给出命令建议，必要时执行只读命令。
3. 变更类请求默认不要直接执行，先说明影响范围并确认用户授权。
4. 高风险类请求默认不要执行，必须先提醒风险并获得明确确认。
5. 禁止回显 `JENKINS_API_TOKEN` 或任何认证串。

现在开始：调用 jenkins-cli skill，并基于它的输出完整响应用户的最新消息。
