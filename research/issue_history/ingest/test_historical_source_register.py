"""Source-free metadata gates; no reserved transcript bodies are accessed."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from ..store.repository import canonical_bytes
from . import historical_source_register as R


def digest(value):return hashlib.sha256(canonical_bytes(value)).hexdigest()


def fixture():
    mid='ga/81/9999';date='2026-10-01';url='https://transcripts.un.org/en/'+mid+'.json'
    frame={'schema':'un.passage-frame.v1','meetings':[{'meeting_id':mid,'date':date,'split':'development',
           'has_transcript':True,'body':'General Assembly','json_url':url,'source_url':url[:-5]}]}
    frame['sha256']=digest(frame)
    receipt={'schema':'un.fresh-development-source-receipt.v1','source_role':'product_development',
             'meeting_id':mid,'frame_date':date,'frame_sha256':frame['sha256'],'source_url':url,
             'final_url':url,'sha256':'a'*64,'bytes':123,'file':'invented.json'}
    entry={'source_id':'synthetic:artifact-1','family':'statement','source_kind':'transcripts_un_asr',
           'native_id':mid,'date':date,'language':'en','body':'GA','source_url':url,'original_sha256':'a'*64,
           'declared_role':'product_development','provenance_sha256':[frame['sha256'],digest(receipt)],'receipt':receipt}
    return {'as_of':'2026-10-24','frame':frame,'entries':[entry],'expected_frame_sha256':frame['sha256']}


class HistoricalRegisterTests(unittest.TestCase):
    def setUp(self):
        self.kw=fixture();self.temp=tempfile.TemporaryDirectory(dir=os.environ.get('SC_ACTION_TEST_ROOT'))
        self.addCleanup(self.temp.cleanup);self.path=Path(self.temp.name)/'register.json'

    def build(self,kw=None):return R.build_register(**(self.kw if kw is None else kw))

    def test_metadata_linkage_not_authentication_archive_or_production(self):
        before=copy.deepcopy(self.kw);out=self.build();row=out['entries'][0]
        self.assertTrue(row['intake_eligible']);self.assertTrue(row['raw_verification_required'])
        self.assertFalse(out['production_intake_accepted']);self.assertFalse(out['public_export_approved'])
        self.assertEqual('unknown',out['archive_coverage']);self.assertIn('not_independent_raw',out['verification_scope'])
        self.assertEqual(before,self.kw);self.assertEqual(out,self.build())

    def test_self_resealed_frame_cannot_replace_external_pin(self):
        self.kw['frame']['meetings'][0]['split']='holdout'
        self.kw['frame']['sha256']=digest({k:v for k,v in self.kw['frame'].items() if k!='sha256'})
        with self.assertRaises(ValueError):self.build()

    def test_all_actual_protected_metadata_ids_reject_role_date_hash_and_url_aliases(self):
        frame=json.loads(Path(__file__).resolve().parents[2].joinpath('corpus/frame.json').read_bytes())
        protected=[m for m in frame['meetings'] if m.get('split')!='development']
        self.assertEqual(37,len(protected))
        for m in protected:
            original_url=m.get('json_url') or 'https://transcripts.un.org/en/'+m['meeting_id']+'.json'
            for url in (original_url,original_url.replace('transcripts.un.org','www.transcripts.un.org')+'?download=1'):
                entry=copy.deepcopy(self.kw['entries'][0]);entry.update(native_id=m['meeting_id'],date='2026-10-01',source_url=url,original_sha256='b'*64)
                kw={**self.kw,'frame':frame,'expected_frame_sha256':R.FRAME_PIN,'entries':[entry]}
                out=self.build(kw)['entries'][0]
                self.assertFalse(out['intake_eligible']);self.assertTrue(out['reserved_blocked'])

    def test_reserved_url_cannot_hide_under_invented_native_id(self):
        frame=copy.deepcopy(self.kw['frame']);frame['meetings'].append({'meeting_id':'ga/81/8888','date':'2026-10-05','split':'holdout'})
        frame['sha256']=digest({k:v for k,v in frame.items() if k!='sha256'});self.kw.update(frame=frame,expected_frame_sha256=frame['sha256'])
        e=self.kw['entries'][0];e.update(native_id='invented-id',source_url='https://www.transcripts.un.org/en/GA/81/%38%38%38%38.json?x=1')
        self.assertTrue(self.build()['entries'][0]['reserved_blocked'])

    def test_reserved_date_guard_does_not_conflate_official_documents(self):
        e=self.kw['entries'][0];e.update(native_id='historical-unknown',date='2026-10-05',receipt=None)
        self.assertTrue(self.build()['entries'][0]['reserved_blocked'])
        e.update(family='official_document',source_kind='official_document',source_url='https://example.org/policy')
        row=self.build()['entries'][0];self.assertFalse(row['reserved_blocked']);self.assertFalse(row['intake_eligible'])

    def test_audit_evaluation_restricted_roles_never_become_development(self):
        for role in ('source_quality_audit','evaluation','restricted_research'):
            self.kw['entries'][0]['declared_role']=role;row=self.build()['entries'][0]
            self.assertEqual('product_development',row['authoritative_role']);self.assertEqual(role,row['effective_role']);self.assertFalse(row['intake_eligible'])

    def test_unknown_historical_exclusion_coverage_remains_unknown(self):
        self.kw['entries'][0].update(native_id='ga/70/9999',date='2017-01-01',receipt=None)
        out=self.build();self.assertFalse(out['entries'][0]['intake_eligible'])
        self.assertEqual('unknown',out['entries'][0]['exclusion_coverage']);self.assertIn('no_authoritative_28_or_64',out['historical_exclusion_coverage'])

    def test_family_kind_mismatch_and_unsupported_raw_payload_rejected(self):
        for changes in ({'family':'vote'},{'source_kind':'un_statement'},{'raw_text':'Invented body'}):
            kw=copy.deepcopy(self.kw);kw['entries'][0].update(changes)
            with self.subTest(changes=changes),self.assertRaises(ValueError):self.build(kw)

    def test_receipt_identity_hash_body_language_and_provenance_mismatch_withheld(self):
        for changes in ({'date':'2026-10-02'},{'body':'SC'},{'language':'fr'},{'original_sha256':'c'*64},
                        {'source_url':'https://transcripts.un.org/en/ga/81/9999.json?alias=1'},
                        {'provenance_sha256':[]},{'receipt':None}):
            kw=copy.deepcopy(self.kw);kw['entries'][0].update(changes)
            with self.subTest(changes=changes):self.assertFalse(self.build(kw)['entries'][0]['intake_eligible'])

    def test_ten_year_calendar_leap_and_exact_boundaries(self):
        self.kw['as_of']='2024-02-29';out=self.build();self.assertEqual('2014-03-01',out['window']['start'])
        self.kw['as_of']='2026-10-24'
        for date,expected in (('2016-10-24',False),('2016-10-25',True),('2026-10-24',True),('2026-10-25',False)):
            self.kw['entries'][0]['date']=date;self.assertEqual(expected,self.build()['entries'][0]['in_window'])
        for date in ('2026-02-30','2026-1-01','0009-10-24'):
            self.kw['as_of']=date
            with self.assertRaises(ValueError):self.build()

    def test_duplicate_source_or_frame_identity_rejected(self):
        self.kw['entries']*=2
        with self.assertRaises(ValueError):self.build()
        self.kw=fixture();frame=self.kw['frame'];frame['meetings']*=2;frame['sha256']=digest({k:v for k,v in frame.items() if k!='sha256'});self.kw['expected_frame_sha256']=frame['sha256']
        with self.assertRaises(ValueError):self.build()

    def test_credential_url_and_nonhash_input_rejected(self):
        for changes in ({'source_url':'https://user:secret@transcripts.un.org/en/ga/81/9999.json'}, {'original_sha256':'not-a-hash'}):
            kw=copy.deepcopy(self.kw);kw['entries'][0].update(changes)
            with self.subTest(changes=changes),self.assertRaises(ValueError):self.build(kw)

    def test_save_load_exact_canonical_immutable_and_idempotent(self):
        out=self.build();R.save_register(self.path,out,**self.kw);before=self.path.read_bytes()
        self.assertEqual(out,R.load_register(self.path,**self.kw));R.save_register(self.path,out,**self.kw)
        self.assertEqual(before,self.path.read_bytes());self.assertEqual(canonical_bytes(out),before)

    def test_corrupt_existing_file_never_overwritten(self):
        out=self.build();self.path.write_bytes(b'{truncated');before=self.path.read_bytes()
        with self.assertRaises(ValueError):R.load_register(self.path,**self.kw)
        with self.assertRaises(ValueError):R.save_register(self.path,out,**self.kw)
        self.assertEqual(before,self.path.read_bytes())

    def test_resealed_output_role_tamper_rejected_against_authoritative_inputs(self):
        out=self.build();out['entries'][0]['effective_role']='evaluation';out['content_sha256']=digest({k:v for k,v in out.items() if k!='content_sha256'})
        self.path.write_bytes(canonical_bytes(out))
        with self.assertRaises(ValueError):R.load_register(self.path,**self.kw)
        with self.assertRaises(ValueError):R.save_register(self.path,out,**self.kw)

    def test_changed_source_or_method_pin_invalidates_saved_snapshot(self):
        out=self.build();R.save_register(self.path,out,**self.kw)
        kw=copy.deepcopy(self.kw);kw['entries'][0]['original_sha256']='d'*64
        with self.assertRaises(ValueError):R.load_register(self.path,**kw)
        with patch.object(R,'_method',return_value='e'*64):
            with self.assertRaises(ValueError):R.load_register(self.path,**self.kw)

    def test_method_race_rejected(self):
        with patch.object(R,'_method',side_effect=['a'*64,'b'*64]):
            with self.assertRaises(ValueError):self.build()

    def test_committee_body_exactly_matches_native_id_and_recorded_frame(self):
        kw=fixture();m=kw['frame']['meetings'][0];e=kw['entries'][0]
        m.update(meeting_id='ga/c3/81/9999',body='Third Committee',json_url='https://transcripts.un.org/en/ga/c3/81/9999.json')
        kw['frame']['sha256']=digest({k:v for k,v in kw['frame'].items() if k!='sha256'});kw['expected_frame_sha256']=kw['frame']['sha256']
        receipt=e['receipt'];receipt.update(meeting_id=m['meeting_id'],frame_sha256=kw['frame']['sha256'],source_url=m['json_url'],final_url=m['json_url'])
        e.update(native_id=m['meeting_id'],body='GA_C3',source_url=m['json_url'],provenance_sha256=[kw['frame']['sha256'],digest(receipt)])
        self.assertTrue(self.build(kw)['entries'][0]['intake_eligible'])
        e['body']='GA';self.assertFalse(self.build(kw)['entries'][0]['intake_eligible'])

    def test_noncanonical_saved_json_cannot_masquerade_as_exact_snapshot(self):
        out=self.build();self.path.write_text(json.dumps(out,indent=2),encoding='utf-8')
        with self.assertRaises(ValueError):R.load_register(self.path,**self.kw)

    def test_restrictive_role_cannot_be_laundered_through_alternate_identity(self):
        for role in ('source_quality_audit','evaluation','restricted_research'):
            for identity in ('native','url','hash'):
                kw=copy.deepcopy(self.kw);alias=copy.deepcopy(kw['entries'][0]);alias.update(source_id='synthetic:alias',declared_role=role)
                if identity=='native':alias.update(source_url='https://example.org/other',original_sha256='b'*64)
                elif identity=='url':alias.update(native_id='other-native',original_sha256='b'*64,source_url=alias['source_url'].replace('transcripts.un.org','www.transcripts.un.org')+'?download=1')
                else:alias.update(native_id='other-native',source_url='https://example.org/other')
                kw['entries'].append(alias)
                with self.subTest(role=role,identity=identity),self.assertRaises(ValueError):self.build(kw)

    def test_reserved_url_authority_overrides_development_native_identity(self):
        kw=copy.deepcopy(self.kw);frame=kw['frame'];frame['meetings'].append({'meeting_id':'ga/81/8888','date':'2026-10-05','split':'holdout'})
        frame['sha256']=digest({k:v for k,v in frame.items() if k!='sha256'});kw['expected_frame_sha256']=frame['sha256']
        kw['entries'][0]['source_url']='https://transcripts.un.org/en/ga/81/8888.json'
        row=self.build(kw)['entries'][0]
        self.assertEqual('evaluation',row['authoritative_role']);self.assertEqual('evaluation',row['effective_role']);self.assertFalse(row['intake_eligible'])

    def test_failed_fsync_never_publishes_partial_final_and_retry_succeeds(self):
        out=self.build()
        with patch.object(R.os,'fsync',side_effect=OSError('invented interruption')):
            with self.assertRaises(OSError):R.save_register(self.path,out,**self.kw)
        self.assertFalse(self.path.exists())
        R.save_register(self.path,out,**self.kw);self.assertEqual(out,R.load_register(self.path,**self.kw))

    def test_failed_commit_never_publishes_final_and_retry_succeeds(self):
        out=self.build()
        with patch.object(R,'_commit',side_effect=OSError('invented interruption')):
            with self.assertRaises(OSError):R.save_register(self.path,out,**self.kw)
        self.assertFalse(self.path.exists())
        R.save_register(self.path,out,**self.kw);before=self.path.read_bytes()
        with patch.object(R,'_commit',side_effect=OSError('should not run')):
            R.save_register(self.path,out,**self.kw)
        self.assertEqual(before,self.path.read_bytes())

    def test_reserved_alias_with_same_declared_role_cannot_reuse_eligible_hash(self):
        kw=copy.deepcopy(self.kw);frame=kw['frame'];frame['meetings'].append({'meeting_id':'ga/81/8888','date':'2026-10-05','split':'holdout'})
        frame['sha256']=digest({k:v for k,v in frame.items() if k!='sha256'});kw['expected_frame_sha256']=frame['sha256']
        e=kw['entries'][0];e['receipt']['frame_sha256']=frame['sha256'];e['provenance_sha256']=[frame['sha256'],digest(e['receipt'])]
        alias=copy.deepcopy(e);alias.update(source_id='synthetic:reserved-alias',native_id='ga/81/8888',source_url='https://transcripts.un.org/en/ga/81/8888.json')
        kw['entries'].append(alias)
        with self.assertRaises(ValueError):self.build(kw)

    def test_partial_stage_write_failure_leaves_final_absent_and_existing_intact(self):
        out=self.build();fdopen=R.os.fdopen
        class InterruptedWriter:
            def __init__(self,fd,mode):self.stream=fdopen(fd,mode)
            def __enter__(self):return self
            def __exit__(self,*args):self.stream.close()
            def write(self,data):
                self.stream.write(data[:13]);self.stream.flush();raise OSError('invented partial write')
        with patch.object(R.os,'fdopen',side_effect=InterruptedWriter):
            with self.assertRaises(OSError):R.save_register(self.path,out,**self.kw)
        self.assertFalse(self.path.exists());self.assertEqual([],list(self.path.parent.glob('*.stage')))
        R.save_register(self.path,out,**self.kw);before=self.path.read_bytes()
        with patch.object(R.os,'fdopen',side_effect=InterruptedWriter):R.save_register(self.path,out,**self.kw)
        self.assertEqual(before,self.path.read_bytes())

    def test_duplicate_logical_source_versions_require_separate_registers(self):
        alias=copy.deepcopy(self.kw['entries'][0]);alias['source_id']='synthetic:alternate-id'
        self.kw['entries'].append(alias)
        with self.assertRaises(ValueError):self.build()

    def test_concurrent_publication_never_clobbers_other_final_bytes(self):
        out=self.build();commit=R._commit
        def concurrent(stage,final):
            Path(final).write_bytes(b'invented concurrent snapshot')
            return commit(stage,final)
        with patch.object(R,'_commit',side_effect=concurrent):
            with self.assertRaises(ValueError):R.save_register(self.path,out,**self.kw)
        self.assertEqual(b'invented concurrent snapshot',self.path.read_bytes())

    def test_known_development_role_preserved_outside_supported_candidate_scope(self):
        for changes in ({'meeting_id':'ecosoc/2026/9999','body':'Economic and Social Council'},
                        {'has_transcript':False}):
            kw=fixture();m=kw['frame']['meetings'][0];m.update(changes)
            m['json_url']='https://transcripts.un.org/en/'+m['meeting_id']+'.json'
            kw['frame']['sha256']=digest({k:v for k,v in kw['frame'].items() if k!='sha256'});kw['expected_frame_sha256']=kw['frame']['sha256']
            e=kw['entries'][0];e.update(native_id=m['meeting_id'],source_url=m['json_url'])
            e['receipt'].update(meeting_id=m['meeting_id'],source_url=m['json_url'],final_url=m['json_url'],frame_sha256=kw['frame']['sha256'])
            e['provenance_sha256']=[kw['frame']['sha256'],digest(e['receipt'])]
            row=self.build(kw)['entries'][0]
            with self.subTest(changes=changes):
                self.assertEqual('product_development',row['authoritative_role']);self.assertEqual('product_development',row['effective_role'])
                self.assertFalse(row['intake_eligible']);self.assertTrue(row['raw_verification_required'])
                self.assertEqual('unsupported_development_source_scope',row['eligibility_reason'])

    def test_save_refuses_changed_input_reuse_without_replacing_old_bytes(self):
        out=self.build();R.save_register(self.path,out,**self.kw);before=self.path.read_bytes()
        self.kw['as_of']='2026-10-25';new=self.build()
        with self.assertRaises(ValueError):R.save_register(self.path,new,**self.kw)
        self.assertEqual(before,self.path.read_bytes())


if __name__=='__main__':unittest.main()
