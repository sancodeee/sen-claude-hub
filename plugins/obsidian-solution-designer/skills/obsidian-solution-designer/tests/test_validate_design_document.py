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

    def test_frontmatter_placeholders_fail(self):
        for placeholder in ("{{文档标题}}", "【文档标题】", "TODO"):
            with self.subTest(placeholder=placeholder):
                document = VALID_DOCUMENT.replace("title: 示例详细设计方案", f"title: {placeholder}")
                errors = self.validate_text(document)
                self.assertTrue(any("Frontmatter" in error and "占位符" in error for error in errors))

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

    def test_unrelated_body_link_fails(self):
        errors = self.validate_text(VALID_DOCUMENT + "\n参考 [[未登记资料]]。\n")
        self.assertTrue(any("未登记资料" in error for error in errors))

    def test_pending_section_fails(self):
        errors = self.validate_text(VALID_DOCUMENT + "\n## 待确认问题\n- 字段语义未知\n")
        self.assertTrue(any("待确认" in error for error in errors))

    def test_flow_style_tags_and_related_pass(self):
        document = VALID_DOCUMENT.replace(
            "tags:\n  - sample\n  - backend\n  - interface-design\n  - detailed-design\n",
            "tags: [sample, backend, interface-design, detailed-design]\n",
        ).replace(
            "related:\n  - \"[[示例需求]]\"\n",
            "related: [\"[[示例需求]]\"]\n",
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
