---
name: git-worktree-helper
description: 当用户要为当前 Git 项目创建 worktree、同步本地代理配置，或回收配置后清理已完成的 worktree 与分支时使用。
argument-hint: "创建：[目标目录] [--base-branch <分支>] [--new-branch <分支>]；清理：[worktree目录] [--keep-branch] [--force] [--dry-run]"
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash
---

# Git Worktree Helper

使用随附脚本创建 worktree 并复制本地配置，或先回收配置变更，再清理目录与分支。

## 选择操作与确认参数

- 创建：明确源项目、目标目录、基准引用和新分支。默认源项目为当前目录，基准为当前分支，新分支为目标目录 basename。
- 清理：明确目标 worktree 和是否保留分支；必要时先只读执行 `git worktree list --porcelain` 定位。目标不明确或有多个候选时，只询问缺失信息，不猜测、不批量删除。
- 已提供的参数与授权直接沿用。执行前简要说明解析结果；不为已明确授权的同一操作重复询问。
- 仅咨询或索要示例：展示命令或 `--dry-run` 示例，不实际执行创建/清理。明确要求预演时，所有调用均带 `--dry-run`。
- 本技能只实现创建与清理。移动、重命名请求应说明当前不支持；不因此自动修改插件源码，也不绕过脚本操作。

## 初始化插件路径

`${PLUGIN_ROOT}` 必须指向当前已加载插件的绝对根目录：

- Claude Code：执行 `PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:?CLAUDE_PLUGIN_ROOT is not set}"`。
- Codex：从当前加载的 `SKILL.md` 绝对路径取得技能目录，再向上两级得到插件根目录；不要使用 Claude Code 的环境变量。

例如技能文件位于 `/path/to/git-worktree-helper/skills/git-worktree-helper/SKILL.md`：

```bash
PLUGIN_ROOT="/path/to/git-worktree-helper"
```

每次运行脚本，都在**同一次 shell 调用**中先按宿主初始化 `PLUGIN_ROOT`，再运行使用 `${PLUGIN_ROOT:?PLUGIN_ROOT must be set}` 的命令；不依赖上次调用的 shell 变量。路径无法确定时停止，不以空路径继续。

## 创建

从源项目目录执行，按需追加参数：

```bash
# Codex 示例：替换为当前已加载插件的真实绝对路径；Claude Code 使用上节的环境变量赋值。
PLUGIN_ROOT="/path/to/git-worktree-helper"
python3 "${PLUGIN_ROOT:?PLUGIN_ROOT must be set}/skills/git-worktree-helper/scripts/create_worktree.py" "<target_dir>" --base-branch "<base_ref>" --new-branch "<new_branch>"
```

| 参数 | 行为 |
|---|---|
| `--base-branch` | 可省略，默认当前分支；detached HEAD 时必须明确提供基准引用 |
| `--new-branch` | 可省略，默认目标目录 basename；始终创建新分支 |
| `--repo` | 可省略，默认当前目录；从其他目录调用时显式提供源项目 |
| `--dry-run` | 仅预演，不创建目录、分支或基线 |

- 目标目录必须不存在，新分支必须不存在且名称合法。
- 目录 basename 必须等于分支名最后一级，例如 `wk-demo` 对应 `wk-demo` 或 `codex/wk-demo`。这是本插件的命名约定。
- 实际创建为 `git worktree add -b <new_branch> <target_dir> <base_ref>`；不使用 `--force`、`-B` 覆盖已有状态。
- 基准引用在校验时固定为 commit，预演和实际创建均使用该提交；默认基准从当前 HEAD 解析，避免同名标签歧义。输出同时报告引用与提交。
- 显式基准短名称优先匹配本地分支 `refs/heads/...`，其次匹配远程跟踪分支 `refs/remotes/...`，再按 Git 引用/提交表达式解析。需要同名标签时使用完整 `refs/tags/...`；`HEAD` 始终按当前 HEAD 解析。
- 仅复制下表存在的配置路径；目标路径已存在时整项跳过、不覆盖，也不递归补齐已有目录。因此已纳入 Git 的配置以基准引用的检出内容为准。
- 创建预演根据固定提交的文件树判断目标是否已有配置；稀疏检出时还按 Git 的 sparse checkout 规则过滤。Git 缺少 `sparse-checkout check-rules` 能力时明确报错，不输出猜测计划。
- 顶层符号链接（含失效链接）按原链接文本复制，不展开链接目录，也不覆盖目标已有的失效链接。相对链接在新 worktree 中仍按相对路径解释；基线记录链接本身，不回收链接目标目录中的文件内容。
- 复制完成后，在 worktree 的 Git 元数据目录写入基线，不写进项目目录。基线 v2 记录普通文件内容与权限；符号链接记录链接目标。
- 实际创建还会在公共 Git 元数据目录写入 `git-worktree-helper-main-worktree.json`，保存已验证的主 worktree 路径。每次使用前校验它属于同一仓库且不是 linked worktree；预演不写该文件。
- 不把其他未提交业务代码复制进新 worktree。

## 配置范围与回收规则

| 路径 | 创建时复制 | 清理前回收 |
|---|---|---|
| `.claude/`、`CLAUDE.md`、`.mcp.json` | 是 | 是 |
| `.codex/`、`AGENTS.md` | 是 | 是 |
| `.java-local.properties` | 是 | 否，仅单向复制 |

清理以创建基线、主 worktree 当前配置、目标 worktree 当前配置做文件级三方比较：

- 仅目标修改/新增：回收到主 worktree；仅主项目修改：保留主项目；两边结果相同：跳过。
- 两边产生不同变更（包括普通文件权限）或文件类型变化：`config_sync_conflict`，不覆盖。
- 目标中的删除不传播到主项目。
- v1 基线仍支持内容回收；缺少原始权限信息且两侧权限不同时阻断，不猜测。没有基线时只补主项目缺失文件，同名不同内容或权限均冲突。
- 完整检查无冲突后才逐文件原子写入；中途写入失败保留 worktree，已写入的文件不自动回滚。
- 被 Git 忽略的受管配置仍参与比较与回收。**受管范围外的未提交、未追踪和忽略文件均阻断默认清理**，包括构建产物和未受管的 `.java-local.properties`；不推断这些文件可丢弃。

## 清理

清理期间暂停其他编辑器、代理和进程对相关配置、目标 worktree 及关联分支的写入。脚本会复核状态，但不提供阻止任意外部写入的文件系统锁。

有已暂存的受管配置时，脚本会实际比较索引对象、类型及可执行位与工作区，差异以 `config_index_conflict` 阻断，包括被 `assume-unchanged` / `skip-worktree` 隐藏的差异；两份内容一致时正常回收。不能只依据 `git status` 的路径分类就自动丢弃索引版本。

主目录按实际主工作树身份、Git 注册信息及已验证的插件定位元数据确定，不根据 `.git` 目录名或调用位置猜测。旧的独立元数据布局若无法确定主目录，停止并用 `--repo "<真实主目录>"` 重试；没有主工作树的 bare 仓库不作为配置回收目的地。

首次调用必须不带 `--force`；可保留用户要求的 `--keep-branch`、`--dry-run`：

```bash
PLUGIN_ROOT="/path/to/git-worktree-helper"
python3 "${PLUGIN_ROOT:?PLUGIN_ROOT must be set}/skills/git-worktree-helper/scripts/remove_worktree.py" "<target_dir>"
```

| 参数 | 行为 |
|---|---|
| `--keep-branch` | 仅删除目录，保留分支；不跳过文件或配置检查 |
| `--repo` | 指定所属仓库；即使在 linked worktree 中调用，配置回收目的地仍是主 worktree |
| `--dry-run` | 打印逐文件计划及删除命令，不同步、不删除；仍执行预检 |
| `--force` | 经默认预检后，允许丢弃非受管本地文件并删除未合并分支；不能绕过下表中的硬性阻断 |

只有配置路径需要强制移除时，脚本会在回收成功后自动使用 Git 的强制移除；该行为不授权丢弃其他路径的数据。

配置计划保留比较时的快照；同步前、同步后和实际删除前复核配置内容、类型及普通文件权限，并检查主项目/目标的 HEAD、分支、受管索引条目与非受管脏路径集合。检测到变化时停止并保留 worktree，不能以 `--force` 绕过；这不保证消除最终检查与删除之间的所有竞争窗口。

### 根据结果决定下一步

`0` 为成功；`1` 为参数、Git 或 I/O 错误；`2` 且包含 `PRECHECK FAIL` 为预检阻断。参数解析也可能退出 `2`，没有该标记时按参数错误处理，不强制重试。

| code / 结果 | 下一步 |
|---|---|
| `main_worktree` | 停止。主 worktree 不能删除，不询问是否强制 |
| `branch_is_head` | 不删除主项目当前分支；用户要求保留分支时可用 `--keep-branch`，否则停止，不强制 |
| `config_sync_conflict` | 展示冲突路径，先解决冲突；即使用户要求强制也不绕过 |
| `config_sync_error` | 修复配置/基线读取或写入问题后重试；不删除或重建基线来消除报错，不强制 |
| `config_index_conflict` | 保留索引和工作区两个版本；先保存或提交所需版本，再整理暂存差异后默认重试，不强制，也不自动 reset / restore / stash |
| `config_sync_changed` / `worktree_changed` | 停止并保留 worktree；暂停其他写入，检查新增变更后重新默认预检，不强制；恢复细节见 [恢复指引](references/recovery.md) |
| `dirty_worktree` | 展示路径，说明含未提交、未追踪或忽略文件；保存后重试，或在明确授权丢弃后使用 `--force` |
| `branch_unmerged` | 说明合并检查以主 worktree 当前 HEAD 为准；可按用户要求保留分支，或在明确授权丢弃提交后使用 `--force` |
| `create_incomplete` / 其他退出 `1` | 先读取 [恢复指引](references/recovery.md)，检查已完成步骤，不直接重跑或强制删除 |

多个 code 同时出现时，任一硬性阻断都必须先解决。仅当剩余问题均为 `dirty_worktree` / `branch_unmerged`，且用户授权覆盖这些具体风险时才能强制；授权已明确则直接继续，不再次询问。

不绕过脚本直接执行 `git worktree remove` 或 `git branch -D`。脚本的通用提示不能覆盖上表的具体错误规则。

## 报告结果

- 创建：报告目标、基准、新分支、复制/跳过路径及基线是否建立。
- 清理：报告回收结果、目录和分支各自是否删除或保留；出错时保留原始 code 与相关路径。
- 预演：明确尚未执行，不能将计划写成已完成。
- 不输出配置正文、密钥或 Token。
