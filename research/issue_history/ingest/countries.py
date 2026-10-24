"""Exact ISO3 registry joins; recorded historical names remain separate."""
import csv
import hashlib
import io
import re
from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=4)
def _registry(path):
    raw=Path(path).read_bytes();rows=list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    mapping={}
    for row in rows:
        code=row.get("iso3");name=row.get("country")
        if not isinstance(code,str) or not re.fullmatch(r"[A-Z]{3}",code) or not name:raise ValueError("Invalid country registry row")
        if code in mapping:raise ValueError("Duplicate ISO3 country registry code")
        mapping[code]=name
    return mapping,hashlib.sha256(raw).hexdigest()

def map_country(code,recorded_name,registry=None):
    if not isinstance(code,str) or not re.fullmatch(r"[A-Z]{3}",code):raise ValueError("Explicit three-letter country code required")
    if not isinstance(recorded_name,str) or not recorded_name.strip():raise ValueError("Recorded source country name required")
    path=Path(registry) if registry else Path(__file__).resolve().parents[3]/"un"/"config"/"countries.csv"
    mapping,revision=_registry(str(path.resolve()))
    country=mapping.get(code)
    return {"country_id":country or "unmapped:"+code,"country_code":code,"recorded_country_name":recorded_name,"country_mapping_status":"registry_mapped" if country else "unmapped_code","country_registry_sha256":revision}
