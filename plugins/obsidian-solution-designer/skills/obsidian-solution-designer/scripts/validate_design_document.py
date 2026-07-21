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
    if match:
        return match.group(1)

    match = re.search(rf"(?m)^{re.escape(key)}:\s*(\[[^\n]*])\s*$", frontmatter)
    if not match:
        return ""
    return "".join(f"  - {value}\n" for value in flow_sequence_values(match.group(1)))


def flow_sequence_values(value: str) -> list[str]:
    if not value.startswith("[") or not value.endswith("]"):
        return []

    values: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False
    for character in value[1:-1]:
        if quote:
            current.append(character)
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
        elif character in {"\"", "'"}:
            quote = character
            current.append(character)
        elif character == ",":
            values.append("".join(current).strip().strip("\"'"))
            current = []
        else:
            current.append(character)
    if quote:
        return []
    values.append("".join(current).strip().strip("\"'"))
    return [item for item in values if item]


TABLE_SEPARATOR_PATTERN = re.compile(r"^\|(?:\s*:?-{3,}:?\s*\|)+\s*$")
UNESCAPED_PIPE_PATTERN = re.compile(r"(?<!\\)\|")


def table_column_count(row: str) -> int:
    return len(UNESCAPED_PIPE_PATTERN.findall(row.strip())) - 1


def validate_tables(prose: str) -> list[str]:
    """校验表格分隔行与表头列数一致；不一致时 Obsidian 不会渲染为表格。"""
    errors: list[str] = []
    lines = prose.splitlines()
    for index in range(1, len(lines)):
        line = lines[index].strip()
        if not TABLE_SEPARATOR_PATTERN.match(line):
            continue
        header = lines[index - 1].strip()
        if not header.startswith("|"):
            continue
        header_columns = table_column_count(header)
        separator_columns = table_column_count(line)
        if header_columns > 0 and header_columns != separator_columns:
            errors.append(
                f"表格分隔行与表头列数不一致（表头 {header_columns} 列 / 分隔行 {separator_columns} 列）: {header[:40]}"
            )
    return errors


FENCE_OPEN_PATTERN = re.compile(r"^( {0,3})(`{3,}|~{3,}).*$", re.MULTILINE)


def fence_close_pattern(marker: str) -> re.Pattern[str]:
    return re.compile(rf"^ {{0,3}}{re.escape(marker[0])}{{{len(marker)},}}[ \t]*$")


def strip_fenced_code(body: str) -> str:
    prose_lines: list[str] = []
    marker: str | None = None
    for line in body.splitlines(keepends=True):
        if marker:
            if fence_close_pattern(marker).match(line.rstrip("\r\n")):
                marker = None
            prose_lines.append("\n" if line.endswith("\n") else "")
            continue

        match = FENCE_OPEN_PATTERN.match(line)
        if match:
            marker = match.group(2)
            prose_lines.append("\n" if line.endswith("\n") else "")
            continue
        prose_lines.append(line)
    return "".join(prose_lines)


def validate_fences(body: str) -> bool:
    marker: str | None = None
    for line in body.splitlines():
        if marker:
            if fence_close_pattern(marker).match(line):
                marker = None
            continue
        match = FENCE_OPEN_PATTERN.match(line)
        if match:
            marker = match.group(2)
    return marker is None


def validate_document(path: Path, expected_mode: str | None = None) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    try:
        frontmatter, body = split_frontmatter(text)
    except ValueError as error:
        return [str(error)]

    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.search(frontmatter):
            errors.append("Frontmatter 存在未替换占位符")
            break

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

    prose = strip_fenced_code(body)
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.search(prose):
            errors.append("正文存在未替换占位符")
            break
    if not validate_fences(body):
        errors.append("Markdown 代码块未闭合")
    errors.extend(validate_tables(prose))

    headings = "\n".join(re.findall(r"(?m)^#{1,6}\s+(.+)$", prose))
    for group in REQUIRED_SECTION_GROUPS:
        if not any(term in headings for term in group):
            errors.append(f"缺少必需章节语义: {'/'.join(group)}")
    if mode == "fullstack" and "前端" not in headings:
        errors.append("全栈设计缺少前端设计章节")
    if re.search(r"(?m)^#{1,6}\s+.*(?:待确认|当前缺口)", prose):
        errors.append("成熟文档仍包含待确认或当前缺口章节")

    related_block = list_block(frontmatter, "related")
    related_links = set(re.findall(r"\[\[([^\]]+)]]", related_block))
    body_links = set(re.findall(r"\[\[([^\]]+)]]", prose))
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
