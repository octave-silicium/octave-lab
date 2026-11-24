import unittest
from pipeline.invoice_benchmark import validated_suite,evaluate,run_baseline,digest
class BenchmarkTests(unittest.TestCase):
    def test_baseline(self):
        r=run_baseline()
        self.assertEqual(r["cases"],16)
        self.assertEqual(r["counts"]["exact_case_correct"],16)
        self.assertIsNone(r["median_wall_seconds"])
    def test_false_accept_and_missing(self):
        d,g=validated_suite()
        sub={"mode":"HUMAN","run_id":"fixture","configuration":{"participant_code":"fixture"},"suite_sha256":digest(d),"outputs":[{"id":k,"decision":"ACCEPT","issues":[]} for k in g["expected"]]}
        r=evaluate(sub,d,g)
        self.assertEqual(r["counts"]["false_accept"],13)
        sub["outputs"].pop()
        with self.assertRaisesRegex(ValueError,"INCOMPLETE"):evaluate(sub,d,g)
    def test_no_unverified_cost(self):
        d,g=validated_suite()
        sub={"mode":"HUMAN","run_id":"fixture","configuration":{"participant_code":"fixture"},"suite_sha256":digest(d),"outputs":[{"id":k,**v,"wall_seconds":1} for k,v in g["expected"].items()]}
        with self.assertRaisesRegex(ValueError,"MEASUREMENT"):evaluate(sub,d,g)
