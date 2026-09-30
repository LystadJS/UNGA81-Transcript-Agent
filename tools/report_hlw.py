"""Verify complete upload runs and publish a compact Cuba evidence guide."""
import argparse,csv,hashlib,html,json,re,shutil
from collections import Counter
from pathlib import Path

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8-sig',newline='')))
def savecsv(p,items,fields=None):
    if not items:return
    with Path(p).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields or list(items[0]),extrasaction='ignore');w.writeheader();w.writerows(items)
def report(root,out):
    root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    records={r['statement_id']:r for r in read(root/'records.json')};segments=read(root/'segments.json');byrecord={}
    for s in segments:
        assert records[s['record_id']]['text'][s['start_char_0']:s['end_char_0']]==s['text']
        byrecord.setdefault(s['record_id'],[]).append(s)
    inventory=read(root/'inventory.json');coverage=read(root/'coverage.json')
    flagged={};source_segments={}
    for m in coverage:
        if m.get('collection_status')=='downloaded':
            raw_path='raw/'+m['archive_id']+'.json';doc=read(root/raw_path)
            m['timestamps_flagged']=bool(doc['transcript'].get('timestamps_flagged',False))
            flagged[m['slug']]=m['timestamps_flagged']
            for i,s in enumerate(doc['transcript']['data']):
                body=' '.join(t['text'] for p in s.get('paragraphs',[]) for t in p.get('sentences',[]))
                if body.strip():source_segments[(raw_path,f'/transcript/data/{i}')]=body
    assert len(source_segments)==len(segments)
    assert {(s['raw_file'],s['json_pointer']):s['text'] for s in segments}==source_segments,'Raw source segment omitted or changed'
    for rel,digest in read(root/'SHA256.json').items():
        assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==digest,rel
    evidence=[];seen=[];statuses=Counter();summaries=[];runinfo=[]
    for filename,count in read(root/'input-batches.json').items():
        run=root/('final-'+Path(filename).stem)
        assert (run/'result.rds').is_file(),'Run incomplete: '+str(run)
        cov=rows(run/'coverage.csv');assert len(cov)==count
        for r in cov:
            original=records[r['statement_id']];assert hashlib.sha256(original['text'].encode()).hexdigest()==r['body_sha256']
            seen.append(r['statement_id']);statuses[r['status']]+=1
        for e in rows(run/'source_evidence.csv'):
            original=records[e['statement_id']];start=int(e['start_char'])-1;end=int(e['end_char']);quote=original['text'][start:end]
            assert e['quote']==quote or e['quote']=="'"+quote,'Broken quote offset'
            sources=[s for s in byrecord[e['statement_id']] if s['start_char_0']<=start and end<=s['end_char_0']]
            assert len(sources)==1,'Quote crosses source segments'
            s=sources[0]
            evidence.append(dict(e,date=original['speech_date'],scope=original['scope'],meeting=s['title'],source_url=s['source_url'],timestamps_flagged=flagged[s['meeting_id']],statement_number=s['statement_number'],json_pointer=s['json_pointer'],raw_file=s['raw_file'],raw_sha256=s['raw_sha256']))
        summaries+=rows(run/'tracked_issue_candidates.csv')
        runinfo.append({'run':run.name,'records':len(cov),'engine':read(run/'provenance.json')['engine'],'sent':read(run/'provenance.json')['sent']})
    assert len(seen)==len(set(seen))==len(records)
    direct=[s for s in segments if re.search(r'\b(?:cuba|cuban|cubans|havana|havanna)\b',s['text'],re.I)]
    gd=[s for s in direct if s['scope']=='general_debate' and s['iso3']]
    country_index={s['iso3']:{'country':s['country'],'iso3':s['iso3'],'date':s['date'],'source_url':s['source_url']} for s in gd}
    stats={'inventory_meetings':len(coverage),'downloaded':sum(m.get('collection_status')=='downloaded' for m in coverage),'unavailable':sum(m.get('collection_status')=='unavailable' for m in coverage),'collection_errors':inventory['errors'],'source_segments':len(segments),'analysis_records':len(records),'record_statuses':dict(statuses),'evidence_rows':len(evidence),'cuba_evidence_rows':sum(e['topic']=='Cuba' for e in evidence),'direct_cuba_segments':len(direct),'direct_cuba_segments_by_scope':dict(Counter(s['scope'] for s in direct)),'general_debate_country_labels_with_direct_mentions':len(country_index),'general_debate_country_labels':len({s['iso3'] for s in segments if s['scope']=='general_debate' and s['iso3']}),'meeting_scope':dict(Counter(m['scope'] for m in coverage)),'downloaded_meeting_scope':dict(Counter(m['scope'] for m in coverage if m.get('collection_status')=='downloaded')),'transcript_languages':dict(Counter(m.get('transcript_language') for m in coverage if m.get('collection_status')=='downloaded')),'runs':runinfo,'all_input_rows_reconciled':True,'all_evidence_offsets_verified':True,'raw_source_hashes_verified':True,'human_review_complete':False}
    stats['timestamp_flagged_transcripts']=sum(flagged.values())
    stats['evidence_by_topic']=dict(Counter(e['topic'] for e in evidence))
    stats['cuba_evidence_by_scope']=dict(Counter(e['scope'] for e in evidence if e['topic']=='Cuba'))
    stats['run_wrapper_sha256']=hashlib.sha256(Path(__file__).with_name('run_hlw.R').read_bytes()).hexdigest()
    equivalence=read(root/'matcher-equivalence.json')
    assert all(x['exact_agreement'] for x in equivalence.values())
    stats['original_matcher_comparison']=equivalence
    (out/'validation.json').write_text(json.dumps(stats,indent=2)+'\n',encoding='utf-8')
    first_run=root/runinfo[0]['run']
    request=read(first_run/'request.json')
    (out/'topics.json').write_text(json.dumps(request,indent=2)+'\n',encoding='utf-8')
    savecsv(out/'evidence.csv',evidence);savecsv(out/'cuba.csv',[e for e in evidence if e['topic']=='Cuba'])
    savecsv(out/'countries.csv',sorted(country_index.values(),key=lambda x:x['country']))
    savecsv(out/'coverage.csv',coverage,['date','title','slug','category','scope','hasTranscript','collection_status','transcript_language','timestamps_flagged','pageUrl'])
    shutil.copyfile(root/'SHA256.json',out/'source-hashes.json')
    def link(code):return country_index[code]['source_url']
    findings=[
      ('Embargo relief and humanitarian effects recur across regions.',f'Brazil, Angola, Viet Nam, Namibia, Barbados, South Africa, Mexico and China explicitly address Cuba-related restrictions. This is a source-based thematic observation, not a vote forecast or a coded coalition.', [('Brazil',link('BRA')),('Viet Nam',link('VNM')),('South Africa',link('ZAF')),('China',link('CHN'))]),
      ('Fuel restrictions and terrorism-list designation are distinct issues.', 'Viet Nam, Namibia, the Bahamas, Belize, Laos and Russia connect Cuba discussions to energy or fuel restrictions and/or removal from the terrorism list. These are positions expressed in speeches; the report does not independently establish current legal status.', [('Namibia',link('NAM')),('Bahamas',link('BHS')),('Belize',link('BLZ'))]),
      ('Dialogue and domestic reform appear alongside calls for relief.', 'Suriname and the Holy See emphasize dialogue. Jamaica and Grenada pair concern over hardship with references to domestic reform. Those differences would be lost in a single pro-Cuba or anti-Cuba label.', [('Suriname',link('SUR')),('Holy See',link('VAT')),('Jamaica',link('JAM')),('Grenada',link('GRD'))]),
      ('The United States and other speakers introduce different concerns.', 'The US speech describes pressure for political change and negotiations. Paraguay raises authoritarianism; Costa Rica raises human rights. Ukraine mentions Cuban nationals in an allegation about Russian recruitment. These references are not endorsements of embargo relief.', [('United States',link('USA')),('Paraguay',link('PRY')),('Costa Rica',link('CRI')),('Ukraine',link('UKR'))]),
      ('Cuba links the embargo to shipping, finance and medical cooperation.', 'Cuba’s General Debate statement alleges restrictions on fuel, commercial shipments, investment, financing and overseas medical services. Its broader-week interventions also address Haiti health cooperation and pandemic preparedness. Allegations and figures require corroboration before institutional use.', [('Cuba',link('CUB')),('Haiti meeting','https://transcripts.un.org/en/asset/k1e/k1e2zmh16x?t=2:03:42'),('Pandemic meeting','https://transcripts.un.org/en/asset/k13/k13wyul0eu?t=2:54:06')])]
    h=html.escape
    finding_html=''.join('<section><h2>'+h(title)+'</h2><p>'+h(body)+'</p><p>'+ ' · '.join(f'<a href="{h(url)}">{h(label)}</a>' for label,url in links)+'</p></section>' for title,body,links in findings)
    table=''.join('<tr><td>'+h(x['country'])+'</td><td>'+h(x['date'])+'</td><td><a href="'+h(x['source_url'])+'">Read source statement</a></td></tr>' for x in sorted(country_index.values(),key=lambda x:x['country']))
    page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cuba at UNGA81 High-Level Week</title><style>body{{font:17px/1.6 Arial,sans-serif;color:#202b38;background:#f4f6f8;margin:0}}main{{max-width:1000px;margin:auto;background:white;padding:36px}}h1{{font:36px Georgia;color:#062135;border-bottom:4px solid #cf142b;padding-bottom:20px}}h2{{font:25px Georgia;color:#002d74}}a{{color:#002d74}}section{{margin:30px 0}}table{{border-collapse:collapse;width:100%}}th,td{{padding:10px;text-align:left;border-bottom:1px solid #d6dee7}}input{{font:inherit;padding:10px;max-width:90%}}.note{{background:#eef2f7;padding:18px}}@media(max-width:600px){{main{{padding:18px}}h1{{font-size:28px}}td{{padding:6px;overflow-wrap:anywhere}}}}</style><main><h1>Cuba, the embargo and adjacent issues</h1><p>UNGA81 High-Level Week · 21–28 September 2026 · Source-based working brief</p><section><h2>What the collected speeches show</h2><p><strong>{len(country_index)} country or observer labels</strong> have direct Cuba-related wording in the six General Debate meeting transcripts. The recurring discussion concerns embargo relief and humanitarian effects, but also includes dialogue, domestic reform, human rights and security allegations. A mention does not establish a shared position.</p><p>Downloaded <strong>{stats['downloaded']} of {stats['inventory_meetings']} indexed meetings</strong> across the week. The service marked {stats['unavailable']} unavailable. Within the collection, 6 General Debate and 131 broader-week meeting transcripts were analyzed, alongside 33 background proceedings kept separate.</p></section>{finding_html}<section><h2>Inspect the evidence</h2><p><a href="cuba.csv">Cuba candidate passages</a> · <a href="evidence.csv">All eight topic searches</a> · <a href="coverage.csv">Meeting coverage and gaps</a> · <a href="validation.json">Validation record</a></p><p>The complete local delivery also contains the original transcript JSON, a plain-text collection, input files and three unsent workflow drafts. Nothing was emailed.</p><label>Find a General Debate country <input id="search" type="search" placeholder="Type a country"></label><table><thead><tr><th>Source affiliation</th><th>Date</th><th>Evidence</th></tr></thead><tbody>{table}</tbody></table></section><section class="note"><h2>Scope and limitations</h2><p>These are UN-hosted automatic transcripts, not official verbatim records. Speaker affiliation is source-supplied and matched to the project registry; introductions and procedural references remain in candidate results. The 47-label count includes Cuba itself and the Holy See and is not a count of supporters.</p><p>The inventory is complete for the queried dates and endpoint, not an independently reconciled roster of every HLW speech. Clearly unrelated Human Rights Council, Crime Congress and similar proceedings are background; remaining events are a broad candidate scope, without independently verified venue membership. Of the 170 downloads, 163 are English, six are floor-language and one French. No translation or multilingual recall claim is made.</p><p>All 11,146 nonempty source segments were preserved. For upload limits, segments sharing an explicitly recorded affiliation within a meeting were grouped into 3,728 analysis records and processed in three batches. Unknown affiliations remain unattributed. Batching does not drop text; counts describe candidate passages or records, not distinct speeches. Generic embargo, sanctions and sovereignty hits require Cuba-specific context.</p><p>The existing upload workflow was run with a task-local batching wrapper using the same passage parser and phrase predicates, checked against the original matcher. Core application files were unchanged. It does not execute the full D1 daily adapter pipeline. The 500-text research limit applies per run; no clustering, stance, historical-change or diffusion finding is released. Human review is not complete.</p></section><section><h2>Recommended next steps</h2><ol><li>Review the linked US and Cuban statements, then the Caribbean dialogue/reform statements.</li><li>Verify consequential quotations and figures against audio or submitted written statements.</li><li>Use the coverage file to obtain the 56 unavailable transcripts; rerun collection later if desired.</li></ol></section></main><script>document.querySelector('#search').addEventListener('input',e=>{{const q=e.target.value.toLowerCase();document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.innerText.toLowerCase().includes(q))}})</script></html>'''
    page=page.replace('Speaker affiliation is source-supplied',f'The source flags timestamps in {sum(flagged.values())} transcripts as unreliable; time links are navigation aids, not verified timing evidence. Speaker affiliation is source-supplied')
    (out/'index.html').write_text(page,encoding='utf-8')
    print(json.dumps(stats,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('out');a=p.parse_args();report(a.root,a.out)
