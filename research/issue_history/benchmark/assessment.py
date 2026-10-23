"""Receipt-gated extraction assessment; synthetic diagnostics cannot promote models."""
from collections import Counter

CLASSES=("support","oppose","qualified","unknown")

def assess(items,predictions,*,provenance="synthetic",minimum_per_class=10,minimum_accuracy=.9,split_protocol=None):
    if provenance not in ("synthetic","owner_confirmed_source_benchmark"):raise ValueError("Unknown benchmark provenance")
    if type(minimum_per_class) is not int or minimum_per_class<1:raise ValueError("Invalid minimum class coverage")
    if not 0<minimum_accuracy<=1:raise ValueError("Invalid accuracy gate")
    ids=[i["record_id"] for i in items]
    if len(ids)!=len(set(ids)):raise ValueError("Duplicate benchmark record IDs")
    predictions_by_id={p["record_id"]:p for p in predictions}
    if len(predictions_by_id)!=len(predictions):raise ValueError("Duplicate candidate predictions")
    if set(predictions_by_id)-set(ids):raise ValueError("Prediction outside benchmark")
    source_splits={};failures=[];class_dimensions=Counter();counts=Counter();correct=Counter();abstained=Counter();errors=Counter();eligible=[]
    from datetime import date
    temporal_ok=isinstance(split_protocol,dict) and split_protocol.get("version")=="source-blocked-temporal-v1"
    if temporal_ok:
        try:
            date.fromisoformat(split_protocol["train_end"]);date.fromisoformat(split_protocol["validation_end"])
            temporal_ok=split_protocol["train_end"]<split_protocol["validation_end"]
        except (ValueError,KeyError,TypeError):temporal_ok=False
    if not temporal_ok:failures.append("missing_temporal_split_protocol")
    for item in items:
        split=item.get("split")
        if split not in ("train","validation","test"):failures.append("invalid_split");continue
        if temporal_ok:
            try:
                date.fromisoformat(item["date"])
                expected="train" if item["date"]<=split_protocol["train_end"] else "validation" if item["date"]<=split_protocol["validation_end"] else "test"
                if split!=expected:failures.append("temporal_split_leakage")
            except (ValueError,KeyError,TypeError):failures.append("invalid_temporal_date")
        source=item.get("source_id")
        if not source:failures.append("missing_source_identity");continue
        if source in source_splits and source_splits[source]!=split:failures.append("source_split_leakage")
        source_splits[source]=split
        source_hash=item.get("text_sha256")
        if not isinstance(source_hash,str) or len(source_hash)!=64 or any(c not in "0123456789abcdef" for c in source_hash):failures.append("missing_source_hash")
        label=item.get("annotation")
        confirmed=item.get("review_state")=="owner_confirmed" and bool(item.get("owner_confirmation_id"))
        if not confirmed or not isinstance(label,dict):failures.append("unconfirmed_labels");continue
        if label.get("stance") not in CLASSES or label.get("attribution") not in ("national","collective","unclear") or not label.get("policy_id") or not label.get("context_id"):
            failures.append("invalid_labels");continue
        if split!="test":continue
        eligible.append(item)
        target=label["stance"];counts[target]+=1;p=predictions_by_id.get(item["record_id"])
        if p is not None and p.get("text_sha256")!=source_hash:failures.append("prediction_source_hash_mismatch");p=None
        abstain=p is None or p.get("abstain") is True
        if abstain:abstained[target]+=1
        for key in ("attribution","stance","policy_id","context_id"):
            if not abstain and p.get(key)==label[key]:correct[key]+=1;class_dimensions[(target,key)]+=1
            else:errors[key]+=1
        if not abstain and all(p.get(k)==label[k] for k in ("attribution","stance","policy_id","context_id")):correct[target]+=1
    n=len(eligible)
    metrics={key:{"correct":correct[key],"denominator":n,"accuracy":correct[key]/n if n else None} for key in ("attribution","stance","policy_id","context_id")}
    per_class={c:{"count":counts[c],"joint_correct":correct[c],"joint_accuracy":correct[c]/counts[c] if counts[c] else None,"dimension_accuracy":{k:class_dimensions[(c,k)]/counts[c] if counts[c] else None for k in ("attribution","stance","policy_id","context_id")},"abstentions":abstained[c],"abstention_rate":abstained[c]/counts[c] if counts[c] else None} for c in CLASSES}
    if provenance!="owner_confirmed_source_benchmark":failures.append("synthetic_not_promotable")
    if not n:failures.append("no_confirmed_test_items")
    if any(counts[c]<minimum_per_class for c in CLASSES):failures.append("insufficient_class_coverage")
    if any(m["accuracy"] is None or m["accuracy"]<minimum_accuracy for m in metrics.values()):failures.append("accuracy_gate_failed")
    # Correctness includes missing predictions as failures: abstention cannot inflate accuracy.
    if any(v["joint_accuracy"] is None or v["joint_accuracy"]<minimum_accuracy for v in per_class.values()):failures.append("class_accuracy_gate_failed")
    return {"schema":"un.issue-extraction-assessment.v1","status":"eligible_for_integration_review" if not failures else "withheld","provenance":provenance,"test_count":n,"metrics":metrics,"per_class":per_class,"failures":sorted(set(failures)),"promotion_applied":False,"limitations":["This assessment never changes a deployed extractor.","Owner receipts must be genuine; the tool does not authenticate a receipt issuer.","Calibration and production resource acceptance require separate evidence."]}
