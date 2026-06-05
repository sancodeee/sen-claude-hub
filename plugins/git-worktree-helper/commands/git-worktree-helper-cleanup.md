---
name: git-worktree-helper:cleanup
description: Immediately call the git-worktree-helper skill to remove a finished Git worktree and its checked-out branch with safety pre-checks.
argument-hint: "[worktree目录] [--keep-branch] [--dry-run] 例如：/tmp/my-worktree"
---

你现在必须**立即且强制**调用已安装的 **git-worktree-helper** 这个 skill 来清理一个已使用完毕的 worktree（删除目录 + 删除该 worktree 所在分支）。

用户提供的额外参数/需求（通过 $ARGUMENTS 传入）：
$ARGUMENTS

核心指令：

1. 调用 skill 中的 `remove_worktree.py` 处理清理，默认 **不要** 带 `--force`。
2. 脚本会先做预检（注册校验、主 worktree 拒绝、未提交改动、未合并分支、当前 HEAD 分支等）。
3. 如果脚本退出码为 `2`（预检阻断），输出会以 `PRECHECK FAIL` 开头并列出 `code:/detail:`。这种情况下：
   - **不要**自动重试加 `--force`。
   - 把每条 `code` 翻译成中文摘要（例如 `dirty_worktree` → "worktree 目录有未提交改动"），告知用户具体影响（强制删除会丢失这些改动 / 分支未合并强删后无法恢复）。
   - 明确询问用户："是否仍要强制删除？" 用户明确同意后才追加 `--force` 重新执行。
   - 如果用户只想保留分支但删目录，改用 `--keep-branch` 而非 `--force`。
4. 如果脚本退出码为 `1`（参数/路径错误，如目标不是已注册 worktree），如实回报给用户，不要尝试强制。
5. 用户明确要求 dry run 时透传 `--dry-run`。
6. 不要主动调用 `git worktree remove` / `git branch -D` 等命令，全部经由脚本执行，保持行为一致。

现在开始：调用 git-worktree-helper skill 的 `remove_worktree.py`，并基于它的输出完整响应用户的最新消息。
