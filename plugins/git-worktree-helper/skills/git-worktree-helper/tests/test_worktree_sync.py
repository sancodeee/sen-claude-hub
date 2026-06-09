from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
CREATE_SCRIPT = SCRIPTS / "create_worktree.py"
REMOVE_SCRIPT = SCRIPTS / "remove_worktree.py"
BASELINE_FILE = "git-worktree-helper-baseline.json"


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


if __name__ == "__main__":
    unittest.main()
