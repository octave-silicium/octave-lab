import unittest,json
from dataclasses import replace
from fractions import Fraction as F
from pipeline.vertical_scenarios import *
from pipeline.vertical_v2 import build,coverage,summary,make_observations
class ScenarioTests(unittest.TestCase):
    def test_zero_and_opposite_signs(self):
        rows={r["id"]:r for r in compare()["result"]["scenarios"]}
        self.assertEqual(rows["reference"]["paid_hours_delta"],"0")
        self.assertLess(F(rows["substitution"]["paid_hours_delta"]),0)
        self.assertGreater(F(rows["complementarity"]["paid_hours_delta"]),0)
        self.assertEqual(rows["retained_payroll"]["paid_hours_delta"],"0")
    def test_threshold(self):
        self.assertEqual(run(CASES[1])["break_even_volume_for_baseline_active_hours"],"2000")
        self.assertEqual(run(CASES[1])["break_even_volume_growth_pct"],"100")
    def test_cash_and_replay(self):
        self.assertEqual(compare(),compare())
        for c in CASES:
            r=run(c);self.assertEqual(sum(map(F,r["incidence_eur"].values())),F(r["buyer_expenditure_delta_eur"]))
            self.assertIsNone(r["actual_jobs"])
    def test_stress(self):
        self.assertGreater(run(CASES[-1])["unserved"],0)
        with self.assertRaisesRegex(ValueError,"SCENARIO_PARAMETER"):run(replace(BASE,pass_through="2"))
    def test_coverage(self):
        c=coverage();self.assertEqual(len(c),140)
        self.assertEqual(len({x["id"] for x in c}),140)
        self.assertTrue(all(x["reason"] for x in c))
    def test_object_and_summary_privacy(self):
        src={"urssaf_headcount":{"sha256":"a","analysis":{"same_quarter_year_on_year":[{"to":"2026Q2","value":"PRIVATE_SENTINEL"}]}},"urssaf_dpae":{"sha256":"b","analysis":{"comparisons":[{"to":"2026Q3","value":"PRIVATE_SENTINEL"}]}},"eurostat_ai":{"sha256":"c","analysis":{}}}
        r=build(src);self.assertEqual(len(r["result"]["sections"]),18)
        self.assertNotIn("PRIVATE_SENTINEL",json.dumps(summary(r)))
        self.assertEqual(r["result"]["publication"],"BLOCK_PUBLICATION")
    def test_unreviewed_source(self):
        with self.assertRaisesRegex(ValueError,"UNREVIEWED_VINTAGE"):make_observations(lambda u:b"wrong")
