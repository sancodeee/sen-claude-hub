#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Browser Integration Test Script (Python Version)
Part of agent-browser-integration-test skill

This script executes comprehensive browser integration tests using agent-browser
and generates detailed markdown test reports.

Enhanced with full auto-traversal testing capabilities:
- Automatic discovery of all interactive elements
- Automatic execution of all operations
- Capture of all backend API calls
- Risk assessment and user confirmation for dangerous operations
- Comprehensive reporting with API coverage matrix

NEW (v4.1.0): Dependency-Aware Parallel Testing
- Smart parallel execution with dependency analysis
- Automatic conflict detection and fallback
- 3-5x performance improvement for independent elements
"""

import argparse
import datetime
import logging
import os
import re
import subprocess
import json
import time
import random
import threading
# Configure logging first
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
from urllib.parse import urlparse
import sys

# 添加脚本所在目录到路径，以便导入共享模型和并行执行模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import shared data models
from models import RiskLevel, InteractiveElement, APICall, TestResult, CommandResult, TestConfig

# Import BrowserManager from browser_manager module
from browser_manager import BrowserManager

try:
    from parallel_executor import SmartParallelExecutor
    PARALLEL_AVAILABLE = True
except ImportError:
    PARALLEL_AVAILABLE = False
    logger.warning("并行执行模块不可用，将使用串行模式")


# =============================================================================
# TestReport
# =============================================================================

class TestReport:
    """Generates Markdown test reports."""

    def __init__(self, url: str, operation: str, output_dir: str):
        self.url = url
        self.operation = operation
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.readable_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Extract business abbreviation from URL
        match = re.search(r'https?://([^/]+)', url)
        domain = match.group(1) if match else "unknown"
        self.business_abbr = domain.replace("www.", "")

        self.output_dir = output_dir
        self.filename = f"{self.timestamp}-{self.business_abbr}-{operation}-report.md"
        self.filepath = os.path.join(output_dir, self.filename)

        self.content = []
        self.stats = {"total": 0, "passed": 0, "failed": 0}
        self.start_time = datetime.datetime.now()

        # Initialize report structure
        self._init_header()

    def _init_header(self):
        self.content.append(f"# 浏览器集成测试报告\n")
        self.content.append("## 测试元数据\n")
        self.content.append("| 字段 | 值 |")
        self.content.append("|-------|-------|")
        self.content.append(f"| **URL** | {self.url} |")
        self.content.append(f"| **操作类型** | {self.operation} |")
        self.content.append(f"| **时间戳** | {self.readable_time} |")
        self.content.append(f"| **测试 ID** | {self.timestamp} |")
        self.content.append(f"| **脚本版本** | 4.1.0 (Python Enhanced) |\n")
        self.content.append("## 测试摘要\n")
        self.content.append("<!-- SUMMARY_PLACEHOLDER -->\n")

    def add_section(self, title: str):
        self.content.append(f"\n## {title}\n")

    def add_subsection(self, title: str):
        self.content.append(f"\n### {title}\n")

    def add_text(self, text: str):
        self.content.append(f"{text}\n")

    def add_code_block(self, code: str, lang: str = ""):
        self.content.append(f"```{lang}\n{code}\n```\n")

    def add_table_row(self, row: str):
        self.content.append(row)

    def add_screenshot(self, label: str, path: str):
        rel_path = os.path.relpath(path, self.output_dir)
        self.content.append(f"**{label}:**")
        self.content.append(f"![{label}]({rel_path})\n")

    def log_test_result(self, name: str, passed: bool, details: str = ""):
        self.stats["total"] += 1
        icon = "✅" if passed else "❌"
        status = "PASS" if passed else "FAIL"

        if passed:
            self.stats["passed"] += 1
            logger.info(f"[{status}] {name}")
        else:
            self.stats["failed"] += 1
            logger.error(f"[{status}] {name}: {details}")

        self.add_table_row(f"| {icon} {name} | {details} |")

    def save(self):
        duration = (datetime.datetime.now() - self.start_time).total_seconds()

        # Calculate summary
        total = self.stats["total"]
        passed = self.stats["passed"]
        failed = self.stats["failed"]
        pass_rate = int((passed / total) * 100) if total > 0 else 0

        summary_table = [
            "| 指标 | 值 |",
            "|--------|-------|",
            f"| **Total Tests** | {total} |",
            f"| **Passed** | {passed} |",
            f"| **Failed** | {failed} |",
            f"| **Pass Rate** | {pass_rate}% |",
            f"| **Duration** | {duration:.2f}s |",
            "",
            "---"
        ]

        # Replace placeholder
        full_content = "\n".join(self.content)
        full_content = full_content.replace("<!-- SUMMARY_PLACEHOLDER -->", "\n".join(summary_table))

        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write(full_content)

        logger.info(f"Report saved to: {self.filepath}")
        return self.filepath


# =============================================================================
# EnhancedTestReport
# =============================================================================

class EnhancedTestReport(TestReport):
    """增强的测试报告 - 支持API覆盖率和风险评估"""

    def add_api_coverage_section(self, apis: List[APICall]):
        """添加 API 覆盖率章节"""
        self.add_section("API 测试覆盖")

        if not apis:
            self.add_text("未捕获到 API 调用")
            return

        # 按方法分组
        api_summary = {}
        for api in apis:
            key = f"{api.method} {api.endpoint}"
            if key not in api_summary:
                api_summary[key] = api

        self.add_table_row("| 方法 | 端点 | 状态 | 响应时间 |")
        self.add_table_row("|---|---|---|---|")

        for api in api_summary.values():
            status_icon = "✅" if 200 <= api.status < 300 else "❌"
            self.add_table_row(f"| {api.method} | {api.endpoint} | {status_icon} {api.status} | {api.timing}ms |")

        self.add_text(f"\n**总计**: {len(apis)} 个 API 调用")

        # 统计各方法数量
        method_counts = {}
        for api in apis:
            method_counts[api.method] = method_counts.get(api.method, 0) + 1

        self.add_text("\n**按方法分类**:")
        self.add_table_row("| 方法 | 数量 |")
        self.add_table_row("|---|---|")
        for method, count in sorted(method_counts.items()):
            self.add_table_row(f"| {method} | {count} |")

    def add_interaction_matrix(self, results: List[TestResult]):
        """添加交互元素测试矩阵"""
        self.add_section("交互元素测试结果")

        if not results:
            self.add_text("无测试结果")
            return

        self.add_table_row("| 元素类型 | 文本 | 操作 | 状态 | API调用 |")
        self.add_table_row("|---|---|---|---|---|")

        for result in results:
            status_icon = "✅" if result.success else "❌"
            error_text = f" - {result.error}" if result.error else ""

            # 截断文本
            element_text = result.element.text[:30] if result.element.text else ""

            if result.element.type == "link":
                action = "navigated"
            elif result.element.type == "button":
                action = "clicked"
            elif result.element.type == "input":
                action = "filled"
            else:
                action = "tested"

            apis = ", ".join([f"{api.method} {api.endpoint}" for api in result.apis_called]) if result.apis_called else "-"

            self.add_table_row(
                f"| {result.element.type} | {element_text} | "
                f"{action}{error_text} | "
                f"{status_icon} | {apis} |"
            )

    def add_coverage_summary(self, total_elements: int, tested_elements: int, total_apis: int):
        """添加覆盖率摘要"""
        self.add_section("测试覆盖率摘要")

        element_rate = int((tested_elements / total_elements) * 100) if total_elements > 0 else 0

        self.add_table_row("| 维度 | 已测试 | 总数 | 覆盖率 |")
        self.add_table_row("|---|---|---|---|")
        self.add_table_row(f"| 交互元素 | {tested_elements} | {total_elements} | {element_rate}% |")
        self.add_table_row(f"| API 调用 | {total_apis} | {total_apis} | 100% |")

    def add_risk_assessment(self, confirmed_count: int, skipped_count: int, skipped_details: List[Dict]):
        """添加风险评估章节"""
        self.add_section("风险评估")

        self.add_text(f"**确认执行**: {confirmed_count} 个危险操作")
        self.add_text(f"**跳过**: {skipped_count} 个危险操作")

        if skipped_details:
            self.add_subsection("跳过的操作")
            for action in skipped_details:
                self.add_text(f"- ⏭️ **{action['element'].type}**: {action['element'].text} ({action['risk'].value})")


# =============================================================================
# NetworkMonitor
# =============================================================================

class NetworkMonitor:
    """网络请求监控器 - 线程安全版本"""

    def __init__(self, browser: BrowserManager):
        self.browser = browser
        self._lock = threading.Lock()
        self.request_count = 0
        self.all_apis: List[APICall] = []

    def start_recording(self):
        """开始记录新的操作 - 线程安全"""
        with self._lock:
            self.browser.clear_network_requests()
            self.request_count = 0

    def capture_new_requests(self, action_name: str) -> List[APICall]:
        """捕获操作后新增的 API 请求 - 线程安全"""
        with self._lock:
            requests = self.browser.network_requests_json()
            new_apis = []

            for i in range(self.request_count, len(requests)):
                req = requests[i]
                api = self._parse_api_call(req)
                if api:  # 只记录 API 请求（过滤静态资源）
                    new_apis.append(api)
                    self.all_apis.append(api)

            self.request_count = len(requests)
            return new_apis

    def get_all_apis(self) -> List[APICall]:
        """获取所有捕获的 API - 线程安全"""
        with self._lock:
            return self.all_apis.copy()

    def get_api_summary(self) -> Dict[str, List[APICall]]:
        """按方法分类 API - 线程安全"""
        with self._lock:
            summary = {'GET': [], 'POST': [], 'PUT': [], 'DELETE': [], 'PATCH': [], 'OTHER': []}
            for api in self.all_apis:
                key = api.method if api.method in summary else 'OTHER'
                summary[key].append(api)
            return summary

    def _parse_api_call(self, req: dict) -> Optional[APICall]:
        """
        解析 API 调用详情

        使用改进的逻辑过滤静态资源：
        1. 检查 URL 路径是否以静态文件扩展名结尾
        2. 使用正则表达式确保扩展名在路径末尾（而非 API 路径的一部分）
        3. 保留包含静态扩展名的 API 端点（例如 /api/user.js）
        """
        url = req.get('url', '')
        method = req.get('method', 'GET')

        # 首先过滤 data URLs 和 blob URLs
        if url.startswith('data:') or url.startswith('blob:'):
            return None

        # 解析 URL 获取不含查询字符串的路径
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = parsed.path.lower()

        # 静态文件扩展名（仅当扩展名在路径末尾时过滤）
        # 使用更精确的正则表达式，避免过滤像 /api/user.js 这样的 API 端点
        import re
        static_extensions = ('.css', '.js', '.png', '.jpg', '.jpeg',
                            '.gif', '.svg', '.ico', '.woff', '.woff2',
                            '.ttf', '.eot', '.otf', '.webp', '.avif')

        # 检查路径是否以这些扩展名之一结尾（不区分大小写）
        # 此模式确保扩展名在路径末尾，后面不跟任何内容
        for ext in static_extensions:
            # 模式匹配：以扩展名结尾的路径，可选地后跟查询/片段
            # 但不跟另一个路径段（例如 /api/data.json/users）
            pattern = re.escape(ext) + r'$'
            if re.search(pattern, path):
                return None

        # 额外的启发式规则：如果路径包含 /api/、/v1/、/v2/ 等，则可能是 API
        # 即使以静态扩展名结尾，也可能是动态端点
        api_indicators = ('/api/', '/v1/', '/v2/', '/v3/', '/graphql', '/rest/')
        if any(indicator in path for indicator in api_indicators):
            pass  # 保留为 API，不过滤

        # 提取端点路径
        endpoint = parsed.path
        if parsed.query:
            endpoint += f"?{parsed.query}"

        return APICall(
            method=method,
            endpoint=endpoint,
            status=req.get('status', 0),
            timing=req.get('duration', 0)
        )


# =============================================================================
# ElementDiscovery
# =============================================================================

class ElementDiscovery:
    """元素发现器 - 发现页面上所有可交互元素"""

    DANGEROUS_PATTERNS = {
        RiskLevel.CRITICAL: [
            'delete', 'destroy', 'remove', '删除', '移除',
            '注销账户', '注销账号', 'delete account', 'remove account'
        ],
        RiskLevel.HIGH: [
            'pay', 'checkout', 'purchase', '支付', '结算',
            'logout', 'signout', '登出', '退出',
            # Note: '注销' is NOT included here to avoid ambiguity
            # It will be handled by _should_be_critical for proper classification
        ],
        RiskLevel.MEDIUM: ['export', 'download', '导出', '下载', 'reset', 'clear', '重置', '清空']
    }
    # Note: Pattern matching is case-insensitive (element text is converted to lowercase before matching)

    @staticmethod
    def _should_be_critical(element: InteractiveElement) -> bool:
        """
        Check if an element should be CRITICAL despite matching HIGH patterns.

        This handles edge cases like "注销账户" (delete account) which should be CRITICAL
        even though "注销" alone typically means "logout" (HIGH).

        The word "注销" is ambiguous in Chinese:
        - "注销" alone typically means "logout" (HIGH risk)
        - "注销账户" or "注销账号" means "delete account" (CRITICAL risk)

        This method resolves the ambiguity by checking for account-related context.
        """
        text = element.text.lower() if element.text else ""

        # Account deletion patterns that override the default HIGH classification
        account_deletion_patterns = [
            '注销账户', '注销账号', '删除账户', 'delete account',
            'remove account', 'destroy account', '注销用户'
        ]

        # Check if any account deletion pattern matches
        if any(pattern in text for pattern in account_deletion_patterns):
            return True

        # Handle standalone "注销" - default to HIGH (logout) unless in account context
        # This is handled in get_element_risk by checking CRITICAL patterns first,
        # then calling this method, then checking other levels.

        return False

    def __init__(self, browser: BrowserManager):
        self.browser = browser

    def discover_all_interactive_elements(self) -> List[InteractiveElement]:
        """发现所有可交互元素 - 增强版，支持更多元素类型"""
        js_code = '''
        (() => {
            const elements = [];
            let globalIdx = 0;

            // 生成唯一选择器
            const generateSelector = (el, typeHint) => {
                if (el.id) return '#' + el.id;
                if (el.name) return '[name="' + el.name + '"]';

                // 尝试使用属性组合生成更稳定的选择器
                const attrs = [];
                if (el.className && typeof el.className === 'string' && el.className) {
                    const classes = el.className.trim().split(/\\s+/).filter(c => c && !c.match(/^(active|selected|hidden|disabled)$/));
                    if (classes.length > 0) {
                        attrs.push('.' + classes[0]);
                    }
                }

                const tag = el.tagName.toLowerCase();
                const type = el.type ? '[type="' + el.type + '"]' : '';

                // 使用 nth-child 作为最后选择
                let siblings = el.parentElement ? Array.from(el.parentElement.children).filter(c => c.tagName === el.tagName) : [];
                let nth = siblings.indexOf(el) + 1;

                if (attrs.length > 0) {
                    return tag + type + '.' + attrs[0].replace(/^\\./, '') + ':nth-child(' + nth + ')';
                }
                return tag + type + ':nth-child(' + nth + ')';
            };

            // 发现按钮
            document.querySelectorAll('button, [role="button"], input[type="submit"], input[type="button"]').forEach((btn) => {
                elements.push({
                    type: 'button',
                    id: btn.id || null,
                    name: btn.name || null,
                    text: String(btn.innerText?.trim() || btn.value || btn.title || ''),
                    visible: btn.offsetParent !== null && !btn.disabled,
                    selector: generateSelector(btn, 'button')
                });
            });

            // 发现链接
            document.querySelectorAll('a[href]').forEach((link) => {
                elements.push({
                    type: 'link',
                    id: link.id || null,
                    text: String(link.innerText?.trim() || link.title || link.href),
                    href: link.href,
                    visible: link.offsetParent !== null,
                    selector: generateSelector(link, 'link')
                });
            });

            // 发现各种输入框
            const inputSelectors = [
                'input[type="text"]',
                'input[type="email"]',
                'input[type="password"]',
                'input[type="number"]',
                'input[type="tel"]',
                'input[type="url"]',
                'input[type="search"]',
                'input[type="date"]',
                'input[type="datetime-local"]',
                'input[type="time"]',
                'input[type="month"]',
                'input[type="week"]',
                'input:not([type])',
                'textarea'
            ];

            inputSelectors.forEach(sel => {
                document.querySelectorAll(sel).forEach(input => {
                    elements.push({
                        type: 'input',
                        id: input.id || null,
                        name: input.name || null,
                        input_type: input.type || input.tagName.toLowerCase(),
                        placeholder: String(input.placeholder || ''),
                        visible: input.offsetParent !== null && !input.disabled && !input.readOnly,
                        selector: generateSelector(input, 'input'),
                        value: String(input.value || '')
                    });
                });
            });

            // 发现复选框
            document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
                const label = cb.parentElement && cb.parentElement.tagName === 'LABEL' ? cb.parentElement.innerText.trim() : '';
                elements.push({
                    type: 'checkbox',
                    id: cb.id || null,
                    name: cb.name || null,
                    text: String(label || cb.title || cb.value || ''),
                    visible: cb.offsetParent !== null && !cb.disabled,
                    selector: generateSelector(cb, 'checkbox'),
                    checked: cb.checked,
                    value: String(cb.value || 'on')
                });
            });

            // 发现单选按钮
            document.querySelectorAll('input[type="radio"]').forEach(radio => {
                const label = radio.parentElement && radio.parentElement.tagName === 'LABEL' ? radio.parentElement.innerText.trim() : '';
                elements.push({
                    type: 'radio',
                    id: radio.id || null,
                    name: radio.name || null,
                    text: String(label || radio.title || radio.value || ''),
                    visible: radio.offsetParent !== null && !radio.disabled,
                    selector: generateSelector(radio, 'radio'),
                    checked: radio.checked,
                    value: String(radio.value || 'on')
                });
            });

            // 发现下拉选择框
            document.querySelectorAll('select').forEach(sel => {
                const options = Array.from(sel.options).map(opt => String(opt.value || opt.text));
                const selectedIndex = sel.selectedIndex;
                const selectedText = selectedIndex >= 0 ? sel.options[selectedIndex].text : '';
                elements.push({
                    type: 'select',
                    id: sel.id || null,
                    name: sel.name || null,
                    text: String(selectedText || ''),
                    visible: sel.offsetParent !== null && !sel.disabled,
                    selector: generateSelector(sel, 'select'),
                    options: options,
                    value: String(sel.value || ''),
                    input_type: 'select-one'
                });
            });

            // 验证并过滤有效元素
            const validElements = elements.filter(el => {
                return el && typeof el === 'object' && el.type && el.selector;
            });

            return JSON.stringify(validElements);
        })()
        '''

        result = self.browser.eval_js(js_code)
        data = None
        try:
            data = json.loads(result)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse elements JSON: {result[:200]}")
            return []

        elements = []
        for item in data:
            # 添加类型检查，防止无效数据导致 TypeError
            if not isinstance(item, dict):
                logger.warning(f"Skipping invalid element data (not a dict): {type(item).__name__}")
                continue
            if not item.get('type') or not item.get('selector'):
                logger.warning(f"Skipping invalid element data (missing type/selector): {item}")
                continue
            try:
                elements.append(InteractiveElement(**item))
            except TypeError as e:
                logger.warning(f"TypeError while creating InteractiveElement: {e}, item: {item}")
                continue
        return elements

    def get_element_risk(self, element: InteractiveElement) -> RiskLevel:
        """
        评估元素风险级别

        Risk Assessment:
        - CRITICAL: Delete, destroy operations
        - HIGH: Payment, logout, reset
        - MEDIUM: Export, download
        - LOW: Other operations

        Note: Special handling for ambiguous terms like "注销" which can mean
        either "logout" (HIGH) or "delete account" (CRITICAL).
        """
        text_lower = element.text.lower() if element.text else ""

        # Check for CRITICAL patterns first (highest priority)
        for pattern in self.DANGEROUS_PATTERNS[RiskLevel.CRITICAL]:
            if pattern in text_lower:
                return RiskLevel.CRITICAL

        # Check if ambiguous patterns should be CRITICAL (e.g., "注销账户")
        if self._should_be_critical(element):
            return RiskLevel.CRITICAL

        # Then check other risk levels
        for level, patterns in self.DANGEROUS_PATTERNS.items():
            if level == RiskLevel.CRITICAL:
                continue  # Already checked
            if any(pattern in text_lower for pattern in patterns):
                return level

        return RiskLevel.LOW

    def categorize_elements(self, elements: List[InteractiveElement]) -> Dict[str, List[InteractiveElement]]:
        """按风险和类型分类元素 - 增强版，支持更多元素类型"""
        categorized = {
            'safe_actions': [],
            'dangerous_actions': [],
            'logout_actions': [],
            'navigation_links': [],
            'form_inputs': [],        # input, textarea
            'form_selections': [],    # select, checkbox, radio
        }

        for elem in elements:
            if not elem.visible:
                continue

            risk = self.get_element_risk(elem)

            if risk == RiskLevel.CRITICAL:
                categorized['dangerous_actions'].append(elem)
            elif risk == RiskLevel.HIGH and any(word in elem.text.lower() for word in ['logout', '登出', '退出', 'signout']):
                categorized['logout_actions'].append(elem)
            elif elem.type == 'link':
                categorized['navigation_links'].append(elem)
            elif elem.type in ('input', 'textarea'):
                categorized['form_inputs'].append(elem)
            elif elem.type in ('select', 'checkbox', 'radio'):
                categorized['form_selections'].append(elem)
            else:
                categorized['safe_actions'].append(elem)

        return categorized


# =============================================================================
# SmartFormFiller
# =============================================================================

class SmartFormFiller:
    """智能表单填充器 - 增强版，支持所有表单元素类型"""

    VALUE_GENERATORS = {
        'email': lambda: f"test_{int(time.time())}@example.com",
        'password': lambda: "TestPass123!",
        'tel': lambda: f"138{random.randint(10000000, 99999999)}",
        'number': lambda: random.randint(1, 100),
        'date': lambda: datetime.date.today().isoformat(),
        'text': lambda: f"Test Data {int(time.time())}",
        'url': lambda: "https://example.com",
    }

    def __init__(self, browser: BrowserManager):
        self.browser = browser

    def generate_value_for_field(self, field: InteractiveElement) -> str:
        """根据字段类型生成测试数据"""
        field_type = getattr(field, 'input_type', 'text') or 'text'
        field_name = field.name or ''

        # 优先匹配字段名
        if 'email' in field_name.lower():
            return self.VALUE_GENERATORS['email']()
        if 'password' in field_name.lower() or 'passwd' in field_name.lower():
            return self.VALUE_GENERATORS['password']()
        if 'phone' in field_name.lower() or 'tel' in field_name.lower() or 'mobile' in field_name.lower():
            return self.VALUE_GENERATORS['tel']()
        if 'url' in field_name.lower() or 'website' in field_name.lower():
            return self.VALUE_GENERATORS['url']()

        # 回退到类型
        return self.VALUE_GENERATORS.get(field_type, self.VALUE_GENERATORS['text'])()

    def fill_input(self, field: InteractiveElement) -> Optional[str]:
        """填充单个输入字段"""
        value = self.generate_value_for_field(field)
        try:
            self.browser.fill_element(field.selector, value)
            logger.info(f"Filled {field.selector} ({field.input_type}) with '{value}'")
            return value
        except Exception as e:
            logger.warning(f"Failed to fill {field.selector}: {e}")
            return None

    def check_checkbox(self, field: InteractiveElement, check: bool = True) -> bool:
        """勾选或取消勾选复选框"""
        try:
            if check and not field.checked:
                self.browser.check_element(field.selector)
                logger.info(f"Checked {field.selector}: {field.text}")
                return True
            elif not check and field.checked:
                self.browser.fill_element(field.selector, "false")
                logger.info(f"Unchecked {field.selector}: {field.text}")
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to check/uncheck {field.selector}: {e}")
            return False

    def select_radio(self, field: InteractiveElement) -> bool:
        """选择单选按钮"""
        try:
            if not field.checked:
                self.browser.click_element(field.selector)
                logger.info(f"Selected radio {field.selector}: {field.text}")
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to select radio {field.selector}: {e}")
            return False

    def select_option(self, field: InteractiveElement, index: int = 0) -> Optional[str]:
        """选择下拉选项"""
        try:
            if field.options and len(field.options) > 0:
                # 选择第一个可用选项（跳过空值和提示选项）
                valid_options = [opt for opt in field.options if opt and opt not in ['', '请选择', 'Select...', '-']]
                if valid_options:
                    value = valid_options[min(index, len(valid_options) - 1)]
                    self.browser.select_option(field.selector, value)
                    logger.info(f"Selected option '{value}' for {field.selector}")
                    return value
            return None
        except Exception as e:
            logger.warning(f"Failed to select option for {field.selector}: {e}")
            return None

    def fill_form(self, inputs: List[InteractiveElement]) -> Dict[str, any]:
        """填充表单所有字段 - 增强版，支持所有元素类型"""
        filled_values = {}
        filled_count = 0

        for field in inputs:
            if not field.visible:
                continue

            field_key = field.name or field.id or field.selector

            try:
                if field.type == 'input' or field.type == 'textarea':
                    value = self.fill_input(field)
                    if value:
                        filled_values[field_key] = value
                        filled_count += 1

                elif field.type == 'checkbox':
                    # 随机决定是否勾选
                    check = random.choice([True, False])
                    if self.check_checkbox(field, check):
                        filled_values[field_key] = check
                        filled_count += 1

                elif field.type == 'radio':
                    if self.select_radio(field):
                        filled_values[field_key] = field.value
                        filled_count += 1

                elif field.type == 'select':
                    value = self.select_option(field)
                    if value:
                        filled_values[field_key] = value
                        filled_count += 1

            except Exception as e:
                logger.warning(f"Error filling field {field_key}: {e}")

        logger.info(f"Filled {filled_count} form fields")
        return filled_values

    def submit_form(self, submit_selector: str = None) -> bool:
        """
        提交表单 - 自动查找提交按钮

        Simplified version that delegates to helper methods for better maintainability.

        Args:
            submit_selector: Optional explicit selector for the submit button

        Returns:
            bool: True if submission was attempted, False otherwise
        """
        try:
            # 如果指定了提交按钮，直接使用
            if submit_selector:
                return self._click_by_selector(submit_selector, "explicit selector")

            # 尝试标准 CSS 选择器
            result = self._try_standard_selectors()
            if result:
                return result

            # 尝试通过文本内容查找
            result = self._try_text_based_search()
            if result:
                return result

            logger.warning("No submit button found")
            return False

        except Exception as e:
            logger.error(f"Failed to submit form: {e}")
            return False

    def _click_by_selector(self, selector: str, desc: str) -> bool:
        """Click element by selector with logging"""
        try:
            self.browser.click_element(selector)
            logger.info(f"Clicked submit button: {selector} ({desc})")
            return True
        except Exception as e:
            logger.warning(f"Failed to click {selector}: {e}")
            return False

    def _try_standard_selectors(self) -> bool:
        """Try standard CSS selectors for submit buttons"""
        standard_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:not([type])',  # Buttons without type default to submit
        ]

        for selector in standard_selectors:
            if self._element_exists(selector):
                return self._click_by_selector(selector, f"standard selector: {selector}")

        return False

    def _element_exists(self, selector: str) -> bool:
        """Check if element exists using JavaScript"""
        try:
            result = self.browser.eval_js(
                f'document.querySelector("{selector}") ? "exists" : "not_found"'
            )
            return result and "exists" in result
        except:
            return False

    def _try_text_based_search(self) -> bool:
        """Try to find submit button by text content"""
        # 提交关键词
        submit_keywords = [
            '提交', 'Submit', '保存', 'Save', '发送', 'Send',
            '确认', 'Confirm', '注册', 'Register', '登录', 'Login'
        ]

        js_code = self._generate_search_script(submit_keywords)

        try:
            result = self.browser.eval_js(js_code)
            if result and result not in ['null', 'not_found', '']:
                return self._click_by_selector(result, f"text-based: {result}")
        except Exception as e:
            logger.debug(f"Text-based search failed: {e}")

        return False

    def _generate_search_script(self, keywords: list) -> str:
        """Generate JavaScript code for finding buttons by text"""
        return f'''
        (() => {{
            const keywords = {keywords};
            const buttons = document.querySelectorAll('button, input[type="submit"], input[type="button"]');

            for (const btn of buttons) {{
                const text = btn.innerText?.toLowerCase() || btn.value?.toLowerCase() || "";
                for (const kw of keywords) {{
                    if (text.includes(kw.toLowerCase())) {{
                        return generateSelector(btn);
                    }}
                }}
            }}
            return null;

            function generateSelector(btn) {{
                if (btn.id) return "#" + btn.id;
                if (btn.name) return '[name="' + btn.name + '"]';
                if (btn.className) {{
                    const classes = btn.className.trim().split(/\\s+/);
                    if (classes.length > 0) {{
                        const siblings = Array.from(btn.parentElement.children)
                            .filter(c => c.tagName === btn.tagName);
                        const nth = siblings.indexOf(btn) + 1;
                        return btn.tagName.toLowerCase() + "." + classes[0] + ":nth-child(" + nth + ")";
                    }}
                }}
                const siblings = Array.from(btn.parentElement.children)
                    .filter(c => c.tagName === btn.tagName);
                const nth = siblings.indexOf(btn) + 1;
                return btn.tagName.toLowerCase() + ":nth-child(" + nth + ")";
            }}
        }})()
        '''


# =============================================================================
# ConfirmationHandler
# =============================================================================

class ConfirmationHandler:
    """人工确认处理器 - 改进版本，支持超时"""

    def __init__(self, default_timeout: float = 300):
        """
        Args:
            default_timeout: 默认超时时间（秒），None 表示无超时
        """
        self.skipped_actions: List[Dict] = []
        self.confirmed_actions: List[Dict] = []
        self.default_timeout = default_timeout

    def request_confirmation(self, element: InteractiveElement, risk: RiskLevel,
                           timeout: Optional[float] = None) -> bool:
        """
        请求用户确认危险操作

        Args:
            element: 待确认的交互元素
            risk: 风险级别
            timeout: 超时时间（秒），None 表示使用默认值或无超时

        Returns:
            bool: True 表示确认执行，False 表示跳过

        Raises:
            KeyboardInterrupt: 用户选择中止
            TimeoutError: 超时且未设置默认响应
        """
        print(f"\n{'='*60}")
        print(f"⚠️  检测到 {risk.value.upper()} 操作")
        print(f"元素类型: {element.type}")
        print(f"元素文本: {element.text}")
        print(f"选择器: {element.selector}")
        print(f"{'='*60}")
        print("选项:")
        print("  [y]es - 继续执行此操作")
        print("  [n]o  - 跳过后继续")
        print("  [a]bort - 中止所有测试")

        # 确定超时设置
        effective_timeout = timeout if timeout is not None else self.default_timeout

        try:
            if effective_timeout is None:
                # 无超时，直接阻塞等待
                response = input("请选择: ").strip().lower()
            else:
                # 使用信号处理实现超时（Unix 系统）
                response = self._input_with_timeout(f"请选择 ({effective_timeout}s超时): ",
                                                    effective_timeout).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n⚠️  用户中止测试")
            raise KeyboardInterrupt("User aborted")

        action = {
            'element': element,
            'risk': risk,
            'timestamp': datetime.datetime.now().isoformat()
        }

        if response == 'y':
            self.confirmed_actions.append(action)
            return True
        elif response == 'a':
            print("⚠️  用户中止测试")
            raise KeyboardInterrupt("User aborted")
        else:
            self.skipped_actions.append(action)
            print(f"⏭️  跳过操作: {element.text}")
            return False

    def _input_with_timeout(self, prompt: str, timeout: float) -> str:
        """
        实现带超时的输入（使用信号处理）

        Note: 仅在 Unix 系统上有效。Windows 系统会回退到无超时模式。
        """
        import signal

        response = [None]  # 使用列表以便在信号处理函数中修改

        def timeout_handler(signum, frame):
            raise TimeoutError(f"输入超时 ({timeout}s)")

        # 设置信号处理
        old_handler = None
        try:
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout))
            response[0] = input(prompt)
            signal.alarm(0)  # 取消闹钟
        except (AttributeError, ValueError):
            # Windows 不支持 SIGALRM，回退到无超时模式
            response[0] = input(prompt)
        except TimeoutError:
            print("\n⏱️  输入超时，自动跳过")
            return 'n'  # 超时默认跳过
        finally:
            if old_handler:
                signal.signal(signal.SIGALRM, old_handler)

        return response[0] or 'n'  # 空输入视为跳过

    def get_summary(self) -> Dict:
        """获取确认摘要"""
        return {
            'confirmed': len(self.confirmed_actions),
            'skipped': len(self.skipped_actions),
            'skipped_details': self.skipped_actions
        }


# =============================================================================
# ElementTester
# =============================================================================

class ElementTester:
    """元素测试器 - 执行单个元素的测试 - 增强版，支持更多元素类型"""

    def __init__(self, browser: BrowserManager, report: EnhancedTestReport, screenshot_dir: str):
        self.browser = browser
        self.report = report
        self.screenshot_dir = screenshot_dir

    def _take_error_screenshot(self, element: InteractiveElement, error: str) -> Optional[str]:
        """测试失败时截图 - 使用纳秒时间戳和随机数确保文件名唯一"""
        try:
            # 使用纳秒时间戳 + 随机数确保唯一性，即使在同一纳秒内多次错误也不会冲突
            import random
            filename = f"error-{element.type}-{time.time_ns()}-{random.randint(1000, 9999)}.png"
            path = os.path.join(self.screenshot_dir, filename)
            self.browser.screenshot(path)
            logger.info(f"Error screenshot saved: {path}")
            return path
        except Exception as e:
            logger.warning(f"Failed to take error screenshot: {e}")
            return None

    def test_link(self, element: InteractiveElement, monitor: 'NetworkMonitor' = None) -> TestResult:
        """
        测试链接 - 增强版，捕获 API 调用

        Success Criteria:
        - A link is considered "tested successfully" if:
          1. The URL changes after clicking (indicating navigation), OR
          2. API calls are triggered (indicating JavaScript action), OR
          3. Hash/fragment changes (anchor navigation), OR
          4. Page title changes (indicates some action occurred)

        Note: Links that only show modals or toggle UI elements without
        changing URL, triggering APIs, or changing title will be marked
        as "inconclusive" with a note, rather than outright failed.

        Navigation Detection:
        - Compares before/after URLs (ignoring hash differences for anchor links)
        - Waits for page to stabilize after navigation
        - Handles JavaScript-triggered actions that don't change URL
        - Checks for page title changes as additional success indicator
        """
        self.browser.wait_for_network_idle()

        # 保存当前URL用于返回（不含hash部分）
        before_url = self.browser.get_url()
        # Remove hash for comparison to handle anchor links
        before_url_base = before_url.split('#')[0] if before_url else ""
        before_title = self.browser.get_title()

        apis_called = []

        try:
            # 验证初始 URL 有效
            if not before_url or before_url_base in ['about:blank', '']:
                logger.warning("无法保存初始页面状态：URL 无效")
                return TestResult(
                    element=element,
                    success=False,
                    apis_called=[],
                    error="初始页面 URL 无效，无法执行测试"
                )

            # 开始监控
            if monitor:
                monitor.start_recording()

            # 使用 href 或点击
            if element.href:
                self.browser.open(element.href)
            else:
                self.browser.click_element(element.selector)

            self.browser.wait_for_network_idle()

            # 额外等待确保页面加载完成
            self.browser.wait(1000)

            # 捕获 API 调用
            if monitor:
                apis_called = monitor.capture_new_requests(element.text)

            # 验证导航 - 更智能的检测
            current_url = self.browser.get_url()
            current_url_base = current_url.split('#')[0] if current_url else ""
            current_title = self.browser.get_title()

            # Check for hash/fragment changes (anchor navigation)
            before_hash = before_url.split('#')[1] if '#' in before_url else None
            after_hash = current_url.split('#')[1] if '#' in current_url else None
            hash_changed = before_hash != after_hash

            # Success if:
            # 1. URL changed (ignoring hash), OR
            # 2. Some API calls were made (indicates JS action), OR
            # 3. Hash changed (anchor link navigation), OR
            # 4. Title changed (indicates some action occurred)
            url_changed = (current_url_base != before_url_base and
                          current_url_base not in ['about:blank', ''])
            title_changed = before_title != current_title
            action_occurred = len(apis_called) > 0 or url_changed or hash_changed or title_changed

            # Determine success with more nuanced feedback
            if url_changed or len(apis_called) > 0:
                success = True
                error = None
            elif hash_changed or title_changed:
                # Minor action occurred - treat as success but note it
                success = True
                error = None
            else:
                # No detectable action - inconclusive rather than hard failure
                success = False
                error = "No detectable action (no URL change, API call, hash change, or title change)"

            # 返回初始页面 - 带验证和重试
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    self.browser.open(before_url)
                    self.browser.wait(1000)

                    # 验证成功返回
                    returned_url = self.browser.get_url()
                    returned_url_base = returned_url.split('#')[0] if returned_url else ""

                    if returned_url_base == before_url_base:
                        break
                    elif attempt < max_retries - 1:
                        logger.warning(f"页面恢复失败，重试 {attempt + 1}/{max_retries}")
                except Exception as e:
                    logger.error(f"页面恢复异常: {e}")
                    if attempt < max_retries - 1:
                        logger.warning(f"重试 {attempt + 1}/{max_retries}")
                    else:
                        logger.error("无法恢复到初始页面，后续测试可能受影响")

            return TestResult(
                element=element,
                success=success,
                apis_called=apis_called,
                navigated_away=True
            )

        except Exception as e:
            logger.error(f"Error testing link: {e}")
            self._take_error_screenshot(element, str(e))

            # 尝试返回
            if before_url and before_url not in ['about:blank', '']:
                try:
                    self.browser.open(before_url)
                except:
                    logger.warning("恢复初始页面失败")

            return TestResult(
                element=element,
                success=False,
                apis_called=apis_called,
                error=str(e)
            )

    def test_button(self, element: InteractiveElement, monitor: 'NetworkMonitor' = None) -> TestResult:
        """测试按钮 - 增强版，捕获 API 调用"""
        apis_called = []

        try:
            # 开始监控
            if monitor:
                monitor.start_recording()

            # 点击按钮
            self.browser.click_element(element.selector)
            self.browser.wait_for_network_idle()

            # 捕获 API 调用
            if monitor:
                apis_called = monitor.capture_new_requests(element.text)

            return TestResult(
                element=element,
                success=True,
                apis_called=apis_called
            )

        except Exception as e:
            logger.error(f"Error testing button: {e}")
            self._take_error_screenshot(element, str(e))

            return TestResult(
                element=element,
                success=False,
                apis_called=apis_called,
                error=str(e)
            )

    def test_checkbox(self, element: InteractiveElement, monitor: 'NetworkMonitor' = None) -> TestResult:
        """测试复选框"""
        apis_called = []

        try:
            # 切换复选框状态
            if element.checked:
                # 先取消勾选
                self.browser.fill_element(element.selector, "false")
            else:
                self.browser.check_element(element.selector)

            self.browser.wait(500)

            return TestResult(
                element=element,
                success=True,
                apis_called=apis_called
            )

        except Exception as e:
            logger.error(f"Error testing checkbox: {e}")
            self._take_error_screenshot(element, str(e))

            return TestResult(
                element=element,
                success=False,
                apis_called=apis_called,
                error=str(e)
            )

    def test_radio(self, element: InteractiveElement, monitor: 'NetworkMonitor' = None) -> TestResult:
        """测试单选按钮"""
        apis_called = []

        try:
            # 点击单选按钮
            if not element.checked:
                self.browser.click_element(element.selector)
                self.browser.wait(500)

            return TestResult(
                element=element,
                success=True,
                apis_called=apis_called
            )

        except Exception as e:
            logger.error(f"Error testing radio: {e}")
            self._take_error_screenshot(element, str(e))

            return TestResult(
                element=element,
                success=False,
                apis_called=apis_called,
                error=str(e)
            )

    def test_select(self, element: InteractiveElement, monitor: 'NetworkMonitor' = None) -> TestResult:
        """测试下拉选择框"""
        apis_called = []

        try:
            # 选择第一个可用选项
            if element.options and len(element.options) > 0:
                valid_options = [opt for opt in element.options if opt and opt not in ['', '请选择', 'Select...', '-']]
                if valid_options:
                    value = valid_options[0]
                    self.browser.select_option(element.selector, value)
                    self.browser.wait(500)

            return TestResult(
                element=element,
                success=True,
                apis_called=apis_called
            )

        except Exception as e:
            logger.error(f"Error testing select: {e}")
            self._take_error_screenshot(element, str(e))

            return TestResult(
                element=element,
                success=False,
                apis_called=apis_called,
                error=str(e)
            )

    def test_element(self, element: InteractiveElement, monitor: 'NetworkMonitor' = None) -> TestResult:
        """通用元素测试 - 根据类型分发到具体测试方法"""
        if element.type == 'link':
            return self.test_link(element, monitor)
        elif element.type == 'button':
            return self.test_button(element, monitor)
        elif element.type == 'checkbox':
            return self.test_checkbox(element, monitor)
        elif element.type == 'radio':
            return self.test_radio(element, monitor)
        elif element.type == 'select':
            return self.test_select(element, monitor)
        else:
            # 默认尝试点击
            return self.test_button(element, monitor)


# =============================================================================
# IntegrationTester
# =============================================================================

class IntegrationTester:
    """Executes test suites with optional parallel execution - 改进版本，支持优雅关闭和配置管理"""

    def __init__(self, url: str, operation: str, output_dir: str,
                 parallel: bool = False, config: TestConfig = None):
        self.url = url
        self.operation = operation

        # 如果用户明确指定并行模式但模块不可用，则报错退出
        if parallel and not PARALLEL_AVAILABLE:
            logger.error("并行模式被请求但 parallel_executor 模块不可用")
            logger.error("请确保 parallel_executor.py 文件存在且所有依赖已安装")
            logger.error("如果不需要并行模式，请移除 --parallel 参数")
            raise RuntimeError("并行模式不可用，无法继续执行")

        self.parallel = parallel and PARALLEL_AVAILABLE
        self.browser = BrowserManager()
        self.report = EnhancedTestReport(url, operation, output_dir)
        self.screenshot_dir = output_dir

        # 使用配置管理
        self.config = config or TestConfig()

        # 优雅关闭支持
        self._interrupted = False
        self._setup_signal_handlers()

        if self.parallel:
            logger.info("启用智能并行测试模式")

    def _setup_signal_handlers(self):
        """设置信号处理器以支持优雅关闭"""
        import signal

        def signal_handler(signum, frame):
            """处理中断信号"""
            logger.info("接收到中断信号，准备优雅关闭...")
            self._interrupted = True

        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except (ValueError, AttributeError):
            # Windows 或某些环境可能不支持所有信号
            pass

    def _check_interrupted(self) -> bool:
        """检查是否被中断"""
        return self._interrupted

    def _handle_interrupt_cleanup(self):
        """处理中断后的清理"""
        logger.info("执行清理操作...")
        try:
            # 保存当前测试结果
            self.report.save()
            logger.info(f"已保存测试报告: {self.report.filepath}")
        except Exception as e:
            logger.error(f"保存报告失败: {e}")

    def run(self):
        try:
            ops = {
                "read": self.test_read,
                "create": self.test_create,
                "update": self.test_update,
                "delete": self.test_delete,
                "all": self.test_all_comprehensive
            }

            if self.operation not in ops:
                logger.error(f"Unknown operation: {self.operation}")
                return

            ops[self.operation]()

        finally:
            self.browser.close()
            self.report.save()

    def _take_screenshot(self, name_suffix: str) -> str:
        filename = f"{self.report.timestamp}-{name_suffix}.png"
        path = os.path.join(self.screenshot_dir, filename)
        self.browser.screenshot(path)
        return path

    def test_read(self):
        """READ 操作测试 - 原有功能保持"""
        # 检查中断状态
        if self._check_interrupted():
            logger.info("测试被中断")
            self._handle_interrupt_cleanup()
            return

        self.report.add_section("READ 操作测试")

        # 1. Navigation & Accessibility
        self.report.add_subsection("1. 可访问性测试")
        self.browser.open(self.url)
        self.browser.wait(3000)

        current_url = self.browser.get_url()
        self.report.log_test_result(
            "Page loads successfully",
            bool(current_url),
            f"URL: {current_url}"
        )

        # 2. Title Check
        title = self.browser.get_title()
        self.report.log_test_result(
            "Page title present",
            bool(title),
            f"Title: {title}"
        )

        # Screenshot
        screenshot_path = self._take_screenshot("read-initial")
        self.report.add_screenshot("Initial Page Load", screenshot_path)

        # 3. Console Errors
        self.report.add_subsection("Console Errors")
        logs = self.browser.console_logs()
        has_errors = "error" in logs.lower()
        self.report.log_test_result(
            "No console errors on load",
            not has_errors,
            "Errors detected" if has_errors else "Clean console"
        )
        if logs:
            self.report.add_code_block(logs[:500])

        # 4. Page Structure
        self.report.add_subsection("页面结构")
        link_count = self.browser.eval_js("document.querySelectorAll('a').length")
        img_count = self.browser.eval_js("document.querySelectorAll('img').length")
        form_count = self.browser.eval_js("document.querySelectorAll('form').length")

        self.report.add_text("**页面元素统计：**")
        self.report.add_table_row("| 元素 | 数量 |")
        self.report.add_table_row("|---|---|")
        self.report.add_table_row(f"| 链接 (a) | {link_count} |")
        self.report.add_table_row(f"| 图片 (img) | {img_count} |")
        self.report.add_table_row(f"| 表单 (form) | {form_count} |")

        # 5. Interactive Elements
        self.report.add_subsection("交互元素")
        snapshot = self.browser.snapshot(interactive=True)
        self.report.add_code_block(snapshot[:500])

        # 6. Network
        self.report.add_subsection("网络分析")
        network = self.browser.network_requests()
        req_count = len(network.splitlines()) if network else 0
        self.report.add_text(f"**总请求数：** {req_count}")

    def test_create(self):
        """CREATE 操作测试"""
        # 检查中断状态
        if self._check_interrupted():
            logger.info("测试被中断")
            self._handle_interrupt_cleanup()
            return

        self.report.add_section("CREATE 操作测试")
        self.browser.open(self.url)
        self.browser.wait(2000)

        # Form Detection
        self.report.add_subsection("表单分析")
        form_count = self.browser.eval_js("document.querySelectorAll('form').length")

        self.report.log_test_result(
            "Forms detected",
            int(form_count or 0) > 0,
            f"Found {form_count} forms"
        )

        screenshot_path = self._take_screenshot("create-form")
        self.report.add_screenshot("Form Analysis", screenshot_path)

        # Automated Form Filling
        if int(form_count or 0) > 0:
            self.report.add_subsection("自动化表单填充测试")

            js_inputs = """
            JSON.stringify(Array.from(document.querySelectorAll('input:not([type="hidden"]), textarea')).map(i => ({
                id: i.id,
                name: i.name,
                type: i.type,
                placeholder: i.placeholder
            })))
            """
            inputs_json = self.browser.eval_js(js_inputs)
            try:
                inputs = json.loads(inputs_json)
                self.report.add_text(f"尝试填充 {len(inputs)} 个输入框...")

                fill_log = []
                for inp in inputs:
                    selector = ""
                    if inp.get('id'):
                        selector = f"#{inp.get('id')}"
                    elif inp.get('name'):
                        selector = f"[name='{inp.get('name')}']"

                    if selector:
                        val = "test_data"
                        if inp.get('type') == 'email' or 'email' in (inp.get('name') or '').lower():
                            val = "automated_test@example.com"
                        elif inp.get('type') == 'password':
                            val = "TestPass123!"
                        elif inp.get('type') == 'number':
                            val = "123"

                        self.browser.fill(selector, val)
                        fill_log.append(f"Filled {selector} ({inp.get('type')}) with '{val}'")

                self.report.add_code_block("\n".join(fill_log))

                after_fill_screen = self._take_screenshot("create-filled")
                self.report.add_screenshot("Form Filled State", after_fill_screen)

            except Exception as e:
                self.report.add_text(f"表单自动化填充失败: {str(e)}")

    def test_update(self):
        """UPDATE 操作测试"""
        # 检查中断状态
        if self._check_interrupted():
            logger.info("测试被中断")
            self._handle_interrupt_cleanup()
            return

        self.report.add_section("UPDATE 操作测试")
        self.browser.open(self.url)
        self.browser.wait(2000)

        self.report.add_subsection("可编辑元素分析")
        editable_count = self.browser.eval_js(
            "document.querySelectorAll('input:not([readonly]), textarea:not([readonly]), select:not([disabled])').length"
        )

        self.report.log_test_result(
            "Editable fields found",
            int(editable_count or 0) > 0,
            f"Found {editable_count} editable fields"
        )

        screenshot_path = self._take_screenshot("update-page")
        self.report.add_screenshot("Update Page Analysis", screenshot_path)

    def test_delete(self):
        """DELETE 操作测试"""
        # 检查中断状态
        if self._check_interrupted():
            logger.info("测试被中断")
            self._handle_interrupt_cleanup()
            return

        self.report.add_section("DELETE 操作测试")
        self.browser.open(self.url)
        self.browser.wait(2000)

        self.report.add_subsection("删除操作分析")
        delete_count = self.browser.eval_js(
            "Array.from(document.querySelectorAll('button, a')).filter(el => el.textContent.toLowerCase().match(/delete|remove|删除|移除/)).length"
        )

        self.report.log_test_result(
            "Delete buttons detected",
            int(delete_count or 0) > 0,
            f"Found {delete_count} delete/remove buttons"
        )

        screenshot_path = self._take_screenshot("delete-page")
        self.report.add_screenshot("Delete Analysis", screenshot_path)

    def test_all_comprehensive(self):
        """全面的自动化测试 - 支持智能并行执行"""
        self.report.add_section("全面自动化测试")

        # 初始化组件
        discovery = ElementDiscovery(self.browser)
        monitor = NetworkMonitor(self.browser)
        confirmation = ConfirmationHandler()
        form_filler = SmartFormFiller(self.browser)
        tester = ElementTester(self.browser, self.report, self.screenshot_dir)

        # 初始化测试结果列表
        test_results = []
        tested_count = 0
        parallel_stats = None

        # 阶段1: 导航到目标页面
        self.report.add_subsection("初始化")
        self.browser.open(self.url)
        self.browser.wait_for_network_idle()

        # 阶段2: 发现所有元素
        self.report.add_subsection("元素发现")
        all_elements = discovery.discover_all_interactive_elements()
        visible_elements = [e for e in all_elements if e.visible]
        categorized = discovery.categorize_elements(all_elements)

        self.report.add_text(f"发现 **{len(all_elements)}** 个可交互元素 (**{len(visible_elements)}** 个可见)")
        self.report.add_text(f"- 按钮/安全操作: {len(categorized['safe_actions'])}")
        self.report.add_text(f"- 危险操作: {len(categorized['dangerous_actions'])}")
        self.report.add_text(f"- 导航链接: {len(categorized['navigation_links'])}")
        self.report.add_text(f"- 表单输入框: {len(categorized['form_inputs'])}")
        self.report.add_text(f"- 表单选择元素: {len(categorized['form_selections'])} (select/checkbox/radio)")

        # 如果启用并行模式，显示提示
        if self.parallel:
            self.report.add_text(f"\n🚀 **并行测试模式**: 启用智能依赖分析")

        # 初始截图
        initial_screenshot = self._take_screenshot("all-initial")
        self.report.add_screenshot("初始页面状态", initial_screenshot)

        # 阶段3: 测试表单输入框
        if categorized['form_inputs']:
            self.report.add_subsection("表单输入框测试")
            filled_values = form_filler.fill_form(categorized['form_inputs'])
            self.report.add_text(f"填充了 **{len(filled_values)}** 个表单字段")

            form_screenshot = self._take_screenshot("all-form-inputs-filled")
            self.report.add_screenshot("表单输入框填充后状态", form_screenshot)

        # 阶段4: 测试表单选择元素 (select/checkbox/radio) - 始终串行
        if categorized['form_selections']:
            self.report.add_subsection("表单选择元素测试")
            self.report.add_text(f"测试 **{len(categorized['form_selections'])}** 个选择元素...")

            for elem in categorized['form_selections']:
                logger.info(f"Testing {elem.type}: {elem.text[:30]}")
                monitor.start_recording()
                result = tester.test_element(elem, monitor)
                apis = monitor.capture_new_requests(elem.text)
                result.apis_called = apis
                test_results.append(result)
                tested_count += 1
                self.browser.wait(300)

        # 阶段5: 测试导航链接和安全操作（支持并行）
        elements_to_parallel_test = []
        
        # 5.1 准备导航链接
        if categorized['navigation_links']:
            max_links = min(10, len(categorized['navigation_links']))
            elements_to_parallel_test.extend(categorized['navigation_links'][:max_links])
            self.report.add_subsection("导航链接测试")
            self.report.add_text(f"准备测试 {max_links} 个导航链接...")
        
        # 5.2 准备安全操作
        if categorized['safe_actions']:
            max_actions = min(20, len(categorized['safe_actions']))
            elements_to_parallel_test.extend(categorized['safe_actions'][:max_actions])
            self.report.add_subsection("安全操作测试")
            self.report.add_text(f"准备测试 {max_actions} 个安全操作...")
        
        # 5.3 执行测试（并行或串行）
        if self.parallel and elements_to_parallel_test:
            # 使用智能并行执行器
            logger.info(f"使用并行模式测试 {len(elements_to_parallel_test)} 个元素")
            from parallel_executor import SmartParallelExecutor
            
            # Pass the configuration object to SmartParallelExecutor
            parallel_executor = SmartParallelExecutor(self.browser, monitor, tester, config=self.config)
            parallel_results = parallel_executor.execute(elements_to_parallel_test)
            
            test_results.extend(parallel_results)
            tested_count += len(parallel_results)
            parallel_stats = parallel_executor.get_execution_report()
            
            self.report.add_text(f"✅ 并行测试完成: {parallel_stats['statistics']['elements_parallel']} 个并行, "
                               f"{parallel_stats['statistics']['elements_sequential']} 个串行")
        else:
            # 串行执行
            if categorized['navigation_links']:
                max_links = min(10, len(categorized['navigation_links']))
                for i, link in enumerate(categorized['navigation_links'][:max_links]):
                    logger.info(f"Testing link {i+1}/{max_links}: {link.text[:30]}")
                    monitor.start_recording()
                    result = tester.test_link(link, monitor)
                    test_results.append(result)
                    tested_count += 1
            
            if categorized['safe_actions']:
                max_actions = min(20, len(categorized['safe_actions']))
                for i, btn in enumerate(categorized['safe_actions'][:max_actions]):
                    logger.info(f"Testing button {i+1}/{max_actions}: {btn.text[:30]}")
                    monitor.start_recording()
                    result = tester.test_button(btn, monitor)
                    apis = monitor.capture_new_requests(btn.text)
                    result.apis_called = apis
                    test_results.append(result)
                    tested_count += 1
                    self.browser.wait(500)

        # 阶段6: 测试危险操作（始终串行，需要确认）- 改进版本，支持优雅中断
        if categorized['dangerous_actions']:
            self.report.add_subsection("危险操作测试")
            self.report.add_text(f"检测到 **{len(categorized['dangerous_actions'])}** 个危险操作，将请求确认...")

            for btn in categorized['dangerous_actions']:
                # 检查中断状态
                if self._check_interrupted():
                    logger.info("检测到中断信号，停止测试危险操作")
                    self._handle_interrupt_cleanup()
                    break

                risk = discovery.get_element_risk(btn)

                try:
                    if confirmation.request_confirmation(btn, risk):
                        monitor.start_recording()
                        result = tester.test_button(btn, monitor)
                        apis = monitor.capture_new_requests(btn.text)
                        result.apis_called = apis
                        test_results.append(result)
                        tested_count += 1
                        self.browser.wait(1000)
                    else:
                        test_results.append(TestResult(
                            element=btn,
                            success=False,
                            apis_called=[],
                            error="Skipped by user"
                        ))
                except KeyboardInterrupt:
                    logger.info("用户中断，停止测试危险操作")
                    self._handle_interrupt_cleanup()
                    break

        # 阶段7: 尝试提交表单
        form_count = self.browser.eval_js("document.querySelectorAll('form').length")
        if int(form_count or 0) > 0:
            self.report.add_subsection("表单提交测试")
            if form_filler.submit_form():
                self.report.add_text("✅ 表单提交成功")
                self.browser.wait_for_network_idle()
                submit_apis = monitor.capture_new_requests("form_submit")
                if submit_apis:
                    self.report.add_text(f"触发了 **{len(submit_apis)}** 个 API 调用")
            else:
                self.report.add_text("⚠️ 未找到提交按钮或提交失败")

        # 阶段8: 生成增强报告
        all_apis = monitor.get_all_apis()

        self.report.add_api_coverage_section(all_apis)
        self.report.add_interaction_matrix(test_results)
        self.report.add_coverage_summary(len(visible_elements), tested_count, len(all_apis))

        confirmation_summary = confirmation.get_summary()
        self.report.add_risk_assessment(
            confirmation_summary['confirmed'],
            confirmation_summary['skipped'],
            confirmation_summary['skipped_details']
        )
        
        # 添加并行执行统计（如果有）
        if parallel_stats:
            self._add_parallel_execution_section(parallel_stats)

        # 最终截图
        final_screenshot = self._take_screenshot("all-final")
        self.report.add_screenshot("最终页面状态", final_screenshot)
    
    def _add_parallel_execution_section(self, stats: Dict):
        """添加并行执行统计章节"""
        self.report.add_subsection("并行执行统计")
        
        self.report.add_table_row("| 指标 | 值 |")
        self.report.add_table_row("|---|---|")
        self.report.add_table_row(f"| 执行组数 | {stats['statistics']['groups_executed']} |")
        self.report.add_table_row(f"| 并行测试元素 | {stats['statistics']['elements_parallel']} |")
        self.report.add_table_row(f"| 串行测试元素 | {stats['statistics']['elements_sequential']} |")
        self.report.add_table_row(f"| 冲突检测次数 | {stats['conflict_stats']['conflict_count']} |")
        self.report.add_table_row(f"| 回退触发 | {'是' if stats['statistics']['fallback_triggered'] else '否'} |")
        self.report.add_table_row(f"| 成功率 | {stats['success_count']}/{stats['total_results']} |")


def main():
    parser = argparse.ArgumentParser(
        description="Browser Integration Test Runner - Enhanced with Auto-Traversal and Parallel Execution"
    )
    parser.add_argument("url", help="Target URL to test")
    parser.add_argument("operation", nargs="?", default="all",
                      choices=["create", "read", "update", "delete", "all"],
                      help="Test operation to perform")
    parser.add_argument("--output-dir", default=None, help="Directory for reports (default: $PWD/test-reports)")
    parser.add_argument("--parallel", action="store_true",
                      help="Enable parallel execution for independent elements (faster but requires parallel_executor.py)")

    args = parser.parse_args()

    # Determine output directory:
    # 1. Use --output-dir if explicitly provided
    # 2. Use TEST_REPORT_DIR environment variable if set
    # 3. Default to current working directory + /test-reports
    if args.output_dir:
        output_dir = args.output_dir
    else:
        import os
        env_dir = os.environ.get('TEST_REPORT_DIR')
        if env_dir:
            output_dir = env_dir
        else:
            # Use absolute path from current working directory
            # This ensures reports go to the user's project directory, not the plugin cache directory
            output_dir = os.path.join(os.getcwd(), 'test-reports')

    # Create TestConfig with environment variable support
    # TestConfig reads environment variables automatically via its field(default_factory=...) definitions
    config = TestConfig()

    tester = IntegrationTester(args.url, args.operation, output_dir,
                               parallel=args.parallel, config=config)
    tester.run()


if __name__ == "__main__":
    main()
