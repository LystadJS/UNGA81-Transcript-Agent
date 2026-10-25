"""Invented packets only; no private actual transcripts or reviewer labels."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from ..ingest import test_transcript_context as context_fixtures
from . import private_packet as P


class PrivatePacketTests(unittest.TestCase):
    setUp=context_fixtures.TranscriptContextTests.setUp
    prepare=context_fixtures.TranscriptContextTests.prepare
    snapshot=context_fixtures.TranscriptContextTests.snapshot
    pointer=context_fixtures.TranscriptContextTests.pointer
    rows=context_fixtures.TranscriptContextTests.rows

    def inputs(self,capacity=None):
        entry={k:v for k,v in self.frame.items() if k!='frame_sha256'}
        frame={'schema':'un.passage-frame.v1','meetings':[entry]}
        sha=P.digest(frame);frame['sha256']=sha
        self.frame={**entry,'frame_sha256':sha}
        self.base_receipt={**self.base_receipt,'frame_sha256':sha};self.prepare()
        if capacity is not None:self.reviews[0]['capacity']=capacity
        bundle={'raw':self.raw,'receipt':self.receipt,'frame_entry':self.frame,'reviews':self.reviews,'context_reviews':self.rows()}
        pins={self.frame['meeting_id']:{'raw_sha256':hashlib.sha256(self.raw).hexdigest(),**{k+'_sha256':P.digest(bundle[k]) for k in ('receipt','frame_entry','reviews','context_reviews')}}}
        return {'store':self.store,'bundles':[bundle],'frame':frame,'expected_inputs':pins},sha

    def test_country_first_bound_source_quotes_null_labels_no_database_writes(self):
        kwargs,sha=self.inputs();before=self.snapshot()
        with patch.object(P,'FRAME_SHA256',sha):
            value=P.build_packet(**kwargs)
            self.assertEqual(value,P.build_packet(**kwargs))
        self.assertEqual(before,self.snapshot());self.assertEqual('Nigeria',value['country_groups'][0]['country'])
        row=value['rows'][0];self.assertIsNone(row['owner_decision'])
        self.assertEqual(['policy','object','context'],[e['kind'] for e in row['evidence']])
        self.assertFalse(value['accepted_positions']);self.assertFalse(value['comparisons_eligible'])
        P.validate_packet_identity(value)

    def test_reserved_or_forged_frame_rejected_before_source_review(self):
        kwargs,sha=self.inputs()
        with self.assertRaisesRegex(ValueError,'Authoritative'):P.build_packet(**kwargs)
        for field,value in (('split','holdout'),('date','2026-10-05'),('meeting_id','ga/reserved')):
            altered=copy.deepcopy(kwargs['bundles']);altered[0]['frame_entry'][field]=value
            with patch.object(P,'FRAME_SHA256',sha),self.assertRaisesRegex(ValueError,'membership'):
                P.build_packet(**{**kwargs,'bundles':altered})

    def test_changed_acceptance_pins_and_duplicate_membership_rejected(self):
        kwargs,sha=self.inputs()
        with patch.object(P,'FRAME_SHA256',sha):
            pins=copy.deepcopy(kwargs['expected_inputs']);pins[self.frame['meeting_id']]['reviews_sha256']='a'*64
            with self.assertRaisesRegex(ValueError,'pins'):P.build_packet(**{**kwargs,'expected_inputs':pins})
            with self.assertRaisesRegex(ValueError,'membership'):P.build_packet(**{**kwargs,'bundles':kwargs['bundles']*2})
            with self.assertRaisesRegex(ValueError,'membership'):P.build_packet(**{**kwargs,'expected_inputs':{**kwargs['expected_inputs'],'extra':{}}})

    def test_unresolved_context_still_has_policy_support(self):
        kwargs,sha=self.inputs();context=kwargs['bundles'][0]['context_reviews'][0]
        context.update(state='unresolved',object_evidence=[],context_evidence=[],relation=None,reason='no_literal_context')
        kwargs['expected_inputs'][self.frame['meeting_id']]['context_reviews_sha256']=P.digest(kwargs['bundles'][0]['context_reviews'])
        with patch.object(P,'FRAME_SHA256',sha):value=P.build_packet(**kwargs)
        self.assertEqual(['policy'],[e['kind'] for e in value['rows'][0]['evidence']])
        self.assertEqual('unresolved',value['rows'][0]['assistant_proposal']['context_state'])

    def test_packet_exact_immutable_reopen_changed_inputs_and_tampering(self):
        kwargs,sha=self.inputs();path=Path(self.temp.name)/'packet.json'
        with patch.object(P,'FRAME_SHA256',sha):
            packet=P.build_packet(**kwargs);P.save_packet(path,packet,**kwargs)
            self.assertEqual(packet,P.load_packet(path,**kwargs));P.save_packet(path,packet,**kwargs)
            altered=copy.deepcopy(packet);altered['rows'][0]['country']='Invented'
            with self.assertRaises(ValueError):P.save_packet(path,altered,**kwargs)
            data=path.read_bytes();path.write_bytes(data+b' ')
            with self.assertRaisesRegex(ValueError,'Noncanonical'):P.load_packet(path,**kwargs)

    def test_changed_current_batch_fails_reopen(self):
        kwargs,sha=self.inputs();path=Path(self.temp.name)/'packet.json'
        with patch.object(P,'FRAME_SHA256',sha):
            packet=P.build_packet(**kwargs);P.save_packet(path,packet,**kwargs)
            with patch('research.issue_history.ingest.transcript_context.get_current_batch',return_value=None),self.assertRaises(ValueError):P.load_packet(path,**kwargs)

    def decisions(self,packet):
        return P.build_decisions(packet,[{'row_id':r['id'],'label':None,'note':''} for r in packet['rows']],{'country':'all','policy':'all','status':'all'})

    def test_null_choices_filters_and_revisions_saved_separately(self):
        kwargs,sha=self.inputs()
        with patch.object(P,'FRAME_SHA256',sha):packet=P.build_packet(**kwargs)
        first=self.decisions(packet);path=Path(self.temp.name)/'choices1.json'
        P.save_decisions(path,first,packet=packet);self.assertEqual(first,P.load_decisions(path,packet=packet))
        choices=copy.deepcopy(first['choices']);choices[0]['label']='unclear'
        second=P.build_decisions(packet,choices,{'country':'Nigeria','policy':'humanitarian_access','status':'unclear'},first)
        path2=Path(self.temp.name)/'choices2.json';P.save_decisions(path2,second,packet=packet,previous=first)
        self.assertEqual(second,P.load_decisions(path2,packet=packet,previous=first))
        self.assertEqual(2,second['revision']);self.assertEqual(first['revision_sha256'],second['parent_revision_sha256'])
        self.assertFalse(second['owner_identity_verified']);self.assertFalse(second['accepted_positions'])
        with self.assertRaises(ValueError):P.load_decisions(path2,packet=packet)
        self.assertIsNone(packet['rows'][0]['owner_decision'])

    def test_choice_membership_filters_and_acceptance_claims_rejected(self):
        kwargs,sha=self.inputs()
        with patch.object(P,'FRAME_SHA256',sha):packet=P.build_packet(**kwargs)
        value=self.decisions(packet)
        for label in ('human_confirmed','accepted',True):
            choices=copy.deepcopy(value['choices']);choices[0]['label']=label
            with self.assertRaises(ValueError):P.build_decisions(packet,choices,value['filters'])
        with self.assertRaises(ValueError):P.build_decisions(packet,[],value['filters'])
        for key in ('country','policy','status'):
            with self.assertRaises(ValueError):P.build_decisions(packet,value['choices'],{**value['filters'],key:'invented'})
        for key in ('owner_identity_verified','accepted_positions','comparisons_eligible'):
            bad=copy.deepcopy(value);bad[key]=True;bad['revision_sha256']=P.digest({k:v for k,v in bad.items() if k!='revision_sha256'})
            with self.assertRaises(ValueError):P.save_decisions(Path(self.temp.name)/key,bad,packet=packet)

    def test_method_drift_rejects_saved_packet(self):
        kwargs,sha=self.inputs();path=Path(self.temp.name)/'packet.json'
        with patch.object(P,'FRAME_SHA256',sha):
            packet=P.build_packet(**kwargs);P.save_packet(path,packet,**kwargs)
            with patch.object(P,'_method',return_value='f'*64),self.assertRaises(ValueError):P.load_packet(path,**kwargs)

    def test_collective_source_is_not_assigned_to_registry_country(self):
        self.doc['transcript']['data'][0]['speaker']['group']='Synthetic Group'
        kwargs,sha=self.inputs(capacity='collective')
        with patch.object(P,'FRAME_SHA256',sha):packet=P.build_packet(**kwargs)
        self.assertEqual([],packet['country_groups']);self.assertEqual(1,len(packet['non_national_row_ids']))
        self.assertIsNone(packet['rows'][0]['country']);self.assertEqual('Synthetic Group',packet['rows'][0]['group'])

    def test_final_packet_current_batch_recheck(self):
        kwargs,sha=self.inputs()
        with patch.object(P,'FRAME_SHA256',sha),patch.object(P,'get_current_batch',return_value=None),self.assertRaisesRegex(ValueError,'Current batch'):
            P.build_packet(**kwargs)

    def test_changed_packet_and_immutable_decision_file_rejected(self):
        kwargs,sha=self.inputs()
        with patch.object(P,'FRAME_SHA256',sha):packet=P.build_packet(**kwargs)
        first=self.decisions(packet);path=Path(self.temp.name)/'first.json';P.save_decisions(path,first,packet=packet)
        second=P.build_decisions(packet,first['choices'],{**first['filters'],'status':'unreviewed'},first)
        with self.assertRaisesRegex(ValueError,'Immutable'):P.save_decisions(path,second,packet=packet,previous=first)
        altered=copy.deepcopy(packet);altered['input_fingerprints']['packet_method_sha256']='f'*64
        altered['packet_id']=P.digest({k:v for k,v in altered.items() if k!='packet_id'})
        with self.assertRaisesRegex(ValueError,'identity'):P.load_decisions(path,packet=altered)


if __name__=='__main__':unittest.main()
