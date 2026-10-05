"""Render the repository's static HTML comparison from saved, inspectable results.
No transcript text is embedded in this public report. Original sources stay linked.
"""
import argparse
import html
import json
from pathlib import Path

LABELS = {'full': 'Complete corpus', 'substantive': 'Substantive subset', 'inclusive': 'Including mixed / fragment'}
TYPE_LABELS = {'substantive_speech':'Substantive address','procedure':'Procedure','right_of_reply':'Right of reply',
               'mixed_speech_procedure':'Mixed speech / procedure','speech_fragment':'Address fragment',
               'suspected_transcription_issue':'Possible extraneous text','uncertain':'Uncertain'}
COLORS = ['#002d74','#697884','#b04438','#217777','#8662a7','#ad701e','#929da7']
esc = lambda v: html.escape(str(v), quote=True)
num = lambda v: 'Not assessed' if v is None else f'{v:.3f}'


def table(headers, rows):
    return '<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+esc(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'


def render(comparison, destination):
    d = json.loads(Path(comparison).read_text(encoding='utf-8'))
    policies = d['policies']; hdb = [(key,f) for key,p in policies.items() for f in p['fits'] if f['mode']=='hdbscan']
    strict_hdb = [f for f in policies['substantive']['fits'] if f['mode']=='hdbscan']
    empty_samples = [sum(r['assigned_count']==0 for r in f['stability']['assignment_coverage']) for f in strict_hdb]
    total = d['counts']['matched']; bars=[]
    for i,(kind,label) in enumerate(TYPE_LABELS.items()):
        n=d['type_counts'].get(kind,0);y=34+i*45
        bars.append(f'<text x="0" y="{y+19}">{esc(label)}</text><rect x="270" y="{y}" width="{440*n/total}" height="26" fill="{COLORS[i]}"/><text x="{280+440*n/total}" y="{y+19}">{n} ({100*n/total:.1f}%)</text>')
    types_chart='<svg viewBox="0 0 850 370" role="img" aria-label="Passage types, counts out of all source segments"><title>Provisional types: all source segments; bars start at zero</title>'+''.join(bars)+'<text x="270" y="365">0</text><text x="710" y="365" text-anchor="end">'+str(total)+' segments</text></svg>'
    bars=[]
    for i,(policy,f) in enumerate(hdb):
        y=35+i*50;n=f['passages'];assigned=f['assigned'];width=430*assigned/n
        bars.append(f'<text x="0" y="{y+18}">{esc(LABELS[policy])} · {f["representation"].upper()}</text><rect x="320" y="{y}" width="430" height="26" fill="#a4adb6"/><rect x="320" y="{y}" width="{width}" height="26" fill="#002d74"/><text x="760" y="{y+18}">{assigned}/{n}</text>')
    coverage_chart='<svg viewBox="0 0 880 385" role="img" aria-label="HDBSCAN assigned share, zero to one hundred percent"><title>HDBSCAN assignment coverage for each policy and representation</title>'+''.join(bars)+'<text x="320" y="362">0%</text><text x="750" y="362" text-anchor="end">100%</text></svg>'
    metric_rows=[]
    for policy,p in policies.items():
        for f in p['fits']:
            metric_rows.append([LABELS[policy],f['mode'].upper(),f['representation'].upper(),f['passages'],', '.join(str(g['size']) for g in f['groups']) or 'No groups',f['unassigned'],num(f['silhouette']),num(f['stability']['ari']['mean']),f['stability']['ari']['count']])
    composition=[]
    for _,f in hdb[:2]:
        for g in f['groups']:
            composition.append([f['representation'].upper(),'Cluster '+str(g['cluster']),g['size'],*[(g['types'].get(t,0)) for t in TYPE_LABELS]])
        composition.append([f['representation'].upper(),'Unassigned',f['unassigned'],*[(f['unassigned_types'].get(t,0)) for t in TYPE_LABELS]])
    extra=[]
    for policy,f in hdb:
        links=''.join(f'<li><a href="{esc(p["source_url"])}" target="_blank" rel="noopener noreferrer">{esc(p["id"])}</a> · {esc(TYPE_LABELS[p["type"]])}</li>' for p in f['unassigned_passages'])
        extra.append(f'<details><summary>{esc(LABELS[policy])} · {f["representation"].upper()} · {f["unassigned"]} unassigned</summary><ul>{links}</ul></details>')
    text=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Passage composition comparison · UN Transcript Agent</title>
<style>body{{margin:0;background:#f2f5f7;color:#152c43;font:16px/1.65 Arial,sans-serif}}main{{max-width:1160px;margin:auto;padding:28px}}header{{border-bottom:3px solid #b1242e;padding-bottom:16px}}h1,h2{{font-family:Georgia,serif;line-height:1.2}}h1{{font-size:36px}}h2{{font-size:25px}}section{{background:white;border:1px solid #d6dfe6;padding:24px;margin:24px 0}}a{{color:#002d74}}.warning{{padding:16px;border-left:3px solid #b1242e;background:#fff2ed}}.metrics{{display:flex;flex-wrap:wrap;gap:14px}}.metrics div{{padding:15px;background:#eaf0f5;flex:1;min-width:170px}}.metrics strong{{display:block;font:700 32px Georgia,serif}}.table-wrap,.chart{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{padding:9px;text-align:left;border-bottom:1px solid #d4dee5;vertical-align:top}}th{{background:#eef3f7}}svg{{display:block;width:100%;height:auto;min-width:760px}}svg text{{fill:#152c43;font:15px Arial,sans-serif}}.note{{font-size:14px;color:#536577}}summary{{cursor:pointer;font-weight:bold}}details{{padding:12px 0;border-bottom:1px solid #d6dfe6}}li{{overflow-wrap:anywhere}}code{{overflow-wrap:anywhere}}@media(max-width:600px){{main{{padding:16px}}section{{padding:16px}}h1{{font-size:29px}}}}@media print{{body{{background:white}}main{{max-width:none;padding:0}}section{{break-inside:avoid}}svg{{min-width:0}}.table-wrap{{overflow:visible}}}}</style></head><body><main>
<header><p>UN Transcript Agent · {esc(d['selection']['start'])} to {esc(d['selection']['end'])}</p><h1>What changes when procedure is separated from speeches?</h1><p>Complete collection, substantive segments, and a broader boundary check.</p><a href="./#analyze">Open analysis workspace</a></header>
<p class="warning"><strong>Provisional source types.</strong> {d['human_confirmed']} of {total} records have a human-confirmed decision. Structural text checks support this exploratory comparison; source audio and factual claims have not been verified. No thematic labels are assigned.</p>
<div class="metrics"><div><strong>{total}</strong>original segments, preserved</div><div><strong>{policies['substantive']['selected']}</strong>substantive candidates</div><div><strong>{policies['inclusive']['selected']}</strong>with mixed remarks and fragment</div></div>
<section><h2>Source composition</h2><div class="chart">{types_chart}</div><p class="note">Counts use original source segments, not verified complete national addresses. The strict subset excludes replies because their intervention context differs, even when they contain substantive policy content. The broader subset adds {policies['inclusive']['selected']-policies['substantive']['selected']} mixed or fragment records without editing them.</p></section>
<section><h2>HDBSCAN assignment coverage</h2><p class="warning">The substantive subset has no selected groups in {empty_samples[0]} of 30 PCA samples and {empty_samples[1]} of 30 LSA samples. High agreement among the remaining assigned passages does not establish a reliable thematic partition.</p><p>Navy: assigned. Gray: unassigned. Labels give assigned / usable passages.</p><div class="chart">{coverage_chart}</div><p class="note">Same settings throughout: 20 components, minimum group size 15, density neighbors 5, EOM selection. Zero-term exclusions are separate. Every subset is refitted; the full-corpus coordinates are not reused.</p></section>
<section><h2>Fixed-method comparison</h2><p>Each row uses 30 whole-meeting samples with refitted TF-IDF, representation and clustering. Only six meeting groups are available, so repeated omissions are not independent replications.</p>{table(['Inclusion','Method','Representation','Usable','Group sizes','Unassigned','Silhouette','Mean ARI','Assessable ARIs'],metric_rows)}<p class="note">For HDBSCAN, silhouette uses assigned passages and ARI uses shared assigned passages with two represented groups in both fits. “Not assessed” is distinct from zero. Other methods force four groups. These diagnostics do not measure thematic validity.</p></section>
<section><h2>What the full-corpus HDBSCAN groups contain</h2>{table(['Representation','Assignment','Count',*TYPE_LABELS.values()],composition)}<p class="note">Types are provisional and mutually exclusive. Group numbers are local to each fit; a shared number does not establish correspondence.</p></section>
<section><h2>Inspect unassigned passages</h2><p>Unassigned does not mean irrelevant or erroneous. All affected source identifiers are retained below, including those that become unassigned only after the subset is refitted.</p>{''.join(extra)}</section>
<section><h2>Boundaries to resolve before thematic interpretation</h2><ul><li>The Assembly president's opening and closing remarks mix substantive material with procedure.</li><li>Ecuador's source segment includes a chair introduction.</li><li>Egypt's closing sentence continues a preceding address in a separate source segment.</li><li>Three records contain apparently unrelated song/show wording; source/audio verification is still needed.</li></ul><p>Confirm or revise these choices in the separate review packet, then repeat the fixed comparison. Review replies as their own population before using them to support a claim about national addresses. NMF remains the next planned method.</p></section>
<section><h2>Evidence and reproducibility</h2><p><a href="https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/main/docs/PASSAGE_TYPES.md">Review scope and reproduction guide</a> · <a href="https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/main/docs/passage-type-mask.json">Separate inclusion mask</a> · <a href="https://github.com/LystadJS/UNGA81-Transcript-Agent/blob/main/docs/passage-type-comparison.json">Full comparison data</a></p><p class="note">Original collection SHA-256: <code>{d['corpus_sha256']}</code><br>Mask SHA-256: <code>{d['mask_sha256']}</code><br>Engine: {esc(d['engine'])}. No text was trimmed, merged or overwritten. The saved collection and local packet remain separate from this public summary.</p></section>
</main></body></html>'''
    Path(destination).write_text(text,encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('comparison');parser.add_argument('output');args=parser.parse_args();render(args.comparison,args.output)
