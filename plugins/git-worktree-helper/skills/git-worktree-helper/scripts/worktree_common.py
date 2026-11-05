#!/usr/bin/env python3
"""Shared Git worktree helpers."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path


MAIN_WORKTREE_FILE = "git-worktree-helper-main-worktree.json"


class WorktreeError(Exception):
    """Raised for expected user-facing failures."""


def run_git(
    repo: Path, args: list[str], check: bool = True, input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise WorktreeError(detail or f"git {' '.join(args)} failed")
    return result


def parse_worktree_list(repo: Path) -> list[dict]:
    """NUL records preserve paths that Git would otherwise quote or split over lines."""
    raw = run_git(repo, ["worktree", "list", "--porcelain", "-z"]).stdout
    entries: list[dict] = []
    current: dict = {}
    for field in raw.split("\0"):
        if not field:
            if current:
                entries.append(current)
                current = {}
        elif field.startswith("worktree "):
            current["path"] = Path(field[len("worktree "):]).resolve()
        elif field.startswith("branch "):
            current["branch"] = field[len("branch "):].removeprefix("refs/heads/")
        elif field in {"bare", "detached"}:
            current[field] = True
    if current:
        entries.append(current)
    return entries


def _git_path(repo: Path, option: str) -> Path:
    path = Path(run_git(repo, ["rev-parse", option]).stdout.rstrip("\n"))
    return (path if path.is_absolute() else repo / path).resolve()


def _is_main_repo(candidate: Path, common_dir: Path) -> bool:
    try:
        top = run_git(candidate, ["rev-parse", "--show-toplevel"], check=False)
        return top.returncode == 0 and Path(top.stdout.rstrip("\n")).resolve() == candidate and (
            _git_path(candidate, "--git-dir") == common_dir == _git_path(candidate, "--git-common-dir")
        )
    except (OSError, WorktreeError):
        return False


def resolve_main_repo(start: Path) -> Path:
    """Validate the actual main worktree; separate metadata is not itself a worktree."""
    common_dir = _git_path(start, "--git-common-dir")
    top = run_git(start, ["rev-parse", "--show-toplevel"], check=False)
    if top.returncode == 0:
        candidate = Path(top.stdout.rstrip("\n")).resolve()
        if _is_main_repo(candidate, common_dir):
            return candidate
    entries = parse_worktree_list(start)
    if entries and not entries[0].get("bare") and _is_main_repo(entries[0]["path"], common_dir):
        return entries[0]["path"]
    record = common_dir / MAIN_WORKTREE_FILE
    if record.exists():
        try:
            payload = json.loads(record.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or type(payload.get("version")) is not int or (
                payload["version"] != 1 or not isinstance(payload.get("path"), str)
            ):
                raise ValueError("invalid main worktree metadata")
            candidate = Path(payload["path"])
            if candidate.is_absolute() and _is_main_repo(candidate.resolve(), common_dir):
                return candidate.resolve()
        except (OSError, ValueError) as exc:
            raise WorktreeError(f"无法读取主 worktree 定位信息 {record}: {exc}") from exc
    raise WorktreeError("无法可靠定位主 worktree；请从主项目调用，或用 --repo 指定真实主目录。")


def record_main_repo(repo: Path, main_repo: Path) -> None:
    common_dir = _git_path(repo, "--git-common-dir")
    if not _is_main_repo(main_repo, common_dir):
        raise WorktreeError("主 worktree 与当前仓库不匹配，拒绝记录或回收配置。")
    payload = {"version": 1, "path": str(main_repo)}
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=common_dir, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(json.dumps(payload, ensure_ascii=True) + "\n")
        except OSError:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, common_dir / MAIN_WORKTREE_FILE)
    finally:
        temporary.unlink(missing_ok=True)
