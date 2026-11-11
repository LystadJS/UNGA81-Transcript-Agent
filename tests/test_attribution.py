import unittest

from un_transcript.attribution import METHOD_VERSION, infer_capacity


class AttributionTests(unittest.TestCase):
    def segment(self,text,**extra):
        return dict(text=text,country="FRA",capacity="unknown",**extra)

    def test_explicit_first_person_national_claim_has_exact_source_evidence(self):
        original=self.segment("I speak on behalf of the Government of France. We support this proposal.")
        result=infer_capacity(original)
        self.assertEqual(result["attribution_kind"],"national")
        self.assertEqual(result["capacity"],"unknown")
        self.assertNotIn("attribution_kind",original)
        self.assertEqual(result["canonical_country"],"FRA")
        self.assertEqual(result["attribution_method_version"],METHOD_VERSION)
        for span in result["attribution_evidence"]:
            self.assertEqual(original["text"][span["start"]:span["end"]],span["quote"])

    def test_delegation_and_representative_constructions(self):
        for text in ("On behalf of the delegation of France, I thank the Chair.",
                     "As the representative of France, I support the proposal.",
                     "I am speaking as the representative of France.",
                     "I have the honour to speak on behalf of the Government of France."):
            with self.subTest(text=text):
                self.assertEqual(infer_capacity(self.segment(text))["attribution_kind"],"national")

    def test_collective_statement_anywhere_overrides_national(self):
        for capacity in ("unknown","national"):
            segment={"text":"I speak on behalf of the Government of France. I speak on behalf of the European Union.","country":"FRA","capacity":capacity}
            result=infer_capacity(segment)
            self.assertEqual(result["attribution_kind"],"collective")
            self.assertEqual(result["capacity"],capacity)
        result=infer_capacity(self.segment("I speak on behalf of the delegation of France and Germany."))
        self.assertEqual(result["attribution_kind"],"collective")
        for group in ("France and Germany","G77 and China","AOSIS"):
            result=infer_capacity(self.segment("I speak on behalf of "+group+"."))
            self.assertEqual(result["attribution_kind"],"collective")

    def test_third_party_negated_hypothetical_and_quoted_claims_stay_unknown(self):
        for text in ("The representative said I speak on behalf of the Government of France.",
                     'He stated: "I speak on behalf of the Government of France."',
                     '“I speak on behalf of the Government of France.”',
                     "I do not speak on behalf of the Government of France.",
                     "If I speak on behalf of the Government of France, this would change.",
                     "As representative of France, he supports the proposal.",
                     "Yesterday I said I speak on behalf of the Government of France."):
            with self.subTest(text=text):
                self.assertEqual(infer_capacity(self.segment(text))["attribution_kind"],"unknown")

    def test_recorded_affiliation_alone_is_not_national_capacity(self):
        self.assertEqual(infer_capacity(self.segment("We support the proposal."))["attribution_kind"],"unknown")
        self.assertEqual(infer_capacity(self.segment("I speak on behalf of the Government of Germany."))["attribution_kind"],"unknown")
        result=infer_capacity({"text":"I speak on behalf of the Government of France.","country":"unrecognized","capacity":"unknown"})
        self.assertEqual(result["attribution_kind"],"unknown")

    def test_aliases_and_declared_collective_are_preserved(self):
        result=infer_capacity({"text":"I speak on behalf of the Government of the United States of America.","country":"USA","capacity":"unknown"})
        self.assertEqual(result["attribution_kind"],"national")
        result=infer_capacity({"text":"I speak on behalf of the Government of France.","country":"FRA","capacity":"collective","group_name":"Invented group"})
        self.assertEqual(result["attribution_kind"],"collective")
        self.assertEqual(result["group_name"],"Invented group")


if __name__ == "__main__":
    unittest.main()
