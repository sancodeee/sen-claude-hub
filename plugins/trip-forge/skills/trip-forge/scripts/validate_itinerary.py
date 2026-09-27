#!/usr/bin/env python3
"""Validate the itinerary contract of a generated TripForge HTML report."""

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


HEADERS = ("时段", "安排", "天气依赖", "建议交通", "耗时/游玩", "人流提示", "雨天替代")
TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "report-template.html"


class Element:
    def __init__(self, tag, attrs):
        self.tag = tag
        self.attrs = dict(attrs)
        self.children = []
        self.content = []

    def has_class(self, name):
        return name in self.attrs.get("class", "").split()

    def descendants(self, tag=None, class_name=None):
        for child in self.children:
            if (tag is None or child.tag == tag) and (class_name is None or child.has_class(class_name)):
                yield child
            yield from child.descendants(tag, class_name)

    def text(self):
        return "".join(part if isinstance(part, str) else part.text() for part in self.content)


class Document(HTMLParser):
    VOID_TAGS = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Element("document", [])
        self.stack = [self.root]
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        element = Element(tag, attrs)
        self.stack[-1].children.append(element)
        self.stack[-1].content.append(element)
        if tag not in self.VOID_TAGS:
            self.stack.append(element)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        self.stack[-1].content.append(data)


def one(elements):
    return elements[0] if len(elements) == 1 else None


def direct_child(parent, tag=None, class_name=None):
    return [child for child in parent.children if (tag is None or child.tag == tag) and (class_name is None or child.has_class(class_name))]


def is_only_match(root, element, class_name):
    return element is not None and list(root.descendants(class_name=class_name)) == [element]


def check_day(day, index, errors):
    prefix = f"第 {index} 张日卡"
    date = day.attrs.get("data-date", "").strip()
    label = day.attrs.get("data-label", "").strip()
    if not re.fullmatch(r"\d{1,2}/\d{1,2}", date):
        errors.append(f"{prefix} data-date 应为月/日，例如 09/27")
    if not label or "{{" in label:
        errors.append(f"{prefix} 缺少有效 data-label")
    if not one(list(day.descendants(class_name="itinerary-day-number"))):
        errors.append(f"{prefix} 缺少 .itinerary-day-number")
    if not one(list(day.descendants(tag="h3"))):
        errors.append(f"{prefix} 缺少唯一的 h3 日期主题")

    table = one(list(day.descendants(tag="table")))
    if table is None or not table.has_class("itinerary-table"):
        errors.append(f"{prefix} 缺少唯一的 table.itinerary-table")
        return date
    headings = [heading.text().strip() for heading in table.descendants(tag="th")]
    if tuple(headings) != HEADERS:
        errors.append(f"{prefix} 行程表须保留七列：{' / '.join(HEADERS)}")
    body = one(list(table.descendants(tag="tbody")))
    if body is None:
        errors.append(f"{prefix} 行程表缺少 tbody")
        return date
    rows = direct_child(body, tag="tr")
    if not rows:
        errors.append(f"{prefix} 行程表没有时间行")
    meals = set()
    for row in rows:
        cells = direct_child(row, tag="td")
        if len(cells) != 7:
            errors.append(f"{prefix} 每个时间行必须有七个单元格")
            continue
        slot = cells[0].text().strip()
        if slot in {"午餐", "晚餐"}:
            meals.add(slot)
            if not row.has_class("meal"):
                errors.append(f"{prefix} {slot}行缺少 meal 类名")
    if meals != {"午餐", "晚餐"}:
        errors.append(f"{prefix} 必须分别有午餐和晚餐时间行")
    return date


def validate(report_html, expected_days, template_html):
    document = Document(report_html).root
    template = Document(template_html).root
    errors = []
    all_itineraries = [node for node in document.descendants() if "data-itinerary" in node.attrs]
    if len(all_itineraries) != 1:
        errors.append("整份报告必须有唯一的 data-itinerary 行程根节点")
    sections = [section for section in document.descendants(tag="section") if section.attrs.get("id") == "d1"]
    section = one(sections)
    if section is None:
        errors.append("必须有唯一的 #d1 行程章节")
    else:
        itineraries = [node for node in section.descendants() if "data-itinerary" in node.attrs and node.has_class("itinerary")]
        itinerary = one(itineraries)
        if itinerary is None:
            errors.append("#d1 必须有唯一的 .itinerary[data-itinerary]，不可使用旧式逐日普通表格")
        else:
            if set(itinerary.attrs.get("class", "").split()) != {"itinerary"} or "style" in itinerary.attrs or "hidden" in itinerary.attrs:
                errors.append("行程根初始状态只能有 itinerary 类名，且不能带内联样式或 hidden")
            controls = {
                "工具栏": ("div", "itinerary-toolbar"),
                "日期导航": ("nav", "itinerary-nav"),
                "日卡容器": ("div", "itinerary-days"),
                "翻页控件": ("div", "itinerary-pager"),
            }
            for name, (tag, class_name) in controls.items():
                direct = one(direct_child(itinerary, tag, class_name))
                if not is_only_match(itinerary, direct, class_name):
                    errors.append(f"行程区缺少唯一的{name} .{class_name}")
            toolbar = one(direct_child(itinerary, "div", "itinerary-toolbar"))
            pager = one(direct_child(itinerary, "div", "itinerary-pager"))
            if toolbar is not None:
                expand = one(list(toolbar.descendants(tag="button", class_name="itinerary-expand")))
                if not is_only_match(itinerary, expand, "itinerary-expand"):
                    errors.append("工具栏缺少唯一的 button.itinerary-expand")
            if pager is not None:
                for class_name in ("itinerary-prev", "itinerary-next"):
                    button = one(list(pager.descendants(tag="button", class_name=class_name)))
                    if not is_only_match(itinerary, button, class_name):
                        errors.append(f"翻页控件缺少唯一的 button.{class_name}")
                position = one(list(pager.descendants(class_name="itinerary-position")))
                if not is_only_match(itinerary, position, "itinerary-position") or not one(list(position.descendants(tag="strong"))):
                    errors.append("翻页控件缺少 .itinerary-position strong 页码")
            deck = one(direct_child(itinerary, "div", "itinerary-days"))
            if deck is not None:
                if set(deck.attrs.get("class", "").split()) != {"itinerary-days"} or "style" in deck.attrs or "hidden" in deck.attrs:
                    errors.append("日卡容器只能有 itinerary-days 类名，不能用内联样式或 hidden 覆盖横滑布局")
                days = direct_child(deck, "article", "itinerary-day")
                if len(days) != expected_days or len(deck.children) != len(days):
                    errors.append(f"日卡数量应为 {expected_days}，且每一天须是 .itinerary-days 的直接 article.itinerary-day 子元素；实际为 {len(days)}")
                if list(deck.descendants(class_name="itinerary-day")) != days:
                    errors.append("日卡内部不能嵌套或额外使用 .itinerary-day，脚本会把它误认为另一天")
                for index, day in enumerate(days, 1):
                    if set(day.attrs.get("class", "").split()) != {"itinerary-day"} or "style" in day.attrs or "hidden" in day.attrs:
                        errors.append(f"第 {index} 张日卡不能用内联样式、hidden 或额外状态类覆盖横滑布局")
                dates = [check_day(day, index, errors) for index, day in enumerate(days, 1)]
                if len(set(dates)) != len(dates):
                    errors.append("日卡 data-date 不可重复")
                card_tables = {id(table) for day in days for table in day.descendants(tag="table")}
                if any(id(table) not in card_tables for table in section.descendants(tag="table")):
                    errors.append("#d1 存在日卡外的旧式纵向表格")

    styles = list(document.descendants(tag="style"))
    template_style = one(list(template.descendants(tag="style")))
    if len(styles) != 1 or styles[0].attrs != template_style.attrs or styles[0].text().strip() != template_style.text().strip():
        errors.append("行程横滑样式须原样保留模板中的完整内联 <style>")
    scripts = list(document.descendants(tag="script"))
    template_script = one(list(template.descendants(tag="script")))
    if len(scripts) != 1 or scripts[0].attrs != template_script.attrs or scripts[0].text().strip() != template_script.text().strip():
        errors.append("行程初始化内联脚本须原样保留模板中的完整 <script>")
    else:
        body = one(list(document.descendants(tag="body")))
        if body is None or not body.children or body.children[-1] is not scripts[0]:
            errors.append("行程初始化内联脚本必须放在静态正文之后，作为 body 最后的元素")
    return errors


def main():
    parser = argparse.ArgumentParser(description="检查 TripForge 报告的横滑行程区")
    parser.add_argument("report", type=Path, help="待检查的 HTML 报告")
    parser.add_argument("--days", type=int, required=True, help="用户要求的行程天数")
    args = parser.parse_args()
    if args.days < 1:
        parser.error("--days 必须大于 0")
    try:
        report_html = args.report.read_text(encoding="utf-8")
        template_html = TEMPLATE.read_text(encoding="utf-8")
    except OSError as error:
        print(f"无法读取文件：{error}", file=sys.stderr)
        return 2
    errors = validate(report_html, args.days, template_html)
    if errors:
        for error in errors:
            print(f"✗ {error}", file=sys.stderr)
        return 1
    print(f"✓ 行程区结构通过：{args.days} 张日卡，模板样式与脚本完整")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
