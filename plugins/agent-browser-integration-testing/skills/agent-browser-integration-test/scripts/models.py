#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shared Data Models for agent-browser-integration-test

This module contains data classes used by both run_test.py and parallel_executor.py
to avoid circular imports.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import os


# =============================================================================
# Enums
# =============================================================================

class RiskLevel(Enum):
    """Risk level enumeration for element operations"""
    CRITICAL = "critical"  # Deletion, payment
    HIGH = "high"          # Logout, reset
    MEDIUM = "medium"      # Export, download
    LOW = "low"            # Other operations


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class APICall:
    """API call data class"""
    method: str            # GET, POST, PUT, DELETE
    endpoint: str          # /api/users
    status: int            # 200, 201, 404, etc.
    timing: int            # Response time (ms)
    request_body: Optional[dict] = None
    response_body: Optional[dict] = None


@dataclass
class InteractiveElement:
    """Interactive element data class"""
    type: str              # button, link, input, select, checkbox, radio, textarea
    selector: str          # CSS selector or semantic locator
    text: str              # Element text
    ref: Optional[str]     # Snapshot reference (@e1, @e2)
    visible: bool          # Whether visible
    id: Optional[str] = None
    name: Optional[str] = None
    form_id: Optional[str] = None
    input_type: Optional[str] = None
    href: Optional[str] = None
    placeholder: Optional[str] = None
    checked: Optional[bool] = None     # For checkbox/radio
    value: Optional[str] = None        # For select/checkbox/radio
    options: List[str] = field(default_factory=list)  # For select: available options

    # Note: No __post_init__ needed because field(default_factory=list)
    # ensures options is never None


@dataclass
class TestResult:
    """Test result data class"""
    element: InteractiveElement
    success: bool
    apis_called: List[APICall]
    error: Optional[str] = None
    screenshot: Optional[str] = None
    navigated_away: bool = False


@dataclass
class CommandResult:
    """
    Command execution result for BrowserManager

    Provides clear distinction between successful execution with empty output
    and failed execution (timeout or error).
    """
    success: bool           # True if command succeeded
    output: str             # Command stdout output (empty if failed)
    error: Optional[str] = None  # Error message if failed
    timed_out: bool = False     # True if command timed out

    @classmethod
    def success_result(cls, output: str) -> 'CommandResult':
        """Create a successful result"""
        return cls(success=True, output=output, error=None, timed_out=False)

    @classmethod
    def error_result(cls, error: str) -> 'CommandResult':
        """Create an error result"""
        return cls(success=False, output="", error=error, timed_out=False)

    @classmethod
    def timeout_result(cls, command: str) -> 'CommandResult':
        """Create a timeout result"""
        return cls(success=False, output="",
                   error=f"Command timed out: {command}", timed_out=True)


@dataclass
class TestConfig:
    """
    集中配置管理类

    所有硬编码的配置值都应该在这里定义，便于维护和调整。
    支持通过环境变量覆盖配置值。
    """
    # 命令超时设置
    default_timeout: int = field(default_factory=lambda: int(os.getenv('TEST_DEFAULT_TIMEOUT', '30')))
    page_load_timeout: int = field(default_factory=lambda: int(os.getenv('TEST_PAGE_LOAD_TIMEOUT', '60')))

    # 并行执行设置
    max_workers: int = field(default_factory=lambda: int(os.getenv('TEST_MAX_WORKERS', '5')))
    lock_timeout: float = field(default_factory=lambda: float(os.getenv('TEST_LOCK_TIMEOUT', '5.0')))

    # 测试限制
    max_links: int = field(default_factory=lambda: int(os.getenv('TEST_MAX_LINKS', '10')))
    max_actions: int = field(default_factory=lambda: int(os.getenv('TEST_MAX_ACTIONS', '20')))

    # 等待时间（毫秒）
    wait_after_click: int = field(default_factory=lambda: int(os.getenv('TEST_WAIT_AFTER_CLICK', '500')))
    wait_after_fill: int = field(default_factory=lambda: int(os.getenv('TEST_WAIT_AFTER_FILL', '300')))
    wait_after_navigation: int = field(default_factory=lambda: int(os.getenv('TEST_WAIT_AFTER_NAVIGATION', '1000')))

    # 用户交互设置
    confirmation_timeout: float = field(default_factory=lambda: float(os.getenv('TEST_CONFIRMATION_TIMEOUT', '300')))
    enable_parallel: bool = field(default_factory=lambda: os.getenv('TEST_ENABLE_PARALLEL', 'true').lower() == 'true')

    # 截图设置
    screenshot_format: str = field(default_factory=lambda: os.getenv('TEST_SCREENSHOT_FORMAT', 'png'))

    # 资源管理
    lock_cleanup_interval: int = field(default_factory=lambda: int(os.getenv('TEST_LOCK_CLEANUP_INTERVAL', '300')))
    max_api_records: int = field(default_factory=lambda: int(os.getenv('TEST_MAX_API_RECORDS', '10000')))

    def get_wait_ms(self, wait_type: str) -> int:
        """根据类型获取等待时间（毫秒）"""
        wait_times = {
            'click': self.wait_after_click,
            'fill': self.wait_after_fill,
            'navigation': self.wait_after_navigation,
        }
        return wait_times.get(wait_type, self.wait_after_click)
