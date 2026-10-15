"""Fail-closed public artifact inspection; only synthetic test data is provided."""
from __future__ import annotations
import base64
import json
from pathlib import Path
import re

SENTINELS = (
    'SYNTHETIC_PRIVATE_TRANSCRIPT_SENTINEL',
    'SYNTHETIC_SECRET_SENTINEL',
    'SYNTHETIC_CACHED_VECTOR_SENTINEL',
)
BAD_EXTENSIONS = {'.npy', '.npz', '.pkl', '.pickle', '.pt', '.pth', '.safetensors', '.onnx', '.faiss', '.index'}
SECRET_PATTERNS = {
    'private key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'GitHub token': re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}'),
    'AWS access key': re.compile(rb'(?:AKIA|ASIA)[A-Z0-9]{16}'),
    'credential assignment': re.compile(rb'(?i)(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*[=:]\s*["\']?[A-Za-z0-9_\-]{24,}'),
}
PRIVATE_KEYS = {
    'transcript_text', 'raw_transcript', 'raw_passage', 'passage_quote',
    'private_review', 'reviewer_annotation', 'embedding_vector',
    'cached_vectors', 'raw_response_bytes', 'private_transcript',
}
RECORD_SIGNATURE = {'text_sha256', 'source_url', 'country', 'id'}


def scan_bytes(data: bytes) -> list[str]:
    problems=[]
    for marker in SENTINELS:
        token=marker.encode()
        encodings=(token, marker.encode('utf-16-le'), marker.encode('utf-16-be'),
                   base64.b64encode(token))
        if any(e in data for e in encodings):
            problems.append('synthetic private sentinel')
    for reason, pattern in SECRET_PATTERNS.items():
        if pattern.search(data): problems.append(reason)
    return sorted(set(problems))


def _inspect_json(obj, *, path='$', depth=0) -> list[str]:
    if depth>32: return [path+': excessive JSON nesting']
    findings=[]
    if isinstance(obj, dict):
        keys=set(obj)
        if keys.intersection(PRIVATE_KEYS):
            findings.append(path+': private/embedding field')
        if RECORD_SIGNATURE.issubset(keys):
            findings.append(path+': row-level source record')
        for key,value in obj.items():
            findings.extend(_inspect_json(value, path=path+'.'+key, depth=depth+1))
    elif isinstance(obj, list):
        for i,v in enumerate(obj):
            findings.extend(_inspect_json(v, path=f'{path}[{i}]', depth=depth+1))
    return findings


def scan_public(root: Path, *, max_file_bytes=5_000_000, max_files=10000) -> list[dict]:
    """Scan only an explicitly supplied public staging directory, never private inputs.

    NOT a replacement for authenticated source/selection review or human approval.
    Every uninspectable artifact is a finding, never a clean bill of health.
    """
    directory=Path(root)
    if not directory.exists() or not directory.is_dir() or directory.is_symlink():
        return [{'path': '.', 'reason': 'public root unavailable'}]
    findings=[]
    count=0
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():
            findings.append({'path': path.relative_to(directory).as_posix(), 'reason': 'symlink not inspected'})
            continue
        if not path.is_file(): continue
        count+=1
        rel=path.relative_to(directory).as_posix()
        if count > max_files:
            findings.append({'path': '.', 'reason': 'file limit exceeded'})
            break
        if path.suffix.lower() in BAD_EXTENSIONS:
            findings.append({'path':rel,'reason':'cached model/vector artifact'})
        try:
            size=path.stat().st_size
            if size>max_file_bytes:
                findings.append({'path':rel,'reason':'file too large for complete inspection'})
                continue
            data=path.read_bytes()
        except OSError:
            findings.append({'path':rel,'reason':'unreadable artifact'})
            continue
        for reason in scan_bytes(data):
            findings.append({'path':rel,'reason':reason})
        if path.suffix.lower() in ('.json','.jsonl'):
            try:
                if path.suffix.lower()=='.json':
                    records=[json.loads(data)]
                else:
                    records=[json.loads(line) for line in data.splitlines() if line.strip()]
                for obj in records:
                    for reason in _inspect_json(obj):
                        findings.append({'path':rel,'reason':reason})
            except (ValueError,UnicodeError,RecursionError):
                findings.append({'path':rel,'reason':'invalid JSON release artifact'})
    return sorted(findings, key=lambda x:(x['path'],x['reason']))
