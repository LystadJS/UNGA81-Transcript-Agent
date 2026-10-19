"""Fail-closed local checkpoint integrity and synthetic representation diagnostics."""
import hashlib
import json
import math
from pathlib import Path

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def verify_checkpoint(directory, manifest):
    """Verify an immutable revision and all local artifacts, rejecting unlisted files."""
    root = Path(directory)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("checkpoint must be a real local directory")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("revision"), str):
        raise ValueError("missing checkpoint revision")
    if len(manifest["revision"]) != 40 or any(c not in "0123456789abcdef" for c in manifest["revision"]):
        raise ValueError("revision must be an exact 40-hex commit")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError("complete artifact map required")
    observed = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("symlink checkpoint artifact")
        if path.is_file():
            observed[path.relative_to(root).as_posix()] = sha256(path.read_bytes())
    if set(observed) != set(artifacts):
        raise ValueError("incomplete or extra artifact inventory")
    for name, value in artifacts.items():
        if not isinstance(name, str) or name.startswith("/") or ".." in Path(name).parts:
            raise ValueError("unsafe artifact path")
        if not isinstance(value, str) or len(value) != 64 or observed[name] != value:
            raise ValueError("artifact checksum mismatch")
    if not any("tokenizer" in name for name in artifacts):
        raise ValueError("missing pinned tokenizer artifact")
    return sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode())

def token_windows(text, tokenizer, max_tokens, overlap=0):
    """Token windows with original-token offsets, using a caller-supplied local tokenizer."""
    if not isinstance(text, str) or not text:
        raise ValueError("nonempty text required")
    if not isinstance(max_tokens, int) or not isinstance(overlap, int) or not 0 <= overlap < max_tokens:
        raise ValueError("invalid token window")
    ids = tokenizer.encode(text, add_special_tokens=False)
    if not ids or not isinstance(ids, list):
        raise ValueError("tokenizer produced no tokens")
    windows = []
    step = max_tokens - overlap
    for start in range(0, len(ids), step):
        part = ids[start:start + max_tokens]
        if not part:
            break
        windows.append({"start_token": start, "end_token": start + len(part), "token_ids": part})
        if start + max_tokens >= len(ids):
            break
    if windows[0]["start_token"] != 0 or windows[-1]["end_token"] != len(ids):
        raise ValueError("incomplete token coverage")
    return windows

def negative_control_metrics(ids, lexical, semantic, controls, k=1):
    """Auditable contrast ranks. Nearness never supplies diplomatic stance."""
    if len(set(ids)) != len(ids) or len(ids) < 3 or not 1 <= k < len(ids):
        raise ValueError("invalid observation population")
    if set(ids) != set(lexical) or set(ids) != set(semantic):
        raise ValueError("missing or mismatched representation observations")
    def ranked(matrix, anchor):
        row = matrix[anchor]
        if set(row) != set(ids) - {anchor}:
            raise ValueError("incomplete distance row")
        if any(not math.isfinite(v) or v < 0 for v in row.values()):
            raise ValueError("invalid distance")
        return sorted(row, key=lambda j: (row[j], j))
    records = []
    for item in controls:
        anchor, target = item["anchor"], item["target"]
        if anchor == target or anchor not in ids or target not in ids:
            raise ValueError("bad contrast case")
        left, right = ranked(lexical, anchor), ranked(semantic, anchor)
        records.append({"case": item["case"], "anchor": anchor, "target": target,
                        "lexical_rank": left.index(target) + 1,
                        "semantic_rank": right.index(target) + 1,
                        "semantic_top_k": target in right[:k],
                        "stance_inference_permitted": False})
    overlap = sum(len(set(ranked(lexical, i)[:k]) & set(ranked(semantic, i)[:k]))
                  for i in ids) / (len(ids) * k)
    return {"observations": len(ids), "k": k, "neighbor_overlap": overlap,
            "controls": records, "publication_eligible": False,
            "checkpoint_performance_evaluated": False}
