#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Browser Integration Test Scripts Package

This package provides comprehensive browser integration testing capabilities
using agent-browser CLI with full auto-traversal and parallel execution support.

Modules:
    - browser_manager: Thread-safe agent-browser CLI wrapper
    - models: Shared data models and configuration
    - parallel_executor: Dependency-aware parallel test execution
    - run_test: Main test execution script

Version: 4.1.0
"""

__version__ = "4.1.0"
__author__ = "Claude"

# Make key classes available at package level
from .models import (
    RiskLevel,
    InteractiveElement,
    APICall,
    TestResult,
    CommandResult,
    TestConfig,
)
from .browser_manager import BrowserManager

__all__ = [
    "RiskLevel",
    "InteractiveElement",
    "APICall",
    "TestResult",
    "CommandResult",
    "TestConfig",
    "BrowserManager",
]
