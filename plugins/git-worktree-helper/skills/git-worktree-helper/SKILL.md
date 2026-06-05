---
name: git-worktree-helper
description: 为当前 Git 项目基于指定分支或当前分支创建 worktree，并复制本地代理和项目配置文件。适用于用户需要基于同一个分支创建多个 worktree，并同步 .claude、CLAUDE.md、.codex、AGENTS.md、.mcp.json、.java-local.properties 等本地配置的场景。
argument-hint: "[目标目录] [--base-branch 分支名] [--new-branch 新分支名] 例如：/tmp/my-worktree --base-branch feature/a"
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash
---

# Git Worktree Helper

本技能用于从当前项目创建新的 Git worktree，并复制本地代理/项目配置文件。

## 使用场景

- 用户要为当前项目创建一个新的 worktree。
- 用户要把当前项目的本地代理配置同步到新 worktree。
- 用户提到 `git worktree add`、创建工作区、副本目录、并行开发目录。

## 脚本入口

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

## 行为规则

- 如果用户传入 `--base-branch`，以该分支作为基准。
- 如果用户不传 `--base-branch`，以当前目录项目正在使用的分支作为基准。
- 每个 worktree 都会创建并检出一个新分支，默认新分支名为目标目录 basename。
- 实际命令形态是 `git worktree add -b <new_branch> <target_dir> <base_branch>`。
- 基准分支不会被重复检出；它只作为新分支的起点。
- 不使用 `git worktree add --force`。
- 不使用 `git worktree add -B` 覆盖已有分支。
- 目标目录必须不存在。

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
