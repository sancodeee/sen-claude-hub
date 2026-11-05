#!/usr/bin/env python3
"""Manage worktree configuration baselines and cleanup synchronization."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path

from worktree_common import WorktreeError, run_git


MANAGED_PATHS = [
    ".claude",
    "CLAUDE.md",
    ".mcp.json",
    ".codex",
    "AGENTS.md",
]
BASELINE_FILE = "git-worktree-helper-baseline.json"
BASELINE_VERSION = 2


@dataclass(frozen=True)
class Entry:
    kind: str
    digest: str
    mode: int | None = None


@dataclass(frozen=True)
class SyncAction:
    action: str
    relative_path: str
    detail: str = ""


@dataclass(frozen=True)
class SyncPlan:
    actions: list[SyncAction]
    has_baseline: bool
    main_snapshot: dict[str, Entry]
    worktree_snapshot: dict[str, Entry]


class ConfigSyncChanged(WorktreeError):
    """The configuration no longer matches the plan validated for cleanup."""


def worktree_metadata_dir(worktree: Path) -> Path:
    git_dir = run_git(worktree, ["rev-parse", "--git-dir"]).stdout.strip()
    path = Path(git_dir)
    if not path.is_absolute():
        path = worktree / path
    return path.resolve()


def baseline_path(worktree: Path) -> Path:
    return worktree_metadata_dir(worktree) / BASELINE_FILE


def describe_path(path: Path) -> Entry | None:
    if path.is_symlink():
        return Entry("symlink", os.readlink(path))
    if path.is_file():
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        return Entry("file", digest.hexdigest(), stat.S_IMODE(path.stat().st_mode))
    if path.exists():
        return Entry("other", "")
    return None


def snapshot_managed_paths(root: Path) -> dict[str, Entry]:
    snapshot: dict[str, Entry] = {}
    for managed_path in MANAGED_PATHS:
        source = root / managed_path
        entry = describe_path(source)
        if entry is None:
            continue
        if entry.kind != "other":
            snapshot[managed_path] = entry
            continue
        if not source.is_dir():
            snapshot[managed_path] = entry
            continue
        snapshot[managed_path] = Entry("dir", "")
        for child in sorted(source.rglob("*")):
            child_entry = describe_path(child)
            if child_entry is None:
                continue
            if child_entry.kind == "other" and child.is_dir():
                child_entry = Entry("dir", "")
            snapshot[child.relative_to(root).as_posix()] = child_entry
    return snapshot


def write_baseline(worktree: Path) -> Path:
    destination = baseline_path(worktree)
    payload = {
        "version": BASELINE_VERSION,
        "paths": {
            path: {"kind": entry.kind, "digest": entry.digest, "mode": entry.mode}
            for path, entry in snapshot_managed_paths(worktree).items()
        },
    }
    destination.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination


def load_baseline(worktree: Path) -> dict[str, Entry] | None:
    source = baseline_path(worktree)
    if not source.exists():
        return None
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("baseline must be an object")
        version = payload.get("version")
        if type(version) is not int or version not in {1, BASELINE_VERSION}:
            raise ValueError(f"unsupported version: {version}")
        paths = payload.get("paths")
        if not isinstance(paths, dict):
            raise ValueError("paths must be an object")
        entries: dict[str, Entry] = {}
        for relative_path, value in paths.items():
            path = Path(relative_path)
            if path.is_absolute() or ".." in path.parts or not is_managed_status_path(relative_path):
                raise ValueError(f"invalid managed path: {relative_path}")
            if not isinstance(value, dict):
                raise ValueError(f"invalid entry: {relative_path}")
            kind = value.get("kind")
            digest = value.get("digest")
            mode = value.get("mode") if version == BASELINE_VERSION else None
            if kind not in {"file", "symlink", "dir", "other"} or not isinstance(digest, str):
                raise ValueError(f"invalid entry type or digest: {relative_path}")
            if kind == "file":
                if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                    raise ValueError(f"invalid file digest: {relative_path}")
                if version == BASELINE_VERSION and (type(mode) is not int or not 0 <= mode <= 0o7777):
                    raise ValueError(f"invalid file mode: {relative_path}")
            elif mode is not None:
                raise ValueError(f"unexpected file mode: {relative_path}")
            entries[relative_path] = Entry(kind, digest, mode)
        return entries
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise WorktreeError(f"无法读取配置同步基线 {source}: {exc}") from exc


def matches_baseline(entry: Entry | None, baseline: Entry) -> bool:
    """Old baselines can establish content ancestry, but cannot establish permission ancestry."""
    return entry is not None and entry.kind == baseline.kind and entry.digest == baseline.digest and (
        baseline.mode is None or entry.mode == baseline.mode
    )


def plan_sync(main_repo: Path, worktree: Path) -> SyncPlan:
    baseline = load_baseline(worktree)
    main_snapshot = snapshot_managed_paths(main_repo)
    worktree_snapshot = snapshot_managed_paths(worktree)
    paths = sorted(set(main_snapshot) | set(worktree_snapshot) | set(baseline or {}))
    actions: list[SyncAction] = []

    for relative_path in paths:
        base = baseline.get(relative_path) if baseline is not None else None
        main = main_snapshot.get(relative_path)
        target = worktree_snapshot.get(relative_path)

        if target is None:
            if base is not None:
                actions.append(SyncAction("IGNORE_DELETE", relative_path))
            continue
        if target.kind == "dir":
            if (main is not None and main.kind != "dir") or (base is not None and base.kind != "dir"):
                actions.append(SyncAction("CONFLICT", relative_path, "file type changed"))
            continue
        if (main is not None and main.kind != target.kind) or (
            base is not None and base.kind != target.kind
        ):
            actions.append(SyncAction("CONFLICT", relative_path, "file type changed"))
            continue
        if main == target:
            actions.append(SyncAction("SKIP", relative_path, "same content"))
            continue

        if baseline is None:
            if main is None:
                actions.append(SyncAction("COPY", relative_path))
            else:
                actions.append(SyncAction("CONFLICT", relative_path, "legacy worktree has no baseline"))
            continue

        if base is None:
            if main is None:
                actions.append(SyncAction("COPY", relative_path))
            else:
                actions.append(SyncAction("CONFLICT", relative_path, "both sides added different content"))
            continue

        if base.kind == "file" and base.mode is None and main is not None and main.mode != target.mode:
            actions.append(SyncAction("CONFLICT", relative_path, "legacy baseline has no permission history"))
        elif matches_baseline(target, base):
            actions.append(SyncAction("SKIP", relative_path, "worktree unchanged"))
        elif matches_baseline(main, base):
            actions.append(SyncAction("UPDATE", relative_path))
        else:
            actions.append(SyncAction("CONFLICT", relative_path, "both sides changed"))

    return SyncPlan(actions, baseline is not None, main_snapshot, worktree_snapshot)


def verify_sync_state(main_repo: Path, worktree: Path, plan: SyncPlan, after_sync: bool) -> None:
    expected_main = plan.main_snapshot.copy()
    if after_sync:
        for action in plan.actions:
            if action.action not in {"COPY", "UPDATE"}:
                continue
            expected_main[action.relative_path] = plan.worktree_snapshot[action.relative_path]
            for parent in Path(action.relative_path).parents:
                relative_parent = parent.as_posix()
                if relative_parent in plan.worktree_snapshot:
                    expected_main.setdefault(relative_parent, plan.worktree_snapshot[relative_parent])
    try:
        snapshots = [
            ("worktree", plan.worktree_snapshot, snapshot_managed_paths(worktree)),
            ("main", expected_main, snapshot_managed_paths(main_repo)),
        ]
    except OSError as exc:
        raise ConfigSyncChanged(f"无法复核配置状态，保留 worktree: {exc}") from exc
    for label, expected, actual in snapshots:
        changed = sorted(path for path in set(expected) | set(actual) if expected.get(path) != actual.get(path))
        if changed:
            raise ConfigSyncChanged(f"{label} 配置在计划后发生变化: {', '.join(changed[:10])}")


def _remove_destination(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def _copy_atomically(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        temporary = destination.parent / f".{destination.name}.tmp-{os.getpid()}"
        _remove_destination(temporary)
        temporary.symlink_to(os.readlink(source))
        os.replace(temporary, destination)
        return

    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.tmp-",
        dir=destination.parent,
    )
    os.close(file_descriptor)
    temporary = Path(temporary_name)
    try:
        shutil.copy2(source, temporary, follow_symlinks=False)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def apply_sync(main_repo: Path, worktree: Path, plan: SyncPlan) -> None:
    verify_sync_state(main_repo, worktree, plan, after_sync=False)
    for action in plan.actions:
        if action.action not in {"COPY", "UPDATE"}:
            continue
        source = worktree / action.relative_path
        destination = main_repo / action.relative_path
        try:
            if describe_path(source) != plan.worktree_snapshot[action.relative_path] or (
                describe_path(destination) != plan.main_snapshot.get(action.relative_path)
            ):
                raise ConfigSyncChanged(f"同步前配置发生变化: {action.relative_path}")
            _copy_atomically(source, destination)
        except OSError as exc:
            raise WorktreeError(f"同步 {action.relative_path} 失败: {exc}") from exc
    verify_sync_state(main_repo, worktree, plan, after_sync=True)


def print_sync_plan(actions: list[SyncAction], has_baseline: bool) -> None:
    print(f"Config baseline: {'found' if has_baseline else 'missing (legacy mode)'}")
    for action in actions:
        suffix = f" ({action.detail})" if action.detail else ""
        print(f"{action.action} {action.relative_path}{suffix}")
    counts: dict[str, int] = {}
    for action in actions:
        counts[action.action] = counts.get(action.action, 0) + 1
    summary = ", ".join(f"{key.lower()}={value}" for key, value in sorted(counts.items()))
    print(f"Config sync summary: {summary or 'no managed files'}")


def is_managed_status_path(relative_path: str) -> bool:
    normalized = relative_path.rstrip("/")
    return any(
        normalized == managed_path or normalized.startswith(f"{managed_path}/")
        for managed_path in MANAGED_PATHS
    )
