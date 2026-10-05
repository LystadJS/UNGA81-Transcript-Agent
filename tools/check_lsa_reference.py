"""Independent NumPy SVD and scikit-learn neighborhood checks on public text.

Usage: python tools/check_lsa_reference.py saved-corpus.json
The first 72 unique included passages are a bounded numerical fixture. This
checks implementations, not the substantive validity of any resulting groups.
"""
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from sklearn.manifold import trustworthiness


def check(path):
    script = r"""
const fs=require('node:fs'),A=require('./site/analysis-core.js'),C=require('./site/cluster-core.js'),M=require('./site/representation-metrics.js');
(async()=>{
  const corpus=A.validateCorpus(JSON.parse(fs.readFileSync(process.argv[1],'utf8')));
  const dates=corpus.records.map(r=>r.date).sort();
  const result=await A.analyze(corpus,{topic:'',start:dates[0],end:dates.at(-1),scope:'all',region:'All regions',methods:['tfidf']});
  const records=result.matched.slice(0,72),vectors=A.tfidf(records).vectors.filter(v=>v.size);
  const pca=C.pca(vectors,20),lsa=C.lsa(vectors,20);
  const random=C.rng(987),x=Array.from({length:23},()=>Array.from({length:6},()=>random()*4-2));
  const y=x.map(r=>[r[0]+r[1]*r[2],r[3]-r[4]*r[5]]);
  console.log(JSON.stringify({vectors:vectors.map(v=>[...v]),pca,lsa,x,y,
    metrics:M.agreement(M.order(M.denseDistances(x)),M.order(M.denseDistances(y)),4)}));
})().catch(e=>{console.error(e);process.exitCode=1;});
"""
    repo = Path(__file__).resolve().parents[1]
    output = subprocess.run(["node", "-e", script, str(Path(path).resolve())], cwd=repo,
                            check=True, capture_output=True, text=True, encoding="utf-8")
    result = json.loads(output.stdout)
    terms = sorted({term for row in result["vectors"] for term, _ in row})
    term_index = {term: i for i, term in enumerate(terms)}
    x = np.zeros((len(result["vectors"]), len(terms)))
    for i, row in enumerate(result["vectors"]):
        for term, weight in row:
            x[i, term_index[term]] = weight
    checks = {}
    for method in ["pca", "lsa"]:
        source = x - x.mean(axis=0) if method == "pca" else x
        u, singular, vh = np.linalg.svd(source, full_matrices=False)
        fit = result[method]
        k = fit["components"]
        expected = u[:, :k] * singular[:k]
        actual = np.array(fit["scores"])
        geometry = lambda z: np.sum((z[:, None, :] - z[None, :, :]) ** 2, axis=2)
        distance_error = float(np.max(np.abs(geometry(expected) - geometry(actual))))
        ratios = expected.var(axis=0) / x.var(axis=0).sum()
        variance_error = float(np.max(np.abs(ratios - fit["explained_variance_ratio"])))
        assert distance_error < 1e-9 and variance_error < 1e-9
        checks[method] = {"components": k, "max_squared_distance_error": distance_error,
                          "max_centered_variance_ratio_error": variance_error}
        if method == "lsa":
            energy = np.sum(singular[:k] ** 2) / np.sum(x ** 2)
            reconstruction = expected @ vh[:k]
            residual = np.linalg.norm(x - reconstruction) / np.linalg.norm(x)
            assert abs(energy - fit["retained_energy"]) < 1e-10
            assert abs(residual - fit["relative_reconstruction_error"]) < 1e-10
            loading_error = 0.0
            for c, description in enumerate(fit["component_terms"]):
                anchor = np.argmax(np.abs(expected[:, c]))
                sign = -1 if expected[anchor, c] < 0 else 1
                for term in description["positive"] + description["negative"]:
                    loading_error = max(loading_error, abs(sign * vh[c, term_index[term["term"]]] - term["weight"]))
            assert loading_error < 1e-9
            checks[method].update({"retained_energy_error": float(abs(energy - fit["retained_energy"])),
                                   "reconstruction_error_difference": float(abs(residual - fit["relative_reconstruction_error"])),
                                   "max_signed_loading_error": float(loading_error)})
    high, low = np.array(result["x"]), np.array(result["y"])
    trust = trustworthiness(high, low, n_neighbors=4)
    continuity = trustworthiness(low, high, n_neighbors=4)
    assert abs(trust - result["metrics"]["trustworthiness"]) < 1e-12
    assert abs(continuity - result["metrics"]["continuity"]) < 1e-12
    checks["neighborhood_metrics"] = {"trustworthiness": trust, "continuity": continuity,
                                      "reference": "scikit-learn trustworthiness, both directions on untied geometry"}
    return {"passages": len(x), "vocabulary": len(terms), "checks": checks,
            "reference": "NumPy full SVD; sign-invariant geometry plus oriented loadings"}


if __name__ == "__main__":
    print(json.dumps(check(sys.argv[1]), indent=2))
