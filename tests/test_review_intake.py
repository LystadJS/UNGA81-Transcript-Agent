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
              'review_export':{'kind':'reviewed_subset','packet':identity}}
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
