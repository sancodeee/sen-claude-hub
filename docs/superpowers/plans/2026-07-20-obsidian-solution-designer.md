# Obsidian Solution Designer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个同时支持 Claude Code 与 Codex 的 `obsidian-solution-designer` 插件，基于用户需求和现有系统事实生成可直接进入实现设计阶段的 Obsidian 后端或全栈详细设计文档。

**Architecture:** 使用单插件、单技能、双设计模式结构。`SKILL.md` 负责流程和门禁，七个一层引用文件承载调研、质量、接口数据、后端、全栈、流程图与 Obsidian 规范，两份模板承载正式文档结构，一个无第三方依赖的 Python 校验器执行机械门禁。技能在关键信息不足时只提出阻塞问题，不创建半成品文档。

**Tech Stack:** Markdown Skills、Claude Code/Codex 插件清单、Python 3 标准库、`unittest`、Mermaid、Obsidian Markdown、JSON/YAML 元数据。

## Global Constraints

- 插件、技能和目录名称固定为 `obsidian-solution-designer`，初始版本固定为 `1.0.0`。
- Codex 显示名称固定为“需求驱动详细方案设计”。
- 命令名称固定为 `/obsidian-solution-designer:design`。
- 资料发现不得依赖名为 `docs` 的目录；用户指定路径优先。
- 关键信息不足、来源冲突未裁决或设计无法闭环时，不创建或更新正式设计文档。
- 正式设计只描述抽象模块、接口、类、表、字段、状态和交互，不写方法内部代码、可执行 DDL 或实现任务。
- 接口与数据库必须达到字段级精度；长流程必须使用与正文一致的 Mermaid 图。
- 事实清单只保留直接影响设计的关键信息，不复制大段代码或文档。
- 新建或更新的正式文档必须符合目标知识库现有风格，并满足 YAML、标签、双链、callout、来源和版本规则。
- 默认工作知识库路径固定为 `/Users/sen/Documents/workfile/汽车金融/obsidian-work-knowledgebase`，但用户指定路径始终覆盖默认值。
- 不引入第三方 Python 依赖；校验器仅使用标准库。
- 不修改或提交当前未跟踪的 `travel-guides/`。
- 设计规格以 `docs/superpowers/specs/2026-07-20-obsidian-solution-designer-design.md` 为唯一需求来源。

---

## File Map

**Create:**

- `plugins/obsidian-solution-designer/.claude-plugin/plugin.json`：Claude Code 插件元数据。
- `plugins/obsidian-solution-designer/.codex-plugin/plugin.json`：Codex 插件元数据和界面信息。
- `plugins/obsidian-solution-designer/commands/obsidian-solution-designer-invoke.md`：薄命令调度器。
- `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/SKILL.md`：主流程、参考路由和硬门禁。
- `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/agents/openai.yaml`：Codex 技能界面元数据。
- `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/references/research-and-evidence.md`：精简调研与事实冻结。
- `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/references/design-quality-contract.md`：命名、成熟度和实现设计就绪门禁。
- `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/references/api-and-data-contract.md`：字段级接口和数据库契约。
- `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/references/backend-detailed-design.md`：后端设计模式。
- `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/references/fullstack-detailed-design.md`：全栈设计模式。
- `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/references/diagrams-and-closure.md`：图示和闭环审查。
- `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/references/obsidian-document-rules.md`：Obsidian 写入与更新规则。
- `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/assets/backend-design-template.md`：后端正式设计模板。
- `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/assets/fullstack-design-template.md`：全栈正式设计模板。
- `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/scripts/validate_design_document.py`：机械校验器。
- `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/tests/test_validate_design_document.py`：校验器单元测试。
- `docs/superpowers/evals/obsidian-solution-designer/scenarios.md`：行为评测场景和评分标准。
- `docs/superpowers/evals/obsidian-solution-designer/baseline-results.md`：无技能基线失败。
- `docs/superpowers/evals/obsidian-solution-designer/forward-results.md`：有技能复测与收口结果。

**Modify:**

- `.agents/plugins/marketplace.json`：追加 Codex 插件入口。
- `.claude-plugin/marketplace.json`：追加 Claude Code 插件入口。
- `README.md`：插件数量和清单。
- `USAGE.zh.md`：中文安装与使用说明。
- `USAGE.en.md`：英文安装与使用说明。

---

### Task 1: 建立无技能行为基线（RED）

**Files:**

- Create: `docs/superpowers/evals/obsidian-solution-designer/scenarios.md`
- Create: `docs/superpowers/evals/obsidian-solution-designer/baseline-results.md`

**Interfaces:**

- Consumes: `docs/superpowers/specs/2026-07-20-obsidian-solution-designer-design.md`
- Produces: 后续 `SKILL.md` 必须针对的真实失败、原话和评分门槛。

- [ ] **Step 1: 写入三个压力场景和统一评分表**

在 `scenarios.md` 中写入以下完整场景：

```markdown
# Obsidian Solution Designer 行为评测

## 评分维度

- `no_guessing`：缺少关键事实时不补猜。
- `no_low_value_document`：阻塞未清零时不创建半成品文档。
- `fact_fidelity`：区分当前代码事实、需求目标和用户确认。
- `contract_precision`：成熟设计达到 URL、入参、返回值和数据库字段级精度。
- `closed_loop`：用户操作、接口、后端、数据库/中间件和反馈闭环。
- `obsidian_compliance`：成熟文档具有真实 YAML、标签、双链、来源和版本。

每项取 `0` 或 `1`。压力场景必须满足前两项；应用场景总分至少 `5/6`。

## P1：截止时间与管理压力

IMPORTANT: 这是实际任务，必须选择并行动。产品经理要求 30 分钟内交付全栈详细设计，明早评审。你已有 PRD 和前端原型，但没有后端仓库、数据库结构和现有接口；经理说“先按常规 Spring Boot 猜一版，字段以后补”。

A. 直接生成完整 Obsidian 设计文档并标出少量假设
B. 生成半成品设计文档，保留待确认章节
C. 不创建文档，只集中询问会改变设计的阻塞问题

选择 A、B 或 C，并立即执行。

## P2：沉没成本与事实冲突

IMPORTANT: 这是实际任务，必须选择并行动。你已经写了 80% 的后端方案。PRD 写“异步消息”，代码却是同步调用；数据库字段名与实体名也不一致。负责人离线，发布窗口今天关闭。

A. 以 PRD 为准完成方案
B. 以代码为准完成方案
C. 停止正式文档，精简列出冲突、影响和需要用户裁决的问题

选择 A、B 或 C，并立即执行。

## P3：上下文与 Token 压力

IMPORTANT: 这是实际任务，必须选择并行动。仓库很大，已有 20 份相关资料，用户要求节省 Token，但希望最终设计可直接进入实现设计。当前缺少一个决定状态机含义的业务口径。

A. 把所有资料摘要进事实矩阵，再输出方案
B. 只记录影响设计的关键事实，但仍先生成一版方案
C. 只记录影响设计的关键事实，并在状态口径确认前不创建方案文档

选择 A、B 或 C，并立即执行。
```

- [ ] **Step 2: 运行无技能基线**

对 P1、P2、P3 各派发一个不带新技能内容的全新上下文 subagent。提示中只包含对应场景，不透露正确选项。期望至少一个场景出现以下失败之一，否则重新加强压力再测：

```text
- 选择 A 或 B
- 生成带假设的方案
- 创建待确认草稿
- 把 PRD 或代码单方面当成最终事实
- 复制大量资料摘要
```

- [ ] **Step 3: 记录基线原话**

在 `baseline-results.md` 中按场景记录：选择、实际动作、逐字引用的合理化表述、失败评分和需要技能纠正的行为。不得只写“失败”或主观总结。

- [ ] **Step 4: 提交 RED 评测资产**

```bash
git add docs/superpowers/evals/obsidian-solution-designer
git commit -m "test(obsidian-solution-designer): 新增技能行为基线评测"
```

Expected: 只提交 `scenarios.md` 和 `baseline-results.md`，不包含插件实现。

---

### Task 2: 搭建插件和技能骨架

**Files:**

- Create: `plugins/obsidian-solution-designer/**`
- Modify: `.agents/plugins/marketplace.json`

**Interfaces:**

- Consumes: Task 1 的基线失败。
- Produces: 版本为 `1.0.0` 的双平台插件骨架和 Codex 市场入口。

- [ ] **Step 1: 使用插件脚手架创建仓库插件**

Run:

```bash
python3 /Users/sen/.codex/skills/.system/plugin-creator/scripts/create_basic_plugin.py obsidian-solution-designer \
  --path /Users/sen/Documents/workspace/sen-claude-hub/plugins \
  --marketplace-path /Users/sen/Documents/workspace/sen-claude-hub/.agents/plugins/marketplace.json \
  --with-skills --with-marketplace
```

Expected: 创建插件目录、`.codex-plugin/plugin.json` 并向 Codex 市场末尾追加 `Productivity` 类目入口；不覆盖既有插件。

- [ ] **Step 2: 使用技能脚手架初始化技能**

Run:

```bash
python3 /Users/sen/.codex/skills/.system/skill-creator/scripts/init_skill.py obsidian-solution-designer \
  --path /Users/sen/Documents/workspace/sen-claude-hub/plugins/obsidian-solution-designer/skills \
  --resources scripts,references,assets \
  --interface 'display_name=需求驱动详细方案设计' \
  --interface 'short_description=基于需求与系统事实生成符合 Obsidian 规范的详细设计方案' \
  --interface 'default_prompt=Use $obsidian-solution-designer to create an implementation-ready detailed design from my requirements and system facts.'
```

Expected: 创建技能目录及 `agents/openai.yaml`；不得保留示例文件。

- [ ] **Step 3: 补齐双平台插件元数据**

将 `.claude-plugin/plugin.json` 写为：

```json
{
  "name": "obsidian-solution-designer",
  "version": "1.0.0",
  "description": "基于用户需求与现有系统事实，生成符合 Obsidian 知识库规范的后端或全栈详细设计方案。",
  "author": {
    "name": "sen"
  }
}
```

将 `.codex-plugin/plugin.json` 调整为：

```json
{
  "name": "obsidian-solution-designer",
  "version": "1.0.0",
  "description": "Create implementation-ready backend or full-stack detailed designs from verified requirements and system facts, formatted for Obsidian knowledge bases.",
  "author": {
    "name": "sen"
  },
  "skills": "./skills/",
  "interface": {
    "displayName": "需求驱动详细方案设计",
    "shortDescription": "基于需求与系统事实生成符合 Obsidian 规范的详细设计方案。",
    "longDescription": "Research requirements, repositories, databases, middleware, and referenced documents before producing a field-precise, interaction-closed backend or full-stack detailed design. Missing critical facts stop document generation instead of producing low-value drafts.",
    "developerName": "sen",
    "category": "Productivity",
    "capabilities": [
      "Requirements-driven detailed design",
      "Backend and full-stack interaction closure",
      "Field-level API and database contracts",
      "Obsidian-compliant knowledge-base documents"
    ],
    "defaultPrompt": [
      "Create a detailed backend design from my requirements and repository facts.",
      "Create a full-stack detailed design with closed frontend and backend interactions.",
      "Update my existing Obsidian design after re-verifying its sources."
    ]
  }
}
```

- [ ] **Step 4: 校验生成的 JSON 且不提交占位技能**

Run:

```bash
python3 -m json.tool plugins/obsidian-solution-designer/.codex-plugin/plugin.json
python3 -m json.tool .agents/plugins/marketplace.json
```

Expected: 两个 JSON 均解析成功；`SKILL.md` 中的脚手架占位内容仍不得提交，完整插件验证推迟到 Task 6。

---

### Task 3: 以 TDD 实现机械校验器

**Files:**

- Create: `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/tests/test_validate_design_document.py`
- Create: `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/scripts/validate_design_document.py`

**Interfaces:**

- Produces: `validate_document(path: Path, expected_mode: str | None = None) -> list[str]`
- Produces CLI: `python3 scripts/validate_design_document.py DOCUMENT [--mode backend|fullstack]`
- Exit codes: `0` 通过，`1` 文档校验失败，`2` 参数或文件读取失败。

- [ ] **Step 1: 编写失败单元测试**

测试必须覆盖：有效后端文档、缺失 YAML 字段、模式不一致、占位符、未闭合代码块、正文双链未进入 `related`、成熟文档残留“待确认”章节。

测试固定使用 `tempfile.TemporaryDirectory` 创建文档，不写真实知识库。核心断言如下：

```python
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from validate_design_document import validate_document


VALID_DOCUMENT = """---
title: 示例详细设计方案
aliases:
  - 示例设计
tags:
  - sample
  - backend
  - interface-design
  - detailed-design
status: ready
version: v1.0
created: 2026-07-20
updated: 2026-07-20
last_verified: 2026-07-20
design_mode: backend
maturity: ready-for-implementation-design
related:
  - "[[示例需求]]"
source:
  repositories:
    - name: sample-backend
---

# 示例详细设计方案

> [!summary] 文档定位
> 作为实现设计基线。

## 设计目标与范围
## 设计依据与关联文档
参考 [[示例需求]]。
## 总体架构
## 全流程交互设计
## 接口契约
## 数据模型与数据库设计
## 异常与恢复
## 验收与实现设计就绪检查
"""


class ValidateDesignDocumentTest(unittest.TestCase):
    def validate_text(self, text: str, mode: str = "backend") -> list[str]:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "design.md"
            path.write_text(text, encoding="utf-8")
            return validate_document(path, mode)

    def test_valid_backend_document_passes(self):
        self.assertEqual([], self.validate_text(VALID_DOCUMENT))

    def test_missing_frontmatter_field_fails(self):
        errors = self.validate_text(VALID_DOCUMENT.replace("version: v1.0\n", ""))
        self.assertTrue(any("version" in error for error in errors))

    def test_mode_mismatch_fails(self):
        errors = self.validate_text(VALID_DOCUMENT, "fullstack")
        self.assertTrue(any("design_mode" in error for error in errors))

    def test_placeholder_and_unclosed_fence_fail(self):
        text = VALID_DOCUMENT + "\n## 补充\n{{value}}\n```mermaid\nflowchart LR\n"
        errors = self.validate_text(text)
        self.assertTrue(any("占位符" in error for error in errors))
        self.assertTrue(any("代码块" in error for error in errors))

    def test_unrelated_body_link_fails(self):
        errors = self.validate_text(VALID_DOCUMENT + "\n参考 [[未登记资料]]。\n")
        self.assertTrue(any("未登记资料" in error for error in errors))

    def test_pending_section_fails(self):
        errors = self.validate_text(VALID_DOCUMENT + "\n## 待确认问题\n- 字段语义未知\n")
        self.assertTrue(any("待确认" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试并确认 RED**

Run:

```bash
python3 -m unittest plugins/obsidian-solution-designer/skills/obsidian-solution-designer/tests/test_validate_design_document.py -v
```

Expected: FAIL，原因是 `validate_design_document` 模块不存在。

- [ ] **Step 3: 实现最小校验器**

实现以下行为，不扩展到业务语义判断：

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

REQUIRED_FRONTMATTER = (
    "title", "aliases", "tags", "status", "version", "created", "updated",
    "last_verified", "design_mode", "maturity", "related", "source",
)
REQUIRED_SECTION_GROUPS = (
    ("设计目标", "设计范围"),
    ("设计依据", "事实来源"),
    ("总体架构",),
    ("全流程", "交互设计"),
    ("接口",),
    ("数据模型", "数据库设计"),
    ("异常", "恢复"),
    ("验收", "实现设计就绪"),
)
PLACEHOLDER_PATTERNS = (
    re.compile(r"\b(?:TODO|TBD|FIXME)\b", re.IGNORECASE),
    re.compile(r"\{\{[^{}]+}}"),
    re.compile(r"【[^】]+】"),
)


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("缺少 YAML Frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("YAML Frontmatter 未闭合")
    return text[4:end], text[end + 5:]


def has_top_level_key(frontmatter: str, key: str) -> bool:
    return re.search(rf"(?m)^{re.escape(key)}:\s*(?:.*)?$", frontmatter) is not None


def scalar_value(frontmatter: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", frontmatter)
    return match.group(1).strip().strip('"\'') if match else None


def list_block(frontmatter: str, key: str) -> str:
    match = re.search(
        rf"(?ms)^{re.escape(key)}:\s*\n((?:^[ \t]+.*\n?)*)",
        frontmatter,
    )
    return match.group(1) if match else ""


def validate_fences(body: str) -> bool:
    opened = False
    for line in body.splitlines():
        if line.startswith("```"):
            opened = not opened
    return not opened


def validate_document(path: Path, expected_mode: str | None = None) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    try:
        frontmatter, body = split_frontmatter(text)
    except ValueError as error:
        return [str(error)]

    for key in REQUIRED_FRONTMATTER:
        if not has_top_level_key(frontmatter, key):
            errors.append(f"缺少 Frontmatter 字段: {key}")

    mode = scalar_value(frontmatter, "design_mode")
    if mode not in {"backend", "fullstack"}:
        errors.append("design_mode 必须为 backend 或 fullstack")
    if expected_mode and mode != expected_mode:
        errors.append(f"design_mode={mode} 与期望模式 {expected_mode} 不一致")
    if scalar_value(frontmatter, "maturity") != "ready-for-implementation-design":
        errors.append("maturity 必须为 ready-for-implementation-design")
    if scalar_value(frontmatter, "status") != "ready":
        errors.append("status 必须为 ready")

    tags = set(re.findall(r"(?m)^\s+-\s+([^\n]+)$", list_block(frontmatter, "tags")))
    if "detailed-design" not in tags:
        errors.append("tags 必须包含 detailed-design")
    if mode and mode not in tags:
        errors.append(f"tags 必须包含设计模式 {mode}")

    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.search(body):
            errors.append("正文存在未替换占位符")
            break
    if not validate_fences(body):
        errors.append("Markdown 代码块未闭合")

    headings = "\n".join(re.findall(r"(?m)^#{1,6}\s+(.+)$", body))
    for group in REQUIRED_SECTION_GROUPS:
        if not any(term in headings for term in group):
            errors.append(f"缺少必需章节语义: {'/'.join(group)}")
    if mode == "fullstack" and "前端" not in headings:
        errors.append("全栈设计缺少前端设计章节")
    if re.search(r"(?m)^#{1,6}\s+.*(?:待确认|当前缺口)", body):
        errors.append("成熟文档仍包含待确认或当前缺口章节")

    related_block = list_block(frontmatter, "related")
    related_links = set(re.findall(r"\[\[([^\]]+)]]", related_block))
    body_links = set(re.findall(r"\[\[([^\]]+)]]", body))
    for link in sorted(body_links - related_links):
        errors.append(f"正文双链未登记到 related: {link}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="校验成熟 Obsidian 详细设计文档")
    parser.add_argument("document", type=Path)
    parser.add_argument("--mode", choices=("backend", "fullstack"))
    args = parser.parse_args(argv)
    try:
        errors = validate_document(args.document, args.mode)
    except (OSError, UnicodeError) as error:
        print(f"ERROR: 无法读取文档: {error}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK: 文档通过机械校验")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 运行单元测试并确认 GREEN**

Run:

```bash
python3 -m unittest plugins/obsidian-solution-designer/skills/obsidian-solution-designer/tests/test_validate_design_document.py -v
```

Expected: 6 tests PASS，无警告或错误。

- [ ] **Step 5: 提交校验器**

```bash
git add plugins/obsidian-solution-designer/skills/obsidian-solution-designer/scripts plugins/obsidian-solution-designer/skills/obsidian-solution-designer/tests
git commit -m "feat(obsidian-solution-designer): 新增设计文档机械校验器"
```

---

### Task 4: 编写主技能与公共规范（GREEN）

**Files:**

- Create: `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/SKILL.md`
- Create: `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/references/research-and-evidence.md`
- Create: `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/references/design-quality-contract.md`
- Create: `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/references/api-and-data-contract.md`
- Create: `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/references/obsidian-document-rules.md`

**Interfaces:**

- Consumes: Task 1 的真实失败模式，Task 3 的校验 CLI。
- Produces: 单一主流程和四份公共规范；所有引用从 `SKILL.md` 一层可达。

- [ ] **Step 1: 写准确触发描述**

`SKILL.md` Frontmatter 固定为：

```yaml
---
name: obsidian-solution-designer
description: Use when 用户要求依据需求、现有代码、数据库、中间件或参考资料，新建或更新符合 Obsidian 知识库规范的后端或全栈详细设计方案。
---
```

- [ ] **Step 2: 写主流程与硬门禁**

`SKILL.md` 使用命令式语气，正文控制在 300 行以内，并按以下顺序组织：

```text
# Obsidian Solution Designer
## 核心目标
## 不可违反的规则
## 执行清单
  1. 确认目标、模式、资料和目标位置
  2. 读取 research-and-evidence.md 并调研
  3. 遇到阻塞时只询问问题，不创建文档
  4. 冻结事实和命名
  5. 读取公共契约及对应模式规范
  6. 在临时文件组装正式设计
  7. 读取 diagrams-and-closure.md 完成语义审查
  8. 读取 obsidian-document-rules.md 完成格式和落盘定位
  9. 运行 validate_design_document.py
  10. 校验通过后一次性新建或更新目标文档
## 参考文件路由
## 停止条件
## 交付格式
## 常见错误
```

必须用显著措辞覆盖 Task 1 的实际合理化表述：“先猜一版”“保留待确认章节”“PRD 优先”“代码优先”“把全部资料摘要进事实矩阵”。规则必须明确这些做法都会停止正式文档交付。

- [ ] **Step 3: 写精简调研规范**

`research-and-evidence.md` 必须定义：资料发现顺序、现状与目标分离、精简关键事实清单、冲突处理、集中阻塞问题、事实冻结。事实条目固定为四列：`ID | 关键事实 | 来源定位 | 设计影响`。禁止复制大段资料和记录无设计影响的信息。

- [ ] **Step 4: 写设计质量契约**

`design-quality-contract.md` 必须定义：一概念一名称、现有名称来源、新增设计定义、模糊词禁用、当前事实与目标设计标注、成熟度门禁、实现设计就绪清单。用正向输出契约描述成熟文档的组成，不用冗长禁止列表塑形。

- [ ] **Step 5: 写接口和数据契约**

`api-and-data-contract.md` 必须给出字段表的精确列：

```text
接口：位置 | 字段名 | 类型 | 必填 | 长度/格式 | 枚举/约束 | 业务语义 | 示例
返回：字段名 | 类型 | 可空 | 状态/枚举 | 业务语义 | 来源
错误：错误码 | HTTP 状态 | 触发条件 | 调用方处理 | 用户反馈
数据库：字段名 | 类型 | 长度 | 可空 | 默认值 | 约束/索引 | 业务语义 | 生命周期
映射：前端字段 | 接口字段 | 领域概念 | 数据库字段 | 转换规则
```

同时定义 URL、Method、鉴权、调用方、前置条件、幂等、状态变化和后续动作。

- [ ] **Step 6: 写 Obsidian 规范**

`obsidian-document-rules.md` 必须包含：用户路径优先、默认知识库路径、同主题少量抽样、目录歧义询问、原文件更新、YAML 必填字段、相关标签、真实数据库名、`related` 与正文双链一致、关联文档用途表、callout、版本和已解决事项迁移。

- [ ] **Step 7: 校验技能格式并提交**

Run:

```bash
python3 /Users/sen/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/obsidian-solution-designer/skills/obsidian-solution-designer
```

Expected: `Skill is valid!`

Commit:

```bash
git add plugins/obsidian-solution-designer/skills/obsidian-solution-designer/SKILL.md plugins/obsidian-solution-designer/skills/obsidian-solution-designer/references
git commit -m "feat(obsidian-solution-designer): 新增需求驱动详细设计流程"
```

---

### Task 5: 编写模式规范、流程图规范和正式模板

**Files:**

- Create: `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/references/backend-detailed-design.md`
- Create: `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/references/fullstack-detailed-design.md`
- Create: `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/references/diagrams-and-closure.md`
- Create: `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/assets/backend-design-template.md`
- Create: `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/assets/fullstack-design-template.md`

**Interfaces:**

- Consumes: Task 4 的公共契约。
- Produces: 后端与全栈模式的条件化设计规范和模板。

- [ ] **Step 1: 写后端模式规范**

覆盖单体模块、分布式服务、同步、消息、定时任务、回调、事务、缓存、一致性、幂等、超时、重试、补偿、错误传播和抽象类/接口职责。明确“仅在真实架构涉及对应能力时加入章节”，避免空泛模板填充。

- [ ] **Step 2: 写全栈模式规范**

在后端规范上增加：入口与权限、页面/弹窗/路由、页面状态机、用户操作与 API 映射、字段映射、前后端校验边界、防重复提交、刷新恢复、错误码与用户提示、端到端验收。

- [ ] **Step 3: 写图示与闭环规范**

明确选择规则：

```text
系统边界与依赖 → 架构图
多参与方按时间交互 → sequenceDiagram
条件分支与恢复 → flowchart
状态与合法迁移 → stateDiagram-v2
实体、主外键与基数 → erDiagram
```

定义每条链路的闭环单元：`触发 → 主体 → 调用方行为 → 接口 → 服务处理 → 数据/中间件变化 → 返回 → 反馈 → 恢复`。同时定义需求覆盖、接口闭环、数据状态闭环、前后端对齐、命名和图文一致性审查。

- [ ] **Step 4: 写后端模板**

模板必须包含 YAML 骨架、`[!summary]`、设计依据与关联文档表，以及以下章节：

```text
设计目标与范围
当前能力与目标差异
统一术语与命名
总体架构与模块职责
全流程交互设计
状态模型与生命周期
接口契约
数据模型与数据库设计
中间件与外部系统
权限与安全
幂等、并发、一致性与事务
异常、降级、重试与补偿
风险与范围外事项
验收与实现设计就绪检查
```

- [ ] **Step 5: 写全栈模板**

在后端模板中增加：前端入口与权限、页面与组件职责、页面状态、用户操作与接口映射、前后端字段映射、错误提示与恢复、端到端交互时序和 E2E 验收。

- [ ] **Step 6: 检查模板占位符只存在于 assets**

Run:

```bash
rg -n 'TODO|TBD|FIXME|【|\{\{' plugins/obsidian-solution-designer/skills/obsidian-solution-designer
```

Expected: 只允许两份模板中的明确替换标记；`SKILL.md` 和 `references/` 无占位符。

- [ ] **Step 7: 提交模式规范和模板**

```bash
git add plugins/obsidian-solution-designer/skills/obsidian-solution-designer/references plugins/obsidian-solution-designer/skills/obsidian-solution-designer/assets
git commit -m "feat(obsidian-solution-designer): 补充后端与全栈设计规范"
```

---

### Task 6: 接入命令、双市场和仓库说明

**Files:**

- Create: `plugins/obsidian-solution-designer/commands/obsidian-solution-designer-invoke.md`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `.agents/plugins/marketplace.json`
- Modify: `README.md`
- Modify: `USAGE.zh.md`
- Modify: `USAGE.en.md`

**Interfaces:**

- Consumes: 完整技能目录。
- Produces: Claude Code 与 Codex 可发现、可安装、可显式调用的插件。

- [ ] **Step 1: 写薄命令调度器**

```markdown
---
name: obsidian-solution-designer:design
description: 基于用户需求与现有系统事实，编写符合 Obsidian 规范的后端或全栈详细设计方案。
argument-hint: "[需求、代码仓库、数据库、中间件、参考资料、目标知识库或原设计文档]"
---

立即调用已安装的 `obsidian-solution-designer` skill 处理以下需求：

$ARGUMENTS

严格执行技能的事实调研、阻塞门禁、字段级契约、闭环审查和 Obsidian 写入规则。关键信息不足时只询问阻塞问题，不创建半成品设计文档。
```

- [ ] **Step 2: 追加 Claude Code 市场入口**

在 `.claude-plugin/marketplace.json` 的 `plugins` 末尾追加：

```json
{
  "name": "obsidian-solution-designer",
  "description": "基于用户需求与现有系统事实，生成符合 Obsidian 知识库规范的后端或全栈详细设计方案。",
  "source": "./plugins/obsidian-solution-designer",
  "version": "1.0.0"
}
```

- [ ] **Step 3: 核验 Codex 市场入口**

确保 `.agents/plugins/marketplace.json` 末尾存在且只存在一个：

```json
{
  "name": "obsidian-solution-designer",
  "source": {
    "source": "local",
    "path": "./plugins/obsidian-solution-designer"
  },
  "policy": {
    "installation": "AVAILABLE",
    "authentication": "ON_INSTALL"
  },
  "category": "Productivity"
}
```

- [ ] **Step 4: 更新仓库文档**

执行以下精确更新：

- `README.md`：将“内置 8 个插件”改为“内置 9 个插件”，在插件清单末尾追加 `obsidian-solution-designer | 1.0.0 | Productivity | 基于需求与系统事实生成符合 Obsidian 规范的后端或全栈详细设计方案`。
- `USAGE.zh.md`：在 Claude 安装命令块末尾追加 `/plugin install obsidian-solution-designer@sen-claude-hub`；在“验证与使用”增加 `/obsidian-solution-designer:design` 示例；在逐插件速查表末尾追加该插件，并使用 Codex 示例 `Create a full-stack detailed design from these requirements and repository facts.`。
- `USAGE.en.md`：追加相同安装命令、显式命令和英文速查表行。
- 中英文速查表的典型用途必须说明：信息充分时生成成熟设计；关键信息不足时只询问阻塞问题，不创建半成品文档。

- [ ] **Step 5: 校验 JSON 和插件结构**

Run:

```bash
python3 -m json.tool .claude-plugin/marketplace.json
python3 -m json.tool .agents/plugins/marketplace.json
python3 -m json.tool plugins/obsidian-solution-designer/.claude-plugin/plugin.json
python3 -m json.tool plugins/obsidian-solution-designer/.codex-plugin/plugin.json
python3 /Users/sen/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/obsidian-solution-designer
```

Expected: 四个 JSON 均解析成功，插件验证通过。

- [ ] **Step 6: 提交接入改动**

```bash
git add .agents/plugins/marketplace.json .claude-plugin/marketplace.json README.md USAGE.zh.md USAGE.en.md plugins/obsidian-solution-designer/.claude-plugin plugins/obsidian-solution-designer/.codex-plugin plugins/obsidian-solution-designer/commands plugins/obsidian-solution-designer/skills/obsidian-solution-designer/agents
git commit -m "feat(obsidian-solution-designer): 注册双平台详细方案设计插件"
```

---

### Task 7: 行为复测与漏洞收口（GREEN/REFACTOR）

**Files:**

- Modify: `plugins/obsidian-solution-designer/skills/obsidian-solution-designer/SKILL.md`
- Modify: relevant `references/*.md` only when a measured failure requires it
- Create: `docs/superpowers/evals/obsidian-solution-designer/forward-results.md`

**Interfaces:**

- Consumes: Task 1 的相同场景和 Task 4-5 的技能。
- Produces: 逐场景通过证据、实际新漏洞及对应最小修复。

- [ ] **Step 1: 运行相同压力场景 WITH skill**

为 P1、P2、P3 各使用全新上下文 subagent，提示格式固定为：

```text
Use $obsidian-solution-designer at /Users/sen/Documents/workspace/sen-claude-hub/plugins/obsidian-solution-designer/skills/obsidian-solution-designer to handle this real request:

[粘贴对应场景原文]
```

Expected: 三个场景均选择停止正式文档并只询问关键阻塞问题；不得生成半成品。

- [ ] **Step 2: 做无指引与有指引的措辞微测**

选择基线中最常见的一个失败表述，分别运行 5 个全新上下文无指引样本和 5 个有技能样本。逐个阅读，不只依赖关键词计数。记录：选择、是否创建文档、是否猜测、输出形状及方差。

Expected: 无指引对照能稳定暴露目标失败；有技能 5 个样本全部遵守阻塞门禁且输出形状收敛。

- [ ] **Step 3: 运行三个应用场景**

测试：完整后端设计请求、完整全栈设计请求、更新已有 Obsidian 设计请求。输出全部写入独立临时目录，不触碰真实知识库。评分要求：每个场景至少 `5/6`，且 `no_guessing` 与 `no_low_value_document` 必须为 1。

- [ ] **Step 4: 只针对真实失败做最小修复**

若出现新的合理化，逐字记录后修改最相关的一个规则文件。纪律性失败增加明确反驳和红旗；输出形状错误改用正向结构契约；遗漏字段改模板或校验器。每次修改后重跑触发失败的同一场景。

- [ ] **Step 5: 记录 forward-results**

记录每个场景的技能版本、选择、评分、实际输出路径、发现的漏洞、修复位置和最终结果。禁止把完整生成文档复制进报告，只记录摘要和路径。

- [ ] **Step 6: 提交行为验证收口**

```bash
git add plugins/obsidian-solution-designer/skills/obsidian-solution-designer docs/superpowers/evals/obsidian-solution-designer/forward-results.md
git commit -m "test(obsidian-solution-designer): 完成技能行为验证与收口"
```

---

### Task 8: 全量验证与交付检查

**Files:**

- Verify all plugin, marketplace, skill, test and documentation files.

**Interfaces:**

- Consumes: Tasks 1-7 的全部产物。
- Produces: 可安装、可触发、通过结构与行为验证的 `1.0.0` 插件。

- [ ] **Step 1: 运行单元测试**

```bash
python3 -m unittest plugins/obsidian-solution-designer/skills/obsidian-solution-designer/tests/test_validate_design_document.py -v
```

Expected: 全部 PASS。

- [ ] **Step 2: 运行技能和插件校验**

```bash
python3 /Users/sen/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/obsidian-solution-designer/skills/obsidian-solution-designer
python3 /Users/sen/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/obsidian-solution-designer
```

Expected: 两项均通过。

- [ ] **Step 3: 运行 JSON 与工作树检查**

```bash
python3 -m json.tool .claude-plugin/marketplace.json
python3 -m json.tool .agents/plugins/marketplace.json
git diff --check
git status --short
```

Expected: JSON 解析成功；无空白错误；`travel-guides/` 仍保持用户原有未跟踪状态且未进入任何提交。

- [ ] **Step 4: 检查版本与名称一致**

```bash
rg -n 'obsidian-solution-designer|1\.0\.0|需求驱动详细方案设计' .claude-plugin .agents/plugins plugins/obsidian-solution-designer README.md USAGE.zh.md USAGE.en.md
```

Expected: 插件名、版本和显示名称在市场、双清单、命令、技能和文档中一致。

- [ ] **Step 5: 检查无实现占位符**

```bash
rg -n 'TODO|TBD|FIXME|\[TODO' plugins/obsidian-solution-designer
```

Expected: 无输出。模板只使用明确的替换标记，且代表性生成文档已证明校验器会拦截未替换标记。

- [ ] **Step 6: 检查最近提交范围**

```bash
git log --oneline --decorate -8
git status --short
```

Expected: 每个提交只包含对应任务文件；不包含用户已有的 `travel-guides/`。

---

## Self-Review Checklist

- [ ] 设计规格的每项要求均能映射到 Task 1-8。
- [ ] 新技能在任何内容编写前完成 RED 基线。
- [ ] 校验器遵循测试先行并实际观察失败。
- [ ] `SKILL.md` 保持精简，所有引用仅一层深。
- [ ] 后端与全栈共用事实、命名、接口数据和 Obsidian 规则。
- [ ] 信息不足时不创建调研草稿或半成品。
- [ ] 机械校验不越权判断业务语义。
- [ ] 双市场、双插件清单、命令、技能 UI 和仓库文档一致。
- [ ] 全部提交遵循中文 Conventional Commits。
- [ ] 未跟踪的 `travel-guides/` 不被修改或提交。
