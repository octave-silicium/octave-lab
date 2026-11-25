import unittest
from dataclasses import replace
from fractions import Fraction as F
from pipeline.economic_sector_make_buy_pilot import fixture
from pipeline.economic_sector_make_buy import bridge

class MakeBuyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.s,cls.e,cls.m,cls.a,cls.mp=fixture()
    def test_quantity(self):
        r=bridge(self.s,self.e,self.m,self.mp)["result"];q=r["quantities"]
        self.assertEqual(q["external_before"]-q["external_after"],q["internal_after"])
        self.assertEqual(q["total"],45)
    def test_consolidation(self):
        r=bridge(self.s,self.e,self.a,self.mp)["result"]
        for x in r["direct_chain"].values():
            self.assertEqual(F(x["buyer_cash_eur"])+F(x["seller_cash_cost_eur"])-F(x["external_transfer_eur"]),F(x["consolidated_cash_cost_eur"]))
    def test_capital_separate(self):
        r=bridge(self.s,self.e,self.a,self.mp)["result"]
        self.assertEqual(F(r["capital_separate_mEUR"]["investment_delta"]),F("2/5"))
        self.assertEqual(F(r["capital_separate_mEUR"]["transition_delta"]),F("1/50"))
        self.assertAlmostEqual(sum(r["sector"]["demand_shapley"]),0)
    def test_reverse(self):
        r=bridge(self.s,self.a,self.e,self.mp)["result"]
        self.assertGreater(F(r["recurring_buyer_reference_mEUR"]["external_delta"]),0)
    def test_manual_auto(self):
        r=bridge(self.s,self.m,self.a,self.mp)["result"]
        self.assertEqual(F(r["recurring_buyer_reference_mEUR"]["external_delta"]),0)
        self.assertLess(F(r["recurring_buyer_reference_mEUR"]["payroll_delta"]),0)
    def test_missing_cost_mapping(self):
        with self.assertRaisesRegex(ValueError,"ALLOCATION_COVERAGE"):bridge(self.s,self.e,self.a,replace(self.mp,allocations=self.mp.allocations[:-1]))
    def test_unqualified(self):
        with self.assertRaisesRegex(ValueError,"INTERNAL_UNQUALIFIED"):bridge(self.s,self.e,replace(self.a,internal_production=None),self.mp)
    def test_period(self):
        with self.assertRaisesRegex(ValueError,"NATIVE_PERIOD"):bridge(self.s,self.e,self.a,replace(self.mp,periods=100))
    def test_coverage(self):
        with self.assertRaisesRegex(ValueError,"BASE_COVERAGE"):bridge(self.s,self.e,self.a,replace(self.mp,cohorts="100000"))
    def test_empirical(self):
        with self.assertRaisesRegex(ValueError,"ADMISSION"):bridge(replace(self.s,origin="PINNED_2022_CONDITIONAL"),self.e,self.a,self.mp)
