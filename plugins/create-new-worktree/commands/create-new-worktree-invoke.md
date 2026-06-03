---
name: create-new-worktree:invoke
description: Immediately call the create-new-worktree skill to create a Git worktree and copy local agent/project configuration files.
argument-hint: "[目标目录] [--branch 分支名] 例如：/tmp/my-worktree 或 /tmp/my-worktree --branch feature/foo"
---

你现在必须**立即且强制**调用已安装的 **create-new-worktree** 这个 skill 来处理用户当前的需求。

用户提供的额外参数/需求（通过 $ARGUMENTS 传入）：
$ARGUMENTS

核心指令：
1. 使用 create-new-worktree skill 中的脚本和安全规则处理 worktree 创建。
2. 默认使用当前分支；如果用户指定 `--branch`，只能使用已存在分支。
3. 不自动创建新分支，不使用 `git worktree add --force`。
4. 创建 worktree 后，只复制 skill 中列出的本地配置路径；不存在则跳过。
5. 如果目标目录已存在或 Git 拒绝创建 worktree，报告原因，不自动改用其他分支策略。

现在开始：调用 create-new-worktree skill，并基于它的输出完整响应用户的最新消息。
