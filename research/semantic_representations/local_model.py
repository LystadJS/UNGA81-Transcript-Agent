"""Optional strictly offline Sentence Transformers inference; no remote endpoint."""
def load_local(checkpoint_path, revision, expected_config_sha256):
    import hashlib
    from pathlib import Path
    path=Path(checkpoint_path)
    if not path.is_dir(): raise ValueError("local checkpoint required")
    config=path/"config.json"
    if not config.is_file() or hashlib.sha256(config.read_bytes()).hexdigest()!=expected_config_sha256:
        raise ValueError("checkpoint config checksum mismatch")
    import os
    os.environ["HF_HUB_OFFLINE"]="1"
    os.environ["TRANSFORMERS_OFFLINE"]="1"
    from sentence_transformers import SentenceTransformer
    model=SentenceTransformer(str(path),local_files_only=True,trust_remote_code=False,device="cpu")
    return lambda passages: model.encode(passages,batch_size=16,show_progress_bar=False,convert_to_numpy=True,normalize_embeddings=False).tolist()
