import copy,json,tempfile,unittest
from pathlib import Path
import pilot_review as pilot
import remote_packets as remote

class RemoteTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name)
        source=self.base/'source.json';source.write_text(json.dumps([dict(iso3='AAA',date='2026-09-24',source_url='https://example.org',text='Artificial intelligence requires careful fictional governance.')]))
        self.root=self.base/'packet';pilot.prepare(self.root,source)
        policy=json.loads((self.root/'bundle.json').read_text());policy['engineering_fixture']=True;(self.root/'bundle.json').write_text(json.dumps(policy))
        self.packet=remote.packet(self.root)
        self.review=dict(schema='un.remote.review.v1',packet_id=self.packet['packet_id'],packet_sha256=remote.identity(self.packet),role=self.packet['role'],reviewer='ENGINEERING-FIXTURE',confirmed=True,completed_at=pilot.now(),rows=[dict(passage_id=p['passage_id'],boundary='national_address',label='relevant',rationale='Fictional engineering test') for p in self.packet['passages']])
    def tearDown(self):self.temp.cleanup()
    def apply(self):
        f=self.base/'returned.json';f.write_text(json.dumps(self.review));return remote.import_review(self.root,f)
    def test_export_has_no_private_token_or_labels(self):
        s=json.dumps(self.packet);meta=json.loads((self.root/'pilot.json').read_text());self.assertNotIn(meta['csrf'],s);self.assertNotIn('reviewer',s);self.assertNotIn('annotations',s)
    def test_round_trip(self):self.assertTrue(self.apply()['passed'])
    def test_changed_packet_rejected(self):
        self.review['packet_sha256']='0'*64
        with self.assertRaises(ValueError):self.apply()
    def test_role_change_rejected(self):
        self.review['role']='held_out_test'
        with self.assertRaises(ValueError):self.apply()
    def test_confirmation_required(self):
        self.review['confirmed']=False
        with self.assertRaises(ValueError):self.apply()
    def test_boundary_required(self):
        self.review['rows'][0]['boundary']='uncertain'
        with self.assertRaises(ValueError):self.apply()
    def test_second_finalization_rejected(self):
        self.apply()
        with self.assertRaises(ValueError):self.apply()
    def test_source_tampering_rejected(self):
        (self.root/'texts/s0001.txt').write_text('changed')
        with self.assertRaises(ValueError):remote.packet(self.root)

if __name__=='__main__':unittest.main()
