"""Reproducible, audit-only lexical exploration of the embargo review queue.

Separate selected-passage analysis; never substitutes for frozen D1 full-corpus methods.
"""
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import scipy
import sklearn
from sklearn.cluster import AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score

TOPICS = ['Embargo and blockade', 'Unilateral sanctions',
          'Terrorism-list designation', 'Extraterritorial restrictions']


def segment(r):
    return (r['raw_file'], r['json_pointer'])


def analyze(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    scoped = [r for r in rows if r['scope'] != 'other_week_proceedings']
    cuba = {segment(r) for r in scoped if r['topic'] == 'Cuba'}
    selected = [r for r in scoped if r['topic'] in TOPICS and segment(r) in cuba]
    # Collapse repeated topic hits at identical source offsets; retain their labels.
    grouped = {}
    for r in selected:
        identity = (r['statement_id'], r['start_char'], r['end_char'])
        if identity not in grouped:
            grouped[identity] = dict(r, topics=[])
        assert grouped[identity]['quote'] == r['quote']
        grouped[identity]['topics'].append(r['topic'])
    docs = sorted(grouped.values(), key=lambda r: (r['date'], r['statement_id'], int(r['start_char'])))
    if not 6 <= len(docs) <= 500:
        raise ValueError('Explorer requires 6–500 selected passages; no silent sampling.')
    vectorizer = TfidfVectorizer(stop_words='english', lowercase=True,
                                ngram_range=(1, 1), min_df=1, norm='l2', sublinear_tf=True)
    matrix = vectorizer.fit_transform([r['quote'] for r in docs])
    if (matrix.getnnz(axis=1) == 0).any():
        raise ValueError('Empty lexical vector; inspect source before analysis.')
    dense = matrix.toarray()
    pca = PCA(n_components=2, svd_solver='full')
    xy = pca.fit_transform(dense)
    terms = vectorizer.get_feature_names_out()
    partitions = []
    for k in range(2, min(6, len(docs)-1)+1):
        raw = AgglomerativeClustering(n_clusters=k, metric='cosine', linkage='average').fit_predict(dense)
        # Stable, size-ordered display IDs rather than arbitrary estimator IDs.
        order = sorted(set(raw), key=lambda g: (-int((raw == g).sum()), int(np.flatnonzero(raw == g)[0])))
        labels = np.array([order.index(g)+1 for g in raw])
        clusters = []
        for g in range(1, k+1):
            indices = np.flatnonzero(labels == g)
            mean = dense[indices].mean(axis=0)
            top = np.argsort(-mean, kind='stable')[:6]
            clusters.append({'id': g, 'n': len(indices), 'terms': [str(terms[t]) for t in top],
                             'weights': [float(mean[t]) for t in top]})
        partitions.append({'k': k, 'silhouette': float(silhouette_score(dense, labels, metric='cosine')),
                           'labels': labels.tolist(), 'clusters': clusters,
                           'smallest_cluster': min(c['n'] for c in clusters)})
    best = max(partitions, key=lambda p: (p['silhouette'], -p['k']))
    points = []
    for i, r in enumerate(docs):
        point = {field: r[field] for field in ['country', 'date', 'scope', 'quote', 'source_url',
                 'raw_file', 'raw_sha256', 'json_pointer', 'statement_id', 'start_char', 'end_char',
                 'timestamps_flagged', 'topics']}
        point.update(id=hashlib.sha256('|'.join([r['statement_id'], r['start_char'], r['end_char']]).encode()).hexdigest()[:12],
                     x=float(xy[i, 0]), y=float(xy[i, 1]), words=len(re.findall(r'\b\w+\b', r['quote'])))
        points.append(point)
    memberships = [{segment(r) for r in selected if r['topic'] == topic} for topic in TOPICS]
    overlap = [[{'intersection': len(a & b), 'union': len(a | b),
                 'jaccard': len(a & b)/len(a | b) if a | b else None}
                for b in memberships] for a in memberships]
    lengths = [p['words'] for p in points]
    result = {
        'schema': 'hlw.lexical-explorer.v1', 'audit_only': True, 'human_review_complete': False,
        'source': {'file': 'evidence.csv', 'sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest()},
        'methods': {'selection': 'HLW restriction-topic rows whose source segment also has a Cuba-topic match',
                    'unit': 'Unique statement_id/start_char/end_char passage; repeated topic hits collapsed',
                    'representation': 'English stop words; lowercase unigram TF-IDF; sublinear TF; smooth IDF; L2 norm; min_df=1; no truncation',
                    'projection': 'Centered PCA, full SVD, two dimensions',
                    'clustering': 'Average-linkage agglomerative clustering on full TF-IDF cosine distances, k=2..6',
                    'default_k': 'Highest observed cosine silhouette among tested k; descriptive selection, not validation',
                    'overlap': 'Jaccard = shared source segments / union of source segments; four restriction topics',
                    'versions': {'numpy': np.__version__, 'scipy': scipy.__version__, 'sklearn': sklearn.__version__}},
        'counts': {'topic_rows': len(selected), 'passages': len(points), 'source_segments': len({segment(r) for r in selected}),
                   'affiliation_labels': len({r['country'] for r in docs if r['country']}), 'vocabulary': len(terms),
                   'median_words': float(np.median(lengths)), 'q1_words': float(np.quantile(lengths, .25)),
                   'q3_words': float(np.quantile(lengths, .75)), 'min_words': min(lengths), 'max_words': max(lengths)},
        'variance_ratio': pca.explained_variance_ratio_.tolist(), 'default_k': best['k'],
        'points': points, 'partitions': partitions, 'topics': TOPICS, 'overlap': overlap,
        'limitations': ['Candidate selection is not a reviewed Cuba-embargo label.',
                       'Same-speaker passages and formulaic diplomatic wording are dependent observations.',
                       'Lexical clusters are not stance, alliance, sentiment, causality, or legal-status judgments.',
                       'Projection loses information; clustering uses full vectors, not plot coordinates.',
                       'No population inference, p-values, or confidence intervals from this selected corpus.',
                       'Recovered captions/ASR drafts are not yet merged; original D1 research gates remain unchanged.']}
    assert np.isfinite(xy).all()
    return result


def build(folder):
    folder = Path(folder)
    result = analyze(folder/'evidence.csv')
    payload = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    (folder/'explorer.json').write_text(payload+'\n', encoding='utf-8')
    (folder/'explorer-data.js').write_text('window.HLW_EXPLORER='+payload.replace('<', '\\u003c')+';\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder')
    result = build(parser.parse_args().folder)
    print(json.dumps({'counts': result['counts'], 'variance': result['variance_ratio'],
                      'partitions': [{k:p[k] for k in ['k', 'silhouette', 'smallest_cluster']} for p in result['partitions']]}))
