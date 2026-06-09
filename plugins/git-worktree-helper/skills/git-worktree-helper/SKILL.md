---
name: git-worktree-helper
description: 为当前 Git 项目创建 worktree 并同步本地代理与项目配置，或在安全回收 worktree 中的配置变更后清理目录与对应分支。
argument-hint: "创建：[目标目录] [--base-branch <分支>] [--new-branch <分支>]；清理：[worktree目录] [--keep-branch] [--force] [--dry-run]"
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash
---

# Git Worktree Helper

本技能用于从当前项目**创建**新的 Git worktree 并同步本地代理/项目配置，或先把配置变更安全回收到主项目，再**清理**用完的 worktree（目录 + 对应分支）。

下列命令中的 `${PLUGIN_ROOT}` 表示插件根目录。执行脚本前必须先完成初始化：

- Claude Code：执行 `PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:?CLAUDE_PLUGIN_ROOT is not set}"`。
- Codex：agent 必须从已加载技能的绝对路径中取得当前 `SKILL.md` 所在目录，再向上两级得到插件根目录，并将该绝对路径赋给
  `PLUGIN_ROOT`。不要在 Codex 中执行 Claude Code 的赋值命令。

Codex 示例：若当前技能文件是
`/path/to/git-worktree-helper/skills/git-worktree-helper/SKILL.md`，则必须执行：

```bash
PLUGIN_ROOT="/path/to/git-worktree-helper"
```

所有脚本命令都使用 `${PLUGIN_ROOT:?PLUGIN_ROOT must be set}`，未正确初始化时应立即停止，禁止以空路径继续执行。

## 使用场景

- 用户要为当前项目创建一个新的 worktree。
- 用户要把当前项目的本地代理配置同步到新 worktree。
- 用户提到 `git worktree add`、创建工作区、副本目录、并行开发目录。
- 用户已完成某个 worktree 的工作，要回收目录与对应分支（"删 worktree"、"清理 worktree"、"工作区用完了"）。

## 创建脚本入口

从用户当前项目目录执行：

```bash
python3 "${PLUGIN_ROOT:?PLUGIN_ROOT must be set}/skills/git-worktree-helper/scripts/create_worktree.py" <target_dir>
```

指定基准分支：

```bash
python3 "${PLUGIN_ROOT:?PLUGIN_ROOT must be set}/skills/git-worktree-helper/scripts/create_worktree.py" <target_dir> --base-branch <branch>
```

指定新 worktree 分支名：

```bash
python3 "${PLUGIN_ROOT:?PLUGIN_ROOT must be set}/skills/git-worktree-helper/scripts/create_worktree.py" <target_dir> --base-branch <branch> --new-branch <new_branch>
```

调试或说明执行计划时使用 dry run：

```bash
python3 "${PLUGIN_ROOT:?PLUGIN_ROOT must be set}/skills/git-worktree-helper/scripts/create_worktree.py" <target_dir> --dry-run
```

## 清理脚本入口

默认安全模式（不带 `--force`，触发预检；预检失败仅报告不删除）：

```bash
python3 "${PLUGIN_ROOT:?PLUGIN_ROOT must be set}/skills/git-worktree-helper/scripts/remove_worktree.py" <target_dir>
```

只删 worktree、保留分支：

```bash
python3 "${PLUGIN_ROOT:?PLUGIN_ROOT must be set}/skills/git-worktree-helper/scripts/remove_worktree.py" <target_dir> --keep-branch
```

强制模式（跳过阻断性预检，`worktree remove --force` + `branch -D`，**只在用户明确确认后使用**）：

```bash
python3 "${PLUGIN_ROOT:?PLUGIN_ROOT must be set}/skills/git-worktree-helper/scripts/remove_worktree.py" <target_dir> --force
```

预演：

```bash
python3 "${PLUGIN_ROOT:?PLUGIN_ROOT must be set}/skills/git-worktree-helper/scripts/remove_worktree.py" <target_dir> --dry-run
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
- 创建完成后，在 worktree 的 Git 元数据目录记录受管配置的文件级基线；基线不会写入项目目录。

### 清理

- 删除前必须比较并同步 `.claude/`、`CLAUDE.md`、`.mcp.json`、`.codex/`、`AGENTS.md`。
- 使用创建时基线、当前主项目和待删 worktree 做三方比较：
  - 仅 worktree 修改或新增：同步到主项目。
  - 仅主项目修改：保留主项目。
  - 两边修改结果相同：跳过。
  - 两边产生不同修改或文件类型变化：以 `config_sync_conflict` 阻断。
  - worktree 中的删除不传播到主项目。
- 没有基线的旧 worktree 使用保守模式：只复制主项目缺失文件；同名不同内容视为冲突。
- 同步计划完整检查无冲突后才写入；写入失败以 `config_sync_error` 阻断并保留 worktree。
- 未提交改动全部位于受管路径时，同步成功后可自动强制移除 worktree；其他路径改动仍按 `dirty_worktree` 阻断。
- **必须先用默认模式**调用 `remove_worktree.py`（不带 `--force`），触发预检。
- 预检不通过时，脚本退出码 `2` 并打印 `PRECHECK FAIL` + `code:/detail:` 列表。常见 code：
  - `main_worktree`：拒绝清理主 worktree（即使 `--force` 也不允许）。
  - `dirty_worktree`：目标 worktree 有未提交改动 / 未追踪文件，强制删除会丢失。
  - `branch_unmerged`：分支未合并到主仓库 HEAD，强制删除后不可恢复。
  - `branch_is_head`：分支正是主仓库当前 HEAD，禁止删除。
  - `config_sync_conflict`：主项目和 worktree 的受管配置存在冲突，必须人工处理。
  - `config_sync_error`：配置读取或写入失败，必须修复后重试。
- 预检阻断时，必须向用户复述具体问题与影响，并征得明确同意后才能加 `--force` 重新执行。
- `config_sync_conflict` 和 `config_sync_error` 不允许使用 `--force` 绕过。
- 用户希望保留分支只删目录 → 用 `--keep-branch`，不要直接 `--force`。
- 退出码 `1`（如目标不是已注册 worktree）属于参数错误，直接回报用户，不要尝试强制。
- 不要绕过脚本直接执行 `git worktree remove` / `git branch -D`。
- `--dry-run` 输出逐文件同步计划，不同步也不删除。

## 复制路径

worktree 创建成功后，从源项目复制以下存在的路径到新 worktree：

- `.claude/`
- `CLAUDE.md`
- `.mcp.json`
- `.codex/`
- `AGENTS.md`
- `.java-local.properties`

不存在的源路径会跳过。目标路径已存在时会跳过，不覆盖。

cleanup 回收范围不包含 `.java-local.properties`；该文件只维持创建时单向复制行为。

## 使用原则

- 执行前确认目标目录、基准分支和新分支名。
- 不把未提交改动复制到新 worktree，除非这些改动位于上述本地配置路径且文件系统中存在。
- 如果用户只是询问怎么做，先给 dry-run 或命令说明。
- 出错时优先展示脚本输出，不临场改成强制添加 worktree 或覆盖已有分支。
