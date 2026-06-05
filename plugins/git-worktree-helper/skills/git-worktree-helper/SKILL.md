---
name: git-worktree-helper
description: 为当前 Git 项目基于指定分支或当前分支创建 worktree 并同步本地代理与项目配置（.claude、CLAUDE.md、.codex、AGENTS.md、.mcp.json、.java-local.properties 等），或清理已使用完毕的 worktree（目录 + 对应分支，带预检与确认流程）。
argument-hint: "创建：[目标目录] [--base-branch <分支>] [--new-branch <分支>]；清理：[worktree目录] [--keep-branch] [--force] [--dry-run]"
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash
---

# Git Worktree Helper

本技能用于从当前项目**创建**新的 Git worktree 并同步本地代理/项目配置，或**清理**用完的 worktree（目录 + 对应分支）。

## 使用场景

- 用户要为当前项目创建一个新的 worktree。
- 用户要把当前项目的本地代理配置同步到新 worktree。
- 用户提到 `git worktree add`、创建工作区、副本目录、并行开发目录。
- 用户已完成某个 worktree 的工作，要回收目录与对应分支（"删 worktree"、"清理 worktree"、"工作区用完了"）。

## 创建脚本入口

从用户当前项目目录执行：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/git-worktree-helper/scripts/create_worktree.py <target_dir>
```

指定基准分支：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/git-worktree-helper/scripts/create_worktree.py <target_dir> --base-branch <branch>
```

指定新 worktree 分支名：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/git-worktree-helper/scripts/create_worktree.py <target_dir> --base-branch <branch> --new-branch <new_branch>
```

调试或说明执行计划时使用 dry run：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/git-worktree-helper/scripts/create_worktree.py <target_dir> --dry-run
```

## 清理脚本入口

默认安全模式（不带 `--force`，触发预检；预检失败仅报告不删除）：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/git-worktree-helper/scripts/remove_worktree.py <target_dir>
```

只删 worktree、保留分支：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/git-worktree-helper/scripts/remove_worktree.py <target_dir> --keep-branch
```

强制模式（跳过阻断性预检，`worktree remove --force` + `branch -D`，**只在用户明确确认后使用**）：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/git-worktree-helper/scripts/remove_worktree.py <target_dir> --force
```

预演：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/git-worktree-helper/scripts/remove_worktree.py <target_dir> --dry-run
```

退出码：`0` 成功，`1` 一般错误（如路径不是已注册 worktree），`2` 预检阻断。

## 行为规则

### 创建

- 如果用户传入 `--base-branch`，以该分支作为基准。
- 如果用户不传 `--base-branch`，以当前目录项目正在使用的分支作为基准。
- 每个 worktree 都会创建并检出一个新分支，默认新分支名为目标目录 basename。
- 实际命令形态是 `git worktree add -b <new_branch> <target_dir> <base_branch>`。
- 基准分支不会被重复检出；它只作为新分支的起点。
- 不使用 `git worktree add --force`。
- 不使用 `git worktree add -B` 覆盖已有分支。
- 目标目录必须不存在。

### 清理

- **必须先用默认模式**调用 `remove_worktree.py`（不带 `--force`），触发预检。
- 预检不通过时，脚本退出码 `2` 并打印 `PRECHECK FAIL` + `code:/detail:` 列表。常见 code：
  - `main_worktree`：拒绝清理主 worktree（即使 `--force` 也不允许）。
  - `dirty_worktree`：目标 worktree 有未提交改动 / 未追踪文件，强制删除会丢失。
  - `branch_unmerged`：分支未合并到主仓库 HEAD，强制删除后不可恢复。
  - `branch_is_head`：分支正是主仓库当前 HEAD，禁止删除。
- 预检阻断时，必须向用户复述具体问题与影响，并征得明确同意后才能加 `--force` 重新执行。
- 用户希望保留分支只删目录 → 用 `--keep-branch`，不要直接 `--force`。
- 退出码 `1`（如目标不是已注册 worktree）属于参数错误，直接回报用户，不要尝试强制。
- 不要绕过脚本直接执行 `git worktree remove` / `git branch -D`。

## 复制路径

worktree 创建成功后，从源项目复制以下存在的路径到新 worktree：

- `.claude/`
- `CLAUDE.md`
- `.mcp.json`
- `.codex/`
- `AGENTS.md`
- `.java-local.properties`

不存在的源路径会跳过。目标路径已存在时会跳过，不覆盖。

## 使用原则

- 执行前确认目标目录、基准分支和新分支名。
- 不把未提交改动复制到新 worktree，除非这些改动位于上述本地配置路径且文件系统中存在。
- 如果用户只是询问怎么做，先给 dry-run 或命令说明。
- 出错时优先展示脚本输出，不临场改成强制添加 worktree 或覆盖已有分支。
