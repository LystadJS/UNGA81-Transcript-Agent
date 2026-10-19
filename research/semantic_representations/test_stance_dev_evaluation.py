"""Prespecified adversarial controls; invented text only."""
import copy
import unittest

from fixtures import fixture_frame
from pipeline import validate_frame
from stance_dev_evaluation import cases, sign, proposition, scored_pair, STRATA_COUNTS, ROLES


class PredeclaredCaseTests(unittest.TestCase):
    def test_counts_unique_four_roles_and_no_source_text(self):
        data=cases()
        self.assertEqual(len(data),30)
        self.assertEqual(len({c["id"] for c in data}),30)
        self.assertEqual({s:sum(c["stratum"]==s for c in data) for s in STRATA_COUNTS},STRATA_COUNTS)
        self.assertEqual(len(fixture_frame(data)["rows"]),120)
        for case in data:
            for role in ROLES:
                self.assertTrue(case[role])
                self.assertNotIn("A/81/PV",case[role])

    def test_explicit_and_negation_polarity(self):
        explicit=[c for c in cases() if c["stratum"] in ("explicit","negated")]
        self.assertEqual(len(explicit),14)
        for case in explicit:
            self.assertIsNotNone(sign(case["anchor"]))
            self.assertEqual(sign(case["anchor"]),sign(case["paraphrase"]))
            self.assertEqual(sign(case["opposite"]),-sign(case["anchor"]))
            self.assertEqual(sign(case["protocol"]),-sign(case["anchor"]))
            self.assertEqual(proposition(case,"anchor"),proposition(case,"opposite"))

    def test_all_prospective_guards_abstain_without_imputation(self):
        guards=[c for c in cases() if c["stratum"] not in ("explicit","negated")]
        self.assertEqual(len(guards),16)
        for case in guards:
            for role in ROLES[1:]:
                self.assertIsNone(scored_pair(case,role,0.91,0), (case["id"],role))
                self.assertIsNone(scored_pair(case,role,0.91,2), (case["id"],role))

    def test_out_of_scope_proposition_never_promoted(self):
        scope=[c for c in cases() if c["stratum"]=="scope"]
        self.assertEqual(len(scope),4)
        for case in scope:
            self.assertNotEqual(proposition(case,"anchor"),proposition(case,"opposite"))
            self.assertIsNone(scored_pair(case,"opposite",0.99,0))

    def test_quote_third_party_ambiguous_and_conditional_refusal(self):
        for text in ('The observer quoted "We support more clinics."',
                     "Our delegation favors more clinics only if costs decline.",
                     "We oppose more clinics unless staff increases.",
                     "It may be useful to consider more clinics.",
                     "According to the report, we endorse more clinics."):
            self.assertIsNone(sign(text),text)

    def test_duplicate_source_ids_fail_closed(self):
        frame=fixture_frame(cases())
        frame["rows"][1]["id"]=frame["rows"][0]["id"]
        with self.assertRaisesRegex(ValueError,"duplicate"):
            validate_frame(frame)

    def test_corrupted_text_digest_fails_closed(self):
        frame=fixture_frame(cases())
        frame["rows"][0]["text"]+=" altered"
        with self.assertRaisesRegex(ValueError,"hash"):
            validate_frame(frame)

    def test_reserved_split_fails_closed(self):
        frame=fixture_frame(cases())
        frame["split"]="holdout"
        with self.assertRaisesRegex(ValueError,"holdout"):
            validate_frame(frame)

    def test_explicit_rank_rule_refuses_opposition(self):
        case=next(c for c in cases() if c["stratum"]=="explicit")
        self.assertGreater(scored_pair(case,"paraphrase",0.25,0),
                           scored_pair(case,"opposite",0.99,0))
        self.assertGreater(scored_pair(case,"paraphrase",0.0,2),
                           scored_pair(case,"opposite",1.0,2))


if __name__=="__main__":
    unittest.main()
