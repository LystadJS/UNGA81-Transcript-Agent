"""Invented corrections only; no private text or human acceptance."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch
from . import test_private_packet as fixtures
from . import private_packet as P
from . import corrections as C


class CorrectionTests(unittest.TestCase):
    setUp=fixtures.PrivatePacketTests.setUp
    prepare=fixtures.PrivatePacketTests.prepare
    snapshot=fixtures.PrivatePacketTests.snapshot
    pointer=fixtures.PrivatePacketTests.pointer
    rows=fixtures.PrivatePacketTests.rows
    inputs=fixtures.PrivatePacketTests.inputs
    def setup_correction(self):
        kwargs,sha=self.inputs()
        with patch.object(P,'FRAME_SHA256',sha):row=P.build_packet(**kwargs)['rows'][0]
        item={'row_id':row['id'],'original_row_sha256':P.digest(row),'source_sha256':row['source']['sha256'],'status':'corrected','replacement':{k:copy.deepcopy(row[k]) for k in ('country','group','capacity','assistant_proposal')},'evidence':[{k:row['evidence'][0][k] for k in ('pointer','quote')}],'note':'A cautious synthetic clarification.','unresolved_reasons':[],'interpretation':{k:'' for k in C.INTERPRETATION_FIELDS}}
        item['interpretation']['claim_qualification']='Attributed source claim.'
        return {**kwargs,'corrections':[item],'expected_corrections_sha256':P.digest([item]),'expected_flagged_row_ids':[row['id']]},sha

    def test_correction_provenance_and_blank_owner(self):
        kwargs,sha=self.setup_correction();before=self.snapshot()
        with patch.object(P,'FRAME_SHA256',sha):packet=C.build_packet(**kwargs)
        row=packet['rows'][0];self.assertEqual(P.digest(row['original_proposal']),kwargs['corrections'][0]['original_row_sha256'])
        self.assertIsNone(row['owner_decision']);self.assertEqual('assistant_provisional',row['correction']['review_state']);self.assertEqual(before,self.snapshot());C.validate_packet_identity(packet)
        self.assertFalse(packet['accepted_positions'])

    def test_reject_source_quote_row_and_membership_drift(self):
        kwargs,sha=self.setup_correction()
        for field,value in [('original_row_sha256','0'*64),('source_sha256','0'*64),('evidence',[{'pointer':kwargs['corrections'][0]['evidence'][0]['pointer'],'quote':'Fabricated evidence'}]),('replacement',{'country':'Nigeria','group':None,'capacity':'collective','assistant_proposal':kwargs['corrections'][0]['replacement']['assistant_proposal']})]:
            bad={**kwargs,'corrections':copy.deepcopy(kwargs['corrections'])};bad['corrections'][0][field]=value;bad['expected_corrections_sha256']=P.digest(bad['corrections'])
            with patch.object(P,'FRAME_SHA256',sha),self.assertRaises(ValueError):C.build_packet(**bad)
        bad={**kwargs,'corrections':copy.deepcopy(kwargs['corrections'])};bad['expected_flagged_row_ids']=[]
        with patch.object(P,'FRAME_SHA256',sha),self.assertRaises(ValueError):C.build_packet(**bad)

    def test_unresolved_and_no_canonical_binding(self):
        kwargs,sha=self.setup_correction();item=kwargs['corrections'][0];item['status']='unresolved';item['unresolved_reasons']=['Ambiguous synthetic scope.'];kwargs['expected_corrections_sha256']=P.digest(kwargs['corrections'])
        with patch.object(P,'FRAME_SHA256',sha):packet=C.build_packet(**kwargs)
        self.assertEqual('unresolved',packet['rows'][0]['correction']['status'])
        self.assertEqual([packet['rows'][0]['id']],packet['source_warnings'][0]['affected_row_ids'])
        self.assertEqual(['Ambiguous synthetic scope.'],packet['source_warnings'][0]['unresolved_reasons'])
        kwargs['corrections'][0]['replacement']['policy_id']='invented';kwargs['expected_corrections_sha256']=P.digest(kwargs['corrections'])
        with patch.object(P,'FRAME_SHA256',sha),self.assertRaises(ValueError):C.build_packet(**kwargs)

    def test_immutable_reopen_and_corrected_filters_decision_binding(self):
        kwargs,sha=self.setup_correction();path=Path(self.temp.name)/'correction.json';dpath=Path(self.temp.name)/'choices.json'
        with patch.object(P,'FRAME_SHA256',sha):
            packet=C.build_packet(**kwargs);C.save_packet(path,packet,**kwargs);self.assertEqual(packet,C.load_packet(path,**kwargs))
            filters={'country':'Nigeria','capacity':'national_candidate','policy':packet['rows'][0]['policy_id'],'correction_status':'corrected','status':'unreviewed'}
            choices=[{'row_id':r['id'],'label':None,'note':''} for r in packet['rows']]
            d=C.build_decisions(packet,choices,filters);C.save_decisions(dpath,d,packet=packet);self.assertEqual(d,C.load_decisions(dpath,packet=packet))
            nextd=C.build_decisions(packet,choices,filters,d);self.assertEqual(d['revision_sha256'],nextd['parent_revision_sha256'])
            bad=copy.deepcopy(packet);bad['rows'][0]['correction']['note']='Changed';bad.pop('packet_id');bad['packet_id']=P.digest(bad)
            with self.assertRaises(ValueError):C.load_decisions(dpath,packet=bad)
            kwargs['corrections'][0]['note']='New source review';kwargs['expected_corrections_sha256']=P.digest(kwargs['corrections'])
            with self.assertRaises(ValueError):C.load_packet(path,**kwargs)

    def test_no_corrections_keeps_all_original_rows(self):
        kwargs,sha=self.setup_correction();kwargs.update(corrections=[],expected_corrections_sha256=P.digest([]),expected_flagged_row_ids=[])
        with patch.object(P,'FRAME_SHA256',sha):
            packet=C.build_packet(**kwargs);original=P.build_packet(**{k:v for k,v in kwargs.items() if k not in ('corrections','expected_corrections_sha256','expected_flagged_row_ids')})
        self.assertEqual(original['rows'],packet['rows'])

    def test_context_consistency_and_end_build_dependency_race(self):
        kwargs,sha=self.setup_correction()
        for state,relation,reason in [('anchored',None,None),('anchored','same_sentence','bad'),('unresolved','full_statement_review','ambiguous'),('unresolved',None,None)]:
            bad={**kwargs,'corrections':copy.deepcopy(kwargs['corrections'])}
            bad['corrections'][0]['replacement']['assistant_proposal'].update(context_state=state,context_relation=relation,context_reason=reason)
            bad['expected_corrections_sha256']=P.digest(bad['corrections'])
            with patch.object(P,'FRAME_SHA256',sha),self.assertRaises(ValueError):C.build_packet(**bad)
        with patch.object(P,'FRAME_SHA256',sha):
            original=P.build_packet(**{k:v for k,v in kwargs.items() if k not in ('corrections','expected_corrections_sha256','expected_flagged_row_ids')})
            altered=copy.deepcopy(original);altered['packet_id']='0'*64
            with patch.object(P,'build_packet',side_effect=[original,altered]),self.assertRaisesRegex(ValueError,'dependencies changed'):C.build_packet(**kwargs)
