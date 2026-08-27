from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from validate_design_document import main, validate_document


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
提供经过鉴权的示例查询能力，不调整现有写入流程。
## 设计依据与关联文档
参考 [[示例需求]]。
## 总体架构
请求由现有示例模块处理，数据仍归属该模块。
## 全流程交互设计
| 场景 | 触发与主体 | 调用与契约 | 处理与数据状态 | 结果与反馈 | 异常恢复与验收 |
| --- | --- | --- | --- | --- | --- |
| FLOW-01 示例查询 | 已授权调用方发起查询 | API-01 | 示例模块读取 DATA-01，不改变业务状态 | 返回查询结果 | ERR-01；AC-01 |

### FLOW-01 示例查询
调用方发起查询，服务校验后返回结果，失败时返回稳定错误码。
## 接口契约
### API-01 示例查询接口
`GET /api/examples/{id}` 返回示例详情。
## 数据模型与数据库设计
### DATA-01 示例实体
沿用现有示例实体，不新增或调整数据库字段。
## 异常与恢复
### ERR-01 查询失败恢复
参数错误由调用方修正，基础设施错误停止自动重试并告警。
## 验收与实现设计就绪检查
### AC-01 示例查询验收
查询成功和参数错误场景均具有可观察结果。
"""

VALID_FULLSTACK_DOCUMENT = VALID_DOCUMENT.replace(
    "  - backend\n",
    "  - fullstack\n",
).replace(
    "design_mode: backend",
    "design_mode: fullstack",
).replace(
    "## 总体架构\n",
    "## 前端设计\n页面入口、权限、页面状态和失败恢复均已定义。\n"
    "## 总体架构\n",
)

VALID_COMPACT_BACKEND_DOCUMENT = VALID_DOCUMENT.replace(
    "## 设计目标与范围\n提供经过鉴权的示例查询能力，不调整现有写入流程。\n"
    "## 设计依据与关联文档\n参考 [[示例需求]]。",
    "## 设计概览\n"
    "### 设计目标与范围\n提供经过鉴权的示例查询能力，不调整现有写入流程。\n"
    "### 设计依据与关联文档\n参考 [[示例需求]]。",
).replace(
    "## 接口契约\n### API-01 示例查询接口",
    "## 契约附录\n### API-01 示例查询接口契约",
).replace(
    "## 数据模型与数据库设计\n### DATA-01 示例实体",
    "### DATA-01 示例实体数据模型与数据库设计",
)

VALID_COMPACT_FULLSTACK_DOCUMENT = VALID_COMPACT_BACKEND_DOCUMENT.replace(
    "  - backend\n",
    "  - fullstack\n",
).replace(
    "design_mode: backend",
    "design_mode: fullstack",
).replace(
    "## 总体架构\n",
    "## 前端设计\n页面入口、权限、页面状态和失败恢复均已定义。\n"
    "## 总体架构\n",
)


class ValidateDesignDocumentTest(unittest.TestCase):
    def validate_text(self, text: str, mode: str = "backend") -> list[str]:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "design.md"
            path.write_text(text, encoding="utf-8")
            return validate_document(path, mode)

    def test_valid_backend_document_passes(self):
        self.assertEqual([], self.validate_text(VALID_DOCUMENT))

    def test_valid_fullstack_document_passes(self):
        self.assertEqual([], self.validate_text(VALID_FULLSTACK_DOCUMENT, "fullstack"))

    def test_fullstack_frontend_section_must_be_h2_with_content(self):
        empty_section = VALID_FULLSTACK_DOCUMENT.replace(
            "## 前端设计\n页面入口、权限、页面状态和失败恢复均已定义。\n",
            "## 前端设计\n",
        )
        fake_subheading = VALID_FULLSTACK_DOCUMENT.replace(
            "## 前端设计\n页面入口、权限、页面状态和失败恢复均已定义。\n",
            "### 前端接口\n页面入口、权限、页面状态和失败恢复均已定义。\n",
        )
        for document in (empty_section, fake_subheading):
            with self.subTest(document=document):
                errors = self.validate_text(document, "fullstack")
                self.assertTrue(any("前端设计" in error for error in errors))

    def test_compact_six_section_backend_document_passes(self):
        self.assertEqual(6, VALID_COMPACT_BACKEND_DOCUMENT.count("\n## "))
        self.assertEqual([], self.validate_text(VALID_COMPACT_BACKEND_DOCUMENT))

    def test_compact_seven_section_fullstack_document_passes(self):
        self.assertEqual(7, VALID_COMPACT_FULLSTACK_DOCUMENT.count("\n## "))
        self.assertEqual([], self.validate_text(VALID_COMPACT_FULLSTACK_DOCUMENT, "fullstack"))

    def test_body_title_must_match_frontmatter_title(self):
        for document in (
            VALID_DOCUMENT.replace("# 示例详细设计方案\n\n", ""),
            VALID_DOCUMENT.replace("# 示例详细设计方案", "# 另一个详细设计方案"),
        ):
            with self.subTest(document=document):
                errors = self.validate_text(document)
                self.assertTrue(any("正文一级标题" in error for error in errors))

    def test_utf8_bom_before_frontmatter_is_allowed(self):
        self.assertEqual([], self.validate_text("\ufeff" + VALID_DOCUMENT))

    def test_body_must_have_exactly_one_level_one_title(self):
        errors = self.validate_text(VALID_DOCUMENT + "\n# 重复一级标题\n重复内容。\n")
        self.assertTrue(any("只能包含一个" in error for error in errors))

    def test_heading_inside_html_comment_does_not_count(self):
        document = VALID_DOCUMENT.replace(
            "# 示例详细设计方案\n\n",
            "<!--\n# 示例详细设计方案\n-->\n\n",
        )
        errors = self.validate_text(document)
        self.assertTrue(any("正文一级标题" in error for error in errors))

    def test_required_semantic_section_must_have_content(self):
        document = VALID_DOCUMENT.replace(
            "## 总体架构\n请求由现有示例模块处理，数据仍归属该模块。\n",
            "## 总体架构\n",
        )
        errors = self.validate_text(document)
        self.assertTrue(any("总体架构" in error and "内容为空" in error for error in errors))

    def test_html_comment_does_not_count_as_section_content(self):
        document = VALID_DOCUMENT.replace(
            "## 总体架构\n请求由现有示例模块处理，数据仍归属该模块。\n",
            "## 总体架构\n<!-- 仅供模板作者阅读 -->\n",
        )
        errors = self.validate_text(document)
        self.assertTrue(any("总体架构" in error and "内容为空" in error for error in errors))

    def test_titled_bare_callout_does_not_count_as_section_content(self):
        document = VALID_DOCUMENT.replace(
            "## 总体架构\n请求由现有示例模块处理，数据仍归属该模块。\n",
            "## 总体架构\n> [!note] 架构说明\n",
        )
        errors = self.validate_text(document)
        self.assertTrue(any("总体架构" in error and "内容为空" in error for error in errors))

    def test_empty_table_row_does_not_count_as_section_content(self):
        document = VALID_DOCUMENT.replace(
            "## 总体架构\n请求由现有示例模块处理，数据仍归属该模块。\n",
            "## 总体架构\n| 模块 | 职责 |\n| --- | --- |\n|  |  |\n",
        )
        errors = self.validate_text(document)
        self.assertTrue(any("总体架构" in error and "内容为空" in error for error in errors))

    def test_empty_markdown_structure_does_not_count_as_section_content(self):
        document = VALID_DOCUMENT.replace(
            "## 总体架构\n请求由现有示例模块处理，数据仍归属该模块。\n",
            "## 总体架构\n> [!note] 架构说明\n>\n-\n",
        )
        errors = self.validate_text(document)
        self.assertTrue(any("总体架构" in error and "内容为空" in error for error in errors))

    def test_document_requires_populated_closure_navigation(self):
        table = """| 场景 | 触发与主体 | 调用与契约 | 处理与数据状态 | 结果与反馈 | 异常恢复与验收 |
| --- | --- | --- | --- | --- | --- |
| FLOW-01 示例查询 | 已授权调用方发起查询 | API-01 | 示例模块读取 DATA-01，不改变业务状态 | 返回查询结果 | ERR-01；AC-01 |

"""
        errors = self.validate_text(VALID_DOCUMENT.replace(table, ""))
        self.assertTrue(any("闭环导航" in error for error in errors))

    def test_closure_references_must_resolve_to_defined_sections(self):
        document = VALID_DOCUMENT.replace(
            "### API-01 示例查询接口",
            "### API-02 示例查询接口",
        )
        errors = self.validate_text(document)
        self.assertTrue(any("API-01" in error and "未定义" in error for error in errors))

    def test_chinese_adjacent_closure_reference_must_resolve(self):
        errors = self.validate_text(VALID_DOCUMENT + "\n该步骤关联API-99接口。\n")
        self.assertTrue(any("API-99" in error and "未定义" in error for error in errors))

    def test_optional_api_data_and_error_identifiers_may_be_omitted(self):
        document = VALID_DOCUMENT.replace(
            "| FLOW-01 示例查询 | 已授权调用方发起查询 | API-01 | 示例模块读取 DATA-01，不改变业务状态 | 返回查询结果 | ERR-01；AC-01 |",
            "| FLOW-01 示例查询 | 已授权调用方发起查询 | 模块内本地动作 | 读取内存快照，不持久化且不改变业务状态 | 返回查询结果 | 失败直接返回调用方；AC-01 |",
        ).replace(
            "## 接口契约\n### API-01 示例查询接口\n`GET /api/examples/{id}` 返回示例详情。",
            "## 接口契约\n本场景为模块内本地动作，不新增或调整接口。",
        ).replace(
            "## 数据模型与数据库设计\n### DATA-01 示例实体\n沿用现有示例实体，不新增或调整数据库字段。",
            "## 数据模型与数据库设计\n本场景只读取内存快照，不访问或调整持久化数据。",
        ).replace(
            "## 异常与恢复\n### ERR-01 查询失败恢复\n参数错误由调用方修正，基础设施错误停止自动重试并告警。",
            "## 异常与恢复\n失败直接返回调用方，不建立跨流程统一错误策略。",
        )
        self.assertEqual([], self.validate_text(document))

    def test_closure_navigation_row_must_link_flow_and_acceptance(self):
        document = VALID_DOCUMENT.replace(
            "| FLOW-01 示例查询 | 已授权调用方发起查询 | API-01 | 示例模块读取 DATA-01，不改变业务状态 | 返回查询结果 | ERR-01；AC-01 |",
            "| 示例查询 | 已授权调用方发起查询 | API-01 | 示例模块读取 DATA-01，不改变业务状态 | 返回查询结果 | ERR-01 |",
        )
        errors = self.validate_text(document)
        self.assertTrue(any("FLOW" in error and "AC" in error for error in errors))

    def test_closure_navigation_flow_must_be_in_first_cell(self):
        document = VALID_DOCUMENT.replace(
            "| FLOW-01 示例查询 | 已授权调用方发起查询 | API-01 | 示例模块读取 DATA-01，不改变业务状态 | 返回查询结果 | ERR-01；AC-01 |",
            "| 示例查询 | 已授权 FLOW-01 调用方发起查询 | API-01 | 示例模块读取 DATA-01，不改变业务状态 | 返回查询结果 | ERR-01；AC-01 |",
        )
        errors = self.validate_text(document)
        self.assertTrue(any("FLOW" in error and "首列" in error for error in errors))

    def test_closure_navigation_cells_must_be_populated(self):
        document = VALID_DOCUMENT.replace(
            "| FLOW-01 示例查询 | 已授权调用方发起查询 | API-01 | 示例模块读取 DATA-01，不改变业务状态 | 返回查询结果 | ERR-01；AC-01 |",
            "| FLOW-01 示例查询 | 已授权调用方发起查询 |  | 示例模块读取 DATA-01，不改变业务状态 | 返回查询结果 | ERR-01；AC-01 |",
        )
        errors = self.validate_text(document)
        self.assertTrue(any("闭环导航行单元格不能为空" in error for error in errors))

    def test_closure_acceptance_must_be_in_acceptance_cell(self):
        document = VALID_DOCUMENT.replace(
            "| FLOW-01 示例查询 | 已授权调用方发起查询 | API-01 | 示例模块读取 DATA-01，不改变业务状态 | 返回查询结果 | ERR-01；AC-01 |",
            "| FLOW-01 示例查询；AC-01 | 已授权调用方发起查询 | API-01 | 示例模块读取 DATA-01，不改变业务状态 | 返回查询结果 | ERR-01；失败后停止重试 |",
        )
        errors = self.validate_text(document)
        self.assertTrue(any("AC" in error and "验收列" in error for error in errors))

    def test_document_must_have_exactly_one_closure_navigation_table(self):
        duplicate_table = """
| 场景 | 触发与主体 | 调用与契约 | 处理与数据状态 | 结果与反馈 | 异常恢复与验收 |
| --- | --- | --- | --- | --- | --- |
| FLOW-01 示例查询 | 已授权调用方发起查询 | API-01 | 示例模块读取 DATA-01，不改变业务状态 | 返回查询结果 | ERR-01；AC-01 |
"""
        errors = self.validate_text(VALID_DOCUMENT + duplicate_table)
        self.assertTrue(any("闭环导航表只能包含一张" in error for error in errors))

    def test_ready_document_rejects_template_only_instructions(self):
        for marker in ("落盘门禁", "本文件仅为骨架", "模板骨架"):
            with self.subTest(marker=marker):
                document = VALID_DOCUMENT.replace(
                    "> 作为实现设计基线。",
                    f"> 作为实现设计基线。\n\n> [!important] {marker}",
                )
                errors = self.validate_text(document)
                self.assertTrue(any("模板编写说明" in error for error in errors))

    def test_closure_definition_allows_chinese_colon_after_identifier(self):
        document = VALID_DOCUMENT
        for identifier, title in (
            ("FLOW-01", "示例查询"),
            ("API-01", "示例查询接口"),
            ("DATA-01", "示例实体"),
            ("ERR-01", "查询失败恢复"),
            ("AC-01", "示例查询验收"),
        ):
            document = document.replace(
                f"### {identifier} {title}",
                f"### {identifier}：{title}",
            )
        self.assertEqual([], self.validate_text(document))

    def test_closure_identifier_must_not_be_defined_twice(self):
        document = VALID_DOCUMENT.replace(
            "### API-01 示例查询接口\n`GET /api/examples/{id}` 返回示例详情。",
            "### API-01 示例查询接口\n`GET /api/examples/{id}` 返回示例详情。\n\n"
            "### API-01 重复定义\n重复的接口定义。",
        )
        errors = self.validate_text(document)
        self.assertTrue(any("API-01" in error and "重复定义" in error for error in errors))

    def test_closure_definition_must_have_content(self):
        document = VALID_DOCUMENT.replace(
            "### API-01 示例查询接口\n`GET /api/examples/{id}` 返回示例详情。\n",
            "### API-01 示例查询接口\n",
        )
        errors = self.validate_text(document)
        self.assertTrue(any("API-01" in error and "内容为空" in error for error in errors))

    def test_missing_frontmatter_field_fails(self):
        errors = self.validate_text(VALID_DOCUMENT.replace("version: v1.0\n", ""))
        self.assertTrue(any("version" in error for error in errors))

    def test_duplicate_top_level_frontmatter_key_fails(self):
        document = VALID_DOCUMENT.replace("status: ready\n", "status: ready\nstatus: draft\n")
        errors = self.validate_text(document)
        self.assertTrue(any("status" in error and "重复" in error for error in errors))

    def test_required_scalar_frontmatter_value_must_not_be_empty(self):
        for key, value in (
            ("version", "v1.0"),
            ("created", "2026-07-20"),
            ("updated", "2026-07-20"),
            ("last_verified", "2026-07-20"),
        ):
            with self.subTest(key=key):
                document = VALID_DOCUMENT.replace(f"{key}: {value}\n", f"{key}:\n")
                errors = self.validate_text(document)
                self.assertTrue(any(key in error and "不能为空" in error for error in errors))

    def test_yaml_null_scalar_is_treated_as_empty(self):
        for key, value, null_value in (
            ("version", "v1.0", "null"),
            ("created", "2026-07-20", "~"),
            ("updated", "2026-07-20", '""'),
        ):
            with self.subTest(key=key, null_value=null_value):
                document = VALID_DOCUMENT.replace(f"{key}: {value}\n", f"{key}: {null_value}\n")
                errors = self.validate_text(document)
                self.assertTrue(any(key in error and "不能为空" in error for error in errors))

    def test_yaml_inline_comment_on_scalar_is_allowed(self):
        document = VALID_DOCUMENT.replace("status: ready\n", "status: ready # 正式文档\n")
        self.assertEqual([], self.validate_text(document))

    def test_mode_mismatch_fails(self):
        errors = self.validate_text(VALID_DOCUMENT, "fullstack")
        self.assertTrue(any("design_mode" in error for error in errors))

    def test_placeholder_and_unclosed_fence_fail(self):
        text = VALID_DOCUMENT + "\n## 补充\n{{value}}\n```mermaid\nflowchart LR\n"
        errors = self.validate_text(text)
        self.assertTrue(any("占位符" in error for error in errors))
        self.assertTrue(any("代码块" in error for error in errors))

    def test_frontmatter_placeholders_fail(self):
        for placeholder in ("{{文档标题}}", "【待填写文档标题】", "TODO"):
            with self.subTest(placeholder=placeholder):
                document = VALID_DOCUMENT.replace("title: 示例详细设计方案", f"title: {placeholder}")
                errors = self.validate_text(document)
                self.assertTrue(any("Frontmatter" in error and "占位符" in error for error in errors))

    def test_real_chinese_bracketed_copy_is_not_a_placeholder(self):
        document = VALID_DOCUMENT.replace(
            "> 作为实现设计基线。",
            "> 页面成功后展示【操作成功】，该文案已经确认。",
        )
        self.assertEqual([], self.validate_text(document))

    def test_real_templates_fail_when_frontmatter_contains_placeholders(self):
        assets = SKILL_ROOT / "assets"
        for filename, mode in (
            ("backend-design-template.md", "backend"),
            ("fullstack-design-template.md", "fullstack"),
        ):
            with self.subTest(filename=filename):
                with TemporaryDirectory() as temp_dir:
                    path = Path(temp_dir) / filename
                    path.write_text((assets / filename).read_text(encoding="utf-8"), encoding="utf-8")
                    errors = validate_document(path, mode)
                self.assertTrue(any("Frontmatter" in error and "占位符" in error for error in errors))
                # 模板骨架自身的表格结构必须始终合法，防止坏表格被复制进正式设计。
                self.assertFalse(any("表格分隔行" in error for error in errors))

    def test_table_separator_column_mismatch_fails(self):
        text = VALID_DOCUMENT + "\n| 字段名 | 类型 | 业务语义 |\n| --- | --- |\n"
        errors = self.validate_text(text)
        self.assertTrue(any("表格分隔行与表头列数不一致" in error for error in errors))

    def test_table_without_data_rows_fails(self):
        text = VALID_DOCUMENT + "\n| 字段名 | 类型 |\n| --- | --- |\n"
        errors = self.validate_text(text)
        self.assertTrue(any("表格缺少有效数据行" in error for error in errors))

    def test_table_data_row_column_mismatch_fails(self):
        text = VALID_DOCUMENT + "\n| 字段名 | 类型 | 业务语义 |\n| --- | --- | --- |\n| id | long |\n"
        errors = self.validate_text(text)
        self.assertTrue(any("数据行与表头列数不一致" in error for error in errors))

    def test_consistent_table_passes(self):
        text = VALID_DOCUMENT + "\n| 字段名 | 类型 | 业务语义 |\n| --- | --- | --- |\n| id | long | 主键 |\n"
        self.assertEqual([], self.validate_text(text))

    def test_unrelated_body_link_fails(self):
        errors = self.validate_text(VALID_DOCUMENT + "\n参考 [[未登记资料]]。\n")
        self.assertTrue(any("未登记资料" in error for error in errors))

    def test_related_link_must_be_used_in_body(self):
        document = VALID_DOCUMENT.replace(
            "related:\n  - \"[[示例需求]]\"\n",
            "related:\n  - \"[[示例需求]]\"\n  - \"[[未使用资料]]\"\n",
        )
        errors = self.validate_text(document)
        self.assertTrue(any("未使用资料" in error and "正文未使用" in error for error in errors))

    def test_related_comparison_normalizes_alias_and_heading(self):
        for body_link in ("[[示例需求|需求说明]]", "[[示例需求#范围|需求范围]]"):
            with self.subTest(body_link=body_link):
                document = VALID_DOCUMENT.replace("[[示例需求]]。", f"{body_link}。")
                self.assertEqual([], self.validate_text(document))

    def test_pending_section_fails(self):
        errors = self.validate_text(VALID_DOCUMENT + "\n## 待确认问题\n- 字段语义未知\n")
        self.assertTrue(any("待确认" in error for error in errors))

    def test_corrected_history_heading_does_not_count_as_pending(self):
        document = VALID_DOCUMENT + "\n## 已校正：原待确认项\n该事项已经依据最新基线完成校正。\n"
        self.assertEqual([], self.validate_text(document))

    def test_flow_style_tags_and_related_pass(self):
        document = VALID_DOCUMENT.replace(
            "tags:\n  - sample\n  - backend\n  - interface-design\n  - detailed-design\n",
            "tags: [sample, backend, interface-design, detailed-design]\n",
        ).replace(
            "related:\n  - \"[[示例需求]]\"\n",
            "related: [\"[[示例需求]]\"]\n",
        )
        self.assertEqual([], self.validate_text(document))

    def test_quoted_block_style_tags_pass(self):
        document = VALID_DOCUMENT.replace("  - backend\n", '  - "backend"\n').replace(
            "  - detailed-design\n",
            '  - "detailed-design"\n',
        )
        self.assertEqual([], self.validate_text(document))

    def test_closed_fenced_code_is_ignored_by_prose_checks(self):
        document = VALID_DOCUMENT + """
   ````markdown
{{value}}
[[代码示例]]
## 待确认问题
````
~~~text
{{another_value}}
[[另一个代码示例]]
~~~
"""
        self.assertEqual([], self.validate_text(document))

    def test_list_indented_fenced_code_is_ignored_by_prose_checks(self):
        document = VALID_DOCUMENT + """
- 示例代码：
    ````markdown
    {{value}}
    [[代码示例]]
    ## 待确认问题
    ````
"""
        self.assertEqual([], self.validate_text(document))

    def test_cli_exit_codes_are_automated(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "design.md"
            path.write_text(VALID_DOCUMENT, encoding="utf-8")
            stdout, stderr = StringIO(), StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                self.assertEqual(0, main([str(path), "--mode", "backend"]))
            self.assertIn("OK:", stdout.getvalue())

            path.write_text(VALID_DOCUMENT + "\n## 待确认问题\n", encoding="utf-8")
            stdout, stderr = StringIO(), StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                self.assertEqual(1, main([str(path)]))
            self.assertIn("待确认", stderr.getvalue())

            stdout, stderr = StringIO(), StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                self.assertEqual(2, main([str(Path(temp_dir) / "missing.md")]))
            self.assertIn("无法读取文档", stderr.getvalue())

            with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as context:
                main([str(path), "--mode", "invalid"])
            self.assertEqual(2, context.exception.code)


if __name__ == "__main__":
    unittest.main()
