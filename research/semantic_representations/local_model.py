"""Opt-in, strictly offline Sentence Transformers inference.

Checkpoint identity must originate from an externally authenticated exact-revision
manifest listing every model and tokenizer file with SHA-256. No model download.
"""
import os
from controls import verify_checkpoint, token_windows

def load_local(checkpoint_path, manifest):
    manifest_sha256 = verify_checkpoint(checkpoint_path, manifest)
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(str(checkpoint_path), local_files_only=True,
                                trust_remote_code=False, device="cpu")
    model._unga_manifest_sha256 = manifest_sha256
    return model

def encode_local(model, text, window_tokens=126, overlap=16, batch_size=16):
    """Token-aware, explicit pooling; reserve capacity for tokenizer special tokens.

    This method is intentionally restricted to tokenizers where a round trip
    from non-special token IDs can be decoded without dropping content.
    """
    if not 0 <= overlap < window_tokens or batch_size < 1:
        raise ValueError("window configuration")
    tokenizer = model.tokenizer
    allowance = int(getattr(tokenizer, "model_max_length", 0)) - tokenizer.num_special_tokens_to_add(pair=False)
    if allowance <= 0 or window_tokens > allowance:
        raise ValueError("window exceeds checkpoint capacity")
    windows = token_windows(text, tokenizer, window_tokens, overlap)
    passages = [tokenizer.decode(w["token_ids"], skip_special_tokens=False) for w in windows]
    vectors = model.encode(passages, batch_size=batch_size, show_progress_bar=False,
                           convert_to_numpy=True, normalize_embeddings=False)
    import math
    weights = [w["end_token"]-w["start_token"] if i==0 else
               w["end_token"]-w["start_token"]-min(overlap,w["end_token"]-w["start_token"])
               for i,w in enumerate(windows)]
    if any(x<=0 for x in weights): raise ValueError("invalid pooling weights")
    denominator = sum(weights)
    pooled = [sum(float(v[j])*w for v,w in zip(vectors,weights))/denominator
              for j in range(len(vectors[0]))]
    norm = math.sqrt(sum(x*x for x in pooled))
    if not math.isfinite(norm) or not norm: raise ValueError("nonfinite/zero vector")
    return {"vector":[x/norm for x in pooled],
            "window_count":len(windows),"manifest_sha256":model._unga_manifest_sha256,
            "overlap_tokens":overlap,"window_tokens":window_tokens}
