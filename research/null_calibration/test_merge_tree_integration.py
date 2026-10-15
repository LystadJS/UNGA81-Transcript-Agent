"""Real-Git synthetic fixtures for the exact-head effective merge runner."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from merge_tree_integration import inspect


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def fixture(root, conflict=False):
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.name", "Synthetic Tester")
    git(root, "config", "user.email", "synthetic@example.invalid")
    (root / "locked.txt").write_text("frozen\n")
    (root / "shared.txt").write_text("base\n")
    git(root, "add", ".")
    git(root, "commit", "-qm", "base")
    git(root, "checkout", "-qb", "worker")
    (root / "check.py").write_text("from pathlib import Path\nassert Path('main_only.txt').exists()\nassert Path('worker_only.txt').exists()\n")
    (root / "worker_only.txt").write_text("worker\n")
    if conflict:
        (root / "shared.txt").write_text("worker modification\n")
    git(root, "add", ".")
    git(root, "commit", "-qm", "worker")
    worker=git(root, "rev-parse", "HEAD")
    git(root, "checkout", "-q", "main")
    (root / "main_only.txt").write_text("main\n")
    if conflict:
        (root / "shared.txt").write_text("main modification\n")
    git(root, "add", ".")
    git(root, "commit", "-qm", "main")
    main=git(root, "rev-parse", "HEAD")
    git(root, "checkout", "-q", "worker")
    sha=git(root,"hash-object","locked.txt")
    return main,worker,sha


class EffectiveMergeTests(unittest.TestCase):
    def test_clean_merge_executes_actual_merged_tree(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            main,head,locked=fixture(root)
            output=inspect(root,head,main,suites={"merge_smoke":[sys.executable,"check.py"]},frozen={"locked.txt":locked})
            self.assertTrue(output["ready"],output)
            self.assertEqual(output["suites"]["merge_smoke"]["status"],"PASS")
            self.assertEqual(len(output["merge_tree_sha"]),40)
            self.assertEqual(git(root,"rev-parse","HEAD"),head)
            self.assertEqual(git(root,"branch","--list","worker"),"* worker")
            self.assertEqual(len(git(root,"worktree","list","--porcelain").split("\n\n")),1)
    def test_conflict_blocks_test_execution(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);main,head,locked=fixture(root,conflict=True)
            output=inspect(root,head,main,suites={"merge_smoke":[sys.executable,"check.py"]},frozen={"locked.txt":locked})
            self.assertEqual(output["blocker"],"merge_tree_conflict_or_error")
            self.assertEqual(output["suites"],{})
    def test_frozen_hash_and_head_mismatch_refusal(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);main,head,locked=fixture(root)
            out=inspect(root,head,main,suites={},frozen={"locked.txt":"f"*40})
            self.assertEqual(out["blocker"],"frozen_blob_mismatch")
            out=inspect(root,main,head,suites={},frozen={"locked.txt":locked})
            self.assertEqual(out["blocker"],"wrong_checkout_head")
    def test_missing_suite_source_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);main,head,locked=fixture(root)
            out=inspect(root,head,main,suites={"upstream":[sys.executable,"docs/parallel-work/missing.py"]},frozen={"locked.txt":locked})
            self.assertFalse(out["ready"])
            self.assertEqual(out["suites"]["upstream"]["status"],"NOT_RUN")
    def test_no_git_repo_refusal(self):
        with tempfile.TemporaryDirectory() as d:
            out=inspect(d,"a"*40,"b"*40,suites={},frozen={})
            self.assertEqual(out["blocker"],"no_full_git_checkout")
    def test_native_failure_is_not_acceptance(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);main,head,locked=fixture(root)
            out=inspect(root,head,main,suites={"fails":[sys.executable,"-c","raise SystemExit(42)"]},frozen={"locked.txt":locked})
            self.assertEqual(out["suites"]["fails"]["status"],"FAIL")
            self.assertFalse(out["ready"])


if __name__ == "__main__":
    unittest.main()
