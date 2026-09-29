import copy, importlib.util, json, tempfile, unittest, hashlib, subprocess, sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('review_data',Path(__file__).with_name('review_data.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'review';m.initialize(self.root)
        policy={'schema':'un.review.v1','dataset_kind':'real','validation_scheme':'time_and_country','cutoff':'2024-01-01T00:00:00Z','human_review_complete':True}
        (self.root/'bundle.json').write_text(json.dumps(policy));self.tables={k:[] for k in m.SCHEMAS}
        self.tables['propositions']=[dict(proposition_id='p1',version='1',target='fictional target',proposition='Fictional engineering proposition',scope='synthetic test only')]
        for i,(country,year,part) in enumerate(zip(['AAA','BBB','CCC'],[2020,2021,2022],['train','calibration','test'])):
            sid=f's{i}';pid=f'p{i}';text=f'Fictional statement {i} for engineering checks.';raw=text.encode();(self.root/(sid+'.txt')).write_bytes(raw)
            self.tables['sources'].append(dict(source_id=sid,iso3=country,event_date=f'{year}-01-01',available_at=f'{year}-01-02T00:00:00Z',genre='general_debate',language='en',source_url='https://example.invalid/fixture',text_path=sid+'.txt',text_sha256=hashlib.sha256(raw).hexdigest(),duplicate_group=''))
            self.tables['passages'].append(dict(passage_id=pid,source_id=sid,start=0,end=len(text),quote=text))
            for j in range(2):self.tables['annotations'].append(dict(annotation_id=f'a{i}-{j}',passage_id=pid,task='stance',proposition_id='p1',label='descriptive',reviewer_id=f'reviewer{j}',reviewed_at='2023-01-01T00:00:00Z',rationale='Synthetic test rationale'))
            self.tables['adjudications'].append(dict(passage_id=pid,task='stance',proposition_id='p1',final_label='descriptive',adjudicator_id='adjudicator',adjudicated_at='2023-02-01T00:00:00Z',rationale='Synthetic adjudication'))
            self.tables['splits'].append(dict(source_id=sid,split=part))
        self.save()
    def tearDown(self):self.tmp.cleanup()
    def save(self):
        for name,data in self.tables.items():m.write_csv(self.root/(name+'.csv'),m.SCHEMAS[name].split(),data)
    def check_bad(self,fragment,cap='stance'):
        self.save();result=m.validate(self.root,cap);self.assertFalse(result['passed']);self.assertTrue(any(fragment in e for e in result['errors']),result)
    def test_valid_structural_fixture(self):self.assertTrue(m.validate(self.root,'stance')['passed'])
    def test_no_publication_approval(self):self.assertFalse(m.validate(self.root,'stance')['publication_approved'])
    def test_unreviewed_fails(self):
        p=json.loads((self.root/'bundle.json').read_text());p['human_review_complete']=False;(self.root/'bundle.json').write_text(json.dumps(p));self.assertFalse(m.validate(self.root)['passed'])
    def test_quote_tamper(self):self.tables['passages'][0]['quote']='invented';self.check_bad('quotation/offset')
    def test_source_tamper(self):
        (self.root/'s0.txt').write_text('changed');self.check_bad('hash mismatch')
    def test_path_escape(self):self.tables['sources'][0]['text_path']='../outside.txt';self.check_bad('invalid text path')
    def test_reviewer_not_independent(self):self.tables['annotations'][1]['reviewer_id']='reviewer0';self.check_bad('independent reviews')
    def test_adjudicator_not_independent(self):self.tables['adjudications'][0]['adjudicator_id']='reviewer0';self.check_bad('separate adjudicator')
    def test_missing_proposition(self):self.tables['annotations'][0]['proposition_id']='missing';self.check_bad('named proposition')
    def test_no_neutral_stance(self):self.tables['annotations'][0]['label']='neutral';self.check_bad('invalid label')
    def test_country_leakage(self):self.tables['sources'][2]['iso3']='AAA';self.check_bad('Countries cross')
    def test_duplicate_group_leakage(self):
        for s in self.tables['sources']:s['duplicate_group']='duplicate1'
        self.check_bad('Duplicate text/group')
    def test_temporal_leakage(self):self.tables['sources'][2]['event_date']='2019-01-01';self.check_bad('forward in event time')
    def test_cutoff_leakage(self):self.tables['sources'][0]['available_at']='2025-01-01T00:00:00Z';self.check_bad('unavailable at cutoff')
    def test_adjudication_before_review(self):self.tables['adjudications'][0]['adjudicated_at']='2022-01-01T00:00:00Z';self.check_bad('precedes review')
    def test_wrong_header_reported(self):
        (self.root/'events.csv').write_text('wrong\nvalue\n');r=m.validate(self.root);self.assertTrue(any('exact headers' in x for x in r['errors']))
    def test_short_row_reported(self):
        (self.root/'sources.csv').write_text(','.join(m.SCHEMAS['sources'].split())+'\ns0,AAA\n');r=m.validate(self.root);self.assertTrue(any('missing or extra cells' in x for x in r['errors']))
    def history(self):
        for i,s in enumerate(self.tables['sources']):
            s['iso3']='AAA';self.tables['history'].append(dict(source_id=s['source_id'],issue_id='issue1',proposition_id='p1',representation_id='frozen1',comparable_group='pair1',observation_index=i+1))
    def test_history_valid(self):self.history();self.save();self.assertTrue(m.validate(self.root,'history')['passed'])
    def test_history_genre(self):self.history();self.tables['sources'][1]['genre']='different';self.check_bad('mixed genre','history')
    def test_history_basis(self):self.history();self.tables['history'][1]['representation_id']='different';self.check_bad('mixed representation','history')
    def event(self):
        text='Synthetic preexisting edge evidence.';raw=text.encode();(self.root/'edge.txt').write_bytes(raw)
        self.tables['sources'].append(dict(source_id='edge-source',iso3='BBB',event_date='2019-01-01',available_at='2019-01-02T00:00:00Z',genre='event_record',language='en',source_url='https://example.invalid/edge',text_path='edge.txt',text_sha256=hashlib.sha256(raw).hexdigest(),duplicate_group=''))
        for j in range(2):self.tables['annotations'].append(dict(annotation_id=f'ev-{j}',passage_id='p0',task='event',proposition_id='p1',label='confirmed',reviewer_id=f'reviewer{j}',reviewed_at='2023-01-01T00:00:00Z',rationale='Synthetic event coding'))
        self.tables['adjudications'].append(dict(passage_id='p0',task='event',proposition_id='p1',final_label='confirmed',adjudicator_id='adjudicator',adjudicated_at='2023-02-01T00:00:00Z',rationale='Synthetic event adjudication'))
        self.tables['events']=[dict(event_id='e1',source_id='s0',event_type='rhetorical_endorsement',proposition_id='p1',actor='AAA',receiver='',action='endorsed',event_time='2020-01-01T12:00:00Z',available_at='2020-01-02T00:00:00Z',passage_id='p0')]
        self.tables['risk']=[dict(risk_id='r1',iso3='AAA',proposition_id='p1',start='2019-12-01T00:00:00Z',stop='2020-02-01T00:00:00Z',event_id='e1',outcome='1',censor_reason='')]
        self.tables['edges']=[dict(edge_id='n1',sender='BBB',receiver='AAA',layer='observed_interaction',weight=1,measured_at='2019-01-01T00:00:00Z',available_at='2019-01-02T00:00:00Z',source_id='edge-source')]
    def test_event_risk_valid(self):self.event();self.save();self.assertTrue(m.validate(self.root,'diffusion')['passed'])
    def test_edge_future(self):self.event();self.tables['edges'][0]['available_at']='2020-02-01T00:00:00Z';self.check_bad('not preexisting','diffusion')
    def test_event_outside_interval(self):self.event();self.tables['risk'][0]['stop']='2019-12-31T00:00:00Z';self.check_bad('outside risk interval','diffusion')
    def test_risk_after_adoption(self):
        self.event();r=copy.deepcopy(self.tables['risk'][0]);r.update(risk_id='r2',start='2020-02-01T00:00:00Z',stop='2020-03-01T00:00:00Z',outcome='0',event_id='',censor_reason='observed');self.tables['risk'].append(r);self.check_bad('continues after adoption','diffusion')
    def test_event_proposition_mismatch(self):self.event();self.tables['risk'][0]['proposition_id']='other';self.check_bad('proposition mismatch','diffusion')
    def test_event_actor_mismatch(self):self.event();self.tables['risk'][0]['iso3']='CCC';self.check_bad('actor mismatch','diffusion')
    def test_event_review_required(self):self.event();self.tables['adjudications'][-1]['final_label']='insufficient';self.check_bad('event confirmation required','diffusion')
    def test_edge_source_chronology(self):self.event();self.tables['edges'][0]['source_id']='s0';self.check_bad('edge predates available source','diffusion')
    def test_init_never_labels(self):
        root=Path(self.tmp.name)/'blank';m.initialize(root);self.assertEqual(m.rows(root/'annotations.csv')[1],[]);self.assertFalse(m.validate(root)['passed'])
    def test_report_cannot_overwrite_inputs(self):
        before=(self.root/'bundle.json').read_bytes();p=subprocess.run([sys.executable,str(Path(m.__file__)),'validate',str(self.root),'--out',str(self.root/'bundle.json')],capture_output=True);self.assertNotEqual(p.returncode,0);self.assertEqual(before,(self.root/'bundle.json').read_bytes())
    def test_long_text_segmentation_preserves_offsets(self):
        text='A fictional sentence with Unicode café. '*90;src=Path(self.tmp.name)/'replay.json';src.write_text(json.dumps([dict(text=text,iso3='AAA',date='2020-01-01')]),encoding='utf-8');root=Path(self.tmp.name)/'segmented';m.initialize(root,src);ps=m.rows(root/'passages.csv')[1];self.assertGreater(len(ps),1);self.assertTrue(all(text[int(p['start']):int(p['end'])]==p['quote'] and len(p['quote'])<=1000 for p in ps));self.assertEqual(m.rows(root/'annotations.csv')[1],[])

if __name__=='__main__':unittest.main()
