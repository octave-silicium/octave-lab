import unittest
from pipeline.document_benchmark import suite,run_classic,classic
class DocumentBenchTests(unittest.TestCase):
    def test_real_development_run(self):
        r=run_classic()
        self.assertEqual(r["cases"],20)
        self.assertEqual(r["counts"]["exact_case_correct"],11)
        self.assertEqual(r["counts"]["abstain_or_error"],9)
        self.assertEqual(r["counts"]["false_accept"],0)
        self.assertIsNone(r["total_cost_eur"])
        self.assertEqual(r["strata"]["free_text"]["exact"],0)
    def test_conflict_and_missing(self):
        d,_=suite();cases={c["id"]:c for c in d["cases"]}
        self.assertEqual(classic(cases["T11"])["issues"],["CONTRADICTORY_FIELD"])
        self.assertEqual(classic(cases["T12"])["decision"],"ABSTAIN")
        self.assertEqual(classic(cases["T09"])["issues"],["MISSING_DOCUMENT"])
