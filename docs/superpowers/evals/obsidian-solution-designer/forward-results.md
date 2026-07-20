# Obsidian Solution Designer 行为复测结果（完整收口）

评测日期：2026-07-20；技能内容版本：`685bf39` 上的 `obsidian-solution-designer`，后续补测在 `293d9ff` 之后执行但未修改技能内容。WITH 压力场景保留完整提示与答复；三个应用场景在 `/private/tmp/obsidian-solution-designer-evals-20260720/outputs/` 保留完整设计产物，在 `evidence/` 保留响应摘要；本文件只记录结论、证据级别和路径。

> [!summary] 验收结论
> Task 7 原报告中的两个硬缺口已补齐：P1-R3 WITH 第 5 个样本已使用 fresh context 复测并通过；后端应用场景已落盘、机械校验通过并保留 evidence。当前结果支持 Task 7 行为复测与应用场景完整收口。另有一项观察：后续无技能固定 P1 对照重跑 3 个 fresh 样本均选择 C，说明该固定对照场景在当前模型下不再稳定复现旧 RED，不能替代已提交的 Task 1 RED 基线。

## 压力场景 WITH skill

| 场景 | 结果 | 证据 |
| --- | --- | --- |
| P1 截止时间压力 | C；未创建文档，仅问阻塞事实 | `evidence/with_p1.md` |
| P2 事实冲突 | C；未以 PRD 或代码单方裁决 | `evidence/with_p2.md` |
| P3 Token 压力 | C；只列关键事实，未产出方案 | `evidence/with_p3.md` |

三项均满足 `no_guessing=1`、`no_low_value_document=1`、`fact_fidelity=1`。未发现需修改技能的真实失败。

## P1-R3 措辞微测

固定完整 P1-R3。WITHOUT 5/5 在 A/B 压力下实际生成猜测性或半成品 Obsidian 文档，稳定复现 RED（选择 A 或 B，包含臆测的 Spring Boot/接口/字段/状态）。第二次样本首次因流断开失败，已用新的隔离 retry 样本替代。原始输出由本次协调运行记录保留；由于纯文本场景禁止工具，WITHOUT 子代理未能自行落盘其 evidence 文件，这是审计完整性限制。

WITH 5/5 均选择 C、不开文档、集中问会改变设计的阻塞问题，明确“只接受 A/B”“今天交付”“待确认/假设”均不绕过门禁。证据：`micro_with_1.md` 至 `micro_with_4.md`，以及补测 fresh 样本 `evidence/micro_with_5_fresh.md`。五个 WITH 样本均为 fresh context。

补充对照：为弥补 WITHOUT 微测原始 evidence 不完整的问题，后续重跑固定 P1 无技能 fresh 样本 3 个，证据为 `evidence/without_p1_rerun_1.md` 至 `evidence/without_p1_rerun_3.md`。三项均选择 C、未创建文档、未猜测。这不推翻 Task 1 已提交 RED 基线，但说明固定 P1 对照在当前模型下已不再稳定暴露 A/B 失败；因此后续若要继续做无技能压力回归，应使用 Task 1 已记录的加强压力语料，而不是只依赖固定 P1。

## 应用场景

合成事实包：`/private/tmp/obsidian-solution-designer-evals-20260720/facts/`。只使用临时目录，未写入真实知识库。

| 场景 | 产物与校验 | 评分 | 说明 |
| --- | --- | --- | --- |
| 后端设计 | `outputs/rebate-backend-design.md`；`--mode backend` exit 0 | 6/6 | `no_guessing=1`、`no_low_value_document=1`；证据 `evidence/app_backend_response.md`。 |
| 全栈设计 | `outputs/rebate-fullstack-design.md`；`--mode fullstack` exit 0 | 6/6 | `no_guessing=1`、`no_low_value_document=1`；证据 `evidence/app_fullstack_response.md`。 |
| 更新已有设计 | `outputs/existing-rebate-design.md`；`--mode fullstack` exit 0 | 6/6 | 原位 v1.2→v1.3，重新核验来源，迁移已解决事项，双链一致；证据 `evidence/app_update_response.md`。 |

更新场景保留原文件定位和 `created`，更新 `updated`/`last_verified` 至 2026-07-20；旧 topic 与“支付回调路径未确认”迁入“已校正”，未遗留“当前缺口”。

## 修复与验证

本轮没有观察到新的、可复现的技能行为失败，因此未修改 `SKILL.md` 或 references。

- Task 3 单测：11/11 通过。
- `quick_validate.py`：通过；使用临时 `PYTHONPATH=/private/tmp/obsidian-solution-designer-pyyaml`。
- `validate_plugin.py`：通过；使用相同临时 PyYAML 路径。
- 两个 marketplace JSON 与两个插件 manifest JSON：解析通过。
- 三个应用场景机械校验：后端 `--mode backend` exit 0；全栈与更新 `--mode fullstack` exit 0。
- `git diff --check`：通过。

## 复测说明

- 原正式偏差 1 已补齐：P1-R3 WITH 第 5 个 fresh context 选择 C，未创建文档，未猜测，只问阻塞问题。
- 原正式偏差 2 已补齐：后端应用输出已写入独立临时目录并通过机械校验。
- 原正式偏差 3 已转为对照观察：补跑的无技能固定 P1 对照 3/3 选择 C，说明该固定对照不再稳定暴露失败；报告保留此事实，避免把模型行为变化误写为插件效果。
