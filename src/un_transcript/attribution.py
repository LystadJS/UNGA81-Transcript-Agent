"""Conservative, source-evidenced attribution candidates, never identity proof.

Rules only propose national capacity when the speaker expressly identifies the
same recorded country. These rules need empirical attribution evaluation as
part of the accepted stance pipeline; the registry alone establishes no stance.
"""
from __future__ import annotations

import csv
from functools import lru_cache
import hashlib
from pathlib import Path
import re
import unicodedata

METHOD_VERSION = "explicit-national-capacity-1"


def _normalize(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


@lru_cache(maxsize=1)
def _registry():
    path = Path(__file__).resolve().parents[2] / "un/config/countries.csv"
    raw = path.read_bytes()
    aliases = {}
    by_country = {}
    for row in csv.DictReader(raw.decode("utf-8-sig").splitlines()):
        iso = row["iso3"]
        names = {row["country"], iso, *row.get("aliases", "").split("|")}
        for name in names:
            if name.strip():
                aliases.setdefault(_normalize(name),set()).add(iso)
                by_country.setdefault(iso,set()).add(name)
    unambiguous = {name:next(iter(codes)) for name,codes in aliases.items() if len(codes)==1}
    return unambiguous,by_country,hashlib.sha256(raw).hexdigest()


# Require a direct first-person declaration at a sentence boundary. Quoted,
# reported, hypothetical and negative clauses do not match these productions.
PREFIX = r"(?:I\s+(?:speak|am\s+speaking|have\s+the\s+honou?r\s+to\s+speak)|we\s+(?:speak|are\s+speaking))\s+on\s+behalf\s+of\s+(?:the\s+)?"
DECLARATION = re.compile(r"^\s*(?:"+PREFIX+r"(?P<object>[^,;.!?]+)|on\s+behalf\s+of\s+(?:the\s+)?(?P<opening>[^,;.!?]+),\s*(?:I|we)\b)",re.I)
QUOTES = re.compile(r'"[^"\n]*"|“[^”\n]*”|‘[^’\n]*’|(?<!\w)\x27[^\x27\n]*\x27(?!\w)')
GROUP = re.compile(r"\b(?:group|union|coalition|movement|member\s+states|countries|delegations|states\s+parties|community|league|alliance|g-?77|g-?4|g-?20|AOSIS|CARICOM|NAM|ASEAN|EU|OIC|CELAC)\b",re.I)


def infer_capacity(segment):
    """Return a copy with derived fields; retain every original source field.

    Offsets refer to original segment text, in Unicode code points, end
    exclusive. A source-recorded national capacity is preserved unless an
    explicit direct collective declaration contradicts it. Unknown remains
    unknown when this small grammar cannot establish a positive match.
    """
    result = dict(segment)
    text = segment.get("text", "")
    if not isinstance(text,str):
        raise ValueError("Segment text must be a string")
    declared = segment.get("capacity","unknown")
    kind = "national" if declared in ("national","individual_country") else "collective" if declared=="collective" else "unknown"
    aliases,names,registry_sha = _registry()
    recorded = segment.get("country") or ""
    country = aliases.get(_normalize(recorded)) if isinstance(recorded,str) else None
    result.update(attribution_kind=kind,canonical_country=country,
                  attribution_evidence=[],attribution_method_version=METHOD_VERSION,
                  attribution_registry_sha256=registry_sha,
                  attribution_status="recorded_capacity" if kind!="unknown" else "unresolved")
    quoted = [(m.start(),m.end()) for m in QUOTES.finditer(text)]
    national = []
    collective = []
    for sentence in re.finditer(r"[^.!?\n]+[.!?]?",text):
        content=sentence.group()
        # Quoted material is evidence about the quoted speaker, not automatically
        # the current speaker; abstaining across the whole sentence is deliberate.
        if any(a < sentence.end() and b > sentence.start() for a,b in quoted):
            continue
        if re.search(r"[\"“”‘’]",content):
            continue
        claim = DECLARATION.match(content)
        if claim:
            target=(claim.group("object") or claim.group("opening") or "").strip()
            # A recognized single national government/delegation is distinct
            # from "France and ..." or an expressly collective body.
            national_target = re.fullmatch(r"(?:Government|delegation)\s+of\s+(?:the\s+)?(.+)",target,re.I)
            target_country = aliases.get(_normalize(national_target.group(1))) if national_target else None
            multiple_countries = [aliases.get(_normalize(part)) for part in re.split(r"\s+and\s+",target,flags=re.I)]
            if target_country is not None:
                if target_country==country:
                    national.append((sentence.start()+claim.start(),sentence.start()+claim.end()))
            elif GROUP.search(target) or national_target and re.search(r"\band\b",national_target.group(1),re.I) or len(multiple_countries)>1 and all(multiple_countries):
                collective.append((sentence.start()+claim.start(),sentence.start()+claim.end()))
        # A precise country alias is mandatory; there is no fuzzy country match.
        if country:
            for name in sorted(names[country],key=len,reverse=True):
                if aliases.get(_normalize(name)) != country:
                    continue
                alias = re.escape(name).replace(r"\ ",r"\s+").replace(" ",r"\s+")
                as_rep = re.match(r"^\s*(?:as\s+(?:the\s+)?representative\s+of\s+(?:the\s+)?"+alias+r",\s*(?:I|we)\b|I\s+(?:speak|am\s+speaking)\s+as\s+(?:the\s+)?representative\s+of\s+(?:the\s+)?"+alias+r"(?=\s*[,;.!?]|\s*$))",content,re.I)
                if as_rep:
                    national.append((sentence.start()+as_rep.start(),sentence.start()+as_rep.end()))
                    break
    if collective:
        result["attribution_kind"]="collective"
        selected=collective
        result["attribution_status"]="candidate_rule_requires_evaluation"
    elif kind=="unknown" and national:
        result["attribution_kind"]="national"
        selected=national
        result["attribution_status"]="candidate_rule_requires_evaluation"
    else:
        selected=[]
    result["attribution_evidence"]=[{"start":a,"end":b,"quote":text[a:b]} for a,b in sorted(set(selected))]
    return result
