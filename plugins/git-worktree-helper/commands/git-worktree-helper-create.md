---
name: git-worktree-helper:create
description: Call git-worktree-helper to create a Git worktree and copy local agent/project configuration.
argument-hint: "[目标目录] [--base-branch 分支名] [--new-branch 新分支名] [--dry-run]"
---

立即调用已安装的 **git-worktree-helper** skill，按“创建”流程处理下列请求。沿用用户参数和授权，遵循 skill 的命名校验、预演与失败恢复规则。

$ARGUMENTS

所有操作规则以 skill 为准，根据脚本实际结果回复；参数不明确时先只读定位或询问，不直接猜测执行。
