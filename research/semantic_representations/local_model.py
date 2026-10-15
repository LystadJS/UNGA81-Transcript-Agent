"""Read-only adapter for the already accepted, fully pinned offline ONNX encoder.

Unlike the initial scaffold this does not introduce a second unverified checkpoint.
Nothing downloads or sends text to a service. Dependencies loaded only on demand.
"""
from __future__ import annotations
import contextlib
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import sys

UPSTREAM = Path(__file__).resolve().parents[1] / "semantic_review"
UPSTREAM_GIT_BLOBS = {
    "encoder.py": "61929a4db62f82ae3f70a098dd87825d38f35aca",
    "model-lock.json": "04eb74595d88f82c13fc8d3d66e2e0962d1d2156",
    "requirements.txt": "603765a1974df8ec63794a2f6017680da80a4db0",
}
REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEPENDENCIES = {"numpy":"2.3.5","scipy":"1.17.0","scikit-learn":"1.8.0",
                "threadpoolctl":"3.6.0","onnxruntime":"1.23.0","tokenizers":"0.22.1"}


def verify_source(directory: Path = UPSTREAM) -> dict:
    """Verify exact SHA1 Git blobs including lengths; reject namespace drift."""
    for name, expected in UPSTREAM_GIT_BLOBS.items():
        path = directory / name
        if not path.is_file() or path.is_symlink():
            raise ValueError("pinned upstream file missing/symlink: " + name)
        raw = path.read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if actual != expected:
            raise ValueError("pinned upstream file drift: " + name)
    lock = json.loads((directory / "model-lock.json").read_text("utf-8"))
    if (lock.get("schema"), lock.get("repository"), lock.get("revision"), lock.get("license")) != (
            "un.semantic-model-lock.v1", MODEL, REVISION, "apache-2.0"):
        raise ValueError("unapproved model revision/license")
    if not isinstance(lock.get("files"),dict) or len(lock["files"]) != 10:
        raise ValueError("incomplete artifact manifest")
    for name, record in lock["files"].items():
        if not isinstance(name,str) or name.startswith("/") or ".." in Path(name).parts:
            raise ValueError("unsafe model artifact path")
        if not isinstance(record.get("sha256"), str) or len(record["sha256"]) != 64 or not isinstance(record.get("bytes"), int) or record["bytes"] <= 0:
            raise ValueError("invalid artifact manifest")
    req = (directory / "requirements.txt").read_text("utf-8").splitlines()
    pins = dict(line.split("==",1) for line in req if line.strip() and not line.lstrip().startswith("#"))
    if pins != DEPENDENCIES:
        raise ValueError("upstream dependency pins changed")
    return lock


def verify_dependencies() -> dict:
    if sys.version_info[:2] != (3,13):
        raise ValueError("local inference requires pinned Python 3.13 runtime")
    measured = {}
    for package, expected in DEPENDENCIES.items():
        actual = importlib.metadata.version(package)
        if actual != expected:
            raise ValueError(f"dependency drift: {package}={actual}, expected={expected}")
        measured[package] = actual
    return measured


@contextlib.contextmanager
def _offline_env():
    keys=("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE")
    old={key:os.environ.get(key) for key in keys}
    for key in keys:
        os.environ[key]="1"
    try:
        yield
    finally:
        for key,value in old.items():
            if value is None: os.environ.pop(key,None)
            else: os.environ[key]=value


class LocalModelEncoder:
    """Production tokenizer/long-document inference comes from pinned encoder.py."""
    def __init__(self, checkpoint: str | Path, source_root: Path = UPSTREAM):
        self.lock = verify_source(source_root)
        self.runtime = verify_dependencies()
        source_path = source_root / "encoder.py"
        spec = importlib.util.spec_from_file_location("unga81_verified_semantic_encoder", source_path)
        if spec is None or spec.loader is None:
            raise ValueError("verified upstream module unavailable")
        module = importlib.util.module_from_spec(spec)
        with _offline_env():
            # Imported implementation never downloads or accepts custom model code.
            spec.loader.exec_module(module)
            with module.offline():
                self.model = module.LocalEncoder(Path(checkpoint), self.lock)
        self.module = module

    def encode(self, rows: list[dict], batch_size: int = 16):
        # Forbid live internet even if the underlying encoder later regresses.
        with _offline_env(), self.module.offline() as attempts:
            # Upstream model's development-only argument guard is an input API detail;
            # synthetic fixtures retain their true split in the enclosing frame.
            local_rows = [dict(r, split="development") if r.get("split") == "synthetic" else r for r in rows]
            matrix, chunks, audit = self.model.encode(local_rows, batch_size=batch_size)
            if attempts:
                raise RuntimeError("encoder attempted external network access")
        return matrix.tolist(), chunks, audit


def model_identity(source_root: Path = UPSTREAM) -> dict:
    """Read verified lock for pipeline.identity, without exposing or loading text."""
    return verify_source(source_root)
