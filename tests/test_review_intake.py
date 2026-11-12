import copy
import unittest
from test_models import fixtures
from un_transcript.models.contracts import digest
from un_transcript.models.review_intake import reconcile


def packet():
    _,reg,labels,*_=fixtures()
    pin=reg['sources'][0];text='Fictional source statement number 0'
    rows=[{**pin,'pair_id':'p'+str(i),'text':text,'start':0,'end':len(text),'issue_id':'ceasefire',
           'proposition':'Support a ceasefire','status':None,'label':None,'national_attribution_valid':None,'owner_confirmed':False} for i in range(2)]
    draft={'schema':'un.stance-labels.v1','registration_sha256':digest(reg),'owner_confirmed':False,
           'sample_role':'initial_pilot_not_acceptance_benchmark','complete_source_review':{'owner_confirmed':False},'rows':rows}
    identity={'split':'train','dataset_revision':'a'*40,'packet_prefix':'pilots/1-1/','manifest_sha256':'b'*64}
    returned={**copy.deepcopy(draft),'owner_confirmed':True,'reviewer_id':'synthetic-owner','reviewed_at':'2026-11-05T00:00:00Z',
              'rows':[{**rows[0],'status':'clear','label':'support','owner_confirmed':True,'notes':'synthetic'}],
              'review_export':{'schema':'un.owner-browser-review.v1','kind':'reviewed_subset','packet':identity,'total_examples':2,'confirmed_examples':1}}
    return draft,reg,returned,identity

class Intake(unittest.TestCase):
    def test_partial_idempotent_and_not_promoted(self):
        d,r,b,i=packet();out=reconcile(d,r,b,i)
        again=reconcile(d,r,b,i,out)
        self.assertEqual(again,out);self.assertEqual(len(out['rows']),1)
        self.assertFalse(out['complete_source_review']['owner_confirmed'])
        self.assertEqual(out['sample_role'],'initial_pilot_not_acceptance_benchmark')

    def test_source_or_proposition_change_rejected(self):
        for key in ('text','proposition','source_hash','segment_id'):
            d,r,b,i=packet();b['rows'][0][key]='changed'
            with self.assertRaises(ValueError):reconcile(d,r,b,i)

    def test_conflict_preserves_previous(self):
        d,r,b,i=packet();old=reconcile(d,r,b,i);saved=copy.deepcopy(old)
        b['rows'][0]['label']='oppose'
        with self.assertRaisesRegex(ValueError,'Conflicting'):reconcile(d,r,b,i,old)
        self.assertEqual(old,saved)

    def test_progress_foreign_packet_and_duplicate_rejected(self):
        for mode in ('progress','packet','duplicate'):
            d,r,b,i=packet()
            if mode=='progress':b['owner_confirmed']=False;b['review_export']['kind']='progress'
            if mode=='packet':b['review_export']['packet']={**i,'dataset_revision':'c'*40}
            if mode=='duplicate':b['rows'].append(copy.deepcopy(b['rows'][0]))
            with self.assertRaises(ValueError):reconcile(d,r,b,i)

    def test_export_schema_counts_and_prior_receipt_provenance_are_checked(self):
        for key,value in (('schema','foreign'),('total_examples',300),('confirmed_examples',True),('kind','reconciled_training')):
            d,r,b,i=packet();b['review_export'][key]=value
            with self.assertRaises(ValueError):reconcile(d,r,b,i)
        for hashes in ([],['not-a-digest'],['a'*64,'a'*64]):
            d,r,b,i=packet();old=reconcile(d,r,b,i);old['review_export']['input_exports']=hashes
            with self.assertRaises(ValueError):reconcile(d,r,b,i,old)

    def test_different_reviewer_never_reassigns_previous_confirmations(self):
        d,r,b,i=packet();old=reconcile(d,r,b,i);saved=copy.deepcopy(old)
        b['reviewer_id']='different synthetic reviewer'
        with self.assertRaisesRegex(ValueError,'Different reviewer'):reconcile(d,r,b,i,old)
        self.assertEqual(old,saved)

    def test_unknown_label_schema_is_not_silently_reinterpreted(self):
        for target in ('draft','returned','previous'):
            d,r,b,i=packet();old=reconcile(d,r,b,i)
            {'draft':d,'returned':b,'previous':old}[target]['schema']='un.stance-labels.v999'
            with self.subTest(target=target), self.assertRaisesRegex(ValueError,'label schema'):
                reconcile(d,r,b,i,old)

    def test_boolean_source_and_focal_offsets_are_not_integer_positions(self):
        for key in ('start','end','focal_start','focal_end'):
            d,r,b,i=packet()
            # False equals integer zero in Python: the frozen-field comparison
            # alone cannot reject this malformed JSON source coordinate.
            b['rows'][0][key]=False if key.endswith('start') else True
            with self.subTest(key=key), self.assertRaises(ValueError):
                reconcile(d,r,b,i)
