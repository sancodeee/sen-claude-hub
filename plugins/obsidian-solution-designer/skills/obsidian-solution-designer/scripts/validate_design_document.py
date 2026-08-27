#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re
import sys


REQUIRED_FRONTMATTER = (
    "title", "aliases", "tags", "status", "version", "created", "updated",
    "last_verified", "design_mode", "maturity", "related", "source",
)
REQUIRED_SCALAR_FRONTMATTER = (
    "title", "status", "version", "created", "updated", "last_verified",
    "design_mode", "maturity",
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
    re.compile(r"【(?:待填写|待补充|请填写|请补充|占位)[^】]*】", re.IGNORECASE),
)
TEMPLATE_ONLY_MARKERS = ("落盘门禁", "本文件仅为骨架", "模板骨架")


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("缺少 YAML Frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("YAML Frontmatter 未闭合")
    return text[4:end], text[end + 5:]


def top_level_values(frontmatter: str, key: str) -> list[str]:
    return re.findall(rf"(?m)^{re.escape(key)}:[ \t]*(.*?)[ \t]*$", frontmatter)


def strip_yaml_inline_comment(value: str) -> str:
    quote: str | None = None
    escaped = False
    for index, character in enumerate(value):
        if quote:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
        elif character in {"\"", "'"}:
            quote = character
        elif character == "#" and (index == 0 or value[index - 1].isspace()):
            return value[:index].rstrip()
    return value.strip()


def is_yaml_null_scalar(value: str) -> bool:
    value = strip_yaml_inline_comment(value).strip()
    if not value:
        return True
    if value[0] in {"\"", "'"}:
        return len(value) >= 2 and value[-1] == value[0] and not value[1:-1]
    return value == "~" or value.lower() == "null"


def scalar_value(frontmatter: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:[ \t]*(.*?)[ \t]*$", frontmatter)
    if not match:
        return None
    return strip_yaml_inline_comment(match.group(1)).strip().strip("\"'")


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


def table_row_has_content(row: str) -> bool:
    cells = table_cells(row)
    return any(cell.strip() for cell in cells)


def table_cells(row: str) -> list[str]:
    return UNESCAPED_PIPE_PATTERN.split(row.strip().strip("|"))


def validate_tables(prose: str) -> list[str]:
    """校验表格列数和有效数据行；成熟文档不得保留坏表或空表。"""
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
        row_index = index + 1
        has_data_row = False
        while row_index < len(lines) and lines[row_index].strip().startswith("|"):
            row = lines[row_index].strip()
            if not TABLE_SEPARATOR_PATTERN.match(row) and table_row_has_content(row):
                has_data_row = True
                row_columns = table_column_count(row)
                if header_columns > 0 and row_columns != header_columns:
                    errors.append(
                        f"表格数据行与表头列数不一致（表头 {header_columns} 列 / 数据行 {row_columns} 列）: {row[:40]}"
                    )
            row_index += 1
        if not has_data_row:
            errors.append(f"表格缺少有效数据行: {header[:40]}")
    return errors


FENCE_OPEN_PATTERN = re.compile(r"^([ \t]*)(`{3,}|~{3,}).*$", re.MULTILINE)


def fence_close_pattern(marker: str) -> re.Pattern[str]:
    return re.compile(rf"^[ \t]*{re.escape(marker[0])}{{{len(marker)},}}[ \t]*$")


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


HEADING_PATTERN = re.compile(r"(?m)^(#{1,6})\s+(.+?)\s*$")
HTML_COMMENT_PATTERN = re.compile(r"(?s)<!--.*?-->")


def strip_html_comments(text: str) -> str:
    return HTML_COMMENT_PATTERN.sub("", text)


def markdown_sections(prose: str) -> list[tuple[str, str]]:
    matches = list(HEADING_PATTERN.finditer(prose))
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        level = len(match.group(1))
        end = len(prose)
        for next_match in matches[index + 1:]:
            if len(next_match.group(1)) <= level:
                end = next_match.start()
                break
        sections.append((match.group(2).strip(), prose[match.end():end]))
    return sections


def has_meaningful_content(section_body: str) -> bool:
    section_body = strip_html_comments(section_body)
    lines = section_body.splitlines()
    for index, line in enumerate(lines):
        if not TABLE_SEPARATOR_PATTERN.match(line.strip()):
            continue
        row_index = index + 1
        while row_index < len(lines) and lines[row_index].strip().startswith("|"):
            if table_row_has_content(lines[row_index]):
                return True
            row_index += 1

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("|"):
            continue
        if re.fullmatch(r">?\s*\[![^]]+](?:[+-])?(?:\s+.*)?", stripped):
            continue
        if re.fullmatch(r"(?:>|[-+*]|\d+[.)]|[-+*]\s+\[[ xX]])", stripped):
            continue
        return True
    return False


CLOSURE_HEADER_GROUPS = (
    ("场景", "链路"),
    ("触发", "入口"),
    ("主体", "操作"),
    ("接口", "契约", "事件", "任务", "回调"),
    ("处理",),
    ("数据", "状态"),
    ("返回", "反馈"),
    ("恢复",),
    ("验收",),
)
CLOSURE_ID_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])(?:FLOW|API|DATA|ERR|AC)-\d{2,}(?![A-Za-z0-9_])"
)
CLOSURE_DEFINITION_PATTERN = re.compile(
    r"(?m)^#{2,6}\s+((?:FLOW|API|DATA|ERR|AC)-\d{2,})(?![A-Za-z0-9_])"
)
OBSIDIAN_LINK_PATTERN = re.compile(r"\[\[([^\]]+)]]")


def markdown_tables(prose: str) -> list[tuple[str, list[str]]]:
    lines = prose.splitlines()
    tables: list[tuple[str, list[str]]] = []
    for index in range(1, len(lines)):
        if not TABLE_SEPARATOR_PATTERN.match(lines[index].strip()):
            continue
        header = lines[index - 1].strip()
        if not header.startswith("|"):
            continue
        rows: list[str] = []
        row_index = index + 1
        while row_index < len(lines) and lines[row_index].strip().startswith("|"):
            rows.append(lines[row_index].strip())
            row_index += 1
        tables.append((header, rows))
    return tables


def is_closure_navigation_header(header: str) -> bool:
    return all(any(term in header for term in group) for group in CLOSURE_HEADER_GROUPS)


def validate_closure_navigation(prose: str, sections: list[tuple[str, str]]) -> list[str]:
    errors: list[str] = []
    closure_tables = [
        (header, rows)
        for header, rows in markdown_tables(prose)
        if is_closure_navigation_header(header)
    ]
    if not closure_tables or not any(rows for _, rows in closure_tables):
        errors.append("缺少包含数据行的闭环导航表")
    if len(closure_tables) > 1:
        errors.append("闭环导航表只能包含一张")
    for header, rows in closure_tables:
        acceptance_indexes = [
            index for index, cell in enumerate(table_cells(header)) if "验收" in cell
        ]
        for row in rows:
            identifiers = set(CLOSURE_ID_PATTERN.findall(row))
            cells = table_cells(row)
            if any(not cell.strip() for cell in cells):
                errors.append(f"闭环导航行单元格不能为空: {row[:60]}")
            if not cells or not re.match(
                r"[`*_~]*FLOW-\d{2,}(?![A-Za-z0-9_])", cells[0].strip()
            ):
                errors.append(f"闭环导航行首列必须以 FLOW 编号开头: {row[:60]}")
            if not any(identifier.startswith("FLOW-") for identifier in identifiers) or not any(
                identifier.startswith("AC-") for identifier in identifiers
            ):
                errors.append(f"闭环导航行必须同时引用 FLOW 和 AC: {row[:60]}")
            if acceptance_indexes and not any(
                index < len(cells)
                and any(
                    identifier.startswith("AC-")
                    for identifier in CLOSURE_ID_PATTERN.findall(cells[index])
                )
                for index in acceptance_indexes
            ):
                errors.append(f"闭环导航行必须在验收列引用 AC: {row[:60]}")

    definitions = CLOSURE_DEFINITION_PATTERN.findall(prose)
    for identifier, count in sorted(Counter(definitions).items()):
        if count > 1:
            errors.append(f"闭环编号重复定义: {identifier}")

    defined_identifiers = set(definitions)
    for identifier in sorted(set(CLOSURE_ID_PATTERN.findall(prose)) - defined_identifiers):
        errors.append(f"闭环引用未定义: {identifier}")

    section_map: dict[str, str] = {}
    for heading, body in sections:
        identifier_match = CLOSURE_ID_PATTERN.match(heading)
        if identifier_match:
            section_map[identifier_match.group(0)] = body
    for identifier in sorted(defined_identifiers):
        if not has_meaningful_content(section_map.get(identifier, "")):
            errors.append(f"闭环定义内容为空: {identifier}")
    return errors


def obsidian_link_targets(markdown: str) -> set[str]:
    targets: set[str] = set()
    for link in OBSIDIAN_LINK_PATTERN.findall(markdown):
        target = link.split("|", 1)[0].split("#", 1)[0].split("^", 1)[0].strip()
        if target:
            targets.add(target)
    return targets


def validate_document(path: Path, expected_mode: str | None = None) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8").removeprefix("\ufeff")
    try:
        frontmatter, body = split_frontmatter(text)
    except ValueError as error:
        return [str(error)]

    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.search(frontmatter):
            errors.append("Frontmatter 存在未替换占位符")
            break

    for key in REQUIRED_FRONTMATTER:
        values = top_level_values(frontmatter, key)
        if not values:
            errors.append(f"缺少 Frontmatter 字段: {key}")
        elif len(values) > 1:
            errors.append(f"Frontmatter 顶层字段重复: {key}")

    for key in REQUIRED_SCALAR_FRONTMATTER:
        values = top_level_values(frontmatter, key)
        if values and is_yaml_null_scalar(values[0]):
            errors.append(f"Frontmatter 字段不能为空: {key}")

    mode = scalar_value(frontmatter, "design_mode")
    if mode not in {"backend", "fullstack"}:
        errors.append("design_mode 必须为 backend 或 fullstack")
    if expected_mode and mode != expected_mode:
        errors.append(f"design_mode={mode} 与期望模式 {expected_mode} 不一致")
    if scalar_value(frontmatter, "maturity") != "ready-for-implementation-design":
        errors.append("maturity 必须为 ready-for-implementation-design")
    if scalar_value(frontmatter, "status") != "ready":
        errors.append("status 必须为 ready")

    tags = {
        value.strip().strip("\"'")
        for value in re.findall(r"(?m)^\s+-\s+([^\n]+)$", list_block(frontmatter, "tags"))
    }
    if "detailed-design" not in tags:
        errors.append("tags 必须包含 detailed-design")
    if mode and mode not in tags:
        errors.append(f"tags 必须包含设计模式 {mode}")

    body_without_comments = strip_html_comments(body)
    prose = strip_fenced_code(body_without_comments)
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.search(prose):
            errors.append("正文存在未替换占位符")
            break
    if any(marker in prose for marker in TEMPLATE_ONLY_MARKERS):
        errors.append("成熟文档仍包含模板编写说明")
    structural_prose = prose
    frontmatter_title = scalar_value(frontmatter, "title")
    body_titles = re.findall(r"(?m)^#(?!#)\s+(.+?)\s*$", structural_prose)
    if len(body_titles) != 1:
        errors.append("正文一级标题必须存在且只能包含一个")
    elif body_titles[0].strip() != frontmatter_title:
        errors.append("正文一级标题必须存在并与 Frontmatter title 一致")
    if not validate_fences(body_without_comments):
        errors.append("Markdown 代码块未闭合")
    errors.extend(validate_tables(structural_prose))

    sections = markdown_sections(structural_prose)
    for group in REQUIRED_SECTION_GROUPS:
        matching_sections = [
            section_body
            for heading, section_body in sections
            if any(term in heading for term in group)
        ]
        if not matching_sections:
            errors.append(f"缺少必需章节语义: {'/'.join(group)}")
        elif not any(has_meaningful_content(section_body) for section_body in matching_sections):
            errors.append(f"必需章节内容为空: {'/'.join(group)}")
    errors.extend(validate_closure_navigation(structural_prose, sections))
    if mode == "fullstack":
        frontend_h2_headings = {
            match.group(2).strip()
            for match in HEADING_PATTERN.finditer(structural_prose)
            if len(match.group(1)) == 2 and "前端" in match.group(2)
        }
        frontend_sections = [
            section_body
            for heading, section_body in sections
            if heading in frontend_h2_headings
        ]
        if not frontend_sections:
            errors.append("全栈设计缺少 H2 前端设计章节")
        elif not any(has_meaningful_content(section_body) for section_body in frontend_sections):
            errors.append("全栈设计的前端设计章节内容为空")
    if any(
        any(term in heading for term in ("待确认", "当前缺口"))
        and not heading.startswith(("已校正", "已确认", "校正记录"))
        for heading, _ in sections
    ):
        errors.append("成熟文档仍包含待确认或当前缺口章节")

    related_block = list_block(frontmatter, "related")
    related_links = obsidian_link_targets(related_block)
    body_links = obsidian_link_targets(structural_prose)
    for link in sorted(body_links - related_links):
        errors.append(f"正文双链未登记到 related: {link}")
    for link in sorted(related_links - body_links):
        errors.append(f"related 双链在正文未使用: {link}")
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
