# Git Worktree Helper 评测证据

场景见 [scenarios.md](scenarios.md)。以下记录实际评测输出与人工判读，不以措辞匹配代替行为检查。

## 无 skill 对照

独立代理 `skill_baseline_control`：场景 1 停止清理；2 给出强制重试；3 和 4 查询 worktree；5 只给 Git 命令示例；6 给出 Git 移动命令示例。

实际片段：

- 场景 1：“该路径是主 worktree，脚本明确禁止清理，`--force` 也不会放行。已停止清理。”
- 场景 2：`remove_worktree.py /tmp/task --force`，未定位脚本，也未初始化插件路径。
- 场景 3、4：`git -C /tmp/task worktree list --porcelain`。
- 场景 6：仅展示 `git worktree move /tmp/task /tmp/renamed`，未执行。

说明：基础安全决策不全依赖 skill；技能的增益应主要体现在插件专属约束、错误分流和范围控制。

## 原始 2.1.1 skill

独立代理 `skill_baseline_existing`：场景 1、2、3、4、5 的方向正确；场景 6 出现范围扩张。

实际片段：

- 场景 1：“末尾的通用重试提示不适用于 `main_worktree`，我不会执行强制删除。”原始文案冲突没有在本样本中导致错误强制。
- 场景 2：同一次 shell 调用初始化实际 PLUGIN_ROOT 后执行 `remove_worktree.py /tmp/task --force`，未重复询问。
- 场景 4：查询 worktree 并以 `ls -lde` 检查目标与 `.claude` 权限，未覆盖重建。
- 场景 6：“读取现有脚本以扩展移动能力并复用名称校验”，下一步为读取 `create_worktree.py`。用户仅要求移动，skill 将其扩大为插件开发。

## 优化后第一轮

独立代理 `skill_forward`：六个场景的操作方向均符合预期，场景 6 改为说明不支持移动；但脚本调用直接使用绝对路径，遗漏 PLUGIN_ROOT 初始化和保护形式。

实际片段：

- 场景 2：直接调用 `python3 "/Users/sen/Documents/workspace/sen-claude-hub/plugins/git-worktree-helper/skills/git-worktree-helper/scripts/remove_worktree.py" "/tmp/task" --force`。
- 场景 4：先查询 worktree、目标 status（包括 ignored）与 Git 元数据目录，未重跑创建。
- 场景 6：“当前 git-worktree-helper 只支持创建和清理，暂不支持移动或重命名 worktree。”

据此补充了同一次 shell 内初始化的正向命令示例，避免依赖 shell 变量跨调用持久化。

## 优化后第二轮

独立代理 `skill_forward_final`：六个场景的决策和命令形式符合约定。

- 场景 1：报告 `main_worktree` 并停止。
- 场景 2：在同一次 shell 中初始化实际 PLUGIN_ROOT，再通过受保护路径执行 `remove_worktree.py /tmp/task --force`，无多余确认。
- 场景 3：报告配置冲突无法强制绕过，保留目录和分支。
- 场景 4：只读查询 worktree、包括忽略文件的 status、Git 元数据及路径权限，未覆盖重建。
- 场景 5：仅展示创建/清理预演，显式保留 `--repo /tmp/repo`。
- 场景 6：“当前技能仅支持创建和清理，不支持移动或重命名 worktree。”未扩大为插件开发。

这仍为单次独立模拟样本，不能据此宣称所有模型稳定通过。

## 脚本回归

- 修改前新增测试复现权限丢失、忽略文件未阻断、非法基线结构异常、主 HEAD 分支在 force 下先删目录后报错，以及创建失败抛出未处理异常。
- 首轮修改后 26 项测试通过；覆盖旧版内容回收、权限冲突、忽略配置回收、非受管忽略文件阻断、显式强制与预演、两种创建部分失败。
- 通用 skill 校验器不认识原有 Claude 专用 `argument-hint` / `user-invocable` 字段，原版本同样失败；保留原字段，单独校验其值，并在临时副本上对其余结构运行校验器通过。

## 独立代码审查

代理 `worktree_review` 复跑 26 项测试及 7 个补充临时仓库场景后，发现同名 tag 会使 `symbolic-ref --short HEAD` 返回 `heads/task`，导致主 HEAD 保护漏判；Git 最后拒绝删除分支时目录已经删除。

已增加主 HEAD 与同名 tag 的默认/强制/预演保护测试，以及已合并分支在主分支同名 tag 指向旧提交时仍可清理的测试。观察原实现失败后，改为读取完整分支引用并统一去掉 `refs/heads/`；合并检查固定使用主仓库 `HEAD`，避免引用歧义。

最终 28 项 unittest 全部通过。独立审查代理重新测试，并通过 `checkout --ignore-other-worktrees` 复现场景确认默认、`--force`、`--force --dry-run` 都返回 `branch_is_head`，配置未同步、目录未删除；本次复核未发现残留问题。

## 第二轮修复：同步复核、符号链接与预演

新增临时仓库回归测试，先观察原实现失败，再实现修复：

- 同步期间、同步后或同步前主项目发生配置写入：返回 config_sync_changed，保留 worktree 和分支，已有主项目新写入不被覆盖。
- 同步后新增非受管文件、提交或切换分支：返回 worktree_changed，--force 也不删除。
- 顶层目录链接与失效链接按原链接文本复制；目标已有失效链接保持不变；目录链接复制后可正常清理，共享目标中的文件保留。
- 预演按基准 commit 的配置文件树计算复制/跳过；实际创建固定使用同一 commit。当前分支与同名标签并存时，默认基准仍是 HEAD。
- 稀疏检出按具体配置文件运行 Git check-rules 并归并到顶层配置路径，预演与实际一致；旧 Git 缺少该能力时明确报错，不猜测。

独立审查 `worktree_second_review` 首轮发现两个遗漏：状态基线捕获晚于计划计算、非 cone 稀疏检出不一致。均先补失败测试再修复。复核报告：43 项 unittest 全部通过；额外独立验证计划期间新增文件、主 HEAD 变化、预演期间配置变化，以及 cone 稀疏检出，均符合预期，未发现必要残留问题。

独立技能评测 `worktree_second_behavior` 的场景 7—11 均符合约定，实际回答要点：

- config_sync_changed：“既有丢弃授权不能让 --force 绕过”，暂停写入并重新默认预检。
- worktree_changed：停止清理，先核实实际分支与变更。
- 预演：“尚未创建 worktree、复制链接或建立基线”，链接按原文本复制。
- 缺少 check-rules：保持项目状态，只读检查是否有可用 Git，不产生猜测计划。
- 不回滚主项目、不重建基线消除检测；保留第一次同步与第二次新写入，再检查冲突。

并发保护是乐观状态复核，不能锁住任意编辑器或进程；最后检查与删除仍有窗口，skill 明确要求清理期间暂停其他写入。上述技能评测为一次独立模拟样本，不表示跨模型稳定通过率。
