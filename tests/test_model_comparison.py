import unittest,json
from pipeline.model_comparison import compare,classical_submission,ROOT
from pipeline.document_benchmark import suite
class ComparisonTests(unittest.TestCase):
    def test_paired_partition(self):
        d,g=suite()
        sub=json.loads((ROOT/"gpt62_conversation_dev.json").read_text())
        r=compare(d,g,[classical_submission(d),sub])
        self.assertEqual(sum(r["paired"][0]["counts"].values()),20)
        self.assertFalse(r["independent_validation"])
        self.assertIsNone(r["significance_or_generalization"])
        self.assertEqual(r["publication"],"BLOCK_PUBLICATION")
    def test_duplicate_runs(self):
        d,g=suite();s=classical_submission(d)
        with self.assertRaisesRegex(ValueError,"RUN_IDS"):compare(d,g,[s,s])
