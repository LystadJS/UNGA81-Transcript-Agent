"""Pinned, CPU-only MiniLM inference. No downloader, model code, or network fallback."""
from __future__ import annotations
import contextlib, hashlib, importlib.metadata, json, socket
from pathlib import Path
import numpy as np

VERSION = 'local-semantic-1.0.0'
REPOSITORY = 'sentence-transformers/all-MiniLM-L6-v2'
REVISION = '1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
MAX_CONTENT_TOKENS = 254


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def write_json(path: Path, value: object) -> None:
    with path.open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


@contextlib.contextmanager
def offline():
    """Fail loudly on attempted Python socket connections, including future changes."""
    originals = socket.socket.connect, socket.socket.connect_ex, socket.create_connection
    attempts = []
    def blocked(*args, **kwargs):
        attempts.append('blocked network connection')
        raise RuntimeError('Network is disabled during semantic inference and analysis')
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = blocked
    try:
        yield attempts
    finally:
        socket.socket.connect, socket.socket.connect_ex, socket.create_connection = originals


def verify_model(directory: Path, lock: dict) -> None:
    if lock.get('schema') != 'un.semantic-model-lock.v1' or lock.get('repository') != REPOSITORY or lock.get('revision') != REVISION or lock.get('license') != 'apache-2.0':
        raise ValueError('Unexpected model identity, revision, or license')
    trusted = json.loads(Path(__file__).with_name('model-lock.json').read_text())
    if canonical(lock) != canonical(trusted):
        raise ValueError('Model lock differs from the reviewed, checked-in manifest')
    for name, expected in lock['files'].items():
        file = directory / name
        if not file.is_file() or file.is_symlink() or len(file.read_bytes()) != expected['bytes'] or sha(file.read_bytes()) != expected['sha256']:
            raise ValueError('Model artifact missing or altered: ' + name)
    config = json.loads((directory / 'sentence_bert_config.json').read_text())
    pooling = json.loads((directory / '1_Pooling/config.json').read_text())
    if config['max_seq_length'] != 256 or not pooling['pooling_mode_mean_tokens']:
        raise ValueError('Unexpected model context or pooling specification')


def check_rows(rows: list[dict]) -> None:
    if not 1 <= len(rows) <= 5000 or len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Empty, duplicate, or oversized population')
    for r in rows:
        if r.get('split') != 'development' or r.get('language') != 'en':
            raise ValueError('Only explicitly English development passages can be encoded')
        if not isinstance(r.get('text'), str) or sha(r['text'].encode()) != r.get('text_sha256'):
            raise ValueError('Passage text hash mismatch')
        if not r['text'].strip() or len(r['text']) > 100000:
            raise ValueError('Empty or oversized passage; no truncation is applied')


def normalized(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x)
    norms = np.linalg.norm(x, axis=-1, keepdims=True)
    if not np.isfinite(x).all() or np.any(norms < 1e-12):
        raise ValueError('Nonfinite or zero embedding')
    return x / norms


def split_encoding(text: str, ids: list[int], offsets: list[tuple[int, int]], limit: int = MAX_CONTENT_TOKENS) -> list[dict]:
    """Partition ALL wordpieces and bind their source intervals; no text is rewritten."""
    if not isinstance(limit, int) or not 1 <= limit <= MAX_CONTENT_TOKENS or not ids or len(ids) != len(offsets):
        raise ValueError('Invalid token partition')
    if any(not (0 <= a < b <= len(text)) for a, b in offsets):
        raise ValueError('Invalid or padded tokenizer offsets')
    if any(offsets[i][0] < offsets[i-1][0] for i in range(1, len(offsets))):
        raise ValueError('Nonmonotone tokenizer offsets')
    chunks = []
    for start in range(0, len(ids), limit):
        end = min(len(ids), start + limit)
        # Text coverage includes otherwise unrepresented whitespace. Token offsets
        # separately expose normalization and unusual overlapping Unicode spans.
        a = 0 if start == 0 else offsets[start][0]
        b = len(text) if end == len(ids) else offsets[end][0]
        chunks.append({'token_start': start, 'token_end': end,
                       'coverage_start': a, 'coverage_end': b,
                       'text_sha256': sha(text[a:b].encode()),
                       'token_offsets': [list(o) for o in offsets[start:end]],
                       'token_ids': ids[start:end]})
    if [t for c in chunks for t in c['token_ids']] != ids:
        raise ValueError('Token omission or duplication')
    if ''.join(text[c['coverage_start']:c['coverage_end']] for c in chunks) != text:
        raise ValueError('Text coverage gap')
    return chunks


class LocalEncoder:
    def __init__(self, directory: Path, lock: dict):
        verify_model(directory, lock)
        import onnxruntime as ort
        from tokenizers import Tokenizer
        if ort.__version__ != '1.23.0' or importlib.metadata.version('tokenizers') != '0.22.1':
            raise ValueError('Use the pinned ONNX Runtime and tokenizers versions')
        self.lock = lock
        self.tokenizer = Tokenizer.from_file(str(directory / 'tokenizer.json'))
        # Upstream tokenizer.json contains 128-token truncation/padding defaults.
        # Explicitly disable BOTH before collecting the complete token sequence.
        self.tokenizer.no_truncation()
        self.tokenizer.no_padding()
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        self.session = ort.InferenceSession(str(directory / 'onnx/model.onnx'), sess_options=options, providers=['CPUExecutionProvider'])
        if {x.name for x in self.session.get_inputs()} != {'input_ids', 'attention_mask', 'token_type_ids'}:
            raise ValueError('Unexpected model inputs')
        self.cls, self.sep, self.pad = (self.tokenizer.token_to_id(t) for t in ['[CLS]', '[SEP]', '[PAD]'])
        if (self.cls, self.sep, self.pad) != (101, 102, 0):
            raise ValueError('Unexpected tokenizer special tokens')

    def encode(self, rows: list[dict], batch_size: int = 16) -> tuple[np.ndarray, list[dict], dict]:
        check_rows(rows)
        if not isinstance(batch_size, int) or not 1 <= batch_size <= 32:
            raise ValueError('Batch size must be 1–32')
        chunks, token_counts = [], []
        for i, row in enumerate(rows):
            enc = self.tokenizer.encode(row['text'], add_special_tokens=False)
            if len(enc.ids) > 20000:
                raise ValueError('Token envelope exceeded; no silent sampling')
            token_counts.append(len(enc.ids))
            for chunk in split_encoding(row['text'], enc.ids, enc.offsets):
                chunks.append({'row_index': i, 'id': row['id'], 'parent_id': row.get('parent_id'),
                               'parent_offset_base': row.get('parent_start'), **chunk})
        vectors = []
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start:start + batch_size]
            length = max(len(c['token_ids']) for c in batch) + 2
            ids = np.full((len(batch), length), self.pad, np.int64)
            mask = np.zeros_like(ids)
            for j, c in enumerate(batch):
                seq = [self.cls, *c['token_ids'], self.sep]
                ids[j, :len(seq)] = seq
                mask[j, :len(seq)] = 1
            hidden = self.session.run(['last_hidden_state'], {'input_ids': ids, 'attention_mask': mask, 'token_type_ids': np.zeros_like(ids)})[0]
            if hidden.shape != (*ids.shape, 384) or not np.isfinite(hidden).all():
                raise ValueError('Unexpected model output')
            # Official mask-aware mean pooling includes CLS/SEP, excludes padding.
            pooled = (hidden * mask[..., None]).sum(axis=1) / mask.sum(axis=1, keepdims=True)
            vectors.extend(normalized(pooled).astype(np.float32))
        total = np.zeros((len(rows), 384), np.float64)
        for c, vector in zip(chunks, vectors):
            total[c['row_index']] += (c['token_end'] - c['token_start']) * vector
        embeddings = normalized(total).astype(np.float32)
        for c in chunks:
            c['token_ids_sha256'] = sha(canonical(c.pop('token_ids')))
        return embeddings, chunks, {'passages': len(rows), 'chunks': len(chunks),
            'wordpieces': sum(token_counts), 'long_passages': sum(n > MAX_CONTENT_TOKENS for n in token_counts),
            'max_wordpieces': max(token_counts), 'truncated_wordpieces': 0,
            'pooling': 'attention-mask mean incl. CLS/SEP; normalize each chunk; content-token-count weighted mean; normalize passage',
            'tokenizer_normalization': 'Pinned upstream uncased WordPiece normalization; original text and Unicode offsets retained',
            'dropped_passages': 0, 'batch_size': batch_size, 'dimensions': 384}


def identities(rows: list[dict]) -> list[dict]:
    return [{k: r.get(k) for k in ['id', 'text_sha256', 'parent_id', 'meeting_id', 'parent_start', 'parent_end', 'split', 'language']} for r in rows]


def save_cache(out: Path, rows: list[dict], embeddings: np.ndarray, chunks: list[dict], audit: dict, lock: dict) -> dict:
    out.mkdir(parents=True, exist_ok=False)
    np.save(out / 'embeddings.npy', embeddings, allow_pickle=False)
    write_json(out / 'chunks.json', chunks)
    manifest = {'schema': 'un.semantic-cache.v1', 'engine': VERSION, 'model_lock_sha256': sha(canonical(lock)),
        'identities': identities(rows), 'audit': audit,
        'runtime': {name: importlib.metadata.version(name) for name in ['numpy', 'onnxruntime', 'tokenizers']},
        'implementation_sha256': sha(Path(__file__).read_bytes()),
        'files': {n: sha((out / n).read_bytes()) for n in ['embeddings.npy', 'chunks.json']}}
    write_json(out / 'manifest.json', manifest)
    return manifest


def load_cache(out: Path, rows: list[dict], lock: dict) -> tuple[np.ndarray, dict]:
    check_rows(rows)
    manifest = json.loads((out / 'manifest.json').read_text())
    if manifest.get('schema') != 'un.semantic-cache.v1' or manifest.get('model_lock_sha256') != sha(canonical(lock)) or manifest.get('identities') != identities(rows):
        raise ValueError('Cache source, order, or model identity mismatch')
    if manifest.get('engine') != VERSION or manifest.get('implementation_sha256') != sha(Path(__file__).read_bytes()):
        raise ValueError('Cache encoder implementation changed; regenerate explicitly')
    if set(manifest['files']) != {'embeddings.npy', 'chunks.json'}:
        raise ValueError('Unexpected cache file set')
    for name, h in manifest['files'].items():
        if sha((out / name).read_bytes()) != h:
            raise ValueError('Cache artifact digest mismatch')
    E = np.load(out / 'embeddings.npy', allow_pickle=False)
    if E.shape != (len(rows), 384) or E.dtype != np.float32 or not np.isfinite(E).all() or not np.allclose(np.linalg.norm(E, axis=1), 1, atol=1e-6):
        raise ValueError('Invalid cached embeddings')
    return E, manifest
