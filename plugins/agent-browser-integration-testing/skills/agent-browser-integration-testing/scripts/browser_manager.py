#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Browser Manager Module
Part of agent-browser-integration-test skill

Manages agent-browser CLI interactions with thread safety.
"""

import json
import logging
import subprocess
import threading
import time
from typing import List
from models import CommandResult

logger = logging.getLogger(__name__)

class BrowserManager:
    """Manages agent-browser CLI interactions."""

    # Global lock for thread-safe browser command execution
    # The agent-browser CLI is not designed for concurrent access
    # WARNING: This lock serializes all CLI commands, meaning 'parallel' execution
    # happens at the Python logic level (analysis/processing) but actual
    # browser interactions are sequential.
    _command_lock = threading.Lock()

    def __init__(self):
        self.cmd_base = "agent-browser"

    def run_command(self, args: List[str], timeout: int = 30) -> str:
        """
        Executes a browser command and returns stdout.

        Thread-safe: Uses a global lock to ensure only one command
        executes at a time, as the underlying agent-browser CLI
        is not designed for concurrent access.

        Args:
            args: Command arguments (e.g., ['open', 'url'] or ['get', 'title'])
            timeout: Command timeout in seconds

        Returns:
            Command stdout output, or empty string on failure

        Note:
            For better error handling, consider using run_command_ex() which
            returns a CommandResult object with detailed error information.
        """
        result = self.run_command_ex(args, timeout)
        return result.output if result.success else ""

    def run_command_ex(self, args: List[str], timeout: int = 30) -> CommandResult:
        """
        Executes a browser command and returns detailed result.

        Thread-safe: Uses a global lock to ensure only one command
        executes at a time, as the underlying agent-browser CLI
        is not designed for concurrent access.

        Args:
            args: Command arguments (e.g., ['open', 'url'] or ['get', 'title'])
            timeout: Command timeout in seconds

        Returns:
            CommandResult object with success status, output, and error details
        """
        cmd_list = [self.cmd_base] + args

        with BrowserManager._command_lock:
            logger.debug(f"Executing: {' '.join(cmd_list)}")
            try:
                result = subprocess.run(
                    cmd_list,
                    shell=False,  # Use list arguments for security (no command injection)
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout,
                    encoding='utf-8'
                )
                return CommandResult.success_result(result.stdout.strip())
            except subprocess.CalledProcessError as e:
                error_msg = f"Command failed: {' '.join(cmd_list)}\nError: {e.stderr}"
                logger.error(error_msg)
                return CommandResult.error_result(error_msg)
            except subprocess.TimeoutExpired:
                error_msg = f"Command timed out after {timeout}s: {' '.join(cmd_list)}"
                logger.error(error_msg)
                return CommandResult.timeout_result(' '.join(cmd_list))

    # Original methods
    def open(self, url: str):
        self.run_command(['open', url], timeout=60)

    def wait(self, duration_ms: int = 2000):
        self.run_command(['wait', str(duration_ms)])

    def get_title(self) -> str:
        return self.run_command(['get', 'title'])

    def get_url(self) -> str:
        return self.run_command(['get', 'url'])

    def screenshot(self, path: str):
        self.run_command(['screenshot', path])

    def snapshot(self, interactive: bool = True) -> str:
        if interactive:
            return self.run_command(['snapshot', '-i'])
        return self.run_command(['snapshot'])

    def eval_js(self, js_code: str) -> str:
        # Note: JavaScript code may need escaping for shell interpretation
        # Since we're using list args, we pass it directly
        return self.run_command(['eval', js_code])

    def console_logs(self) -> str:
        return self.run_command(['console'])

    def network_requests(self) -> str:
        return self.run_command(['network', 'requests'])

    def click(self, selector: str):
        self.run_command(['click', selector])

    def fill(self, selector: str, value: str):
        self.run_command(['fill', selector, value])

    def close(self):
        self.run_command(['close'])

    # 增强方法
    def network_requests_json(self) -> List[dict]:
        """使用 --json 获取结构化请求数据

        注意：取决于 agent-browser 版本，--json 可能不被支持。
        如果失败需要回退解析，但假设 v4+ 版本支持此功能。
        """
        output = self.run_command(['network', 'requests', '--json'])
        if output:
            try:
                import json
                return json.loads(output)
            except json.JSONDecodeError:
                logger.warning("解析网络请求 JSON 失败")
        return []

    def clear_network_requests(self):
        """清空请求历史"""
        self.run_command(['network', 'requests', '--clear'])

    def wait_for_network_idle(self):
        """等待网络空闲"""
        self.run_command(['wait', '--load', 'networkidle'])

    def find_by_role(self, role: str, name: str = None) -> str:
        """通过角色语义定位元素"""
        args = ['find', 'role', role]
        if name:
            args.extend(['--name', name])
        return self.run_command(args)

    def find_by_text(self, text: str) -> str:
        """通过文本内容定位元素"""
        return self.run_command(['find', 'text', text])

    def find_by_label(self, label: str) -> str:
        """通过标签定位元素"""
        return self.run_command(['find', 'label', label])

    def click_element(self, ref: str):
        """点击元素（使用选择器）"""
        self.run_command(['click', ref])

    def fill_element(self, ref: str, value: str):
        """填写表单元素"""
        self.run_command(['fill', ref, value])

    def check_element(self, ref: str):
        """勾选复选框"""
        self.run_command(['check', ref])

    def select_option(self, ref: str, value: str):
        """选择下拉选项"""
        self.run_command(['select', ref, value])

    def wait_for_text(self, text: str):
        """等待指定文本出现"""
        self.run_command(['wait', '--text', text])

    def wait_for_condition(self, condition_js: str):
        """等待 JavaScript 条件满足"""
        self.run_command(['wait', '--fn', condition_js])

    def handle_dialog(self, action: str):
        """处理浏览器对话框 (accept/dismiss)"""
        self.run_command(['dialog', action])

    def wait_for_page_ready(self, timeout_ms: int = 30000) -> bool:
        """
        等待页面完全就绪（针对 SPA 应用优化 - 放宽版本）

        检查：
        1. DOM readyState = complete
        2. 可交互元素存在（放宽 body 可见性检查）
        3. 页面内容非空

        改进点：
        - 放宽 body 可见性检查，某些 SPA 应用可能隐藏 body 但元素仍然可交互
        - 只要有可交互元素就认为页面可用

        Args:
            timeout_ms: 超时时间（毫秒）

        Returns:
            bool: 页面是否成功就绪
        """
        js_code = '''
        (() => {
            if (document.readyState !== 'complete') {
                return { ready: false, reason: 'DOM not complete', readyState: document.readyState };
            }
            if (!document.body) {
                return { ready: false, reason: 'Body element does not exist' };
            }

            // 检查是否有可交互元素（放宽 body 可见性检查）
            const interactiveCount = document.querySelectorAll(
                'button, a, input, select, textarea, [role="button"]'
            ).length;
            if (interactiveCount === 0) {
                return { ready: false, reason: 'No interactive elements found' };
            }

            // 检查 body 可见性但不阻止测试
            const bodyVisible = document.body.offsetParent !== null;
            if (!bodyVisible) {
                // 发出警告但继续（某些 SPA 应用隐藏 body）
                return { ready: true, reason: `Page ready with ${interactiveCount} elements (body hidden but interactive)` };
            }

            return { ready: true, reason: `Page ready with ${interactiveCount} elements` };
        })()
        '''

        start_time = time.time()
        timeout_sec = timeout_ms / 1000
        poll_interval = 0.5

        while True:
            result = self.eval_js(js_code)
            try:
                status = json.loads(result)
                if status.get('ready', False):
                    logger.info(f"Page ready: {status.get('reason')}")
                    return True

                elapsed = time.time() - start_time
                if elapsed >= timeout_sec:
                    logger.error(f"Page ready timeout: {status.get('reason')}")
                    return False

                logger.debug(f"Waiting for page: {status.get('reason')} ({elapsed:.1f}s)")
                time.sleep(poll_interval)

            except Exception as e:
                logger.warning(f"Page ready check error: {e}")
                time.sleep(poll_interval)
