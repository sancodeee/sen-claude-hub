#!/usr/bin/env python3
"""Create a Git worktree and copy selected local project configuration."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


COPY_PATHS = [
    ".claude",
    ".CLAUDE.md",
    ".mcp.json",
    ".codex",
    ".AGENTS.md",
    ".java-local.properties",
]


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


def resolve_repo(path: Path) -> Path:
    result = run_git(path, ["rev-parse", "--show-toplevel"])
    return Path(result.stdout.strip()).resolve()


def current_branch(repo: Path) -> str:
    result = run_git(repo, ["branch", "--show-current"])
    branch = result.stdout.strip()
    if not branch:
        raise WorktreeError("当前仓库处于 detached HEAD，无法默认使用当前分支。请使用 --branch 指定现存分支。")
    return branch


def branch_exists(repo: Path, branch: str) -> bool:
    result = run_git(repo, ["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], check=False)
    return result.returncode == 0


def validate_target(target: Path) -> Path:
    resolved = target.expanduser().resolve()
    if resolved.exists():
        raise WorktreeError(f"目标目录已存在：{resolved}")
    return resolved


def copy_config_paths(source_repo: Path, target_repo: Path, dry_run: bool) -> list[str]:
    messages: list[str] = []
    for relative_path in COPY_PATHS:
        source = source_repo / relative_path
        target = target_repo / relative_path

        if not source.exists():
            messages.append(f"SKIP missing {relative_path}")
            continue

        if target.exists():
            messages.append(f"SKIP exists {relative_path}")
            continue

        if dry_run:
            messages.append(f"WOULD copy {relative_path}")
            continue

        if source.is_dir():
            shutil.copytree(source, target, symlinks=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target, follow_symlinks=False)
        messages.append(f"COPIED {relative_path}")
    return messages


def create_worktree(repo: Path, target: Path, branch: str, dry_run: bool) -> None:
    command = ["git", "worktree", "add", str(target), branch]
    print(f"Repository: {repo}")
    print(f"Target: {target}")
    print(f"Branch: {branch}")
    print(f"Command: {' '.join(command)}")

    if dry_run:
        print("Dry run: worktree will not be created.")
        return

    result = run_git(repo, ["worktree", "add", str(target), branch], check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise WorktreeError(detail or "git worktree add failed")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Git worktree and copy selected local project configuration files.",
    )
    parser.add_argument("target_dir", help="New worktree target directory. It must not already exist.")
    parser.add_argument("--branch", help="Existing local branch to check out. Defaults to current branch.")
    parser.add_argument("--repo", default=".", help="Source repository path. Defaults to current directory.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned actions without changing files.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    try:
        repo = resolve_repo(Path(args.repo).expanduser().resolve())
        branch = args.branch or current_branch(repo)
        if not branch_exists(repo, branch):
            raise WorktreeError(f"分支不存在或不是本地分支：{branch}")

        target = validate_target(Path(args.target_dir))
        create_worktree(repo, target, branch, args.dry_run)

        copy_target = target if not args.dry_run else target
        for message in copy_config_paths(repo, copy_target, args.dry_run):
            print(message)

        print("Done")
        return 0
    except WorktreeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
