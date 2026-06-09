---
name: git-worktree-helper:cleanup
description: Immediately call git-worktree-helper to return managed configuration changes, then safely remove a finished worktree and branch.
argument-hint: "[worktree目录] [--keep-branch] [--dry-run] 例如：/tmp/my-worktree"
---

你现在必须**立即且强制**调用已安装的 **git-worktree-helper** 这个 skill 来清理一个已使用完毕的 worktree（删除目录 + 删除该 worktree 所在分支）。

用户提供的额外参数/需求（通过 $ARGUMENTS 传入）：
$ARGUMENTS

核心指令：

1. 调用 skill 中的 `remove_worktree.py` 处理清理，默认 **不要** 带 `--force`。
2. 脚本会先比较并回收 `.claude/`、`CLAUDE.md`、`.mcp.json`、`.codex/`、`AGENTS.md` 的新增和修改；worktree 中的删除不传播。
3. 配置冲突或写入失败会以 `config_sync_conflict` / `config_sync_error` 阻断，不能通过 `--force` 绕过。
4. 脚本还会做注册校验、主 worktree 拒绝、非受管未提交改动、未合并分支、当前 HEAD 分支等预检。
5. 如果脚本退出码为 `2`（预检阻断），输出会以 `PRECHECK FAIL` 开头并列出 `code:/detail:`。这种情况下：
   - **不要**自动重试加 `--force`。
   - 把每条 `code` 翻译成中文摘要（例如 `dirty_worktree` → "worktree 目录有未提交改动"），告知用户具体影响（强制删除会丢失这些改动 / 分支未合并强删后无法恢复）。
   - 明确询问用户："是否仍要强制删除？" 用户明确同意后才追加 `--force` 重新执行。
   - 如果用户只想保留分支但删目录，改用 `--keep-branch` 而非 `--force`。
   - 如果 code 是 `config_sync_conflict` 或 `config_sync_error`，要求用户先处理同步问题，不要询问是否强制删除。
6. 如果脚本退出码为 `1`（参数/路径错误，如目标不是已注册 worktree），如实回报给用户，不要尝试强制。
7. 用户明确要求 dry run 时透传 `--dry-run`，并展示逐文件同步计划。
8. 不要主动调用 `git worktree remove` / `git branch -D` 等命令，全部经由脚本执行，保持行为一致。

现在开始：调用 git-worktree-helper skill 的 `remove_worktree.py`，并基于它的输出完整响应用户的最新消息。
