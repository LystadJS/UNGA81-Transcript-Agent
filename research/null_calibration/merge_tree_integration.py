"""Fail-closed, read-only native regression validation of a Git effective merge tree.

This tool creates an ephemeral *local* merge commit and detached worktree but
NEVER updates a branch or GitHub ref. It never fetches private data or sources.
Tests are synthetic/source-safe according to the pinned coordinator workflows.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

from ci_integration import FROZEN

SCHEMA = "un.null-calibration.effective-merge-regression.v1"
# Source-safe native test commands transcribed from the coordinator workflows.
# Keep original modules and frozen source contracts strictly read-only.
SUITES = {
    "owned_python": ["python3", "-m", "unittest", "discover", "-s", "research/null_calibration", "-p", "test_*.py", "-v"],
    "pr57_locked": ["node", "research/integration/w1_w2/null_calibration/lock.cjs"],
    "pr57_native": ["node", "--test", "research/integration/w1_w2/null_calibration/test-null.cjs"],
    "pr60_guard": ["node", "research/integration/w1_w2/nuisance_estimation/design_guard.cjs"],
    "pr60_native": ["node", "--test", "research/integration/w1_w2/nuisance_estimation/test_estimator.cjs"],
    "w1_framework": ["node", "research/validation_framework/tests/test_framework.cjs"],
    "w1_schema": ["node", "research/validation_framework/tests/test_schema.cjs"],
    "w2_consensus": ["node", "research/consensus/test_consensus.cjs"],
    "w1w2_bridge": ["node", "--test", "research/integration/w1_w2/test-integration.cjs"],
    "w1w2_grouped": ["node", "--test", "research/integration/w1_w2/test-grouped-refits.cjs"],
    "interchange": ["node", "docs/parallel-work/validate-contract.cjs"],
    "frozen_readiness": ["node", "--test", "docs/parallel-work/test-w1-w2-inference-readiness.cjs"],
}
HEX = re.compile(r"^[0-9a-f]{40}$")
ENV = {
    "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
    "PYTHONNOUSERSITE": "1", "GIT_TERMINAL_PROMPT": "0",
}


def invoke(root, command, timeout=300, env=None):
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=root, capture_output=True,
                                text=True, errors="replace", timeout=timeout,
                                env=env or dict(os.environ, **ENV), check=False)
        output = result.stdout + result.stderr
        return {"status": "PASS" if result.returncode == 0 else "FAIL",
                "exit_code": result.returncode,
                "stdout_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
                "output_tail": output[-1500:],
                "duration_seconds": round(time.monotonic() - started, 4)}
    except subprocess.TimeoutExpired:
        return {"status": "FAIL", "reason": "timeout",
                "duration_seconds": round(time.monotonic() - started, 4)}
    except OSError as error:
        return {"status": "NOT_RUN", "reason": type(error).__name__}


def inspect(root, head, main, suites=None, frozen=None, timeout=300):
    """Inspect exact refs, synthetic merge tree, then execute every declared suite.

    For test fixtures only, suites/frozen may be injected; the production CLI
    always uses frozen SHA pins and all native suites.
    """
    suites = SUITES if suites is None else suites
    frozen = FROZEN if frozen is None else frozen
    report = {"schema": SCHEMA, "pr_head": head, "main": main,
              "ready": False, "scientific_eligible": False,
              "publication_eligible": False, "suites": {}, "frozen": {},
              "merge_tree_sha": None}
    if not HEX.fullmatch(head) or not HEX.fullmatch(main):
        return dict(report, blocker="invalid_commit_sha")
    root = Path(root).resolve()
    probe = invoke(root, ["git", "rev-parse", "--show-toplevel"], timeout)
    if probe["status"] != "PASS" or Path(probe["output_tail"].strip()).resolve() != root:
        return dict(report, blocker="no_full_git_checkout")
    actual = invoke(root, ["git", "rev-parse", "HEAD"], timeout)
    if actual["status"] != "PASS" or actual["output_tail"].strip() != head:
        return dict(report, blocker="wrong_checkout_head")
    status = invoke(root, ["git", "status", "--porcelain", "--untracked-files=no"], timeout)
    if status["status"] != "PASS" or status["output_tail"].strip():
        return dict(report, blocker="dirty_checkout")
    for label, sha in (("main", main), ("head", head)):
        obj = invoke(root, ["git", "cat-file", "-t", sha], timeout)
        if obj["status"] != "PASS" or obj["output_tail"].strip() != "commit":
            return dict(report, blocker="missing_" + label + "_commit")
    for path, expected in frozen.items():
        for ref_name, sha in (("main", main), ("head", head)):
            obj = invoke(root, ["git", "rev-parse", f"{sha}:{path}"], timeout)
            blob = obj.get("output_tail", "").strip()
            key = ref_name + ":" + path
            report["frozen"][key] = {
                "expected": expected, "actual": blob,
                "status": "PASS" if obj["status"] == "PASS" and blob == expected else "FAIL",
            }
        if any(value["status"] != "PASS" for value in report["frozen"].values()):
            return dict(report, blocker="frozen_blob_mismatch")
    merged = invoke(root, ["git", "merge-tree", "--write-tree", main, head], timeout)
    if merged["status"] != "PASS":
        return dict(report, blocker="merge_tree_conflict_or_error", merge_diagnostic=merged)
    lines = merged["output_tail"].strip().splitlines()
    if len(lines) != 1 or not HEX.fullmatch(lines[0]):
        return dict(report, blocker="invalid_merge_tree_output", merge_diagnostic=merged)
    tree_sha = lines[0]
    kind = invoke(root, ["git", "cat-file", "-t", tree_sha], timeout)
    if kind["status"] != "PASS" or kind["output_tail"].strip() != "tree":
        return dict(report, blocker="invalid_merge_tree_object")
    report["merge_tree_sha"] = tree_sha
    # Detached, ephemeral commit only. No refs or remote mutations.
    with tempfile.TemporaryDirectory(prefix="pr67-effective-merge-") as scratch:
        env = dict(os.environ, **ENV,
                   GIT_AUTHOR_NAME="Synthetic Merge Check",
                   GIT_AUTHOR_EMAIL="synthetic-merge@example.invalid",
                   GIT_COMMITTER_NAME="Synthetic Merge Check",
                   GIT_COMMITTER_EMAIL="synthetic-merge@example.invalid",
                   GIT_AUTHOR_DATE="2000-01-01T00:00:00+0000",
                   GIT_COMMITTER_DATE="2000-01-01T00:00:00+0000")
        commit = invoke(root, ["git", "commit-tree", tree_sha, "-p", main, "-p", head, "-m", "Synthetic integration validation only"], timeout, env)
        if commit["status"] != "PASS" or not HEX.fullmatch(commit["output_tail"].strip()):
            return dict(report, blocker="ephemeral_merge_commit_failed")
        worktree = str(Path(scratch) / "checkout")
        added = invoke(root, ["git", "worktree", "add", "--detach", "--", worktree,
                              commit["output_tail"].strip()], timeout)
        if added["status"] != "PASS":
            return dict(report, blocker="ephemeral_worktree_failed", diagnostic=added)
        try:
            for name, command in suites.items():
                required = [arg for arg in command if arg.startswith(("research/", "docs/"))]
                missing = [arg for arg in required if not (Path(worktree) / arg).is_file()]
                report["suites"][name] = (
                    {"status": "NOT_RUN", "reason": "missing_native_source", "paths": missing}
                    if missing else invoke(worktree, command, timeout))
            report["ready"] = all(v["status"] == "PASS" for v in report["suites"].values()) \
                              and len(report["suites"]) == len(suites)
        finally:
            removed = invoke(root, ["git", "worktree", "remove", "--force", "--", worktree], timeout)
            if removed["status"] != "PASS":
                report["ready"] = False
                report["cleanup_failure"] = removed
    report["blocker"] = None if report["ready"] else "native_suite_failed_or_not_run"
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--main", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    record = inspect(args.root, args.head, args.main)
    encoded = json.dumps(record, sort_keys=True, indent=2) + "\n"
    path = Path(args.receipt)
    with path.open("x", encoding="utf-8") as file:
        file.write(encoded)
    print(encoded)
    sys.exit(0 if record["ready"] else 1)
