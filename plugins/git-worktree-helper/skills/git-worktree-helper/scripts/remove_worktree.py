#!/usr/bin/env python3
"""Remove a Git worktree and its checked-out branch with safety pre-checks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from config_sync import (
    apply_sync,
    is_managed_status_path,
    plan_sync,
    print_sync_plan,
)
from worktree_common import WorktreeError, run_git


EXIT_OK = 0
EXIT_ERROR = 1
EXIT_PRECHECK = 2


def resolve_main_repo(start: Path) -> Path:
    """Return the main worktree path even when invoked inside a linked worktree."""
    common_dir = run_git(start, ["rev-parse", "--git-common-dir"]).stdout.strip()
    common_path = Path(common_dir)
    if not common_path.is_absolute():
        toplevel = run_git(start, ["rev-parse", "--show-toplevel"]).stdout.strip()
        common_path = (Path(toplevel) / common_path).resolve()
    else:
        common_path = common_path.resolve()
    # `git-common-dir` 通常指向主仓库的 .git 目录；其父目录即主 worktree 根
    if common_path.name == ".git":
        return common_path.parent
    # bare 仓库或自定义 GIT_DIR：退化为 show-toplevel
    return Path(run_git(start, ["rev-parse", "--show-toplevel"]).stdout.strip()).resolve()


def parse_worktree_list(repo: Path) -> list[dict]:
    """Parse `git worktree list --porcelain` into a list of dicts."""
    raw = run_git(repo, ["worktree", "list", "--porcelain"]).stdout
    entries: list[dict] = []
    current: dict = {}
    for line in raw.splitlines():
        if not line.strip():
            if current:
                entries.append(current)
                current = {}
            continue
        if line.startswith("worktree "):
            if current:
                entries.append(current)
            current = {"path": Path(line[len("worktree "):]).resolve()}
        elif line.startswith("branch "):
            ref = line[len("branch "):]
            current["branch"] = ref[len("refs/heads/"):] if ref.startswith("refs/heads/") else ref
        elif line.strip() == "bare":
            current["bare"] = True
        elif line.strip() == "detached":
            current["detached"] = True
    if current:
        entries.append(current)
    return entries


def find_target_entry(entries: list[dict], target: Path) -> dict | None:
    for entry in entries:
        if entry.get("path") == target:
            return entry
    return None


def main_worktree_path(entries: list[dict], main_repo: Path) -> Path | None:
    """The main worktree is the entry whose path equals the main repo root."""
    for entry in entries:
        if entry.get("path") == main_repo:
            return entry.get("path")
    return None


def repo_head_branch(repo: Path) -> str | None:
    result = run_git(repo, ["symbolic-ref", "--quiet", "--short", "HEAD"], check=False)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def worktree_dirty_paths(target: Path) -> tuple[list[str], list[str]]:
    result = run_git(target, ["status", "--porcelain=v1", "-z", "--untracked-files=all"])
    managed: list[str] = []
    unmanaged: list[str] = []
    records = result.stdout.split("\0")
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        status = record[:2]
        relative_path = record[3:]
        paths = [relative_path]
        if "R" in status or "C" in status:
            if index < len(records) and records[index]:
                paths.append(records[index])
                index += 1
        destination = managed if all(is_managed_status_path(path) for path in paths) else unmanaged
        destination.extend(paths)
    return managed, unmanaged


def branch_is_merged(repo: Path, branch: str) -> tuple[bool, str]:
    """Check whether branch is merged into HEAD of the main repo."""
    head = repo_head_branch(repo)
    base = head or "HEAD"
    result = run_git(repo, ["branch", "--merged", base], check=False)
    if result.returncode != 0:
        return False, f"git branch --merged 失败: {result.stderr.strip()}"
    # `git branch --merged` 输出前缀：当前分支为 "* "，linked worktree 中的分支为 "+ "，其它为 "  "
    merged = {l[2:].strip() if len(l) > 2 else l.strip() for l in result.stdout.splitlines() if l.strip()}
    if branch in merged:
        return True, ""
    return False, f"branch {branch} not merged into {base}"


def run_prechecks(
    main_repo: Path,
    target: Path,
    entries: list[dict],
    keep_branch: bool,
) -> tuple[list[tuple[str, str]], dict | None, bool]:
    """Return (failures, target_entry). Failures empty means all checks pass."""
    failures: list[tuple[str, str]] = []

    entry = find_target_entry(entries, target)
    if entry is None:
        # 非注册路径属于参数错误（EXIT_ERROR）而非预检阻断，由调用方区分
        raise WorktreeError(f"目标不是该仓库已注册的 worktree：{target}")

    if main_worktree_path(entries, main_repo) == target:
        failures.append(("main_worktree", "拒绝清理主 worktree"))

    managed_dirty, unmanaged_dirty = worktree_dirty_paths(target)
    if unmanaged_dirty:
        detail = f"{len(unmanaged_dirty)} path(s): {', '.join(unmanaged_dirty[:5])}"
        failures.append(("dirty_worktree", detail))

    branch = entry.get("branch")
    if not keep_branch and branch:
        head = repo_head_branch(main_repo)
        if head and head == branch:
            failures.append(("branch_is_head", f"分支 {branch} 是主仓库当前 HEAD"))
        else:
            merged, detail = branch_is_merged(main_repo, branch)
            if not merged:
                failures.append(("branch_unmerged", detail))

    return failures, entry, bool(managed_dirty)


def print_precheck_report(failures: list[tuple[str, str]]) -> None:
    print("PRECHECK FAIL")
    for code, detail in failures:
        print(f"- code: {code}")
        print(f"  detail: {detail}")
    sync_failure = any(code.startswith("config_sync_") for code, _ in failures)
    if sync_failure:
        print("ACTION REQUIRED: 配置同步问题不能通过 --force 绕过，请处理后重试。")
    else:
        print("ACTION REQUIRED: 若确认丢弃这些改动 / 强制删除未合并分支，请使用 --force 重新执行。")


def remove_worktree(
    main_repo: Path,
    target: Path,
    branch: str | None,
    force_remove: bool,
    force_branch: bool,
    keep_branch: bool,
    dry_run: bool,
) -> None:
    remove_cmd = ["worktree", "remove"]
    if force_remove:
        remove_cmd.append("--force")
    remove_cmd.append(str(target))

    branch_cmd: list[str] | None = None
    if branch and not keep_branch:
        branch_cmd = ["branch", "-D" if force_branch else "-d", branch]

    print(f"Repository: {main_repo}")
    print(f"Target: {target}")
    print(f"Branch: {branch or '(无 / detached)'}")
    print(f"Command: git {' '.join(remove_cmd)}")
    if branch_cmd:
        print(f"Command: git {' '.join(branch_cmd)}")

    if dry_run:
        print("Dry run: 不执行删除。")
        return

    result = run_git(main_repo, remove_cmd, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise WorktreeError(detail or "git worktree remove failed")
    print(f"REMOVED worktree {target}")

    if branch_cmd:
        result = run_git(main_repo, branch_cmd, check=False)
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip()
            raise WorktreeError(detail or f"git branch 删除失败：{branch}")
        print(f"DELETED branch {branch}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove a Git worktree and its checked-out branch with safety pre-checks.",
    )
    parser.add_argument("target_dir", help="要清理的 worktree 目录。")
    parser.add_argument("--repo", default=".", help="源仓库路径，默认当前目录。")
    parser.add_argument("--keep-branch", action="store_true", help="仅移除 worktree，保留分支。")
    parser.add_argument("--force", action="store_true", help="跳过阻断性预检；worktree remove --force + branch -D。")
    parser.add_argument("--dry-run", action="store_true", help="仅打印计划动作。")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        main_repo = resolve_main_repo(Path(args.repo).expanduser().resolve())
        target = Path(args.target_dir).expanduser().resolve()
        entries = parse_worktree_list(main_repo)
        entry = find_target_entry(entries, target)
        if entry is None:
            raise WorktreeError(f"目标不是该仓库已注册的 worktree：{target}")
        if main_worktree_path(entries, main_repo) == target:
            print_precheck_report([("main_worktree", "拒绝清理主 worktree，--force 也不放行")])
            return EXIT_PRECHECK

        try:
            sync_actions, has_baseline = plan_sync(main_repo, target)
        except (WorktreeError, OSError) as exc:
            print_precheck_report([("config_sync_error", str(exc))])
            return EXIT_PRECHECK
        print_sync_plan(sync_actions, has_baseline)
        conflicts = [action for action in sync_actions if action.action == "CONFLICT"]
        if conflicts:
            detail = ", ".join(action.relative_path for action in conflicts[:10])
            print_precheck_report([("config_sync_conflict", detail)])
            return EXIT_PRECHECK

        if args.force:
            branch = entry.get("branch")
            managed_dirty = bool(worktree_dirty_paths(target)[0])
        else:
            failures, entry, managed_dirty = run_prechecks(main_repo, target, entries, args.keep_branch)
            if failures:
                print_precheck_report(failures)
                return EXIT_PRECHECK
            branch = entry.get("branch") if entry else None

        if args.dry_run:
            print("Dry run: 不执行配置同步。")
        else:
            try:
                apply_sync(main_repo, target, sync_actions)
            except WorktreeError as exc:
                print_precheck_report([("config_sync_error", str(exc))])
                return EXIT_PRECHECK
            print("SYNCED managed configuration")

        remove_worktree(
            main_repo=main_repo,
            target=target,
            branch=branch,
            force_remove=args.force or managed_dirty,
            force_branch=args.force,
            keep_branch=args.keep_branch,
            dry_run=args.dry_run,
        )
        print("Done")
        return EXIT_OK
    except WorktreeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
