"""Regression checks for the generated itinerary layout gate."""

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL_DIR / "assets" / "report-template.html"
VALIDATOR = SKILL_DIR / "scripts" / "validate_itinerary.py"


def report_with_days(day_count):
    template = TEMPLATE.read_text(encoding="utf-8")
    match = re.search(r'<article class="itinerary-day".*?</article>', template, re.DOTALL)
    if match is None:
        raise AssertionError("The template has no itinerary day fixture")
    day = match.group()
    cards = []
    for index in range(day_count):
        card = day.replace('data-date="{{月/日}}"', f'data-date="09/{index + 1:02d}"')
        card = card.replace('data-label="{{当天短主题}}"', f'data-label="第{index + 1}天"')
        cards.append(card)
    report = template[:match.start()] + "\n".join(cards) + template[match.end():]
    return re.sub(r"{{[^{}]*}}", "示例", report)


def run_validator(report, days):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "report.html"
        path.write_text(report, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(path), "--days", str(days)],
            capture_output=True,
            text=True,
            check=False,
        )


class ItineraryValidationTests(unittest.TestCase):
    def test_accepts_template_based_multi_day_cards(self):
        result = run_validator(report_with_days(2), 2)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_accepts_nested_markup_without_changing_column_text(self):
        report = report_with_days(2).replace('<th scope="col">天气依赖</th>', '<th scope="col"><span>天气</span>依赖</th>')
        result = run_validator(report, 2)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_rejects_legacy_vertical_tables(self):
        report = '<section id="d1"><h3>Day 1</h3><div class="tbl-wrap"><table><tr><td>上午</td></tr></table></div></section>'
        result = run_validator(report, 2)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("data-itinerary", result.stderr)

    def test_rejects_missing_inline_itinerary_script(self):
        report = re.sub(r"<script>.*?</script>", "", report_with_days(2), flags=re.DOTALL)
        result = run_validator(report, 2)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("内联脚本", result.stderr)

    def test_rejects_missing_horizontal_layout_style(self):
        report = report_with_days(2).replace(
            ".itinerary.is-ready:not(.is-expanded) .itinerary-days{display:flex;",
            ".itinerary.is-ready:not(.is-expanded) .itinerary-days{display:grid;",
        )
        result = run_validator(report, 2)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("样式", result.stderr)

    def test_rejects_wrong_day_count(self):
        result = run_validator(report_with_days(2), 3)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("日卡数量", result.stderr)

    def test_rejects_extra_plain_table_inside_day_card(self):
        report = report_with_days(2).replace("</article>", "<table><tr><td>旧式行程</td></tr></table></article>", 1)
        result = run_validator(report, 2)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("唯一的 table.itinerary-table", result.stderr)

    def test_rejects_nested_day_class_that_breaks_script_initialization(self):
        report = report_with_days(2).replace("</article>", '<div class="itinerary-day"></div></article>', 1)
        result = run_validator(report, 2)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("嵌套", result.stderr)

    def test_rejects_duplicate_deck_before_real_day_cards(self):
        report = report_with_days(2).replace('<div class="itinerary-toolbar" hidden>', '<div class="itinerary-toolbar" hidden><div class="itinerary-days"></div>', 1)
        result = run_validator(report, 2)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("itinerary-days", result.stderr)

    def test_rejects_duplicate_pager_before_real_controls(self):
        report = report_with_days(2).replace('<div class="itinerary-toolbar" hidden>', '<div class="itinerary-toolbar" hidden><div class="itinerary-pager"></div>', 1)
        result = run_validator(report, 2)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("itinerary-pager", result.stderr)

    def test_rejects_wrong_tag_deck_before_real_day_cards(self):
        report = report_with_days(2).replace('<div class="itinerary-toolbar" hidden>', '<div class="itinerary-toolbar" hidden><span class="itinerary-days"></span>', 1)
        result = run_validator(report, 2)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("itinerary-days", result.stderr)

    def test_rejects_wrong_tag_pager_before_real_controls(self):
        report = report_with_days(2).replace('<div class="itinerary-toolbar" hidden>', '<div class="itinerary-toolbar" hidden><span class="itinerary-pager"></span>', 1)
        result = run_validator(report, 2)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("itinerary-pager", result.stderr)

    def test_rejects_missing_expand_button(self):
        report = re.sub(r'<button type="button" class="itinerary-expand".*?</button>', "", report_with_days(2))
        result = run_validator(report, 2)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("itinerary-expand", result.stderr)

    def test_rejects_missing_previous_button(self):
        report = re.sub(r'<button type="button" class="itinerary-prev".*?</button>', "", report_with_days(2))
        result = run_validator(report, 2)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("itinerary-prev", result.stderr)

    def test_rejects_non_executable_script(self):
        report = report_with_days(2).replace("<script>", '<script type="text/plain">')
        result = run_validator(report, 2)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("内联脚本", result.stderr)

    def test_rejects_print_only_style(self):
        report = report_with_days(2).replace("<style>", '<style media="print">')
        result = run_validator(report, 2)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("样式", result.stderr)

    def test_rejects_extra_itinerary_root_before_day_cards(self):
        report = report_with_days(2).replace('<section id="d1">', '<div class="itinerary" data-itinerary></div><section id="d1">')
        result = run_validator(report, 2)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("data-itinerary", result.stderr)

    def test_rejects_initially_expanded_day_cards(self):
        report = report_with_days(2).replace('<div class="itinerary" data-itinerary>', '<div class="itinerary is-expanded" data-itinerary>')
        result = run_validator(report, 2)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("初始状态", result.stderr)

    def test_rejects_inline_layout_override_on_day_deck(self):
        report = report_with_days(2).replace('<div class="itinerary-days">', '<div class="itinerary-days" style="display:block">')
        result = run_validator(report, 2)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("内联样式", result.stderr)

    def test_rejects_script_before_day_cards(self):
        report = report_with_days(2)
        script = re.search(r"<script>.*?</script>", report, re.DOTALL).group()
        report = report.replace(script, "").replace('<section id="d1">', '<section id="d1">' + script)
        result = run_validator(report, 2)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("静态正文之后", result.stderr)


if __name__ == "__main__":
    unittest.main()
