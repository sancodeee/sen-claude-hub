# TripForge 多 Agent 准确性增强协议

本文件只在启用多 Agent 调研或最终核验时使用。它是 `SKILL.md` 的增强规则，不得替代、删除、弱化 `SKILL.md`、`template.md`、`sources.md` 中任何既有强制要求。

## 不可削弱边界

- 现有 `必须`、`强制`、`不得`、`至少交叉核验两处`、`UGC 仅发现线索`、`无法核实标 ❓` 等规则全部继续生效。
- 多 Agent 只是调研与质检增强层，不是最终作者；最终攻略正文、HTML 文件、来源附录和交付判断只能由 Main Orchestrator 统一裁决、统一写入、统一修复。
- 当 subagent 不可用、返回结果缺来源、证据互相冲突且无法裁决、或环境无法执行多 Agent 编排时，回退到单 Agent 严格流程；回退不得降低任何核验、标注、来源附录或交付检查要求。

## 角色边界

- **Main Orchestrator（唯一主控）**：负责读规范、读来源、拆分调研任务、合并证据、事实裁决、选景排程、写 HTML、修复 Review / Verification 发现的问题，并对最终交付负责。
- **Research Subagents（调研员）**：只做调研证据采集和结构化整理；不得写最终正文、不得生成 HTML、不得修改文件、不得把 UGC 单源线索当结论。
- **Consistency Review Agent（内容一致性审查员）**：只检查结构完整性、行程动线、六维度完整性，以及餐饮 / 交通 / 天气 / 住宿之间是否矛盾；不得直接改 HTML。
- **Final Verification Agent（最终核验员）**：作为交付闸门，只核验最终 HTML 与来源附录的事实、来源、置信度、正文-附录一致性；不得润色、补写或直接改文件。未给出“通过”时不得交付。
- **单 Agent 回退核验**：当平台无独立 subagent 时，Main Orchestrator 必须按 Final Verification Agent 的同一输出格式完成最终自检，并显式标注为单 Agent 回退核验；不得省略任何事实、来源、置信度或正文-附录一致性检查。

## Research Subagent 分工

Main Orchestrator 按需拆分以下调研任务；简单行程可不拆分，但准确性要求完全一致：

- 天气 / 日出日落 / 潮汐。
- 跨城交通 / 当地交通。
- 景点 / 门票 / 开放预约。
- 餐饮 / 住宿 / 本地生活。
- 避坑 / UGC 线索甄别。

## 证据卡片格式

所有 Research Subagent 必须按下列证据卡片格式返回。缺任一关键字段的结论不得直接写入正文：

```text
信息项：
结论：
适用日期 / 地点：
来源1：
来源2：
来源类型：官方 / 平台 / UGC
核验日期：
置信度：✅ / ⚠️ / ❓
冲突点：
是否可写入正文：
```

## 事实台账准入规则

- Main Orchestrator 必须先把 subagent 结果合并为事实台账，再写正文；未进入事实台账的信息不得写入正文。
- 没有来源的结论无效；只有 UGC 来源的结论不得写成事实。
- 易变信息不足两处来源时，必须标 `⚠️` 或 `❓`，不得标 `✅`。
- 多来源冲突时，不得静默选择最方便的结论；必须记录冲突，并在正文或来源附录中体现处理方式。
- 正文中的关键数字、时间、价格、预约规则、天气数值、班次和开放信息，必须能回溯到来源附录。

## 执行顺序

1. Main Orchestrator 完整读取 `template.md`、`sources.md` 和本文件。
2. Main Orchestrator 将本文件的角色边界、来源规则、证据卡片格式和禁用事项发送给 Research Subagents。
3. Research Subagents 只返回结构化证据卡片，不写正文、不生成 HTML、不修改文件。
4. Main Orchestrator 建立事实台账，执行双源核验、UGC 降权、冲突处理和置信度裁决。
5. Main Orchestrator 独立完成选景、排程、分段写入 HTML 和来源附录。
6. Consistency Review Agent 输出一致性问题报告，Main Orchestrator 修复。
7. Final Verification Agent 输出最终核验报告；若不通过，Main Orchestrator 修复后重新核验。

## Consistency Review 输出格式

```text
结论：通过 / 不通过

结构完整性问题：
- ...

行程动线问题：
- ...

跨段一致性问题：
- ...

需主控修复后复查：
- ...
```

## Final Verification 输出格式

```text
结论：通过 / 不通过

阻断问题：
- ...

需修复问题：
- ...

可接受风险：
- ...

正文-来源一致性抽查：
- 信息项：
- 正文写法：
- 来源附录：
- 判断：
```

## 不通过条件

出现任一情况，Consistency Review 或 Final Verification 必须判“不通过”：

- 正文存在来源附录无法回溯的关键易变信息。
- 易变信息只有一处来源却标为 `✅`。
- UGC 单源线索被写成确定事实。
- 多来源冲突未记录或未在正文 / 附录体现处理方式。
- 行程表、景点详情卡、吃喝指南、住宿片区、天气调度之间存在明显矛盾。
- 六维度不完整，或维度 4–6 被压缩成泛泛摘要。
- Final Verification 未执行或单 Agent 回退核验未按同一格式执行。
