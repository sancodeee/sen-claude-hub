---
name: git-worktree-helper:cleanup
description: Call git-worktree-helper to return managed configuration changes, then safely remove a completed worktree and branch.
argument-hint: "[worktree目录] [--keep-branch] [--dry-run]"
---

立即调用已安装的 **git-worktree-helper** skill，按“清理”流程处理下列请求。首次使用默认预检，按 skill 的错误分类决定停止、修复或授权后的重试。

$ARGUMENTS

所有操作规则以 skill 为准，根据脚本实际结果回复；已明确覆盖具体风险的授权不重复询问，硬性阻断不能强制绕过。
