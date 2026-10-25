"""Invented primary review receipts only; no private sources or accepted labels."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch
from . import test_corrections as fixtures
from . import private_packet as P
from . import corrections as C
from . import primary_verification as V


class PrimaryVerificationTests(unittest.TestCase):
    setUp=fixtures.CorrectionTests.setUp
    prepare=fixtures.CorrectionTests.prepare
    snapshot=fixtures.CorrectionTests.snapshot
    pointer=fixtures.CorrectionTests.pointer
    rows=fixtures.CorrectionTests.rows
    inputs=fixtures.CorrectionTests.inputs
    setup_correction=fixtures.CorrectionTests.setup_correction
    # Do not duplicate the parent test suite; these helpers construct invented inputs.
    def inputs_primary(self,resolved=True):
        kwargs,sha=self.setup_correction();item=kwargs['corrections'][0]
        item.update(status='unresolved',unresolved_reasons=['Synthetic unclear place.'])
        kwargs['expected_corrections_sha256']=P.digest(kwargs['corrections'])
        with patch.object(P,'FRAME_SHA256',sha):row=C.build_packet(**kwargs)['rows'][0]
        proof={'role':'official_government_written_statement','url':'https://www.un.emb-japan.go.jp/invented-unit-test-only','title':'Invented statement; never fetched','displayed_date':'2026-10-02','locator':'Invented paragraph','summary':'Synthetic explicit country scope.','exact_short_quote':'Invented region','capture_sha256':'1'*64,'capture_hash_scope':'review_receipt_not_primary_bytes','audio_verified':False}
        review={'row_id':row['id'],'original_row_sha256':P.digest(row),'source_sha256':row['source']['sha256'],'status':'written_statement_supported' if resolved else 'unresolved','context_summary':'Invented country context.','note':'Written statement only; audio not checked.','unresolved_reasons':[] if resolved else ['Still unclear.'],'proofs':[proof]}
        return dict(correction_inputs=kwargs,reviews=[review],expected_reviews_sha256=P.digest([review]),expected_row_ids=[row['id']]),sha

    def test_primary_preserves_original_and_blank_owner(self):
        kwargs,sha=self.inputs_primary();before=self.snapshot()
        with patch.object(P,'FRAME_SHA256',sha):
            original=C.build_packet(**kwargs['correction_inputs']);packet=V.build_packet(**kwargs)
        row=packet['rows'][0];self.assertEqual(original['rows'][0],row['pre_primary_verification_proposal'])
        for key in ('source','evidence','country','capacity','owner_decision'):
            self.assertEqual(original['rows'][0][key],row[key])
        self.assertEqual('corrected',row['correction']['status']);self.assertFalse(row['primary_verification']['audio_verified'])
        self.assertEqual(before,self.snapshot());V.validate_packet_identity(packet)

    def test_primary_unresolved_warning_and_drift(self):
        kwargs,sha=self.inputs_primary(False)
        with patch.object(P,'FRAME_SHA256',sha):packet=V.build_packet(**kwargs)
        self.assertEqual('unresolved',packet['rows'][0]['correction']['status']);self.assertEqual(['Still unclear.'],packet['source_warnings'][0]['unresolved_reasons'])
        for key,value in [('original_row_sha256','0'*64),('source_sha256','0'*64),('status','audio_verified')]:
            bad={**kwargs,'reviews':copy.deepcopy(kwargs['reviews'])};bad['reviews'][0][key]=value;bad['expected_reviews_sha256']=P.digest(bad['reviews'])
            with patch.object(P,'FRAME_SHA256',sha),self.assertRaises(ValueError):V.build_packet(**bad)

    def test_primary_proof_separation(self):
        kwargs,sha=self.inputs_primary()
        for key,value in [('audio_verified',True),('role','un_recording_metadata'),('url','http://example.gov/statement'),('url','https://unrelated.fi/statement'),('url','https://invented.gov/statement'),('capture_hash_scope','raw_audio'),('capture_sha256','invalid'),('displayed_date','')]:
            bad={**kwargs,'reviews':copy.deepcopy(kwargs['reviews'])};bad['reviews'][0]['proofs'][0][key]=value;bad['expected_reviews_sha256']=P.digest(bad['reviews'])
            with patch.object(P,'FRAME_SHA256',sha),self.assertRaises(ValueError):V.build_packet(**bad)

    def test_primary_exact_save_reopen_filters_and_choices(self):
        kwargs,sha=self.inputs_primary();path=Path(self.temp.name)/'primary.json';dpath=Path(self.temp.name)/'primary-decisions.json'
        with patch.object(P,'FRAME_SHA256',sha):
            packet=V.build_packet(**kwargs);V.save_packet(path,packet,**kwargs);self.assertEqual(packet,V.load_packet(path,**kwargs))
            choices=[{'row_id':r['id'],'label':None,'note':''} for r in packet['rows']]
            filters={'country':'Nigeria','capacity':'national_candidate','policy':packet['rows'][0]['policy_id'],'correction_status':'corrected','status':'unreviewed'}
            d=V.build_decisions(packet,choices,filters);V.save_decisions(dpath,d,packet=packet);self.assertEqual(d,V.load_decisions(dpath,packet=packet))
            revised=V.build_decisions(packet,choices,filters,d);self.assertEqual(d['revision_sha256'],revised['parent_revision_sha256'])
            choices[0]['label']='accept'
            with self.assertRaises(ValueError):V.build_decisions(packet,choices,filters)
            changed={**kwargs,'reviews':copy.deepcopy(kwargs['reviews'])};changed['reviews'][0]['note']='Changed interpretation';changed['expected_reviews_sha256']=P.digest(changed['reviews'])
            with self.assertRaises(ValueError):V.load_packet(path,**changed)
            changed_packet=V.build_packet(**changed)
            with self.assertRaises(ValueError):V.load_decisions(dpath,packet=changed_packet)
