#!/usr/bin/env python3
"""Remove a Git worktree and its checked-out branch with safety pre-checks."""

from __future__ import annotations

import argparse
import os
import stat
import sys
from dataclasses import dataclass
from pathlib import Path

from config_sync import (
    ConfigSyncChanged,
    MANAGED_PATHS,
    SyncPlan,
    apply_sync,
    is_managed_status_path,
    plan_sync,
    print_sync_plan,
    verify_sync_state,
)
from worktree_common import WorktreeError, parse_worktree_list, resolve_main_repo, run_git


EXIT_OK = 0
EXIT_ERROR = 1
EXIT_PRECHECK = 2


@dataclass(frozen=True)
class CleanupState:
    main_head: str
    target_head: str
    main_branch: str | None
    target_branch: str | None
    unmanaged_paths: tuple[str, ...]
    managed_index: str


class WorktreeChanged(WorktreeError):
    """The repository state changed after the cleanup prechecks."""


class ConfigIndexConflict(WorktreeError):
    """A managed file has distinct staged and unstaged versions that must both be retained."""


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
    result = run_git(repo, ["symbolic-ref", "--quiet", "HEAD"], check=False)
    if result.returncode != 0:
        return None
    return result.stdout.strip().removeprefix("refs/heads/") or None


def worktree_dirty_paths(target: Path) -> tuple[list[str], list[str]]:
    result = run_git(target, ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored"])
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


def managed_index_snapshot(target: Path) -> str:
    raw = run_git(target, ["ls-files", "--stage", "-z", "--", *MANAGED_PATHS]).stdout
    changed = run_git(target, [
        "diff", "--cached", "--name-only", "-z", "--no-renames", "--no-ext-diff", "--no-textconv",
        "--", *MANAGED_PATHS,
    ]).stdout
    staged_paths = set(changed.split("\0"))
    for record in raw.split("\0"):
        if not record:
            continue
        metadata, relative_path = record.split("\t", maxsplit=1)
        if relative_path not in staged_paths:
            continue
        mode, object_id, stage = metadata.split()
        source = target / relative_path
        working_mode = ""
        working_id = ""
        if stage == "0" and mode == "120000" and source.is_symlink():
            working_mode = "120000"
            working_id = run_git(target, ["hash-object", "--stdin"], input_text=os.readlink(source)).stdout.strip()
        elif stage == "0" and mode in {"100644", "100755"} and not source.is_symlink() and source.is_file():
            working_mode = "100755" if source.stat().st_mode & stat.S_IXUSR else "100644"
            working_id = run_git(target, ["hash-object", f"--path={relative_path}", "--", relative_path]).stdout.strip()
        if working_mode != mode or working_id != object_id:
            raise ConfigIndexConflict(f"暂存配置与工作区不同，保留两份版本: {relative_path}")
    return raw


def capture_cleanup_state(main_repo: Path, target: Path) -> CleanupState:
    return CleanupState(
        run_git(main_repo, ["rev-parse", "HEAD"]).stdout.strip(),
        run_git(target, ["rev-parse", "HEAD"]).stdout.strip(),
        repo_head_branch(main_repo),
        repo_head_branch(target),
        tuple(sorted(worktree_dirty_paths(target)[1])),
        managed_index_snapshot(target),
    )


def verify_cleanup_state(main_repo: Path, target: Path, expected: CleanupState) -> None:
    if capture_cleanup_state(main_repo, target) != expected:
        raise WorktreeChanged("清理期间 HEAD、分支、受管索引或非受管路径发生变化；请暂停其他写入后重新预检。")


def branch_is_merged(repo: Path, branch: str) -> tuple[bool, str]:
    """Check whether branch is merged into HEAD of the main repo."""
    base = "HEAD"
    result = run_git(repo, ["branch", "--merged", base], check=False)
    if result.returncode != 0:
        return False, f"git branch --merged 失败: {result.stderr.strip()}"
    # `git branch --merged` 输出前缀：当前分支为 "* "，linked worktree 中的分支为 "+ "，其它为 "  "
    merged = {l[2:].strip() if len(l) > 2 else l.strip() for l in result.stdout.splitlines() if l.strip()}
    if branch in merged:
        return True, ""
    return False, f"branch {branch} not merged into {base}"


def detached_commit_is_preserved(repo: Path, commit: str) -> bool:
    ancestry = run_git(repo, ["merge-base", "--is-ancestor", commit, "HEAD"], check=False)
    if ancestry.returncode == 0:
        return True
    if ancestry.returncode != 1:
        raise WorktreeError(ancestry.stderr.strip() or "无法检查 detached HEAD 的提交可达性")
    references = run_git(repo, [
        "for-each-ref", f"--contains={commit}", "--format=%(refname)",
        "refs/heads/", "refs/tags/", "refs/remotes/",
    ])
    return bool(references.stdout.strip())


def run_prechecks(
    main_repo: Path,
    target: Path,
    entries: list[dict],
    keep_branch: bool,
) -> tuple[list[tuple[str, str]], dict | None, bool]:
    """Return failures, the registered entry, and whether managed paths need forced removal."""
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
    if branch is None:
        commit = run_git(target, ["rev-parse", "HEAD"]).stdout.strip()
        if not detached_commit_is_preserved(main_repo, commit):
            failures.append((
                "detached_unreferenced",
                f"detached HEAD {commit} 未被主 HEAD 或保留引用包含；--keep-branch 不能为其创建引用",
            ))
    elif not keep_branch:
        merged, detail = branch_is_merged(main_repo, branch)
        if not merged:
            failures.append(("branch_unmerged", detail))

    return failures, entry, bool(managed_dirty)


def print_precheck_report(failures: list[tuple[str, str]]) -> None:
    print("PRECHECK FAIL")
    for code, detail in failures:
        print(f"- code: {code}")
        print(f"  detail: {detail}")
    hard_failure = any(
        code in {"main_worktree", "branch_is_head", "worktree_changed", "config_index_conflict"} or code.startswith("config_sync_")
        for code, _ in failures
    )
    if hard_failure:
        print("ACTION REQUIRED: 此类问题不能通过 --force 绕过；请更正目标、保留分支或处理同步问题后重试。")
    else:
        print("ACTION REQUIRED: 若确认丢弃这些改动、未合并分支或无引用提交，请使用 --force 重新执行。")


def remove_worktree(
    main_repo: Path,
    target: Path,
    branch: str | None,
    force_remove: bool,
    force_branch: bool,
    keep_branch: bool,
    dry_run: bool,
    sync_plan: SyncPlan,
    cleanup_state: CleanupState,
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

    verify_cleanup_state(main_repo, target, cleanup_state)
    verify_sync_state(main_repo, target, sync_plan, after_sync=True)
    if branch is None and not force_branch and not detached_commit_is_preserved(main_repo, cleanup_state.target_head):
        raise WorktreeChanged("detached HEAD 的保留引用发生变化，请保存提交并重新预检。")
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
    parser.add_argument("--force", action="store_true", help="允许丢弃未提交及忽略文件、未合并分支或无引用提交；不绕过配置及主 worktree/HEAD 保护。")
    parser.add_argument("--dry-run", action="store_true", help="仅打印计划动作。")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        main_repo = resolve_main_repo(Path(args.repo).expanduser().resolve())
        target = Path(args.target_dir).expanduser().resolve()
        entries = parse_worktree_list(main_repo)
        if entries:
            # Git may list the separate metadata directory as its first entry; identity was validated above.
            entries[0]["path"] = main_repo
        entry = find_target_entry(entries, target)
        if entry is None:
            raise WorktreeError(f"目标不是该仓库已注册的 worktree：{target}")
        if main_worktree_path(entries, main_repo) == target:
            print_precheck_report([("main_worktree", "拒绝清理主 worktree，--force 也不放行")])
            return EXIT_PRECHECK
        cleanup_state = capture_cleanup_state(main_repo, target)
        branch = entry.get("branch")
        if branch != cleanup_state.target_branch:
            raise WorktreeChanged("目标分支与已读取的 worktree 注册信息不一致，请重新预检。")
        if not args.keep_branch and branch and branch == cleanup_state.main_branch:
            print_precheck_report([("branch_is_head", f"分支 {branch} 是主仓库当前 HEAD；可用 --keep-branch 保留分支")])
            return EXIT_PRECHECK

        try:
            sync_plan = plan_sync(main_repo, target)
        except (WorktreeError, OSError) as exc:
            print_precheck_report([("config_sync_error", str(exc))])
            return EXIT_PRECHECK
        print_sync_plan(sync_plan.actions, sync_plan.has_baseline)
        conflicts = [action for action in sync_plan.actions if action.action == "CONFLICT"]
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

        verify_cleanup_state(main_repo, target, cleanup_state)
        if args.dry_run:
            verify_sync_state(main_repo, target, sync_plan, after_sync=False)
            print("Dry run: 不执行配置同步。")
        else:
            try:
                apply_sync(main_repo, target, sync_plan)
            except ConfigSyncChanged:
                raise
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
            sync_plan=sync_plan,
            cleanup_state=cleanup_state,
        )
        print("Done")
        return EXIT_OK
    except ConfigSyncChanged as exc:
        print_precheck_report([("config_sync_changed", str(exc))])
        return EXIT_PRECHECK
    except ConfigIndexConflict as exc:
        print_precheck_report([("config_index_conflict", str(exc))])
        return EXIT_PRECHECK
    except WorktreeChanged as exc:
        print_precheck_report([("worktree_changed", str(exc))])
        return EXIT_PRECHECK
    except WorktreeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
