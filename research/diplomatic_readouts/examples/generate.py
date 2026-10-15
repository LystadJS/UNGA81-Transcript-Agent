"""Synthetic-only demonstration of complete, partial and abstaining readouts."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from readout import export, normalize

def sample():
    return {
        "title": "FICTIONAL thematic comparison",
        "template": "emerging_themes",
        "population": "Two fictional, synthetic source records",
        "period": "Fictional periods A and B",
        "denominator": 2,
        "exclusions": 0,
        "missingness": 0,
        "sources": [{"id": "synthetic:source:A", "sha256": "a"*64, "accepted": True, "privacy": "public"}],
        "gates": {"source": True, "statistical": True, "review": True},
        "findings": [{"label": "Fictional co-occurrence", "supporting": [{"source_id": "synthetic:source:A", "start": 0, "end": 4}], "contrary": [], "interpretation": "Fictional exploratory pattern, not policy agreement", "interpretation_supported": True}],
        "uncertainty": "Fictional uncertainty; not calibrated",
        "sensitivity": "Fictional alternative segmentation not evaluated",
        "alternative_explanations": "Fictional document composition",
        "reviewer_interpretation": "Synthetic fixture only"
    }

def main(root):
    for name in ("complete", "partial", "abstaining"):
        r = sample()
        if name == "partial":
            r["gates"]["statistical"] = False
            r["uncertainty"] = "Statistical calibration withheld"
        if name == "abstaining":
            r["sources"][0]["accepted"] = False
            r["findings"][0]["supporting"] = []
            r["missingness"] = 1
        target = Path(root) / name
        export(r, target)
        state = normalize(r)["release_state"]
        assert state == ("qualified_experimental" if name == "complete" else "withheld")
        print(name, state, str(target))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "synthetic-output")
