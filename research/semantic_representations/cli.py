"""Private, source-bound reproducibility smoke and optional offline local inference.

No network, corpus acquisition, publication endpoint or automatic upload.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

try:
    from .pipeline import canonical, encode, validate_frame
    from .fixtures import (fixture_frame, FixtureEncoder, FIXTURE_MODEL, LEXICAL_MODEL,
                           SEMANTIC_SETTINGS, LEXICAL_SETTINGS, contrast_audit)
    from .local_model import LocalModelEncoder, model_identity
    from .comparison import neighborhood, clustering_sensitivity
    from .interchange import lexical_reference, readonly_browser
except ImportError:
    from pipeline import canonical, encode, validate_frame
    from fixtures import (fixture_frame, FixtureEncoder, FIXTURE_MODEL, LEXICAL_MODEL,
                          SEMANTIC_SETTINGS, LEXICAL_SETTINGS, contrast_audit)
    from local_model import LocalModelEncoder, model_identity
    from comparison import neighborhood, clustering_sensitivity
    from interchange import lexical_reference, readonly_browser

ROOT=Path(__file__).resolve().parents[2]


def private_path(path: Path):
    resolved=path.resolve()
    if resolved.is_relative_to(ROOT):
        raise ValueError("private caches and research outputs must not be stored in public repository")
    return resolved


def execute(mode: str, cache: Path, frame_file=None, model_dir=None, lexical_file=None, k=3) -> dict:
    cache=private_path(cache)
    if mode == "synthetic":
        frame=fixture_frame()
        semantic=encode(frame,FIXTURE_MODEL,SEMANTIC_SETTINGS,FixtureEncoder(),cache/"synthetic-semantic")
        lexical=encode(frame,LEXICAL_MODEL,LEXICAL_SETTINGS,FixtureEncoder(lexical=True),cache/"synthetic-lexical")
        # Length stress is a separate source-bound fixture (never cross-joined as if
        # the altered source text were the same observation).
        long_frame=fixture_frame()
        raw=long_frame["rows"][0]
        raw["text"]="Adaptation resilience "*600
        try:
            from .pipeline import sha as _sha
        except ImportError:
            from pipeline import sha as _sha
        raw["text_sha256"]=_sha(raw["text"].encode("utf-8"))
        long_result=encode(long_frame,FIXTURE_MODEL,SEMANTIC_SETTINGS,FixtureEncoder(),cache/"synthetic-length")
        summary={"fixture_only":True,"model_checkpoint_execution":"NOT_RUN",
                 "synthetic_contrasts":contrast_audit(semantic),
                 "synthetic_length_sensitivity":{"original_tokens":semantic["rows"][0]["tokens"],
                     "long_tokens":long_result["rows"][0]["tokens"],
                     "long_chunks":long_result["rows"][0]["chunks"],
                     "truncated_wordpieces":0,"status":"synthetic_fixture_only"}}
    elif mode == "local":
        if frame_file is None or model_dir is None:
            raise ValueError("local mode requires verified frame and model directory")
        frame=json.loads(Path(frame_file).read_text("utf-8"))
        validate_frame(frame)
        encoder=LocalModelEncoder(model_dir)
        settings={"metric":"cosine","pooling":"upstream_chunk_token_weighted",
                  "max_content_tokens":254,"preprocessing":"verified_uncased_wordpiece_original_utf8",
                  "encoder_git_blob":"61929a4db62f82ae3f70a098dd87825d38f35aca"}
        semantic=encode(frame,model_identity(),settings,encoder,cache/"pinned-semantic")
        lexical=None
        if lexical_file is not None:
            saved=json.loads(Path(lexical_file).read_text("utf-8"))
            lexical=lexical_reference(frame,saved)
        summary={"fixture_only":False,"model_checkpoint_execution":"LOCAL_ONLY",
                 "full_checkpoint_hash_verified":True}
    else:
        raise ValueError("unknown mode")
    summary["semantic_coverage"]=semantic["coverage"]
    summary["semantic_attempts"]=semantic["failure_ledger"]
    summary["semantic_readonly"]=readonly_browser(semantic,public=mode=="synthetic")
    if lexical is not None:
        if semantic["coverage"]["not_fitted"]:
            summary["comparison_status"]="withheld: partial semantic fit"
        else:
            summary["comparison_status"]="descriptive"
            summary["neighborhood"]=neighborhood(lexical,semantic,k,"self")
            if semantic["coverage"]["eligible"]>=k+1 and k>=2:
                summary["clustering"]=clustering_sensitivity(lexical,semantic,k)
    return summary


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("synthetic","local"))
    parser.add_argument("--cache",type=Path,required=True,help="Private local cache root OUTSIDE repository")
    parser.add_argument("--frame",type=Path)
    parser.add_argument("--model-dir",type=Path)
    parser.add_argument("--lexical",type=Path,help="Optional verified saved lexical fit metadata/vectors")
    parser.add_argument("--output",type=Path,required=True,help="Private metadata output OUTSIDE repository")
    parser.add_argument("--k",type=int,default=3)
    args=parser.parse_args(argv)
    out=private_path(args.output)
    if out.exists():
        raise FileExistsError("output already exists; never overwrite attempts")
    report=execute(args.mode,args.cache,args.frame,args.model_dir,args.lexical,args.k)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("x",encoding="utf-8") as stream:
        stream.write(canonical(report).decode("utf-8")+"\n")
    print(json.dumps({"status":"completed","mode":args.mode,"fixture_only":report["fixture_only"],
                      "encoded":report["semantic_coverage"]["encoded"],
                      "not_fitted":report["semantic_coverage"]["not_fitted"],
                      "comparison_status":report.get("comparison_status","not_requested"),"output":str(out)},sort_keys=True))
    if report["semantic_coverage"]["not_fitted"]:
        return 2
    return 0


if __name__=="__main__":
    sys.exit(main())
