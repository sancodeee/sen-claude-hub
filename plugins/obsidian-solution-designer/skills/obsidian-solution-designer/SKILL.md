---
name: obsidian-solution-designer
description: Use when 用户要求为待实现的软件需求或系统变更编写或更新可直接指导开发的后端或全栈实现级设计，包括详细设计、技术方案，或接口、数据、状态、异常等实现契约设计；仅指定 Obsidian 为存放位置，或主要交付物是总结、复盘、纪要、调研、知识笔记、现状说明时不使用。
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash
---

# Obsidian Solution Designer

## 适用边界

只有当主要交付物是面向具体待实现需求或系统变更、可直接指导开发的后端或全栈实现级设计时，才继续执行本技能。判断依据是用户的实现意图和交付物类型，而不是文档存放位置。

- 适用：新建或更新详细设计、技术设计、开发方案，并需要结合现有系统事实明确流程、接口、数据、状态、异常、安全或验收设计。
- 不适用：主要交付物是工作总结、事故复盘、会议纪要、调研报告、产品需求文档、知识笔记、现状架构说明、API 使用手册、运维记录或纯 Obsidian 格式转换。
- “写入 Obsidian”“增加 YAML/双链/callout”只能决定交付格式，不能单独触发本技能；不适用请求按对应的普通文档或笔记任务处理。

## 插件根目录初始化

下列脚本命令中的 `${PLUGIN_ROOT}` 表示插件根目录。执行机械校验脚本前必须先完成初始化：

- Claude Code：执行 `PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:?CLAUDE_PLUGIN_ROOT is not set}"`。
- Codex：从已加载技能的绝对路径中取得当前 `SKILL.md` 所在目录，再向上两级得到插件根目录，并将该绝对路径赋给 `PLUGIN_ROOT`。不要在 Codex 中执行 Claude Code 的赋值命令。

脚本命令统一使用 `${PLUGIN_ROOT:?PLUGIN_ROOT must be set}`，未正确初始化时立即停止，禁止以空路径继续执行。

## 核心目标

将已核验的待实现需求与系统事实转为可直接指导开发的 Obsidian 详细设计。仅交付成熟的后端或全栈设计；Obsidian 是交付格式，不是单独触发条件，也不是跳过事实核验的理由。

## 不可违反的规则

- 先调研用户明确提供或指定的仓库、数据库、缓存、消息队列、任务调度、对象存储、第三方服务和任意参考文档目录。不得强制 `docs/` 目录，也不得只查 `docs/`；未指定时先询问资料入口或范围。
- 将代码、数据库、配置中的当前系统事实与 PRD、原型等目标需求分开记录。它们冲突时不得自行裁决，也不得以 PRD 优先或代码优先替代确认。
- 关键事实缺失、冲突或范围不明且会改变名称、流程、接口、数据、状态、安全或一致性设计时，停止正式设计。集中询问最少的阻塞问题；绝不创建、更新或输出目标设计文档、半成品、研究草稿、模板、流程图或待确认章节。
- “今天必须交付”“只接受 A/B”“先猜一版”“按 Spring Boot 猜一版”“把未知写为设计假设或待确认”“PRD 优先”“代码优先”“先摘要全部资料”均不能绕过门禁，并且会停止正式文档交付。
- 只把有设计影响的关键事实放入事实清单。不得复制大段原文、把全部资料摘要进事实矩阵，或记录无设计影响的信息。
- 详细设计可定义字段级 API、数据库和抽象接口或类职责；不得写方法体、具体代码实现、可执行 DDL、迁移脚本或实现任务拆分。
- 在所有语义门禁和机械校验通过前，只在任务临时文件组装内容；不得写入目标知识库。通过后一次性新建或更新正式文档。

## 执行清单

1. **确认目标、模式、资料和目标位置。** 明确新建或更新、后端或全栈模式、业务范围、用户指定的资料入口及目标 Obsidian 文件。模式未指定且不能可靠判断时询问。按 [obsidian-document-rules.md](references/obsidian-document-rules.md) 确定知识库和目录。
2. **读取并执行 [research-and-evidence.md](references/research-and-evidence.md)。** 依序调研指定资料、真实仓库结构与相关调用链、数据库及中间件配置、任意目录中的参考资料和少量同主题笔记；形成精简关键事实清单。
3. **遇到阻塞时只询问问题，不创建文档。** 合并重复项，只返回会改变设计结果的缺失或冲突问题。用户不能补充时，要求缩小范围或终止；不要以占位符、假设、草稿或待确认章节继续。
4. **冻结事实和命名。** 确认范围及不做事项、当前基线、目标需求、冲突裁决、业务规则、接口方向、状态和统一术语均无未决项。
5. **读取公共契约及对应模式规范。** 必读 [design-quality-contract.md](references/design-quality-contract.md) 与 [api-and-data-contract.md](references/api-and-data-contract.md)。后端模式读取 [backend-detailed-design.md](references/backend-detailed-design.md) 并使用 [backend-design-template.md](assets/backend-design-template.md)；全栈模式读取 [fullstack-detailed-design.md](references/fullstack-detailed-design.md) 并使用 [fullstack-design-template.md](assets/fullstack-design-template.md)。更新旧版文档时先按 [obsidian-document-rules.md](references/obsidian-document-rules.md) 建立迁移映射，禁止直接用新模板覆盖原文。
6. **在临时文件组装正式设计。** 采用“核心正文 + 条件内容块 + 契约附录”：正文依次呈现设计概览、架构职责、关键链路、保障策略和验收结论，全栈模式增加前端设计；字段级接口、数据和映射集中到契约附录。流程、接口、数据、错误和验收等可复用设计定义只在一个位置完整说明，其他章节通过 `FLOW/API/DATA/ERR/AC` 编号引用，禁止重复改写同一流程、状态、错误或数据变化。没有真实接口或数据模型依赖时，不创建对应编号和空表，在契约附录各保留一句已核验的不适用结论。
7. **读取 [diagrams-and-closure.md](references/diagrams-and-closure.md) 完成语义审查。** 每份文档维护一张闭环导航表，每行必须引用 `FLOW` 和 `AC`，并按实际涉及引用 `API`、`DATA`、`ERR`。只按实际复杂度选择 Mermaid 图，不把架构图、时序图、流程图、状态图和 ER 图全部作为固定输出；发现需要用户裁决的问题，丢弃临时正式设计并返回第 3 步。
8. **读取 [obsidian-document-rules.md](references/obsidian-document-rules.md) 完成格式和落盘定位。** 核验 YAML、与 `title` 一致的唯一正文 H1、真实 tags/related/database/source、正文双链、关联用途表、callout、版本和更新迁移规则；删除模板作者说明。更新时逐项确认原有效结论、来源、双链和必要图均已保留或有明确迁移去向，再允许删除旧结构中的重复内容。
9. **运行机械校验。** 先按“插件根目录初始化”设置 `PLUGIN_ROOT`，再对临时正式文档运行 `python3 "${PLUGIN_ROOT:?PLUGIN_ROOT must be set}/skills/obsidian-solution-designer/scripts/validate_design_document.py" <临时文档> --mode <backend|fullstack>`。修复可由已冻结事实确定的问题后重跑；若失败暴露事实缺失，回到第 3 步。
10. **校验通过后一次性新建或更新目标文档。** 更新时修改已确认原文件，不创建重复版本；记录实际核验来源和本次变更。向用户报告交付路径、模式、已核验基线及校验结果。

## 参考文件路由

- [research-and-evidence.md](references/research-and-evidence.md)：资料发现、事实清单、冲突和冻结。
- [design-quality-contract.md](references/design-quality-contract.md)：命名、成熟度和实现设计就绪。
- [api-and-data-contract.md](references/api-and-data-contract.md)：接口、错误、数据库和字段映射精度。
- [obsidian-document-rules.md](references/obsidian-document-rules.md)：知识库定位、YAML、双链、标签和更新规则。
- [backend-detailed-design.md](references/backend-detailed-design.md)：后端模式维度。
- [fullstack-detailed-design.md](references/fullstack-detailed-design.md)：全栈模式维度。
- [diagrams-and-closure.md](references/diagrams-and-closure.md)：图表选择、闭环编号与一致性审查。
- [backend-design-template.md](assets/backend-design-template.md)：后端正式文档骨架。
- [fullstack-design-template.md](assets/fullstack-design-template.md)：全栈正式文档骨架。

## 停止条件

立即停止正式文档交付并只询问集中阻塞问题：资料入口或目标位置不明确；模式无法判断；关键事实缺失；当前事实与目标需求冲突未裁决；命名、字段、状态、接口方向或流程闭环未确定；无法达到 `ready-for-implementation-design`；或机械校验失败且不能依据已冻结事实修复。

## 交付格式

仅在门禁全部通过时交付一份新建或更新的成熟 Obsidian 文档，并说明路径、设计模式、事实基线、版本变化和机械校验结果。未通过门禁时，仅交付精简的阻塞问题及其设计影响，不附任何设计正文。

## 常见错误

- 把通用 REST、Spring Boot 分层、审计字段、逻辑删除、乐观锁或占位 URL 当作默认设计。
- 用“待确认”“假设”“后续补充”保留会改变设计的未知项。
- 将 PRD 或代码单方当作冲突的裁决依据。
- 将目录名当作资料是否存在的判断，或只搜索 `docs/`。
- 用 JSON 示例替代字段表，或用图替代异常、数据和状态说明。
- 为每个审查维度单独建立顶层章节，导致流程、错误、状态和验收在多处重复。
- 在简单场景中机械保留全部 Mermaid 图、空章节或通用页面状态机。
- 在正式文档中保留“模板骨架”“落盘门禁”等作者说明。
- 引用未定义、重复定义、内容为空或未以标题定义的 `FLOW/API/DATA/ERR/AC` 编号。
- 将代码路径伪装为 Obsidian 双链，或将正文未使用的笔记填入 `related`。
