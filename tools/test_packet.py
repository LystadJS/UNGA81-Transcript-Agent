"""Freeze a random, unlabelled September 28 packet after lexical duplicate screening."""
import argparse, hashlib, json, random, re, secrets
from collections import Counter
from pathlib import Path
import review_data as rd
import reviewed_loader as loader
import pilot_review as pilot
import later_review

def tokens(text): return re.findall(r'\w+',text.casefold())
def shingles(text):
    t=tokens(text)
    return {tuple(t[i:i+5]) for i in range(max(0,len(t)-4))}
def duplicate(a,b):
    if tokens(a)==tokens(b): return 'normalized_exact'
    x,y=shingles(a),shingles(b)
    if min(len(x),len(y))>=20:
        overlap=len(x&y)
        if overlap/min(len(x),len(y))>=.8 or overlap/len(x|y)>=.6: return 'near_duplicate'
    return None

def prepare(candidates, development, output, dates=('2026-09-28',), seed=28092026, packet_kind='held_out_test', extra_references=()):
    output=Path(output)
    if output.exists():raise FileExistsError(output)
    bundles=[loader.load_bundle(p) for p in development]
    reviewed=[r for b in bundles for r in b['records']]
    countries={r['iso3'] for r in reviewed}
    for root in map(Path,extra_references):
        countries.update(s['iso3'] for s in rd.rows(root/'sources.csv')[1])
    # Screen against all chunks in consumed development source documents as well
    # as reviewed quotations. This conservatively covers context shown in forms.
    comparison=[r['quote'] for r in reviewed]
    for root in map(Path,list(development)+list(extra_references)):
        for source in rd.rows(root/'sources.csv')[1]:
            text=loader.safe(root,source['text_path']).read_text(encoding='utf-8')
            words=list(re.finditer(r'\S+',text))
            for start in range(0,len(words),75):
                chunk=words[start:start+150]
                if chunk:comparison.append(text[chunk[0].start():chunk[-1].end()])
    candidates=Path(candidates);records=json.loads(candidates.read_text(encoding='utf-8'))
    day=[r for r in records if r['speech_date'] in dates]
    eligible=[r for r in day if r['country_id'] not in countries]
    for r in eligible:
        if hashlib.sha256(r['text'].encode()).hexdigest()!=r['text_sha256']:raise ValueError('Changed candidate source')
    replay=output.parent/(output.name+'-input.json');replay.parent.mkdir(parents=True,exist_ok=True)
    with replay.open('x',encoding='utf-8') as f:json.dump([dict(iso3=r['country_id'],date=r['speech_date'],text=r['text'],source_url=r['source_url']) for r in eligible],f)
    rd.initialize(output,replay)
    passages=rd.rows(output/'passages.csv')[1];rng=random.Random(seed);rng.shuffle(passages)
    refs=[(text,shingles(text),tokens(text)) for text in comparison]
    kept=[];removed=Counter()
    for p in passages:
        tok=tokens(p['quote']);a=shingles(p['quote']);reason=None
        for _,b,bt in refs:
            if tok==bt:reason='normalized_exact';break
            if min(len(a),len(b))>=20:
                n=len(a&b)
                if n/min(len(a),len(b))>=.8 or n/len(a|b)>=.6:reason='near_duplicate';break
        if not reason:
            reason=next((duplicate(p['quote'],q['quote']) for q in kept if duplicate(p['quote'],q['quote'])),None)
            if reason:reason='within_test_'+reason
        if reason:removed[reason]+=1
        else:kept.append(p)
    if len(kept)<24:raise ValueError('Fewer than 24 eligible passages')
    selected=kept[:24];rd.write_csv(output/'passages.csv',rd.SCHEMAS['passages'].split(),selected)
    ids={p['source_id'] for p in selected};sources=rd.rows(output/'sources.csv')[1];when=pilot.now()
    for s in sources:s['available_at']=when
    rd.write_csv(output/'sources.csv',rd.SCHEMAS['sources'].split(),[s for s in sources if s['source_id'] in ids])
    props=rd.rows(Path(development[0])/'propositions.csv')[1];rd.write_csv(output/'propositions.csv',rd.SCHEMAS['propositions'].split(),props)
    policy=json.loads((output/'bundle.json').read_text());policy.update(dataset_kind='real',review_mode='single_reviewer_pilot',cutoff=when,human_review_complete=False,role=packet_kind)
    (output/'bundle.json').write_text(json.dumps(policy,indent=2),encoding='utf-8')
    meta=dict(schema='un.pilot.v1',packet_kind=packet_kind,sampling_method='random_after_exclusions',csrf=secrets.token_urlsafe(24),review_complete=False,count=24,selected_ids=[p['passage_id'] for p in selected],seed=seed)
    (output/'pilot.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    report=dict(candidate_records=len(day),country_overlap_exclusions=len(day)-len(eligible),screened_passages=len(passages),excluded_passages=dict(removed),eligible_passages=len(kept),selected_passages=24,selected_countries=len(ids),selected_dates=['2026-09-28'],development_bundle_hashes=[b['bundle_sha256'] for b in bundles],candidate_sha256=pilot.sha(candidates),seed=28092026,method='Seeded shuffle, duplicate exclusions, first 24 survivors; no keyword sampling',duplicate_rule='Casefolded word equality; 5-word shingle containment >=0.8 or Jaccard >=0.6, minimum 20 shingles',comparison_scope='48 reviewed development quotes plus 150-word windows at stride 75 across their full source texts; within-test comparisons',limitation='Lexical screen cannot guarantee absence of paraphrases or semantic duplication. Human speech-boundary review still required.',human_review_complete=False,training_authorized=False)
    report['frozen_packet_sha256']={name:pilot.sha(output/name) for name in ('passages.csv','sources.csv','propositions.csv')}
    report.update(seed=seed,selected_dates=sorted({s['event_date'] for s in sources if s['source_id'] in ids}),role=packet_kind,comparison_scope='Reviewed quotations and full source text windows from all excluded prior packets; extra reference packet source windows; within-pool duplicate screen',excluded_review_bundle_hashes=[b['bundle_sha256'] for b in bundles],extra_reference_source_hashes=[pilot.sha(Path(p)/'sources.csv') for p in extra_references])
    if len(development)!=2:report.pop('development_bundle_hashes')
    (output/'duplicate-check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    later_review.render(output)
    (output/'sampling.json').write_text(json.dumps([dict(passage_id=p['passage_id'],stratum='random_after_exclusions') for p in selected],indent=2),encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('candidates');p.add_argument('output');p.add_argument('--development',nargs=2,required=True);a=p.parse_args();print(json.dumps(prepare(a.candidates,a.development,a.output),indent=2))
