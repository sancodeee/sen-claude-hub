#!/usr/bin/env python3
"""Create a Git worktree and copy selected local project configuration."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from worktree_common import WorktreeError, record_main_repo, resolve_main_repo, run_git


COPY_PATHS = [
    ".claude",
    "CLAUDE.md",
    ".mcp.json",
    ".codex",
    "AGENTS.md",
    ".java-local.properties",
]


def resolve_repo(path: Path) -> Path:
    result = run_git(path, ["rev-parse", "--show-toplevel"])
    return Path(result.stdout.strip()).resolve()


def current_branch(repo: Path) -> str:
    result = run_git(repo, ["branch", "--show-current"])
    branch = result.stdout.strip()
    if not branch:
        raise WorktreeError("当前仓库处于 detached HEAD，必须使用 --base-branch 指定基准分支。")
    return branch


def validate_base_ref(repo: Path, base_ref: str) -> str:
    if base_ref != "HEAD" and not base_ref.startswith("refs/"):
        for namespace in ["refs/heads", "refs/remotes"]:
            candidate = f"{namespace}/{base_ref}"
            if run_git(repo, ["show-ref", "--verify", "--quiet", candidate], check=False).returncode == 0:
                base_ref = candidate
                break
    result = run_git(repo, ["rev-parse", "--verify", "--quiet", f"{base_ref}^{{commit}}"], check=False)
    if result.returncode != 0:
        raise WorktreeError(f"基准分支或引用不存在：{base_ref}")
    return result.stdout.strip()


def validate_new_branch(repo: Path, branch: str) -> None:
    result = run_git(repo, ["check-ref-format", "--branch", branch], check=False)
    if result.returncode != 0:
        raise WorktreeError(f"新分支名不合法：{branch}。请使用 --new-branch 指定合法分支名。")

    exists = run_git(repo, ["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], check=False)
    if exists.returncode == 0:
        raise WorktreeError(f"新分支已存在：{branch}。请更换目标目录或使用 --new-branch 指定其他名称。")


def validate_worktree_branch_name(target: Path, branch: str) -> None:
    if branch.rsplit("/", maxsplit=1)[-1] != target.name:
        raise WorktreeError(
            f"worktree 目录名与分支名不匹配：目录={target.name}，分支={branch}。"
            "目录名必须等于分支名的最后一级。"
        )


def validate_target(target: Path) -> Path:
    resolved = target.expanduser().resolve()
    if resolved.exists():
        raise WorktreeError(f"目标目录已存在：{resolved}")
    return resolved


def predicted_config_paths(repo: Path, base_commit: str) -> set[str]:
    paths = run_git(repo, ["ls-tree", "-r", "-z", "--name-only", base_commit, "--", *COPY_PATHS]).stdout
    sparse = run_git(repo, ["config", "--bool", "core.sparseCheckout"], check=False)
    if sparse.returncode not in {0, 1}:
        raise WorktreeError(sparse.stderr.strip() or "无法读取 sparse checkout 配置")
    if sparse.stdout.strip() == "true":
        filtered = run_git(repo, ["sparse-checkout", "check-rules", "-z"], input_text=paths, check=False)
        if filtered.returncode != 0:
            raise WorktreeError(
                "无法预演 sparse checkout；需要支持 sparse-checkout check-rules 的 Git。"
                f" {filtered.stderr.strip()}"
            )
        paths = filtered.stdout
    return {path.split("/", maxsplit=1)[0] for path in paths.split("\0") if path}


def copy_config_paths(
    source_repo: Path,
    target_repo: Path,
    dry_run: bool,
    predicted_existing: set[str] | None = None,
) -> list[str]:
    messages: list[str] = []
    existing_paths = predicted_existing or set()
    for relative_path in COPY_PATHS:
        source = source_repo / relative_path
        target = target_repo / relative_path

        if not source.exists() and not source.is_symlink():
            messages.append(f"SKIP missing {relative_path}")
            continue

        if target.exists() or target.is_symlink() or relative_path in existing_paths:
            messages.append(f"SKIP exists {relative_path}")
            continue

        if dry_run:
            messages.append(f"WOULD copy {relative_path}")
            continue

        if source.is_dir() and not source.is_symlink():
            shutil.copytree(source, target, symlinks=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target, follow_symlinks=False)
        messages.append(f"COPIED {relative_path}")
    return messages


def create_worktree(
    repo: Path, target: Path, base_branch: str, new_branch: str, dry_run: bool, base_commit: str,
) -> None:
    command = ["git", "worktree", "add", "-b", new_branch, str(target), base_commit]
    print(f"Repository: {repo}")
    print(f"Target: {target}")
    print(f"Base branch: {base_branch}")
    print(f"Base commit: {base_commit}")
    print(f"New branch: {new_branch}")
    print(f"Command: {' '.join(command)}")

    if dry_run:
        print("Dry run: worktree will not be created.")
        return

    result = run_git(repo, ["worktree", "add", "-b", new_branch, str(target), base_commit], check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise WorktreeError(detail or "git worktree add failed")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Git worktree and copy selected local project configuration files.",
    )
    parser.add_argument("target_dir", help="New worktree target directory. It must not already exist.")
    parser.add_argument("--base-branch", help="Base branch/ref used to create the new worktree branch.")
    parser.add_argument(
        "--new-branch",
        help="New branch name. Its final component must match the target directory name.",
    )
    parser.add_argument("--repo", default=".", help="Source repository path. Defaults to current directory.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned actions without changing files.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    created = False

    try:
        repo = resolve_repo(Path(args.repo).expanduser().resolve())
        main_repo = resolve_main_repo(repo)
        target = validate_target(Path(args.target_dir))
        base_branch = args.base_branch or current_branch(repo)
        new_branch = args.new_branch or target.name
        base_commit = validate_base_ref(repo, args.base_branch or "HEAD")
        validate_new_branch(repo, new_branch)
        validate_worktree_branch_name(target, new_branch)

        predicted_existing = predicted_config_paths(repo, base_commit) if args.dry_run else set()

        create_worktree(repo, target, base_branch, new_branch, args.dry_run, base_commit)
        created = not args.dry_run

        for message in copy_config_paths(repo, target, args.dry_run, predicted_existing):
            print(message)

        if not args.dry_run:
            from config_sync import write_baseline

            record_main_repo(repo, main_repo)
            baseline = write_baseline(target)
            print(f"BASELINE {baseline}")

        print("Done")
        return 0
    except (WorktreeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if created:
            print("PARTIAL CREATE")
            print("- code: create_incomplete")
            print(f"  target: {target}")
            print(f"  branch: {new_branch}")
            print("ACTION REQUIRED: worktree 和分支已保留；先检查注册状态、配置和基线，不要覆盖重建。")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
