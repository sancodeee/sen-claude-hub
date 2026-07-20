# Obsidian 文档规则

## 位置与抽样

用户指定知识库、目录或文件时优先使用该位置。用户仅说“Obsidian 知识库”“工作知识库”或“我的笔记”时，默认使用 `/Users/sen/Documents/workfile/汽车金融/obsidian-work-knowledgebase`。新建前仅抽样读取目标目录中最相关的少量同主题文档，复用其命名、标签、双链和章节风格；存在多个合理目录时询问用户。更新时修改用户指定或已确认的原文件，不创建重复版本。

## YAML 与来源

新建正式设计必须包含 YAML 字段：`title`、`aliases`、`tags`、`status`、`version`、`created`、`updated`、`last_verified`、`design_mode`、`maturity`、`related`、`source`。成熟文档使用 `status: ready` 和 `maturity: ready-for-implementation-design`，`design_mode` 只能为 `backend` 或 `fullstack`。

`tags` 使用真实项目、业务域、功能模块、设计模式和文档类型标签，优先复用同目录标签，并包含 `detailed-design` 与当前模式。`source` 仅记录实际核验的仓库/分支/提交、真实数据库名及环境、需求或参考资料版本；未涉及的类别不伪造空来源。数据库名称必须是真实数据库名，不能使用示例值。

## 双链与关联

`related` 仅列正文实际使用的 Obsidian wiki-link，正文每个 `[[双链]]` 必须登记到 `related`，且 `related` 中每项必须在正文出现。代码路径、类、接口、表和字段使用行内代码，不伪装为双链。正文设置“设计依据与关联文档”用途表：

| 关联文档 | 类型 | 使用内容 | 影响章节 |
| --- | --- | --- | --- |

除非用户明确要求，不修改 `INDEX.md` 或其他关联文档。

## 正文、版本与更新

正文开头使用 `> [!summary]` 说明文档定位；按实际需要使用 `important`、`note`、`warning` 或 `success` callout，普通块引用不能代替 YAML 元数据。更新原文件时保留有效历史结论与双链，递增 `version` 并更新 `updated`、`last_verified` 和成熟度；在开头加入精简校正记录。已解决或已校正事项移入“已确认”或“已校正”章节，不继续混在“待确认”或“当前缺口”中；受基线变化影响的流程、接口、字段、状态和图必须重新核验。
