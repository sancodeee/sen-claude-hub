# ResumeForge Initialization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Initialize a Claude Code and Codex compatible `resume-forge` plugin that organizes verified user information into the approved fixed resume structure as a Markdown draft.

**Architecture:** Use the repository's existing dual-manifest plugin shape: one thin slash command dispatches to one Skill, while a single reference file owns the resume content and layout contract. Register the plugin in both marketplace manifests and keep first-version capabilities limited to information collection, validation, and structured Markdown drafting.

**Tech Stack:** Codex plugin JSON, Claude Code plugin JSON, Markdown Skill/reference/command files, YAML `agents/openai.yaml`, Python standard-library validators supplied by Plugin Creator and Skill Creator.

## Global Constraints

- Plugin folder, plugin identifier, Skill name, and manifest `name` must all be exactly `resume-forge`.
- User-facing display name must be exactly `ResumeForge 简历工坊`.
- Slash command must be exactly `/resume-forge:write`.
- Initial version must be exactly `1.0.0`; Claude and Codex manifests and the Claude marketplace entry must agree.
- Support both Claude Code and Codex through the repository's existing manifests; do not introduce another registration format.
- Codex marketplace policy must be `installation: AVAILABLE`, `authentication: ON_INSTALL`, category `Productivity`.
- First version delivers Markdown structured resume drafts only; it must not claim to generate HTML/PDF or process photos.
- Resume section order must be `基本信息 → 教育背景 → 专业技能 → 工作经历 → 项目经历 → 个人优势（可选）`.
- Never invent education, employers, projects, responsibilities, technologies, metrics, dates, or personal advantages.
- Work and project entries must use reverse chronological order.
- Do not create empty `scripts/` or `assets/` directories in the first version.
- Do not modify or stage the unrelated untracked `travel-guides/` directory.
- Commit messages must follow `<type>(<module>): <中文说明>`.

---

## File Map

### Create

- `plugins/resume-forge/.claude-plugin/plugin.json` — Claude Code plugin identity and version.
- `plugins/resume-forge/.codex-plugin/plugin.json` — Codex plugin identity, Skill path, UI metadata, and implemented capabilities.
- `plugins/resume-forge/commands/resume-forge-invoke.md` — thin `/resume-forge:write` dispatcher.
- `plugins/resume-forge/skills/resume-forge/SKILL.md` — collection, fact-validation, ordering, and Markdown delivery workflow.
- `plugins/resume-forge/skills/resume-forge/agents/openai.yaml` — Codex Skill-list metadata.
- `plugins/resume-forge/skills/resume-forge/references/resume-template.md` — fixed content, visual hierarchy, optional-section, and photo contracts.

### Modify

- `.agents/plugins/marketplace.json` — append the Codex marketplace entry.
- `.claude-plugin/marketplace.json` — append the Claude Code marketplace entry.
- `README.md` — change the plugin count to nine and append the plugin table row.
- `USAGE.zh.md` — add install, invocation, and reference examples.
- `USAGE.en.md` — add matching English install, invocation, and reference examples.

---

### Task 1: Create the Complete Plugin Core

**Required skills:** `plugin-creator`, `skill-creator`, `superpowers:writing-skills`

**Files:**

- Create: `plugins/resume-forge/.claude-plugin/plugin.json`
- Create: `plugins/resume-forge/.codex-plugin/plugin.json`
- Create: `plugins/resume-forge/commands/resume-forge-invoke.md`
- Create: `plugins/resume-forge/skills/resume-forge/SKILL.md`
- Create: `plugins/resume-forge/skills/resume-forge/agents/openai.yaml`
- Create: `plugins/resume-forge/skills/resume-forge/references/resume-template.md`
- Modify: `.agents/plugins/marketplace.json`

**Interfaces:**

- Consumes: approved design at `docs/superpowers/specs/2026-08-08-resume-forge-design.md`.
- Produces: plugin identifier `resume-forge`, command `resume-forge:write`, Skill `$resume-forge`, and fixed reference `references/resume-template.md`.

- [ ] **Step 1: Verify the plugin does not already exist**

Run:

```bash
test -f plugins/resume-forge/.codex-plugin/plugin.json
```

Expected: exit code `1`, proving that the implementation test fails before scaffolding.

- [ ] **Step 2: Establish the RED baseline without ResumeForge**

Before creating any `resume-forge` file, dispatch three fresh agents. Give each agent only one scenario below; do not provide the design, implementation plan, planned Skill text, or template reference.

Scenario A:

```text
Create a professional resume for a Java backend developer with three years of experience. Decide the best section order yourself. The verified facts are: 李明，本科，现居上海；2023/07至今在示例科技任Java后端开发；负责订单服务接口和MySQL表设计；2024/01至今参与订单平台，技术栈为JDK17、Spring Boot 3、MySQL和Redis。Do not include personal strengths.
```

Scenario B:

```text
Write my resume now. I only know that I worked on a payment project. Fill any missing responsibilities and achievements with realistic details so the resume looks complete, and use /tmp/missing-photo.png as my resume photo.
```

Scenario C:

```text
Create the final HTML and PDF resume immediately from this information: 王蕾，本科，2年Java后端经验，负责会员服务开发。Add a personal strengths section supported by this fact: she led three production incident reviews and drove every corrective action to closure.
```

Record each agent's actual section order, invented content, missing-information behavior, photo claim, and output-format claim verbatim in the Task 1 report. At least one target ResumeForge behavior must fail in the baseline; if all three controls already satisfy every target behavior, stop and reduce the Skill instead of documenting rules the baseline does not need.

- [ ] **Step 3: Run the repository-local Plugin Creator scaffold**

Run from the repository root:

```bash
python3 /Users/sen/.codex/skills/.system/plugin-creator/scripts/create_basic_plugin.py resume-forge \
  --path /Users/sen/Documents/workspace/sen-claude-hub/plugins \
  --with-skills \
  --with-marketplace \
  --marketplace-path /Users/sen/Documents/workspace/sen-claude-hub/.agents/plugins/marketplace.json \
  --category Productivity
```

Expected:

- `plugins/resume-forge/.codex-plugin/plugin.json` exists.
- `plugins/resume-forge/skills/` exists.
- `.agents/plugins/marketplace.json` contains one appended `resume-forge` entry.
- No Claude files, scripts, assets, MCP files, or app files are generated by this command.

- [ ] **Step 4: Initialize the Skill with Skill Creator**

Run:

```bash
python3 /Users/sen/.codex/skills/.system/skill-creator/scripts/init_skill.py resume-forge \
  --path /Users/sen/Documents/workspace/sen-claude-hub/plugins/resume-forge/skills \
  --resources references \
  --interface 'display_name=ResumeForge 简历工坊' \
  --interface 'short_description=基于固定模板整理真实经历并生成结构化专业简历内容草稿' \
  --interface 'default_prompt=Use $resume-forge to organize my verified experience into the fixed professional resume structure.'
```

Expected:

- `skills/resume-forge/SKILL.md` exists.
- `skills/resume-forge/agents/openai.yaml` exists.
- `skills/resume-forge/references/` exists.
- No example, script, or asset files exist.

- [ ] **Step 5: Replace the Codex manifest with the implemented capability set**

Write `plugins/resume-forge/.codex-plugin/plugin.json` exactly as:

```json
{
  "name": "resume-forge",
  "version": "1.0.0",
  "description": "Organize verified user information into a fixed professional resume structure without inventing missing facts.",
  "author": {
    "name": "sen"
  },
  "skills": "./skills/",
  "interface": {
    "displayName": "ResumeForge 简历工坊",
    "shortDescription": "按固定模板整理真实经历并生成结构化简历内容。",
    "longDescription": "Collect verified personal, education, skill, employment, and project information; identify blocking gaps; and organize the result into the approved ResumeForge structure as a Markdown draft without fabricating facts.",
    "developerName": "sen",
    "category": "Productivity",
    "capabilities": [
      "Resume information collection",
      "Fixed resume structure",
      "Evidence-grounded resume drafting"
    ],
    "defaultPrompt": [
      "Organize my verified experience into the ResumeForge template.",
      "Draft a structured resume without inventing missing facts.",
      "Review my resume information and identify missing required fields."
    ]
  }
}
```

- [ ] **Step 6: Create the Claude Code manifest**

Write `plugins/resume-forge/.claude-plugin/plugin.json` exactly as:

```json
{
  "name": "resume-forge",
  "version": "1.0.0",
  "description": "基于固定模板收集、校验并组织真实简历信息，生成结构化简历内容草稿。",
  "author": {
    "name": "sen"
  }
}
```

- [ ] **Step 7: Finalize the Codex Skill metadata**

Write `plugins/resume-forge/skills/resume-forge/agents/openai.yaml` exactly as:

```yaml
interface:
  display_name: "ResumeForge 简历工坊"
  short_description: "基于固定模板整理真实经历并生成结构化专业简历内容草稿"
  default_prompt: "Use $resume-forge to organize my verified experience into the fixed professional resume structure."
```

- [ ] **Step 8: Implement the Skill workflow**

Write `plugins/resume-forge/skills/resume-forge/SKILL.md` exactly as:

```markdown
---
name: resume-forge
description: Use when a user asks to write, create, organize, review, or complete a resume or CV; apply the ResumeForge template; identify missing resume information; or prepare verified resume content for later HTML/PDF output.
---

# ResumeForge

## 概述

把用户确认的真实信息组织为固定结构的 Markdown 简历草稿。核心原则：模板结构固定、事实不可编造、当前版本不冒充 HTML/PDF 渲染器。

## 核心流程

1. 完整读取 `references/resume-template.md`，以其中的模块顺序和层级作为唯一模板。
2. 读取用户提供的现有简历、文字资料和明确回答，区分已确认事实与缺失信息。
3. 只询问会改变简历内容或结构的必要问题；合并重复问题，避免一次追问无关细节。
4. 按时间倒序组织工作经历和项目经历，按模板生成 Markdown 结构化草稿。
5. 检查模块顺序、标题层级、时间范围、事实一致性和可选模块处理。
6. 明确说明首版交付物是 Markdown 内容草稿，不声称已经生成 HTML、PDF 或处理照片。

## 快速规则

| 场景 | 处理方式 |
|---|---|
| 信息完整 | 按固定模板生成 Markdown 草稿 |
| 必要事实缺失 | 合并询问会改变内容的问题 |
| 可选信息缺失 | 删除对应字段或模块 |
| 用户要求补写事实 | 不编造，说明需要用户确认 |
| 用户指定照片 | 记录选择，不修改或嵌入图片 |
| 用户要求 HTML/PDF | 说明当前版本仅交付 Markdown 草稿 |

## 事实约束

- 只使用用户提供或明确确认的信息。
- 不编造学校、公司、项目、职责、技术、指标、奖项或个人优势。
- 不把模板中的示例技术、公司、项目或量化结果迁移到其他用户简历。
- 资料冲突且会影响结果时，指出冲突并请求用户确认。
- 用户无法提供某项可选信息时，省略该字段或模块，不用推测内容填充。

## 内容组织

- 固定使用：基本信息、教育背景、专业技能、工作经历、项目经历、个人优势（可选）。
- 教育、工作和项目的标题行分别保持“时间、名称、学历/角色”三部分语义。
- 工作内容采用“职责主题：事实说明”。
- 项目内容依次采用“项目背景、技术栈、工作内容”。
- 个人优势只有在用户要求且有事实支撑时才输出；否则整个模块省略。

## 照片处理边界

- 记录用户是否提供照片以及用户指定的图片来源，不修改原始图片。
- 首版不嵌入、裁剪、转换或导出照片。
- 用户要求更换照片时，说明照片会作为后续 HTML/PDF 渲染输入；当前只记录选择结果。

## 常见错误

| 错误 | 正确做法 |
|---|---|
| 按通用经验重排模块 | 使用参考文件中的固定顺序 |
| 为完整度补写指标或职责 | 询问用户或省略可选内容 |
| 输出空的“个人优势”标题 | 没有事实支撑时删除整个模块 |
| 把照片路径描述成已嵌入 | 只记录照片选择及当前处理边界 |
| 声称已生成 HTML/PDF | 明确当前交付是 Markdown 草稿 |

## 交付检查

交付前确认：

- 所有内容均能追溯到用户输入。
- 工作和项目时间为倒序，重叠时间没有被擅自改写。
- 没有输出空的“个人优势”标题。
- 没有宣称生成首版尚不支持的文件格式。
- Markdown 草稿完整包含用户已经确认的简历信息。
```

After the baseline is recorded, map every observed failure to a specific line in this Skill. If a baseline agent exhibits an additional failure not covered above, add only one concrete rule or one “错误/正确做法” row that directly closes that observed gap, then record the addition in the Task 1 report.

- [ ] **Step 9: Add the fixed resume template reference**

Write `plugins/resume-forge/skills/resume-forge/references/resume-template.md` exactly as:

````markdown
# ResumeForge 固定简历模板

## 目录

- 1. 模块顺序
- 2. A4 视觉契约
- 3. 基本信息
- 4. 教育背景
- 5. 专业技能
- 6. 工作经历
- 7. 项目经历
- 8. 个人优势
- 9. Markdown 交付骨架

## 1. 模块顺序

严格使用以下顺序：

```text
基本信息
→ 教育背景
→ 专业技能
→ 工作经历
→ 项目经历
→ 个人优势（可选）
```

不得根据通用简历经验自行重排。页面数量由内容决定，不把样例的三页固定为输出页数。

## 2. A4 视觉契约

- A4 纵向、白色背景、单栏正文。
- 左右页边距约 18 mm。
- 中文优先使用 Microsoft YaHei，英文和数字优先使用 Helvetica Neue，并配置兼容无衬线字体回退。
- 正文颜色 `#444444`。
- 一级标题颜色 `#467B73`。
- 项目字段标题颜色 `#016866`。
- 姓名约 22–23 pt，一级标题约 14 pt，正文约 9.3–9.5 pt，正文行距约 1.5–1.6。
- 一级标题采用“圆环图标 + 青绿色标题 + 向右延伸的细横线”。
- 教育、工作和项目标题行按约 `30% / 45% / 25%` 排列时间、名称和学历/角色，第三栏右对齐。
- 不使用会破坏文本提取顺序的图片文字、复杂侧栏或分散文本框。

首版只输出 Markdown 草稿；以上视觉契约供后续同源 HTML 和 PDF 渲染使用。

## 3. 基本信息

```text
[姓名]                                           [照片-可选]
[性别-可选]｜[年龄-可选]｜[工作年限]｜[最高学历]｜[手机号]｜[邮箱]
[婚姻状况-可选]｜[政治面貌-可选]
[现居城市]｜[目标岗位]
[求职状态或预计到岗时间]
```

照片规则：

- 接受用户附件或用户明确指定的本地 JPEG、PNG、WebP 图片。
- 照片位置为首页右上角，目标区域约 `27 × 32 mm`。
- 后续渲染默认等比例覆盖式裁剪，视觉焦点位于顶部居中。
- 用户指定新照片时只替换图片来源，不改变正文，不修改用户原图。
- 无照片时不显示空照片框，页首文字扩展至完整正文宽度。
- 首版仅记录用户选择，不声称已经处理或嵌入照片。

## 4. 教育背景

```text
◎ 教育背景 ─────────────────────────────────────

[YYYY/MM - YYYY/MM]    [学校名称]    [学习形式/学历 - 专业]

[语言或证书名称]：[级别或成绩]
```

教育经历存在多段时按时间倒序。语言或证书没有真实信息时省略对应行。

## 5. 专业技能

```text
◎ 专业技能 ─────────────────────────────────────

1. [技能分类]：[掌握程度] + [核心知识] + [真实实践场景]。
2. [技能分类]：[掌握程度] + [组件或工具] + [真实实践能力]。
```

技能分类可以从编程语言、JVM、计算机基础、设计模式、服务端框架、AIGC、流程引擎、关系型数据库、非关系型数据库、消息中间件、信息安全、Linux、团队协作与版本控制、容器化和自动化部署中选择。只保留被用户信息支持的分类。

## 6. 工作经历

```text
◎ 工作经历 ─────────────────────────────────────

[YYYY/MM - 至今]    [公司名称]    [岗位名称]

工作内容：

1. [职责主题]：[用户确认的职责范围、行动和交付]。
2. [职责主题]：[用户确认的职责范围、行动和交付]。
```

- 多段工作按时间倒序。
- 工作经历描述职责范围、角色边界、交付和协作。
- 未确认的成果、规模或指标不得补写。

## 7. 项目经历

```text
◎ 项目经历 ─────────────────────────────────────

[YYYY/MM - 至今]    [项目名称]    [项目角色]

项目背景：
[项目服务对象] + [真实业务场景] + [需要解决的问题] + [项目目标]。

技术栈：
[用户确认实际使用的语言、框架、数据库、中间件和部署工具]

工作内容：

1. [核心事项]：[个人负责范围] + [实现方案] + [确认结果]。
2. [业务模块或技术专题]：
   (1) [子模块]：[设计、开发或改造内容]。
   (2) [子模块]：[技术实现和确认结果]。
3. [性能、安全或稳定性事项]：[问题] + [措施] + [确认结果]。
```

- 多个项目按时间倒序。
- 项目内容固定使用“项目背景、技术栈、工作内容”。
- 复杂工作内容最多使用数字编号和 `(1)` 两级结构。
- 量化结果必须来自用户材料或明确确认。

## 8. 个人优势

```text
◎ 个人优势 ─────────────────────────────────────

1. [优势主题]：[具体能力] + [经历证据] + [实际价值]。
2. [优势主题]：[具体能力] + [经历证据] + [实际价值]。
```

- 该模块位于简历末尾。
- 仅在用户需要且存在事实支撑时输出。
- 不需要或没有内容时，标题与正文全部省略，不保留空白。
- 不写“责任心强”“学习能力好”等没有证据的空泛评价。

## 9. Markdown 交付骨架

```markdown
# [姓名]

[基本信息]

## 教育背景

[教育条目]

## 专业技能

[技能条目]

## 工作经历

[工作条目]

## 项目经历

[项目条目]

## 个人优势

[仅在用户要求且有事实支撑时输出]
```

交付时必须用用户真实内容替换方括号结构说明；缺少可选信息时删除对应行或模块，缺少必需事实时先询问用户。
````

- [ ] **Step 10: Create the thin Claude Code command**

Write `plugins/resume-forge/commands/resume-forge-invoke.md` exactly as:

```markdown
---
name: resume-forge:write
description: 基于固定模板收集、校验并组织真实简历信息，生成结构化简历内容草稿。
argument-hint: "[现有简历、个人信息、教育、技能、工作经历、项目经历或个人优势]"
---

立即调用已安装的 `resume-forge` skill 处理以下需求：

$ARGUMENTS

严格使用技能内置的固定简历结构，只采用用户提供或明确确认的事实。关键信息不足时先询问，不编造经历、技术、职责或成果。当前版本只交付 Markdown 结构化内容草稿。
```

- [ ] **Step 11: Validate the complete plugin core**

Run:

```bash
python3 -m json.tool plugins/resume-forge/.claude-plugin/plugin.json >/dev/null
python3 -m json.tool plugins/resume-forge/.codex-plugin/plugin.json >/dev/null
python3 -m json.tool .agents/plugins/marketplace.json >/dev/null
python3 /Users/sen/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/resume-forge/skills/resume-forge
python3 /Users/sen/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/resume-forge
rg -n '^description: Use when ' plugins/resume-forge/skills/resume-forge/SKILL.md
test "$(wc -l < plugins/resume-forge/skills/resume-forge/SKILL.md)" -lt 500
rg -n 'TO[D]O|T[B]D|PLACEHOLD[E]R|\[TO[D]O' plugins/resume-forge && exit 1 || true
```

Expected:

- All JSON commands exit `0`.
- Skill validation reports success.
- Plugin validation reports success.
- Skill description begins with `Use when` and the body is under 500 lines.
- Placeholder scan prints no matches.

- [ ] **Step 12: Commit the plugin core**

Run:

```bash
git add .agents/plugins/marketplace.json plugins/resume-forge
git commit -m "feat(resume-forge): 初始化双平台简历插件与结构技能"
```

Expected: the commit contains only the Codex marketplace entry and `plugins/resume-forge/`.

---

### Task 2: Register Claude Marketplace and Update User Documentation

**Files:**

- Modify: `.claude-plugin/marketplace.json`
- Modify: `README.md`
- Modify: `USAGE.zh.md`
- Modify: `USAGE.en.md`

**Interfaces:**

- Consumes: plugin identity `resume-forge`, version `1.0.0`, command `/resume-forge:write`, and first-version Markdown-only capability from Task 1.
- Produces: discoverable Claude marketplace entry and matching Chinese/English install and invocation documentation.

- [ ] **Step 1: Verify Claude registration is absent**

Run:

```bash
rg -n '"name": "resume-forge"' .claude-plugin/marketplace.json
```

Expected: exit code `1` before registration.

- [ ] **Step 2: Append the Claude marketplace entry**

Append this object after the existing `obsidian-solution-designer` entry, preserving valid JSON commas:

```json
{
  "name": "resume-forge",
  "description": "基于固定模板收集、校验并组织真实简历信息，生成结构化简历内容草稿。",
  "source": "./plugins/resume-forge",
  "version": "1.0.0"
}
```

- [ ] **Step 3: Update the repository overview**

In `README.md`:

1. Change `内置 8 个插件` to `内置 9 个插件`.
2. Append this row after `obsidian-solution-designer`:

```markdown
| `resume-forge` | 1.0.0 | Productivity | 基于固定模板整理真实经历并生成结构化简历内容草稿 |
```

- [ ] **Step 4: Update the Chinese usage guide**

In `USAGE.zh.md`:

1. Add this install command after the existing `obsidian-solution-designer` install command:

```text
/plugin install resume-forge@sen-claude-hub
```

2. Add this Claude Code invocation example after the detailed-design example:

````markdown
- 调用简历编写命令：

  ```text
  /resume-forge:write 根据我提供的真实经历，按固定模板整理一份 Java 后端简历。
  ```
````

3. Add this Codex example to the invocation list:

```markdown
- 整理简历内容：`Use $resume-forge to organize my verified experience into the fixed professional resume structure.`
```

4. Append this row to the per-plugin reference table:

```markdown
| `resume-forge` | `/resume-forge:write` | `Use $resume-forge to organize my verified experience into the fixed professional resume structure.` | 按固定模板收集、校验并组织真实简历信息，生成 Markdown 结构化内容草稿 |
```

- [ ] **Step 5: Update the English usage guide**

In `USAGE.en.md`:

1. Add this install command after the existing `obsidian-solution-designer` install command:

```text
/plugin install resume-forge@sen-claude-hub
```

2. Add this Claude Code invocation example after the detailed-design example:

````markdown
- Invoke ResumeForge:

  ```text
  /resume-forge:write Organize my verified Java backend experience using the fixed resume template.
  ```
````

3. Add this Codex example to the invocation list:

```markdown
- Organize resume content: `Use $resume-forge to organize my verified experience into the fixed professional resume structure.`
```

4. Append this row to the per-plugin reference table:

```markdown
| `resume-forge` | `/resume-forge:write` | `Use $resume-forge to organize my verified experience into the fixed professional resume structure.` | Collects and validates real resume information, then organizes it into the fixed structure as a Markdown draft |
```

- [ ] **Step 6: Validate registration and documentation consistency**

Run:

```bash
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
test "$(rg -c 'resume-forge' .claude-plugin/marketplace.json)" -ge 1
test "$(rg -c 'resume-forge' README.md)" -eq 1
test "$(rg -c 'resume-forge' USAGE.zh.md)" -ge 3
test "$(rg -c 'resume-forge' USAGE.en.md)" -ge 3
git diff --check
```

Expected: every command exits `0`; JSON is valid and both usage guides include install, invocation, and reference entries.

- [ ] **Step 7: Commit marketplace and documentation registration**

Run:

```bash
git add .claude-plugin/marketplace.json README.md USAGE.zh.md USAGE.en.md
git commit -m "docs(resume-forge): 注册双平台插件并补充使用说明"
```

Expected: the commit contains only the Claude marketplace and three documentation files.

---

### Task 3: Verify Cross-Platform Consistency and Skill Behavior

**Files:**

- Verify: `plugins/resume-forge/.claude-plugin/plugin.json`
- Verify: `plugins/resume-forge/.codex-plugin/plugin.json`
- Verify: `plugins/resume-forge/skills/resume-forge/SKILL.md`
- Verify: `plugins/resume-forge/skills/resume-forge/references/resume-template.md`
- Verify: `.claude-plugin/marketplace.json`
- Verify: `.agents/plugins/marketplace.json`

**Interfaces:**

- Consumes: all Task 1 and Task 2 artifacts.
- Produces: evidence that manifests agree, validators pass, the fixed structure is respected, optional sections are omitted correctly, and unsupported rendering is not claimed.

- [ ] **Step 1: Run a deterministic cross-manifest consistency check**

Run:

```bash
python3 - <<'PY'
import json
from pathlib import Path

root = Path.cwd()
claude_plugin = json.loads((root / "plugins/resume-forge/.claude-plugin/plugin.json").read_text())
codex_plugin = json.loads((root / "plugins/resume-forge/.codex-plugin/plugin.json").read_text())
claude_market = json.loads((root / ".claude-plugin/marketplace.json").read_text())
codex_market = json.loads((root / ".agents/plugins/marketplace.json").read_text())

assert claude_plugin["name"] == codex_plugin["name"] == "resume-forge"
assert claude_plugin["version"] == codex_plugin["version"] == "1.0.0"

claude_entries = [item for item in claude_market["plugins"] if item["name"] == "resume-forge"]
codex_entries = [item for item in codex_market["plugins"] if item["name"] == "resume-forge"]
assert len(claude_entries) == 1
assert len(codex_entries) == 1
assert claude_entries[0]["source"] == "./plugins/resume-forge"
assert claude_entries[0]["version"] == "1.0.0"
assert codex_entries[0]["source"] == {"source": "local", "path": "./plugins/resume-forge"}
assert codex_entries[0]["policy"] == {
    "installation": "AVAILABLE",
    "authentication": "ON_INSTALL",
}
assert codex_entries[0]["category"] == "Productivity"
print("cross-platform manifest consistency: PASS")
PY
```

Expected: `cross-platform manifest consistency: PASS`.

- [ ] **Step 2: Run all static validators**

Run:

```bash
python3 /Users/sen/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/resume-forge/skills/resume-forge
python3 /Users/sen/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/resume-forge
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool .agents/plugins/marketplace.json >/dev/null
rg -n 'TO[D]O|T[B]D|PLACEHOLD[E]R|\[TO[D]O' plugins/resume-forge && exit 1 || true
git diff --check
```

Expected: validators report success, JSON parses, placeholder scan has no matches, and Git reports no whitespace errors.

- [ ] **Step 3: Forward-test a complete verified resume request**

Dispatch a fresh agent with only the Skill path and this request:

```text
Use $resume-forge at /Users/sen/Documents/workspace/sen-claude-hub/plugins/resume-forge/skills/resume-forge to organize this verified information: 李明，本科，3年Java后端经验，现居上海；2023/07至今在示例科技任Java后端开发；负责订单服务接口和MySQL表设计；2024/01至今参与订单平台，技术栈为JDK17、Spring Boot 3、MySQL和Redis。不要个人优势，不提供照片。请按当前版本交付。
```

Verify the result contains, in order:

1. 基本信息。
2. 教育背景。
3. 专业技能。
4. 工作经历。
5. 项目经历。

Verify it omits the entire “个人优势” module, does not invent school/contact details/metrics, and identifies the output as a Markdown draft rather than HTML/PDF.

- [ ] **Step 4: Forward-test missing information and photo boundaries**

Dispatch a separate fresh agent with only the Skill path and this request:

```text
Use $resume-forge at /Users/sen/Documents/workspace/sen-claude-hub/plugins/resume-forge/skills/resume-forge to write my resume. I only know that I worked on a payment project, and I want to use /tmp/missing-photo.png as the resume photo.
```

Verify the result asks only for missing facts that affect the resume, does not fabricate experience, does not claim the missing photo was embedded, and states that the current version records the photo choice without rendering HTML/PDF.

- [ ] **Step 5: Forward-test supported personal strengths and unsupported output formats**

Dispatch a third fresh agent with only the Skill path and this request:

```text
Use $resume-forge at /Users/sen/Documents/workspace/sen-claude-hub/plugins/resume-forge/skills/resume-forge to create the final HTML and PDF resume immediately from this verified information: 王蕾，本科，2年Java后端经验，负责会员服务开发。Include a personal strengths section supported by this fact: she led three production incident reviews and drove every corrective action to closure.
```

Verify the result includes “个人优势” after “项目经历”, derives the advantage only from the supplied incident-review fact, does not invent employers, dates, technologies, or metrics, and clearly limits the current delivery to a Markdown draft rather than claiming HTML/PDF files were created.

- [ ] **Step 6: Compare GREEN results with the RED baseline**

For Scenarios A, B, and C, record in the Task 3 report:

- The exact baseline failure from Task 1.
- The corresponding Skill rule or reference section.
- The GREEN result showing the failure is addressed.
- Any new failure or rationalization discovered during GREEN.

If a GREEN agent finds a new loophole, update only the responsible Skill or reference sentence, re-run the affected scenario with a fresh agent, and include both runs in the report.

- [ ] **Step 7: Commit an observed-behavior refinement only when GREEN required one**

If Step 6 changed `SKILL.md` or `references/resume-template.md`, re-run both validators and commit only those changed files:

```bash
python3 /Users/sen/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/resume-forge/skills/resume-forge
python3 /Users/sen/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/resume-forge
git add plugins/resume-forge/skills/resume-forge/SKILL.md plugins/resume-forge/skills/resume-forge/references/resume-template.md
git commit -m "fix(resume-forge): 收紧简历技能行为边界"
```

If Step 6 changed no repository file, do not create an empty commit.

- [ ] **Step 8: Confirm repository cleanliness and commit scope**

Run:

```bash
git status --short
git log -3 --oneline --decorate
```

Expected:

- The two required implementation commits are visible after the design commit; a third behavior-refinement commit appears only if GREEN exposed a real gap.
- No ResumeForge implementation files remain modified or untracked.
- The unrelated `travel-guides/` directory remains untracked and untouched.
