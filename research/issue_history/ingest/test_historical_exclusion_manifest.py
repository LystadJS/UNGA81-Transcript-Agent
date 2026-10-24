"""Invented historical metadata only; no PDF, archive, index or model reads."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from ..store.repository import canonical_bytes
from . import historical_exclusion_manifest as M


def digest(value):return hashlib.sha256(canonical_bytes(value)).hexdigest()


def fixture():
    rows=[{'year':2015,'symbol':'A/70/PV.99','phase':'development_acquisition'},
          {'year':2016,'symbol':'A/71/PV.88','phase':'independent_source_auth_quality_audit'},
          {'year':2020,'symbol':'A/75/PV.77','phase':'development_acquisition'}]
    design=b'A/70/PV.99\nA/71/PV.88\n';authority={'split_code_sha256':'a'*64,'sampler_code_sha256':'b'*64}
    pins={**authority,'split_records_sha256':digest(rows),'design_bytes_sha256':hashlib.sha256(design).hexdigest()}
    return {'as_of':'2026-10-24','split_records':rows,'design_bytes':design,
            'authority_pins':authority,'expected_authority_pins':pins}


class HistoricalExclusionTests(unittest.TestCase):
    def setUp(self):
        self.kw=fixture();self.temp=tempfile.TemporaryDirectory(dir=os.environ.get('SC_ACTION_TEST_ROOT'))
        self.addCleanup(self.temp.cleanup);self.path=Path(self.temp.name)/'manifest.json'

    def build(self,kw=None):return M.build_exclusion_manifest(**(self.kw if kw is None else kw))

    def repin(self,kw):
        kw['expected_authority_pins']['split_records_sha256']=digest(kw['split_records'])
        kw['expected_authority_pins']['design_bytes_sha256']=hashlib.sha256(kw['design_bytes']).hexdigest()

    def test_research_development_never_product_intake_and_audit_stays_excluded(self):
        before=copy.deepcopy(self.kw);out=self.build();rows={r['symbol']:r for r in out['entries']}
        self.assertEqual('research_development',rows['A/70/PV.99']['upstream_role'])
        self.assertEqual('restricted_research',rows['A/70/PV.99']['effective_role'])
        self.assertEqual('source_quality_audit',rows['A/71/PV.88']['effective_role'])
        self.assertTrue(rows['A/71/PV.88']['design_selected'])
        self.assertTrue(all(r['product_intake_eligible'] is False for r in rows.values()))
        self.assertFalse(out['full_design_digests_recomputed']);self.assertFalse(out['sampling_weights_inferred'])
        self.assertEqual(before,self.kw);self.assertEqual(out,self.build())

    def test_self_resealed_metadata_or_code_claim_cannot_replace_trusted_pin(self):
        for mutation in ('phase','code','design'):
            kw=copy.deepcopy(self.kw)
            if mutation=='phase':kw['split_records'][0]['phase']='independent_source_auth_quality_audit'
            elif mutation=='code':kw['authority_pins']['split_code_sha256']='c'*64
            else:kw['design_bytes']=b'A/75/PV.77\n'
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):self.build(kw)

    def test_duplicate_conflicting_or_unknown_split_phase_rejected_even_if_repinned(self):
        for mutation in ('duplicate','conflicting','phase','year','extra'):
            kw=copy.deepcopy(self.kw)
            if mutation in ('duplicate','conflicting'):
                row=copy.deepcopy(kw['split_records'][0])
                if mutation=='conflicting':row['phase']='independent_source_auth_quality_audit'
                kw['split_records'].append(row)
            elif mutation=='phase':kw['split_records'][0]['phase']='product_development'
            elif mutation=='year':kw['split_records'][0]['year']=True
            else:kw['split_records'][0]['text']='Invented forbidden body'
            self.repin(kw)
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):self.build(kw)

    def test_design_duplicate_unknown_symbol_or_noncanonical_input_rejected(self):
        for design in (b'A/70/PV.99\nA/70/PV.99\n',b'A/80/PV.9999\n',b'A /69/PV.99\n',b'not a symbol\n'):
            kw=copy.deepcopy(self.kw);kw['design_bytes']=design;self.repin(kw)
            with self.subTest(design=design),self.assertRaises(ValueError):self.build(kw)

    def test_window_preserves_year_uncertainty_instead_of_invented_dates(self):
        out=self.build();rows={r['symbol']:r for r in out['entries']}
        self.assertEqual({'start':'2016-01-01','end':'2016-12-31'},rows['A/71/PV.88']['year_interval'])
        self.assertNotIn('date',rows['A/71/PV.88']);self.assertEqual('2016-10-25',out['window']['start'])
        encoded=json.dumps(rows['A/71/PV.88']);self.assertIn('overlaps_exact_date_unknown',encoded)
        self.assertIn('outside',json.dumps(rows['A/70/PV.99']))
        self.kw['as_of']='2024-02-29';self.assertEqual('2014-03-01',self.build()['window']['start'])

    def test_invalid_dates_and_authority_schema_rejected(self):
        for date in ('2026-02-30','2026-1-01'):
            kw=copy.deepcopy(self.kw);kw['as_of']=date
            with self.assertRaises(ValueError):self.build(kw)
        kw=copy.deepcopy(self.kw);kw['authority_pins']['unverified_extra']='c'*64
        with self.assertRaises(ValueError):self.build(kw)

    def test_symbol_and_official_url_aliases_resolve_without_new_authority(self):
        self.assertEqual('A/70/PV.99',M.resolve_symbol(symbol=' A / 70 / PV.99 '))
        self.assertEqual('A/70/PV.99',M.resolve_symbol(source_url='https://docs.un.org/en/A/70/PV.99'))
        self.assertEqual('A/70/PV.99',M.resolve_symbol(source_url='https://documents.un.org/doc/undoc/gen/n15/000/00/pdf/n1500000.pdf?symbol=A%2F70%2FPV.99'))

    def test_conflicting_or_untrusted_aliases_rejected(self):
        for kwargs in ({'symbol':'A/70/PV.99','source_url':'https://docs.un.org/en/A/71/PV.88'},
                       {'source_url':'https://evil.example/en/A/70/PV.99'},
                       {'source_url':'https://user:secret@docs.un.org/en/A/70/PV.99'},
                       {'symbol':'S/RES/99(2020)'}, {'symbol':'A/70/PV.99/garbage'}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):M.resolve_symbol(**kwargs)

    def test_save_reopen_exact_and_existing_bytes_immutable(self):
        out=self.build();M.save_manifest(self.path,out,**self.kw);before=self.path.read_bytes()
        self.assertEqual(out,M.load_manifest(self.path,**self.kw));M.save_manifest(self.path,out,**self.kw)
        self.assertEqual(before,self.path.read_bytes());self.assertEqual(canonical_bytes(out),before)

    def test_wrong_window_authority_source_and_current_method_invalidate_reopen(self):
        out=self.build();M.save_manifest(self.path,out,**self.kw)
        for field in ('as_of','authority_pins','design_bytes'):
            kw=copy.deepcopy(self.kw)
            if field=='as_of':kw[field]='2026-10-25'
            elif field=='authority_pins':kw[field]['split_code_sha256']='c'*64
            else:kw[field]+=b'\n'
            with self.subTest(field=field),self.assertRaises(ValueError):M.load_manifest(self.path,**kw)
        methods=M._methods();methods['historical_exclusion_manifest.py']='d'*64
        with patch.object(M,'_methods',return_value=methods):
            with self.assertRaises(ValueError):M.load_manifest(self.path,**self.kw)

    def test_corrupt_and_self_resealed_role_tamper_cannot_overwrite(self):
        out=self.build();out['entries'][0]['effective_role']='product_development'
        out['content_sha256']=digest({k:v for k,v in out.items() if k!='content_sha256'})
        self.path.write_bytes(canonical_bytes(out));before=self.path.read_bytes()
        with self.assertRaises(ValueError):M.load_manifest(self.path,**self.kw)
        with self.assertRaises(ValueError):M.save_manifest(self.path,self.build(),**self.kw)
        self.assertEqual(before,self.path.read_bytes())
        self.path.write_bytes(b'{broken')
        with self.assertRaises(ValueError):M.load_manifest(self.path,**self.kw)

    def test_off_roster_lookup_always_has_unknown_exclusion_and_no_intake(self):
        result=M.lookup_exclusion(self.build(),symbol='A/80/PV.9999',**self.kw)
        self.assertEqual('unknown',result['exclusion_coverage']);self.assertIsNone(result['role_metadata'])
        self.assertFalse(result['product_intake_eligible'])

    def test_lf_and_crlf_keep_roles_membership_but_distinct_raw_fingerprints(self):
        lf=self.build();kw=copy.deepcopy(self.kw);kw['design_bytes']=kw['design_bytes'].replace(b'\n',b'\r\n')
        crlf=self.build(kw)
        self.assertEqual(lf['entries'],crlf['entries']);self.assertEqual(lf['public_design_symbols'],crlf['public_design_symbols'])
        self.assertNotEqual(lf['input_fingerprints']['design_bytes_sha256'],crlf['input_fingerprints']['design_bytes_sha256'])
        self.assertEqual(lf['input_fingerprints']['design_lf_sha256'],crlf['input_fingerprints']['design_lf_sha256'])

    def test_method_changes_during_build_rejected(self):
        before=M._methods();after={**before,'historical_exclusion_manifest.py':'0'*64}
        with patch.object(M,'_methods',side_effect=[before,after]):
            with self.assertRaises(ValueError):self.build()

    def test_actual_official_s_selector_and_conflicting_selectors(self):
        url='https://documents.un.org/doc/undoc/gen/n08/000/00/pdf/n0800000.pdf?l=en&s=A%2F63%2FPV.5&t=pdf'
        self.assertEqual('A/63/PV.5',M.resolve_symbol(source_url=url))
        for suffix in ('&symbol=A%2F63%2FPV.5','&s=A%2F63%2FPV.5','&symbol=A%2F64%2FPV.5','&s='):
            with self.subTest(suffix=suffix),self.assertRaises(ValueError):M.resolve_symbol(source_url=url+suffix)

    def test_lookup_recomputes_authority_before_returning_any_role(self):
        value=self.build();result=M.lookup_exclusion(value,symbol='A/71/PV.88',**self.kw)
        self.assertEqual('source_quality_audit',result['role_metadata']['effective_role'])
        value['entries'][1]['effective_role']='product_development';value['content_sha256']=digest({k:v for k,v in value.items() if k!='content_sha256'})
        for symbol in ('A/71/PV.88','A/80/PV.9999'):
            with self.subTest(symbol=symbol),self.assertRaises(ValueError):M.lookup_exclusion(value,symbol=symbol,**self.kw)
        with self.assertRaises((ValueError,TypeError)):M.lookup_exclusion(self.build(),symbol='A/71/PV.88')

    def test_year_and_session_cannot_conflict_even_under_reconfigured_pin(self):
        kw=copy.deepcopy(self.kw);kw['split_records'][0]['year']=2025;self.repin(kw)
        with self.assertRaises(ValueError):self.build(kw)

    def test_canonical_path_and_query_must_identify_same_document(self):
        base='https://docs.un.org/en/A/63/PV.5'
        self.assertEqual('A/63/PV.5',M.resolve_symbol(source_url=base+'?s=A%2F63%2FPV.5'))
        with self.assertRaises(ValueError):M.resolve_symbol(source_url=base+'?s=A%2F64%2FPV.1')


if __name__=='__main__':unittest.main()
