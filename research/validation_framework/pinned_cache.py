"""Read-only, offline bridge for the EXISTING pinned MiniLM cache.

Invoked privately by cli.cjs. No downloaded model, no network and no output file.
The saved vector population must match every retained (id, text hash) exactly.
"""
from __future__ import annotations
import argparse
import json
import socket
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEMANTIC = HERE.parent / "semantic_review"
sys.path.insert(0, str(SEMANTIC))
from encoder import canonical, check_rows, load_cache, offline, sha  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, required=True)
    args = parser.parse_args()
    source = json.load(sys.stdin)
    if source.get("schema") != "un.source-validation.frame.v1" or source.get("split") != "development":
        raise ValueError("Pinned cache bridge accepts authorized development only")
    rows = [r for r in source["observations"]
            if r.get("source_status") == "available" and not r.get("exclusion_reasons")]
    if any(r.get("date") in ("2026-10-05", "2026-10-06") for r in rows):
        raise ValueError("Reserved October 5–6 meetings are prohibited")
    if any(not r.get("meeting_id") for r in rows):
        raise ValueError("Verified meeting IDs are required")
    check_rows(rows)
    lock = json.loads((SEMANTIC / "model-lock.json").read_text(encoding="utf8"))
    with offline() as attempts:
        E, manifest = load_cache(args.cache, rows, lock)
    if attempts:
        raise RuntimeError("Unexpected network attempt")
    identity = {
        "model_lock_sha256": manifest["model_lock_sha256"],
        "encoder": manifest["engine"],
        "implementation_sha256": manifest["implementation_sha256"],
        "manifest_sha256": sha((args.cache / "manifest.json").read_bytes()),
    }
    result = {
        "id": "pinned-minilm-" + manifest["model_lock_sha256"][:20],
        "version": manifest["engine"] + "/" + manifest["implementation_sha256"][:16],
        "kind": "pinned-minilm",
        "verified_pinned_cache": True,
        "identity_sha256": sha(canonical(identity)),
        "rows": [{"id": r["id"], "text_sha256": r["text_sha256"],
                  "vector": v.tolist()} for r, v in zip(rows, E)],
    }
    json.dump(result, sys.stdout, allow_nan=False, separators=(",", ":"))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        # Do not print source text, cache content or vectors on failure.
        sys.stderr.write(type(error).__name__ + ": " + str(error)[:250] + "\n")
        sys.exit(1)
