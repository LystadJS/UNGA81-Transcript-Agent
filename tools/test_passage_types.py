"""Source integrity, boundary screening and explicit decision import tests."""
import copy
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
import passage_type_audit as p


def row(n, text, country='GA'):
    return dict(id=f'asset/test/meeting#{n}', text=text, text_sha256=p.digest(text.encode()),
                source_url=f'https://transcripts.un.org/en/asset/test/meeting?t={n}',
                country=country,date='2026-09-22',region='Unmapped')


class PassageTypes(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.corpus=self.root/'original.json'
        self.records=[row(0,'We will continue the general debate tomorrow. The exercise of the right of reply has been requested.'),row(1,'We respond to the earlier statement.','Example'),row(2,'The next meeting is called to order. The Assembly will hear an address.'),row(3,'Mr. President, I would like to thank my colleagues. '+'Policy development. '*550,'Example')]
        p.write(self.corpus,dict(schema='un.browser.corpus.v1',records=self.records))
        self.before=self.corpus.read_bytes()

    def tearDown(self):
        self.tmp.cleanup()

    def test_reply_context_reset_and_long_greeting(self):
        rows=p.propose(self.records)
        self.assertEqual([r['proposed_type'] for r in rows],['procedure','right_of_reply','procedure','substantive_speech'])

    def test_original_hash_and_duplicate_ids(self):
        data=json.loads(self.before);data['records'][1]['text']+=' changed';p.write(self.corpus,data)
        with self.assertRaisesRegex(ValueError,'hash mismatch'):p.load_corpus(self.corpus)
        data=json.loads(self.before);data['records'].append(data['records'][0]);p.write(self.corpus,data)
        with self.assertRaisesRegex(ValueError,'Duplicate'):p.load_corpus(self.corpus)

    def test_packet_escapes_source_script_and_preserves_input(self):
        data=json.loads(self.before);data['records'][1]=row(1,'</script><script>window.bad=true</script>','Example');p.write(self.corpus,data)
        before=self.corpus.read_bytes();p.prepare(self.corpus,self.root/'packet')
        html=(self.root/'packet/review.html').read_text(encoding='utf-8')
        self.assertNotIn('</script><script>window.bad',html);self.assertEqual(before,self.corpus.read_bytes())

    def test_mask_coverage_and_no_human_fabrication(self):
        p.prepare(self.corpus,self.root/'packet');mask=json.loads((self.root/'packet/mask.json').read_text(encoding='utf-8'));data,sha=p.load_corpus(self.corpus)
        self.assertTrue(all(r['confirmed_type'] is None for r in mask['rows']))
        invalid=copy.deepcopy(mask);invalid['rows'][1]=invalid['rows'][0]
        with self.assertRaisesRegex(ValueError,'exactly once'):p.validate_mask(data,sha,invalid)
        mask['rows'][0]['text_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'hash mismatch'):p.validate_mask(data,sha,mask)

    def test_partial_import_and_explicit_confirmation(self):
        p.prepare(self.corpus,self.root/'packet');mask=self.root/'packet/mask.json';data=json.loads(mask.read_text(encoding='utf-8'))
        choice=dict(id=self.records[1]['id'],text_sha256=self.records[1]['text_sha256'],type='right_of_reply',reviewer='Synthetic test reviewer',reviewed_at=dt.datetime.now(dt.timezone.utc).isoformat(),confirmed=False)
        review=self.root/'choices.json';incoming=dict(schema='un.passage-type-review.v1',corpus_sha256=data['corpus_sha256'],choices=[choice]);p.write(review,incoming)
        with self.assertRaisesRegex(ValueError,'Explicit'):p.import_review(self.corpus,mask,review,self.root/'updated.json')
        choice['confirmed']=True;p.write(review,incoming)
        result=p.import_review(self.corpus,mask,review,self.root/'updated.json')
        self.assertEqual(result,{'status':'partially_confirmed','confirmed':1})
        self.assertIn('reviewer-declared',json.loads((self.root/'updated.json').read_text(encoding='utf-8'))['provenance'])
        self.assertEqual(self.before,self.corpus.read_bytes())
        self.assertTrue(all(r['confirmed_type'] is None for r in json.loads(mask.read_text(encoding='utf-8'))['rows']))
        incoming['choices'].append(choice);p.write(review,incoming)
        with self.assertRaisesRegex(ValueError,'Duplicate'):p.import_review(self.corpus,mask,review,self.root/'bad.json')

    def test_protected_output(self):
        p.prepare(self.corpus,self.root/'packet')
        with self.assertRaisesRegex(ValueError,'preserve input'):p.import_review(self.corpus,self.root/'packet/mask.json',self.root/'unused.json',self.corpus)
        self.assertEqual(self.before,self.corpus.read_bytes())


if __name__=='__main__':unittest.main()
