# ResumeForge 1.0.1 行为复测结果（GREEN / REFACTOR）

评测日期：2026-09-01。场景与评分标准见 [scenarios.md](scenarios.md)，精确输入见 [fixtures/prompts.md](fixtures/prompts.md)，最终规则的逐字输出见 [evidence/final-results.md](evidence/final-results.md)。

## RED 基线

修改前 `1.0.0` 的 S1 关键阻塞场景仅 `1/5` 通过。四次失败都在声明“不能交付最终版”后，仍擅自输出审阅稿或简历正文；详情见 [baseline-results.md](baseline-results.md)。

## 首轮 GREEN 与 REFACTOR

加入输出路由后，S1 首轮达到 `5/5`。随后相邻路由暴露两个边界问题：

- 明确生成审阅稿时，确认事项曾进入同一 Markdown 文档；因此固定为“`markdown` 代码块正文 → 代码块外确认清单”。
- 路由条件存在语义重叠；因此改为从上到下选择第一个命中的唯一路由，并明确“审阅这份草稿”不等于“生成审阅稿”。

独立审查还发现仅审阅可能给出局部替换文案、数据契约仍写成旧的二选一交付，以及省略项和高风险门禁边界不够清楚。以上问题均已同步修正到 Skill、数据契约和质量清单。

## 最终规则哈希复测

最终验证锁定以下文件哈希：

- Skill：`c87f7f024e26b2109e3732f5f674881bf136173323944c8032e69654b18d6d14`。
- 数据契约：`c7e2823b0e43c0b160f0821a86bc219e7aecc1737b42a1182d7f5d90ebe3e131`。
- 质量清单：`396c682d6b01f8a19f091af09c350f7c1fbb1d4f9243ce4b85d0041bc418c4df`。

所有最终运行均为 `gpt-5.6-sol`、reasoning effort `high`、`fork_turns: none` 的全新隔离上下文。

| 场景 / 运行标签 | 验证结果 | 判定 |
| --- | --- | --- |
| S1 `iso_s1_1`—`iso_s1_5` | 五次都只输出阻塞结论、一次性确认清单或正文外缺口；无简历正文 | `5/5` 通过 |
| S2 `iso_s2_review_only` | 只给问题、影响和操作建议，无替换句或改写正文 | 通过 |
| S3 `iso_s3_review_draft` | `verified` 正文位于 `markdown` 代码块，确认清单位于代码块外 | 通过 |
| S4 `iso_s4_omit` | 不追问省略项，无空模块；交付说明标明“通用版”并说明可继续定制 | 通过 |

最终结果：`fact_fidelity=8/8`，`route_exclusivity=8/8`；专项门禁 `blocker_no_body=5/5`、`review_no_rewrite=1/1`、`draft_separation=1/1`、`omit_no_reask=1/1`。

## 静态验证

最终静态命令结果在完成文档同步后重新执行：

- Plugin Creator `validate_plugin.py`：exit 0。
- 两个 marketplace 与两个 plugin manifest JSON 的 `jq empty`：exit 0。
- `agents/openai.yaml` 与仓库 Skill frontmatter 的 YAML 解析和字段断言：exit 0。
- 两个平台 manifest、Claude marketplace 与 README 的 `1.0.1` 版本一致性：exit 0。
- 四份 references 存在且非空：exit 0。
- 占位符扫描：`rg` exit 1、无匹配；`git diff --check`：exit 0。
- 新增评测文档的行尾空白与本地链接检查：exit 0；证据中的三个 SHA-256 与当前规则文件一致：exit 0。
- Skill Creator `quick_validate.py`：exit 1，仅报告不接受仓库要求的 `user-invocable` 字段；这是已知校验器兼容性诊断，不通过删除仓库必需字段规避，其余 frontmatter 已由上述仓库字段断言验证。
