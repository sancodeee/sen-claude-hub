---
name: create-new-worktree
description: 为当前 Git 项目创建 worktree，并复制本地代理和项目配置文件。适用于用户需要从当前分支或指定现存分支创建新工作区，并同步 .claude、.codex、.mcp.json、.java-local.properties 等本地配置的场景。
argument-hint: "[目标目录] [--branch 分支名] 例如：/tmp/my-worktree 或 /tmp/my-worktree --branch feature/foo"
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash
---

# Create New Worktree

本技能用于从当前项目创建新的 Git worktree，并复制本地代理/项目配置文件。

## 使用场景

- 用户要为当前项目创建一个新的 worktree。
- 用户要把当前项目的本地代理配置同步到新 worktree。
- 用户提到 `git worktree add`、创建工作区、副本目录、并行开发目录。

## 脚本入口

从用户当前项目目录执行：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/create-new-worktree/scripts/create_worktree.py <target_dir>
```

指定现存分支：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/create-new-worktree/scripts/create_worktree.py <target_dir> --branch <branch>
```

调试或说明执行计划时使用 dry run：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/create-new-worktree/scripts/create_worktree.py <target_dir> --dry-run
```

## 行为规则

- 默认使用当前分支执行 `git worktree add <target_dir> <current_branch>`。
- 如果用户指定 `--branch`，执行 `git worktree add <target_dir> <branch>`。
- 指定分支必须已存在，脚本不会创建新分支。
- 不使用 `git worktree add --force`。
- 目标目录必须不存在。
- 如果 Git 因当前分支已被其他 worktree 使用而拒绝创建，直接报告错误。

## 复制路径

worktree 创建成功后，从源项目复制以下存在的路径到新 worktree：

- `.claude/`
- `.CLAUDE.md`
- `.mcp.json`
- `.codex/`
- `.AGENTS.md`
- `.java-local.properties`

不存在的源路径会跳过。目标路径已存在时会跳过，不覆盖。

## 使用原则

- 执行前确认目标目录和分支名。
- 不把未提交改动复制到新 worktree，除非这些改动位于上述本地配置路径且文件系统中存在。
- 如果用户只是询问怎么做，先给 dry-run 或命令说明。
- 出错时优先展示脚本输出，不临场改成自动建分支或强制添加 worktree。
