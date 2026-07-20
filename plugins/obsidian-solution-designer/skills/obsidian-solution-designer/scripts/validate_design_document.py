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
    return match.group(1).strip().strip("\"'") if match else None


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
