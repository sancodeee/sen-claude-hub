from __future__ import annotations

import contextlib
import io
import json
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
CREATE_SCRIPT = SCRIPTS / "create_worktree.py"
REMOVE_SCRIPT = SCRIPTS / "remove_worktree.py"
BASELINE_FILE = "git-worktree-helper-baseline.json"
sys.path.insert(0, str(SCRIPTS))

import config_sync
import create_worktree
import remove_worktree


class WorktreeSyncTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.repo = self.root / "repo"
        self.worktree = self.root / "task"
        self.repo.mkdir()
        (self.repo / ".claude").mkdir()
        (self.repo / ".claude" / "existing.txt").write_text("base skill\n", encoding="utf-8")
        (self.repo / "AGENTS.md").write_text("base agents\n", encoding="utf-8")

        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test User")
        self.git("add", "AGENTS.md")
        self.git("commit", "-qm", "initial")
        result = self.run_script(
            CREATE_SCRIPT,
            str(self.worktree),
            "--repo",
            str(self.repo),
            "--new-branch",
            "task",
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def git(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=cwd or self.repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

    def run_script(self, script: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(script), *args],
            cwd=self.repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def cleanup(self, *args: str) -> subprocess.CompletedProcess[str]:
        return self.run_script(
            REMOVE_SCRIPT,
            str(self.worktree),
            "--repo",
            str(self.repo),
            *args,
        )

    def baseline_path(self) -> Path:
        git_dir = self.git("rev-parse", "--git-dir", cwd=self.worktree).stdout.strip()
        path = Path(git_dir)
        if not path.is_absolute():
            path = self.worktree / path
        return path.resolve() / BASELINE_FILE

    def test_syncs_modified_and_added_files_before_removal(self) -> None:
        (self.worktree / "AGENTS.md").write_text("worktree agents\n", encoding="utf-8")
        (self.worktree / ".claude" / "new-skill.md").write_text("new skill\n", encoding="utf-8")

        result = self.cleanup()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("worktree agents\n", (self.repo / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertEqual(
            "new skill\n",
            (self.repo / ".claude" / "new-skill.md").read_text(encoding="utf-8"),
        )
        self.assertFalse(self.worktree.exists())

    def test_both_sides_changed_blocks_even_with_force(self) -> None:
        (self.repo / "AGENTS.md").write_text("main agents\n", encoding="utf-8")
        (self.worktree / "AGENTS.md").write_text("worktree agents\n", encoding="utf-8")

        result = self.cleanup("--force")

        self.assertEqual(2, result.returncode)
        self.assertIn("config_sync_conflict", result.stdout)
        self.assertTrue(self.worktree.exists())
        self.assertEqual("main agents\n", (self.repo / "AGENTS.md").read_text(encoding="utf-8"))

    def test_worktree_deletion_is_not_propagated(self) -> None:
        (self.worktree / ".claude" / "existing.txt").unlink()

        result = self.cleanup()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(
            "base skill\n",
            (self.repo / ".claude" / "existing.txt").read_text(encoding="utf-8"),
        )

    def test_legacy_worktree_conflict_is_blocked(self) -> None:
        self.baseline_path().unlink()
        (self.worktree / "AGENTS.md").write_text("legacy change\n", encoding="utf-8")

        result = self.cleanup()

        self.assertEqual(2, result.returncode)
        self.assertIn("missing (legacy mode)", result.stdout)
        self.assertIn("config_sync_conflict", result.stdout)
        self.assertTrue(self.worktree.exists())

    def test_legacy_worktree_copies_only_missing_file(self) -> None:
        self.baseline_path().unlink()
        (self.worktree / ".codex").mkdir()
        (self.worktree / ".codex" / "new-skill.md").write_text("legacy skill\n", encoding="utf-8")

        result = self.cleanup()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(
            "legacy skill\n",
            (self.repo / ".codex" / "new-skill.md").read_text(encoding="utf-8"),
        )

    def test_dry_run_does_not_sync_or_remove(self) -> None:
        (self.worktree / "AGENTS.md").write_text("worktree agents\n", encoding="utf-8")

        result = self.cleanup("--dry-run")

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("UPDATE AGENTS.md", result.stdout)
        self.assertEqual("base agents\n", (self.repo / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertTrue(self.worktree.exists())

    def test_unmanaged_dirty_path_still_blocks_cleanup(self) -> None:
        (self.worktree / "scratch.txt").write_text("do not lose\n", encoding="utf-8")

        result = self.cleanup()

        self.assertEqual(2, result.returncode)
        self.assertIn("dirty_worktree", result.stdout)
        self.assertTrue(self.worktree.exists())

    def test_main_only_change_is_preserved(self) -> None:
        (self.repo / "AGENTS.md").write_text("main agents\n", encoding="utf-8")

        result = self.cleanup()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("main agents\n", (self.repo / "AGENTS.md").read_text(encoding="utf-8"))

    def test_file_type_change_is_reported_as_conflict(self) -> None:
        agents = self.worktree / "AGENTS.md"
        agents.unlink()
        agents.mkdir()
        (agents / "nested.txt").write_text("invalid type change\n", encoding="utf-8")

        result = self.cleanup("--force")

        self.assertEqual(2, result.returncode)
        self.assertIn("file type changed", result.stdout)
        self.assertTrue(self.worktree.exists())

    def test_invalid_baseline_is_reported_as_sync_error(self) -> None:
        self.baseline_path().write_text("{invalid", encoding="utf-8")

        result = self.cleanup("--force")

        self.assertEqual(2, result.returncode)
        self.assertIn("config_sync_error", result.stdout)
        self.assertTrue(self.worktree.exists())

    def test_permission_only_change_is_returned_to_main(self) -> None:
        agents = self.worktree / "AGENTS.md"
        agents.chmod(0o755)

        result = self.cleanup()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(0o755, stat.S_IMODE((self.repo / "AGENTS.md").stat().st_mode))
        self.assertFalse(self.worktree.exists())

    def test_different_permission_changes_block_even_with_force(self) -> None:
        (self.repo / "AGENTS.md").chmod(0o600)
        (self.worktree / "AGENTS.md").chmod(0o755)

        result = self.cleanup("--force")

        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn("config_sync_conflict", result.stdout)
        self.assertEqual(0o600, stat.S_IMODE((self.repo / "AGENTS.md").stat().st_mode))
        self.assertTrue(self.worktree.exists())

    def downgrade_baseline(self) -> None:
        payload = json.loads(self.baseline_path().read_text(encoding="utf-8"))
        payload["version"] = 1
        for entry in payload["paths"].values():
            entry.pop("mode", None)
        self.baseline_path().write_text(json.dumps(payload), encoding="utf-8")

    def test_v1_baseline_still_syncs_content_changes(self) -> None:
        self.downgrade_baseline()
        (self.worktree / "AGENTS.md").write_text("legacy content update\n", encoding="utf-8")

        result = self.cleanup()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("legacy content update\n", (self.repo / "AGENTS.md").read_text(encoding="utf-8"))

    def test_v1_baseline_preserves_main_only_content_changes(self) -> None:
        self.downgrade_baseline()
        (self.repo / "AGENTS.md").write_text("main only legacy update\n", encoding="utf-8")

        result = self.cleanup()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("main only legacy update\n", (self.repo / "AGENTS.md").read_text(encoding="utf-8"))

    def test_v1_permission_difference_blocks_without_guessing(self) -> None:
        self.downgrade_baseline()
        (self.worktree / "AGENTS.md").chmod(0o755)

        result = self.cleanup()

        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn("config_sync_conflict", result.stdout)
        self.assertTrue(self.worktree.exists())

    def test_malformed_baseline_shapes_are_reported_without_traceback(self) -> None:
        payloads = [
            [], None, {"version": 1, "paths": []},
            {"version": 1, "paths": {"AGENTS.md": []}},
            {"version": 1, "paths": {"AGENTS.md": {"kind": "file", "digest": 123}}},
            {"version": 2, "paths": {"AGENTS.md": {"kind": "file", "digest": "a" * 64, "mode": "755"}}},
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                self.baseline_path().write_text(json.dumps(payload), encoding="utf-8")

                result = self.cleanup("--force", "--dry-run")

                self.assertEqual(2, result.returncode, result.stdout + result.stderr)
                self.assertIn("config_sync_error", result.stdout)
                self.assertNotIn("Traceback", result.stderr)
                self.assertTrue(self.worktree.exists())

    def test_ignored_nonmanaged_file_blocks_before_config_sync(self) -> None:
        (self.repo / ".git" / "info" / "exclude").write_text("local-notes/\n", encoding="utf-8")
        notes = self.worktree / "local-notes"
        notes.mkdir()
        (notes / "draft.txt").write_text("keep my notes\n", encoding="utf-8")
        (self.worktree / "AGENTS.md").write_text("pending config\n", encoding="utf-8")

        result = self.cleanup()

        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn("dirty_worktree", result.stdout)
        self.assertTrue((notes / "draft.txt").exists())
        self.assertEqual("base agents\n", (self.repo / "AGENTS.md").read_text(encoding="utf-8"))

    def test_ignored_managed_config_is_synced_before_cleanup(self) -> None:
        (self.repo / ".git" / "info" / "exclude").write_text(".claude/\n", encoding="utf-8")
        (self.worktree / ".claude" / "existing.txt").write_text("ignored config update\n", encoding="utf-8")

        result = self.cleanup()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("ignored config update\n", (self.repo / ".claude" / "existing.txt").read_text(encoding="utf-8"))
        self.assertFalse(self.worktree.exists())

    def test_explicit_force_can_discard_ignored_nonmanaged_file(self) -> None:
        (self.repo / ".git" / "info" / "exclude").write_text("local-note.txt\n", encoding="utf-8")
        (self.worktree / "local-note.txt").write_text("discardable fixture\n", encoding="utf-8")

        result = self.cleanup("--force")

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertFalse(self.worktree.exists())
        self.assertEqual("", self.git("branch", "--list", "task").stdout)

    def test_main_worktree_block_does_not_suggest_force(self) -> None:
        for flags in [(), ("--force",)]:
            with self.subTest(flags=flags):
                result = self.run_script(REMOVE_SCRIPT, str(self.repo), "--repo", str(self.repo), *flags)

                self.assertEqual(2, result.returncode, result.stdout + result.stderr)
                self.assertIn("main_worktree", result.stdout)
                self.assertNotIn("请使用 --force 重新执行", result.stdout)
                self.assertTrue(self.repo.exists())

    def test_main_head_branch_is_protected_even_with_force(self) -> None:
        self.git("symbolic-ref", "HEAD", "refs/heads/task")

        result = self.cleanup("--force")

        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn("branch_is_head", result.stdout)
        self.assertTrue(self.worktree.exists())
        self.assertNotEqual("", self.git("branch", "--list", "task").stdout)

    def test_same_named_tag_cannot_bypass_main_head_protection(self) -> None:
        self.git("tag", "task")
        self.git("symbolic-ref", "HEAD", "refs/heads/task")
        for flags in [(), ("--force",), ("--force", "--dry-run")]:
            with self.subTest(flags=flags):
                result = self.cleanup(*flags)

                self.assertEqual(2, result.returncode, result.stdout + result.stderr)
                self.assertIn("branch_is_head", result.stdout)
                self.assertTrue(self.worktree.exists())

    def test_merge_check_uses_main_head_instead_of_same_named_tag(self) -> None:
        main_branch = self.git("branch", "--show-current").stdout.strip()
        self.git("tag", main_branch)
        (self.worktree / "feature.txt").write_text("merged work\n", encoding="utf-8")
        self.git("add", "feature.txt", cwd=self.worktree)
        self.git("commit", "-qm", "feature", cwd=self.worktree)
        self.git("merge", "--ff-only", "refs/heads/task")

        result = self.cleanup()

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertFalse(self.worktree.exists())
        self.assertEqual("merged work\n", (self.repo / "feature.txt").read_text(encoding="utf-8"))

    def test_force_dry_run_keeps_ignored_files_and_pending_config(self) -> None:
        (self.repo / ".git" / "info" / "exclude").write_text("local-note.txt\n", encoding="utf-8")
        note = self.worktree / "local-note.txt"
        note.write_text("keep during preview\n", encoding="utf-8")
        (self.worktree / "AGENTS.md").write_text("preview config\n", encoding="utf-8")

        result = self.cleanup("--force", "--dry-run")

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertTrue(note.exists())
        self.assertEqual("base agents\n", (self.repo / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertNotEqual("", self.git("branch", "--list", "task").stdout)

    def test_creation_failure_preserves_worktree_and_reports_partial_state(self) -> None:
        for stage in ["copy", "baseline"]:
            with self.subTest(stage=stage):
                target = self.root / f"partial-{stage}"
                output = io.StringIO()
                error = io.StringIO()
                failing_operation = (
                    patch.object(create_worktree.shutil, "copytree", side_effect=PermissionError("fixture copy denied"))
                    if stage == "copy"
                    else patch.object(config_sync, "write_baseline", side_effect=OSError("fixture disk full"))
                )
                with failing_operation, contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                    code = create_worktree.main([str(target), "--repo", str(self.repo)])

                self.assertEqual(1, code)
                self.assertIn("create_incomplete", output.getvalue() + error.getvalue())
                self.assertIn(str(target), output.getvalue() + error.getvalue())
                self.assertNotIn("Done", output.getvalue())
                self.assertTrue(target.exists())
                self.assertNotEqual("", self.git("branch", "--list", target.name).stdout)

    def test_config_edit_after_sync_blocks_removal_even_with_force(self) -> None:
        (self.worktree / "AGENTS.md").write_text("first edit\n", encoding="utf-8")
        real_apply = remove_worktree.apply_sync

        def edit_after_sync(*args, **kwargs):
            real_apply(*args, **kwargs)
            (self.worktree / "AGENTS.md").write_text("new concurrent edit\n", encoding="utf-8")

        output = io.StringIO()
        with patch.object(remove_worktree, "apply_sync", side_effect=edit_after_sync), contextlib.redirect_stdout(output):
            code = remove_worktree.main([str(self.worktree), "--repo", str(self.repo), "--force"])

        self.assertEqual(2, code, output.getvalue())
        self.assertIn("config_sync_changed", output.getvalue())
        self.assertEqual("new concurrent edit\n", (self.worktree / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertEqual("first edit\n", (self.repo / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertNotEqual("", self.git("branch", "--list", "task").stdout)

    def test_config_edit_during_sync_blocks_removal(self) -> None:
        (self.worktree / "AGENTS.md").write_text("planned edit\n", encoding="utf-8")
        real_copy = config_sync._copy_atomically

        def edit_after_copy(source, destination):
            real_copy(source, destination)
            (self.worktree / "AGENTS.md").write_text("edit during sync\n", encoding="utf-8")

        output = io.StringIO()
        with patch.object(config_sync, "_copy_atomically", side_effect=edit_after_copy), contextlib.redirect_stdout(output):
            code = remove_worktree.main([str(self.worktree), "--repo", str(self.repo)])

        self.assertEqual(2, code, output.getvalue())
        self.assertIn("config_sync_changed", output.getvalue())
        self.assertEqual("edit during sync\n", (self.worktree / "AGENTS.md").read_text(encoding="utf-8"))

    def test_main_config_edit_before_sync_is_not_overwritten(self) -> None:
        (self.worktree / "AGENTS.md").write_text("target edit\n", encoding="utf-8")
        real_apply = remove_worktree.apply_sync

        def edit_before_sync(*args, **kwargs):
            (self.repo / "AGENTS.md").write_text("concurrent main edit\n", encoding="utf-8")
            real_apply(*args, **kwargs)

        output = io.StringIO()
        with patch.object(remove_worktree, "apply_sync", side_effect=edit_before_sync), contextlib.redirect_stdout(output):
            code = remove_worktree.main([str(self.worktree), "--repo", str(self.repo)])

        self.assertEqual(2, code, output.getvalue())
        self.assertIn("config_sync_changed", output.getvalue())
        self.assertEqual("concurrent main edit\n", (self.repo / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertTrue(self.worktree.exists())

    def test_new_unmanaged_file_after_sync_blocks_removal_even_with_force(self) -> None:
        real_apply = remove_worktree.apply_sync
        note = self.worktree / "late-note.txt"

        def add_after_sync(*args, **kwargs):
            real_apply(*args, **kwargs)
            note.write_text("new note\n", encoding="utf-8")

        output = io.StringIO()
        with patch.object(remove_worktree, "apply_sync", side_effect=add_after_sync), contextlib.redirect_stdout(output):
            code = remove_worktree.main([str(self.worktree), "--repo", str(self.repo), "--force"])

        self.assertEqual(2, code, output.getvalue())
        self.assertIn("worktree_changed", output.getvalue())
        self.assertEqual("new note\n", note.read_text(encoding="utf-8"))

    def test_new_commit_after_sync_blocks_removal_even_with_force(self) -> None:
        real_apply = remove_worktree.apply_sync

        def commit_after_sync(*args, **kwargs):
            real_apply(*args, **kwargs)
            (self.worktree / "late-code.txt").write_text("new committed work\n", encoding="utf-8")
            self.git("add", "late-code.txt", cwd=self.worktree)
            self.git("commit", "-qm", "late work", cwd=self.worktree)

        output = io.StringIO()
        with patch.object(remove_worktree, "apply_sync", side_effect=commit_after_sync), contextlib.redirect_stdout(output):
            code = remove_worktree.main([str(self.worktree), "--repo", str(self.repo), "--force"])

        self.assertEqual(2, code, output.getvalue())
        self.assertIn("worktree_changed", output.getvalue())
        self.assertEqual("late work", self.git("log", "-1", "--format=%s", cwd=self.worktree).stdout.strip())

    def test_branch_switch_during_planning_blocks_stale_branch_deletion(self) -> None:
        real_plan = remove_worktree.plan_sync

        def switch_during_plan(*args, **kwargs):
            plan = real_plan(*args, **kwargs)
            self.git("checkout", "-qb", "switched", cwd=self.worktree)
            return plan

        output = io.StringIO()
        with patch.object(remove_worktree, "plan_sync", side_effect=switch_during_plan), contextlib.redirect_stdout(output):
            code = remove_worktree.main([str(self.worktree), "--repo", str(self.repo), "--force"])

        self.assertEqual(2, code, output.getvalue())
        self.assertIn("worktree_changed", output.getvalue())
        self.assertTrue(self.worktree.exists())
        self.assertNotEqual("", self.git("branch", "--list", "task").stdout)
        self.assertEqual("switched", self.git("branch", "--show-current", cwd=self.worktree).stdout.strip())

    def test_branch_switch_before_capture_does_not_accept_stale_entry(self) -> None:
        real_capture = remove_worktree.capture_cleanup_state
        switched = False

        def switch_before_capture(*args, **kwargs):
            nonlocal switched
            if not switched:
                self.git("checkout", "-qb", "switched", cwd=self.worktree)
                switched = True
            return real_capture(*args, **kwargs)

        output = io.StringIO()
        with patch.object(remove_worktree, "capture_cleanup_state", side_effect=switch_before_capture), contextlib.redirect_stdout(output):
            code = remove_worktree.main([str(self.worktree), "--repo", str(self.repo), "--force"])

        self.assertEqual(2, code, output.getvalue())
        self.assertIn("worktree_changed", output.getvalue())
        self.assertTrue(self.worktree.exists())
        self.assertNotEqual("", self.git("branch", "--list", "task").stdout)

    def test_top_level_directory_symlink_is_preserved_and_cleanup_succeeds(self) -> None:
        shared = self.root / "shared-config"
        (self.repo / ".claude").rename(shared)
        (self.repo / ".claude").symlink_to(shared, target_is_directory=True)
        target = self.root / "linked-config"

        created = self.run_script(CREATE_SCRIPT, str(target), "--repo", str(self.repo))

        self.assertEqual(0, created.returncode, created.stdout + created.stderr)
        self.assertTrue((target / ".claude").is_symlink())
        self.assertEqual(shared, (target / ".claude").readlink())
        removed = self.run_script(REMOVE_SCRIPT, str(target), "--repo", str(self.repo))
        self.assertEqual(0, removed.returncode, removed.stdout + removed.stderr)
        self.assertTrue((shared / "existing.txt").is_file())

    def test_dangling_source_link_is_preserved(self) -> None:
        link = self.repo / ".codex"
        link.symlink_to("../missing-config", target_is_directory=True)
        target = self.root / "dangling-config"

        result = self.run_script(CREATE_SCRIPT, str(target), "--repo", str(self.repo))

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertTrue((target / ".codex").is_symlink())
        self.assertEqual(Path("../missing-config"), (target / ".codex").readlink())

    def test_existing_dangling_target_link_is_not_overwritten(self) -> None:
        target = self.root / "copy-target"
        target.mkdir()
        (target / ".claude").symlink_to("../missing-config", target_is_directory=True)

        messages = create_worktree.copy_config_paths(self.repo, target, False)

        self.assertIn("SKIP exists .claude", messages)
        self.assertEqual(Path("../missing-config"), (target / ".claude").readlink())

    def test_preview_matches_checkout_skips_and_does_not_create_state(self) -> None:
        (self.repo / ".claude" / "tracked.md").write_text("tracked config\n", encoding="utf-8")
        self.git("add", ".claude/tracked.md")
        self.git("commit", "-qm", "track config directory")
        (self.repo / "AGENTS.md").write_text("local config edit\n", encoding="utf-8")
        target = self.root / "preview-config"

        preview = self.run_script(CREATE_SCRIPT, str(target), "--repo", str(self.repo), "--dry-run")

        self.assertEqual(0, preview.returncode, preview.stdout + preview.stderr)
        self.assertIn("SKIP exists AGENTS.md", preview.stdout)
        self.assertIn("SKIP exists .claude", preview.stdout)
        self.assertNotIn("WOULD copy AGENTS.md", preview.stdout)
        self.assertFalse(target.exists())
        self.assertEqual("", self.git("branch", "--list", target.name).stdout)
        actual = self.run_script(CREATE_SCRIPT, str(target), "--repo", str(self.repo))
        self.assertEqual(0, actual.returncode, actual.stdout + actual.stderr)
        self.assertIn("SKIP exists AGENTS.md", actual.stdout)
        self.assertIn("SKIP exists .claude", actual.stdout)
        self.assertEqual("base agents\n", (target / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertFalse((target / ".claude" / "existing.txt").exists())

    def test_preview_uses_selected_base_instead_of_current_checkout(self) -> None:
        self.git("add", ".claude/existing.txt")
        self.git("commit", "-qm", "track config on alternate base")
        self.git("branch", "config-base")
        self.git("rm", "--cached", ".claude/existing.txt")
        self.git("commit", "-qm", "leave local config untracked")
        target = self.root / "alternate-base"

        preview = self.run_script(CREATE_SCRIPT, str(target), "--repo", str(self.repo), "--base-branch", "config-base", "--dry-run")
        actual = self.run_script(CREATE_SCRIPT, str(target), "--repo", str(self.repo), "--base-branch", "config-base")

        self.assertEqual(0, preview.returncode, preview.stdout + preview.stderr)
        self.assertEqual(0, actual.returncode, actual.stdout + actual.stderr)
        self.assertIn("SKIP exists .claude", preview.stdout)
        self.assertIn("SKIP exists .claude", actual.stdout)

    def test_default_base_uses_head_when_branch_and_tag_share_name(self) -> None:
        main_branch = self.git("branch", "--show-current").stdout.strip()
        self.git("tag", main_branch)
        (self.repo / "latest.txt").write_text("latest main commit\n", encoding="utf-8")
        self.git("add", "latest.txt")
        self.git("commit", "-qm", "advance main beyond tag")
        expected_head = self.git("rev-parse", "HEAD").stdout.strip()
        target = self.root / "default-head"

        result = self.run_script(CREATE_SCRIPT, str(target), "--repo", str(self.repo))

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(expected_head, self.git("rev-parse", "HEAD", cwd=target).stdout.strip())
        self.assertTrue((target / "latest.txt").exists())

    def test_preview_respects_inherited_sparse_checkout_rules(self) -> None:
        (self.repo / "code").mkdir()
        (self.repo / "code" / "app.txt").write_text("code\n", encoding="utf-8")
        self.git("add", "code/app.txt", ".claude/existing.txt")
        self.git("commit", "-qm", "track code and config")
        self.git("sparse-checkout", "init", "--no-cone")
        self.git("sparse-checkout", "set", "/code/", "/.claude/existing.txt")
        self.assertFalse((self.repo / "AGENTS.md").exists())
        (self.repo / "AGENTS.md").write_text("local sparse config\n", encoding="utf-8")
        target = self.root / "sparse-preview"

        preview = self.run_script(CREATE_SCRIPT, str(target), "--repo", str(self.repo), "--dry-run")

        self.assertEqual(0, preview.returncode, preview.stdout + preview.stderr)
        self.assertIn("WOULD copy AGENTS.md", preview.stdout)
        self.assertIn("SKIP exists .claude", preview.stdout)
        self.assertFalse(target.exists())
        actual = self.run_script(CREATE_SCRIPT, str(target), "--repo", str(self.repo))
        self.assertEqual(0, actual.returncode, actual.stdout + actual.stderr)
        self.assertIn("COPIED AGENTS.md", actual.stdout)
        self.assertIn("SKIP exists .claude", actual.stdout)
        self.assertEqual("local sparse config\n", (target / "AGENTS.md").read_text(encoding="utf-8"))

    def test_creation_pins_validated_base_commit(self) -> None:
        base_commit = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("branch", "moving-base")
        (self.repo / "new-code.txt").write_text("later commit\n", encoding="utf-8")
        self.git("add", "new-code.txt")
        self.git("commit", "-qm", "later work")
        later_commit = self.git("rev-parse", "HEAD").stdout.strip()
        target = self.root / "pinned-base"
        real_create = create_worktree.create_worktree

        def move_ref_before_creation(*args, **kwargs):
            self.git("branch", "-f", "moving-base", later_commit)
            return real_create(*args, **kwargs)

        output = io.StringIO()
        with patch.object(create_worktree, "create_worktree", side_effect=move_ref_before_creation), contextlib.redirect_stdout(output):
            code = create_worktree.main([str(target), "--repo", str(self.repo), "--base-branch", "moving-base"])

        self.assertEqual(0, code, output.getvalue())
        self.assertEqual(base_commit, self.git("rev-parse", "HEAD", cwd=target).stdout.strip())
        self.assertFalse((target / "new-code.txt").exists())

    def test_rejects_branch_whose_last_component_differs_from_target_directory(self) -> None:
        target = self.root / "urgent-demo"

        result = self.run_script(
            CREATE_SCRIPT,
            str(target),
            "--repo",
            str(self.repo),
            "--new-branch",
            "codex/payment-hotfix",
            "--dry-run",
        )

        self.assertEqual(1, result.returncode)
        self.assertIn("worktree 目录名与分支名不匹配", result.stderr)
        self.assertFalse(target.exists())

    def test_accepts_branch_namespace_when_last_component_matches_target_directory(self) -> None:
        target = self.root / "namespaced-task"

        result = self.run_script(
            CREATE_SCRIPT,
            str(target),
            "--repo",
            str(self.repo),
            "--new-branch",
            "codex/namespaced-task",
            "--dry-run",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("New branch: codex/namespaced-task", result.stdout)
        self.assertFalse(target.exists())

    def test_rejects_branch_when_directory_name_is_only_a_substring(self) -> None:
        target = self.root / "wk-demo"

        result = self.run_script(
            CREATE_SCRIPT,
            str(target),
            "--repo",
            str(self.repo),
            "--new-branch",
            "codex/prefix-wk-demo",
            "--dry-run",
        )

        self.assertEqual(1, result.returncode)
        self.assertIn("目录名必须等于分支名的最后一级", result.stderr)
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
