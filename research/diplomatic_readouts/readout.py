"""Offline, deterministic, evidence-first research readouts (stdlib only)."""
import hashlib
import html
import json
from pathlib import Path

TEMPLATES = ("emerging_themes", "discourse_communities", "changing_actor_profiles", "boundary_cases", "source_backed_anomalies")
REQUIRED = ("population", "period", "denominator", "exclusions", "missingness")
RESTRICTIONS = ("Language similarity is not policy agreement.", "Clustering is not coordination.", "Temporal movement is not necessarily diplomatic realignment.")

def validate(report):
    errors = []
    if report.get("template") not in TEMPLATES:
        errors.append("unknown template")
    for key in REQUIRED:
        if key not in report or report[key] is None:
            errors.append("missing disclosure: " + key)
    sources = report.get("sources", [])
    ids = [s.get("id") for s in sources]
    if len(ids) != len(set(ids)) or any(not x for x in ids):
        errors.append("duplicate or missing source identity")
    accepted = {s["id"]: s for s in sources if s.get("accepted") is True and s.get("sha256") and len(s["sha256"]) == 64 and s.get("privacy") == "public"}
    for s in sources:
        if "passage" in s or "text" in s:
            errors.append("embedded source passage forbidden")
    for finding in report.get("findings", []):
        refs = finding.get("supporting", []) + finding.get("contrary", [])
        if not refs:
            errors.append("finding lacks evidence references")
        for ref in refs:
            if ref.get("source_id") not in accepted or not isinstance(ref.get("start"), int) or not isinstance(ref.get("end"), int) or ref["start"] < 0 or ref["end"] <= ref["start"]:
                errors.append("invalid or unaccepted source pointer")
        if finding.get("country_attribution") and not finding.get("country_attribution_verified"):
            errors.append("unverified country attribution")
        if finding.get("stance") and not (finding.get("proposition") and finding.get("stance_evidence_verified")):
            errors.append("stance lacks verified proposition-specific evidence")
    return sorted(set(errors))

def normalize(report):
    r = json.loads(json.dumps(report))
    errors = validate(r)
    for source in r.get("sources", []):
        source.pop("text", None)
        source.pop("passage", None)
    gates = r.get("gates", {})
    permitted = bool(gates.get("source") and gates.get("statistical") and gates.get("review")) and not errors
    for f in r.get("findings", []):
        if not permitted or not f.get("interpretation_supported", False):
            f["interpretation"] = None
            f["status"] = "withheld"
        else:
            f["status"] = "exploratory"
    r["release_state"] = "qualified_experimental" if permitted else "withheld"
    r["validation_errors"] = errors
    r["restrictions"] = list(RESTRICTIONS)
    return r

def render(report, format="json"):
    r = normalize(report)
    if format == "json":
        return json.dumps(r, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    lines = ["# " + str(r.get("title", "Research readout")), "", "Status: " + r["release_state"]]
    for k in REQUIRED:
        lines.append(k.title() + ": " + json.dumps(r.get(k), ensure_ascii=False, sort_keys=True))
    lines.extend(["", "## Findings"])
    for f in r.get("findings", []):
        lines.append("- " + str(f.get("label", "Unnamed")) + " [" + f["status"] + "]: " + str(f.get("interpretation") or "Interpretation withheld"))
        for kind in ("supporting", "contrary"):
            for ref in f.get(kind, []):
                lines.append("  - " + kind + ": " + str(ref["source_id"]) + " [" + str(ref["start"]) + ":" + str(ref["end"]) + "]")
    for key in ("sensitivity", "alternative_explanations", "uncertainty", "reviewer_interpretation"):
        lines.extend(["", "## " + key.replace("_", " ").title(), str(r.get(key) or "Not established")])
    lines.extend(["", "## Restrictions", *("- " + x for x in RESTRICTIONS)])
    if r["validation_errors"]:
        lines.extend(["", "## Validation errors", *("- " + x for x in r["validation_errors"])])
    md = "\n".join(lines) + "\n"
    if format == "markdown":
        return md
    if format == "html":
        return '<!doctype html><html lang="en"><meta charset="utf-8"><title>Research readout</title><body><main><pre>' + html.escape(md) + '</pre></main></body></html>\n'
    raise ValueError("unsupported format")

def export(report, directory):
    dest = Path(directory)
    dest.mkdir(parents=True, exist_ok=True)
    result = {}
    for fmt, ext in (("json", "json"), ("markdown", "md"), ("html", "html")):
        data = render(report, fmt).encode("utf-8")
        path = dest / ("readout." + ext)
        path.write_bytes(data)
        result[ext] = hashlib.sha256(data).hexdigest()
    return result
