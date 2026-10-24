"""Invented inventory and receipt metadata only; never opens transcript wording."""
import copy
import hashlib
import json
import unittest
from .discovery import transcript_inventory
from . import statement_coverage as C


DAY='2024-01-01'


def page(slugs, *, day=DAY, number=1, total=None, more=False, advertised=True):
    meetings=[{'slug':slug,'date':day+'T00:00:00.000Z','body':'Invented catalog body label',
        'category':'Invented category','hasTranscript':advertised,
        'pageUrl':'/en/'+slug,'jsonUrl':'/en/'+slug+'.json','textUrl':'/en/'+slug+'.txt'} for slug in slugs]
    raw=json.dumps({'page':number,'total':len(meetings) if total is None else total,
                    'hasMore':more,'meetings':meetings}).encode()
    return transcript_inventory(raw,day,page=number)


def receipt(p, index=0, *, retrieved=True, verified=False, extracted=False, suffix='jsonUrl'):
    meeting=p['meetings'][index]
    return {'schema':'un.statement-artifact-receipt.v1','meeting_id':meeting['meeting_id'],
        'date':meeting['date'],'body':meeting['body'],'inventory_metadata_sha256':p['metadata_sha256'],
        'source_url':meeting[suffix],'retrieved':retrieved,'hash_verified':verified,
        'extraction_complete':extracted,'expected_sha256':'a'*64 if verified else None,
        'source_sha256':'a'*64 if retrieved else None,
        'normalized_sha256':'c'*64 if extracted else None,
        'extraction_method_version':'synthetic-extractor-1' if extracted else None}


class StatementCoverageTests(unittest.TestCase):
    def build(self, pages, receipts=(), *, start=DAY, end=DAY, bodies=('SC',)):
        return C.reconcile_coverage(start=start,end=end,bodies=list(bodies),pages=pages,receipts=list(receipts))

    def test_complete_catalog_is_not_complete_archive_and_inputs_are_immutable(self):
        p=page(['sc/9999']);r=receipt(p,verified=True,extracted=True)
        before=copy.deepcopy(([p],[r]));result=self.build([p],[r]);row=result['rows'][0]
        self.assertEqual('reconciled_catalog',row['catalog_status'])
        self.assertTrue(row['catalog_pages_reconciled'])
        self.assertEqual(1,row['advertised_meetings']);self.assertEqual(1,row['extraction_complete'])
        self.assertEqual([r],row['meetings'][0]['artifact_receipts'])
        self.assertEqual(p['meetings'][0]['recorded_body'],row['meetings'][0]['recorded_body'])
        self.assertEqual(p['meetings'][0]['category'],row['meetings'][0]['category'])
        self.assertEqual('unknown',result['archive_completeness'])
        self.assertEqual(before,([p],[r]))
        self.assertEqual(result,self.build([p],[r]))
        self.assertNotIn('text',result)

    def test_retrieval_verification_and_extraction_are_separate_counts(self):
        p=page(['sc/9997','sc/9998','sc/9999'])
        result=self.build([p],[receipt(p,0),receipt(p,1,verified=True),receipt(p,2,verified=True,extracted=True)])
        row=result['rows'][0]
        self.assertEqual(3,row['advertised_meetings']);self.assertEqual(3,row['transcript_advertised'])
        self.assertEqual(3,row['retrieved']);self.assertEqual(2,row['receipt_reported_hash_verified']);self.assertEqual(1,row['extraction_complete'])

    def test_not_advertised_is_not_verified_absence_or_opposition(self):
        p=page(['sc/9999'],advertised=False);row=self.build([p])['rows'][0]
        self.assertEqual(1,row['advertised_meetings']);self.assertEqual(0,row['transcript_advertised'])
        self.assertEqual(1,row['not_advertised']);self.assertEqual(0,row['retrieved'])

    def test_missing_day_stays_unknown(self):
        result=self.build([page(['sc/9999'])],end='2024-01-02')
        missing=next(r for r in result['rows'] if r['date']=='2024-01-02')
        self.assertEqual('unknown',missing['catalog_status'])
        self.assertFalse(missing['catalog_pages_reconciled'])
        self.assertEqual('unknown',result['archive_completeness'])

    def test_empty_returned_day_does_not_certify_no_meetings(self):
        row=self.build([page([])])['rows'][0]
        self.assertTrue(row['catalog_pages_reconciled'])
        self.assertEqual('unknown',row['catalog_status'])
        self.assertEqual(0,row['advertised_meetings'])

    def test_missing_page_or_terminal_stays_incomplete(self):
        cases=[[page(['sc/9997'],total=3,more=True),page(['sc/9999'],number=3,total=3)],
               [page(['sc/9997'],total=2,more=True)],
               [page(['sc/9998'],number=2,total=2)]]
        for pages in cases:
            with self.subTest(pages=[p['page'] for p in pages]):
                row=self.build(pages)['rows'][0]
                self.assertEqual('incomplete_pages',row['catalog_status'])
                self.assertFalse(row['catalog_pages_reconciled'])

    def test_complete_multi_page_chain_reconciles_all_bodies_before_filtering(self):
        pages=[page(['sc/9999'],total=3,more=True),
               page(['ga/c3/79/1','ga/79/1'],number=2,total=3)]
        result=self.build(pages,bodies=('GA_C3',))
        self.assertEqual(1,len(result['rows']))
        row=result['rows'][0]
        self.assertEqual('GA_C3',row['body']);self.assertEqual('reconciled_catalog',row['catalog_status'])
        self.assertEqual(1,row['advertised_meetings'])
        self.assertEqual(1,len(row['meetings']))

    def test_exact_ga_and_committee_bodies_do_not_auto_expand(self):
        p=page(['ga/79/1','ga/c1/79/1','ga/c3/79/1'])
        plenary=self.build([p],bodies=('GA',))['rows'][0]
        committee=self.build([p],bodies=('GA_C3',))['rows'][0]
        self.assertEqual(1,plenary['advertised_meetings']);self.assertEqual(1,committee['advertised_meetings'])
        self.assertEqual('GA',plenary['body']);self.assertEqual('GA_C3',committee['body'])

    def test_unstable_totals_duplicate_pages_or_meetings_are_rejected(self):
        first=page(['sc/9997'],total=2,more=True)
        cases=[[first,page(['sc/9998'],number=2,total=3)],
               [first,copy.deepcopy(first)],
               [first,page(['sc/9997'],number=2,total=2)]]
        for pages in cases:
            with self.subTest(pages=pages):
                with self.assertRaises(ValueError):self.build(pages)

    def test_contradictory_terminal_and_short_complete_catalog_rejected(self):
        p=page(['sc/9997'],total=2,more=True);p['has_more']=False
        with self.assertRaises(ValueError):self.build([p])
        first=page(['sc/9997']);second=page(['sc/9998'],number=2,total=1)
        with self.assertRaises(ValueError):self.build([first,second])

    def test_page_meeting_date_body_and_identity_must_match(self):
        for field,value in [('date','2024-01-02'),('body','GA'),('meeting_id','ga/79/1')]:
            p=page(['sc/9999']);p['meetings'][0][field]=value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):self.build([p])

    def test_receipt_must_link_exact_inventory_meeting_date_body_and_hash(self):
        p=page(['sc/9999'])
        for field,value in [('meeting_id','sc/9998'),('date','2024-01-02'),('body','GA'),
                            ('inventory_metadata_sha256','b'*64),('source_url','https://transcripts.un.org/en/sc/9998.json')]:
            r=receipt(p);r[field]=value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):self.build([p],[r])

    def test_verification_requires_matching_hashes_and_extraction_requires_verification(self):
        p=page(['sc/9999']);r=receipt(p)
        invalid=[{**r,'hash_verified':True,'expected_sha256':'b'*64},
                 {**r,'extraction_complete':True},
                 {**r,'source_sha256':None},
                 {**r,'retrieved':False,'hash_verified':True,'expected_sha256':'a'*64}]
        for item in invalid:
            with self.subTest(item=item):
                with self.assertRaises(ValueError):self.build([p],[item])

    def test_multiple_artifacts_and_duplicate_receipts_count_distinct_meetings(self):
        p=page(['sc/9999']);json_receipt=receipt(p,verified=True)
        text_receipt=receipt(p,verified=True,extracted=True,suffix='textUrl')
        row=self.build([p],[json_receipt,copy.deepcopy(json_receipt),text_receipt])['rows'][0]
        self.assertEqual(1,row['advertised_meetings']);self.assertEqual(1,row['retrieved'])
        self.assertEqual(1,row['receipt_reported_hash_verified']);self.assertEqual(1,row['extraction_complete'])

    def test_conflicting_same_artifact_receipts_rejected(self):
        p=page(['sc/9999']);r=receipt(p)
        with self.assertRaises(ValueError):self.build([p],[r,{**r,'source_sha256':'b'*64}])

    def test_raw_wording_and_position_counts_are_not_coverage_metadata(self):
        p=page(['sc/9999']);r=receipt(p)
        for field,value in [('text','Invented wording'),('positions',100),('speaker_records',500)]:
            with self.subTest(field=field):
                with self.assertRaises(ValueError):self.build([p],[{**r,field:value}])

    def test_invalid_window_body_and_page_hash_rejected(self):
        p=page(['sc/9999'])
        for changes in ({'start':'2024-02-30'},{'start':'2024-01-02'},
                        {'bodies':('ga',)},{'bodies':('GA_C7',)}):
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):self.build([p],**changes)
        p['metadata_sha256']='not-a-hash'
        with self.assertRaises(ValueError):self.build([p])

    def test_extraction_requires_normalized_hash_and_method_version(self):
        p=page(['sc/9999']);r=receipt(p,verified=True,extracted=True)
        for field,value in [('normalized_sha256',None),('normalized_sha256','bad'),
                            ('extraction_method_version',None),('extraction_method_version','')]:
            with self.subTest(field=field,value=value):
                with self.assertRaises(ValueError):self.build([p],[{**r,field:value}])

    def test_unknown_meeting_count_does_not_turn_missing_catalog_into_zero(self):
        p=page(['sc/9998','sc/9999'])
        known=self.build([p],[receipt(p)])['rows'][0]
        self.assertEqual(1,known['unknown_meetings'])
        unknown=self.build([],end='2024-01-02')
        self.assertTrue(all(r['unknown_meetings'] is None for r in unknown['rows']))
        self.assertIsNone(unknown['summary']['unknown_meetings'])

    def test_body_date_rows_and_caller_receipts_are_not_evidence_of_opinion(self):
        p=page(['sc/9999']);result=self.build([p],[receipt(p,verified=True,extracted=True)])
        self.assertEqual('provided_receipts_not_recomputed_content',result['verification_scope'])
        self.assertEqual('unknown',result['archive_completeness'])
        self.assertNotIn('opinion',result)
        self.assertNotIn('positions',result['summary'])


if __name__=='__main__':unittest.main()
