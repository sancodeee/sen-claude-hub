#!/usr/bin/env python3
"""Shared Git worktree helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path


class WorktreeError(Exception):
    """Raised for expected user-facing failures."""


def run_git(repo: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise WorktreeError(detail or f"git {' '.join(args)} failed")
    return result
