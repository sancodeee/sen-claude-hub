---
name: git-worktree-helper:invoke
description: Immediately call the git-worktree-helper skill to create a Git worktree and copy local agent/project configuration files.
argument-hint: "[目标目录] [--base-branch 分支名] [--new-branch 新分支名] 例如：/tmp/my-worktree --base-branch feature/a"
---

你现在必须**立即且强制**调用已安装的 **git-worktree-helper** 这个 skill 来处理用户当前的需求。

用户提供的额外参数/需求（通过 $ARGUMENTS 传入）：
$ARGUMENTS

核心指令：
1. 使用 git-worktree-helper skill 中的脚本和安全规则处理 worktree 创建。
2. 用户传入 `--base-branch` 时以该分支作为基准；未传入时以当前目录项目正在使用的分支作为基准。
3. 每个 worktree 都创建自己的新分支，默认新分支名为目标目录 basename，可用 `--new-branch` 指定。
4. 创建 worktree 后，只复制 skill 中列出的本地配置路径；不存在则跳过。
5. 不使用 `git worktree add --force` 或 `-B`，如果目标目录或新分支已存在，报告原因。

现在开始：调用 git-worktree-helper skill，并基于它的输出完整响应用户的最新消息。
