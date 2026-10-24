"""Invented metadata composition checks; no source bodies or private records."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from ..store.repository import canonical_bytes
from . import historical_register_bridge as B
from . import historical_source_register as R
from . import historical_exclusion_manifest as M
from .test_historical_source_register import fixture as register_fixture, digest
from .test_historical_exclusion_manifest import fixture as exclusion_fixture


def fixture():
    return {'register_kwargs':register_fixture(),'exclusion_kwargs':exclusion_fixture()}


def official(kw, symbol='A/71/PV.88', family='statement', native=None, url=None):
    entry=copy.deepcopy(kw['register_kwargs']['entries'][0])
    entry.update(source_id='synthetic:official',family=family,
                 source_kind={'statement':'official_un_meeting_record','vote':'official_un_vote','official_document':'official_document'}[family],
                 native_id=native or symbol,date='2020-10-01',receipt=None,provenance_sha256=[],
                 source_url=url or 'https://docs.un.org/en/'+symbol,original_sha256='c'*64)
    kw['register_kwargs']['entries']=[entry]
    return entry


class HistoricalRegisterBridgeTests(unittest.TestCase):
    def setUp(self):
        self.kw=fixture();self.temp=tempfile.TemporaryDirectory(dir=os.environ.get('SC_ACTION_TEST_ROOT'))
        self.addCleanup(self.temp.cleanup);self.path=Path(self.temp.name)/'bridge.json'

    def build(self,kw=None):return B.build_bridge(**(self.kw if kw is None else kw))

    def test_composes_recomputed_inputs_without_mutation_or_new_permissions(self):
        before=copy.deepcopy(self.kw);out=self.build()
        self.assertEqual(R.build_register(**self.kw['register_kwargs']),out['base_register'])
        self.assertEqual(M.build_exclusion_manifest(**self.kw['exclusion_kwargs']),out['exclusion_manifest'])
        self.assertEqual(before,self.kw);self.assertEqual(out,self.build())
        self.assertTrue(out['entries'][0]['intake_eligible'])
        self.assertFalse(out['base_register']['production_intake_accepted'])
        self.assertFalse(out['exclusion_manifest']['public_export_approved'])

    def test_all_eight_development_metadata_cases_retain_original_semantics(self):
        entries=[];meetings=[]
        for index in range(8):
            item=register_fixture();entry=item['entries'][0];meeting=item['frame']['meetings'][0]
            native='ga/81/'+str(9000+index);url='https://transcripts.un.org/en/'+native+'.json'
            meeting.update(meeting_id=native,json_url=url,source_url=url[:-5])
            entry.update(source_id='synthetic:'+str(index),native_id=native,source_url=url,original_sha256=format(index+1,'064x'))
            entry['receipt'].update(meeting_id=native,source_url=url,final_url=url,sha256=entry['original_sha256'])
            meetings.append(meeting);entries.append(entry)
        frame={'schema':'un.passage-frame.v1','meetings':meetings};frame['sha256']=digest(frame)
        for entry in entries:
            entry['receipt']['frame_sha256']=frame['sha256'];entry['provenance_sha256']=[frame['sha256'],digest(entry['receipt'])]
        self.kw['register_kwargs'].update(frame=frame,expected_frame_sha256=frame['sha256'],entries=entries)
        out=self.build();base={e['source_id']:e for e in out['base_register']['entries']}
        self.assertEqual(8,len(out['entries']))
        for entry in out['entries']:
            self.assertTrue(entry['intake_eligible']);self.assertEqual(base[entry['source_id']]['effective_role'],entry['effective_role'])

    def test_known_audit_and_research_roles_override_product_claim(self):
        for symbol,role in (('A/71/PV.88','source_quality_audit'),('A/75/PV.77','restricted_research')):
            kw=fixture();official(kw,symbol)
            row=self.build(kw)['entries'][0]
            with self.subTest(symbol=symbol):
                self.assertEqual(role,row['effective_role']);self.assertFalse(row['intake_eligible'])
                self.assertFalse(row['metadata_eligible_for_source_validation'])
                self.assertEqual(symbol,row['historical_exclusion']['symbol'])

    def test_new_native_alias_still_uses_official_url_restriction(self):
        official(self.kw,native='invented-alias',url='https://documents.un.org/doc/undoc/gen/n16/000/00/pdf/n1600000.pdf?l=en&s=A%2F71%2FPV.88&t=pdf')
        row=self.build()['entries'][0]
        self.assertEqual('source_quality_audit',row['effective_role']);self.assertFalse(row['intake_eligible'])

    def test_native_and_official_url_conflict_rejected(self):
        official(self.kw,'A/75/PV.77',url='https://docs.un.org/en/A/71/PV.88')
        with self.assertRaises(ValueError):self.build()

    def test_duplicate_official_aliases_cannot_hide_behind_distinct_paths(self):
        first=official(self.kw);other=copy.deepcopy(first)
        other.update(source_id='synthetic:alias',native_id='invented-alias',original_sha256='d'*64,
                     source_url='https://documents.un.org/doc/undoc/gen/n16/000/00/pdf/n1600000.pdf?s=A%2F71%2FPV.88')
        self.kw['register_kwargs']['entries'].append(other)
        with self.assertRaises(ValueError):self.build()

    def test_source_families_remain_separate_not_promoted_by_matching_url(self):
        for family in ('vote','official_document'):
            kw=fixture();official(kw,family=family)
            with self.subTest(family=family),self.assertRaises(ValueError):self.build(kw)
            entry=kw['register_kwargs']['entries'][0]
            entry.update(native_id='synthetic-'+family,source_url='https://example.org/'+family)
            out=self.build(kw);row=out['entries'][0]
            with self.subTest(valid_family=family):
                self.assertEqual(family,row['family']);self.assertFalse(row['intake_eligible'])
                self.assertEqual(0,out['base_register']['summary']['intake_eligible'])

    def test_stronger_existing_restrictions_and_reserved_guard_never_weaken(self):
        for role in ('evaluation','source_quality_audit'):
            kw=fixture();entry=official(kw,'A/75/PV.77');entry['declared_role']=role
            self.assertEqual(role,self.build(kw)['entries'][0]['effective_role'])
        entry=official(self.kw,'A/75/PV.77');entry['date']='2026-10-05'
        row=self.build()['entries'][0]
        self.assertTrue(row['reserved_blocked']);self.assertEqual('evaluation',row['effective_role'])

    def test_non_pv_ga_and_security_council_documents_remain_unknown(self):
        for symbol in ('A/RES/77/1','A/77/123','S/RES/2720(2023)'):
            kw=fixture();official(kw,symbol,family='official_document',native='synthetic-document' if '(' in symbol else symbol)
            row=self.build(kw)['entries'][0]
            with self.subTest(symbol=symbol):
                self.assertEqual('official_document',row['family'])
                self.assertIsNone(row['historical_exclusion']['symbol'])
                self.assertIsNone(row['historical_exclusion']['role_metadata'])
                self.assertFalse(row['intake_eligible'])

    def test_malformed_pv_claims_do_not_silently_become_unknown(self):
        for symbol in ('A/75/PV.bad','A/75/PV.77/extra','A/75/PV'):
            kw=fixture();official(kw,symbol)
            with self.subTest(symbol=symbol),self.assertRaises(ValueError):self.build(kw)

    def test_off_roster_and_missing_receipt_do_not_gain_eligibility(self):
        official(self.kw,'A/80/PV.9999');row=self.build()['entries'][0]
        self.assertFalse(row['intake_eligible']);self.assertEqual('unknown',row['historical_exclusion']['exclusion_coverage'])
        self.kw=fixture();self.kw['register_kwargs']['entries'][0]['receipt']=None
        self.assertFalse(self.build()['entries'][0]['intake_eligible'])

    def test_wrong_window_and_authority_inputs_fail_closed(self):
        for mutation in ('window','authority','roster','frame'):
            kw=copy.deepcopy(self.kw)
            if mutation=='window':kw['exclusion_kwargs']['as_of']='2026-10-23'
            elif mutation=='authority':kw['exclusion_kwargs']['authority_pins']['split_code_sha256']='f'*64
            elif mutation=='roster':kw['exclusion_kwargs']['split_records'][0]['phase']='independent_source_auth_quality_audit'
            else:kw['register_kwargs']['frame']['meetings'][0]['split']='holdout'
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):self.build(kw)

    def test_save_reopen_canonical_idempotent_and_inputs_immutable(self):
        out=self.build();before=copy.deepcopy(self.kw);B.save_bridge(self.path,out,**self.kw);raw=self.path.read_bytes()
        self.assertEqual(canonical_bytes(out),raw);self.assertEqual(out,B.load_bridge(self.path,**self.kw))
        B.save_bridge(self.path,out,**self.kw);self.assertEqual(raw,self.path.read_bytes());self.assertEqual(before,self.kw)

    def test_changed_authoritative_inputs_reject_saved_bridge(self):
        B.save_bridge(self.path,self.build(),**self.kw)
        for mutation in ('date','source','design'):
            kw=copy.deepcopy(self.kw)
            if mutation=='date':
                kw['register_kwargs']['as_of']='2026-10-23';kw['exclusion_kwargs']['as_of']='2026-10-23'
            elif mutation=='source':kw['register_kwargs']['entries'][0]['original_sha256']='e'*64
            else:kw['exclusion_kwargs']['design_bytes']+=b'\n'
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):B.load_bridge(self.path,**kw)

    def test_self_resealed_role_tamper_and_corruption_never_overwrite(self):
        out=self.build();out['entries'][0]['effective_role']='evaluation'
        out['content_sha256']=digest({k:v for k,v in out.items() if k!='content_sha256'})
        self.path.write_bytes(canonical_bytes(out));before=self.path.read_bytes()
        with self.assertRaises(ValueError):B.load_bridge(self.path,**self.kw)
        with self.assertRaises(ValueError):B.save_bridge(self.path,self.build(),**self.kw)
        self.assertEqual(before,self.path.read_bytes());self.path.write_bytes(b'{broken')
        with self.assertRaises(ValueError):B.load_bridge(self.path,**self.kw)

    def test_dependency_method_invalidation_is_recomputed(self):
        B.save_bridge(self.path,self.build(),**self.kw)
        with patch.object(R,'_method',return_value='f'*64):
            with self.assertRaises(ValueError):B.load_bridge(self.path,**self.kw)
        methods=M._methods();methods['historical_exclusion_manifest.py']='e'*64
        with patch.object(M,'_methods',return_value=methods):
            with self.assertRaises(ValueError):B.load_bridge(self.path,**self.kw)
        bridge_methods=B._methods();bridge_methods['historical_register_bridge.py']='d'*64
        with patch.object(B,'_methods',return_value=bridge_methods):
            with self.assertRaises(ValueError):B.load_bridge(self.path,**self.kw)

    def test_dependency_race_and_interrupted_save_do_not_publish(self):
        before=B._methods();after={**before,'historical_register_bridge.py':'f'*64}
        with patch.object(B,'_methods',side_effect=[before,after]):
            with self.assertRaises(ValueError):self.build()
        out=self.build()
        with patch.object(R.os,'fsync',side_effect=OSError('invented interrupted flush')):
            with self.assertRaises(OSError):B.save_bridge(self.path,out,**self.kw)
        self.assertFalse(self.path.exists())
        B.save_bridge(self.path,out,**self.kw);self.assertEqual(out,B.load_bridge(self.path,**self.kw))

    def test_noncanonical_json_is_not_exact_reopening(self):
        import json
        self.path.write_text(json.dumps(self.build(),indent=2),encoding='utf-8')
        with self.assertRaises(ValueError):B.load_bridge(self.path,**self.kw)


if __name__=='__main__':unittest.main()
