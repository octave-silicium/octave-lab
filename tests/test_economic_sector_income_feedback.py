import unittest
from dataclasses import replace
from pipeline.economic_sector_structural import Structure
from pipeline.economic_sector_prices import PricePolicy
from pipeline.economic_sector_budget import HouseholdBasket,BudgetPolicy
from pipeline.economic_sector_income_feedback import IncomeRule,Period,distribute,feedback

class IncomeFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.s=Structure(("A","B"),((0,.5),(0,0)),((0,0),(0,.2)),((1,0),(0,1)),(.5,.1),(0,0),(0,0),(.5,.2),(100,100),"SYNTHETIC")
        self.h=HouseholdBasket((40,40),(20,0),"synthetic")
        self.p=PricePolicy((0,0),(1,1),(1,1),(1,1),(1,1),"synthetic")
        self.b=BudgetPolicy(100,0,1,(10,10),(10,10),(1,1),"synthetic")
        self.r=IncomeRule(.2,0,.2,.5,0,.1,4.6,1,"synthetic")
        self.period=Period(self.s,self.p,self.b,self.r,"synthetic")
    def run_path(self,ps=None,initial=100):
        return feedback(self.s,self.h,ps or (self.period,)*4,initial,period_unit="YEAR",evidence="synthetic")["result"]
    def test_reference_replay(self):
        r=self.run_path()
        for p in r["periods"]:
            self.assertAlmostEqual(p["input_envelope"],100)
            self.assertAlmostEqual(p["income"]["next_basic_price_envelope"],100)
    def test_lag(self):
        t=replace(self.s,wage=(.4,.1),surplus=(.6,.2))
        r=self.run_path((replace(self.period,structure=t),self.period))
        self.assertAlmostEqual(r["periods"][0]["input_envelope"],100)
        self.assertAlmostEqual(r["periods"][0]["income"]["next_basic_price_envelope"],94.6)
        self.assertAlmostEqual(r["periods"][1]["input_envelope"],94.6)
    def test_transfers(self):
        r=self.run_path((replace(self.period,income_rule=replace(self.r,public_transfer=14.6)),self.period))
        self.assertAlmostEqual(r["periods"][1]["input_envelope"],110)
    def test_distribution_conserves(self):
        n={"compensation":100,"gross_surplus_mixed":80,"other_net_production_taxes":-5,"valuation_bridge":-2}
        x=distribute(n,replace(self.r,foreign_wage_share=.1,foreign_distribution_share=.2))
        self.assertAlmostEqual(x["allocation_residual"],0)
        self.assertAlmostEqual(x["foreign_wage"],8)
        self.assertAlmostEqual(x["foreign_capital_allocation"],12.8)
    def test_losses(self):
        n={"compensation":100,"gross_surplus_mixed":-20,"other_net_production_taxes":0,"valuation_bridge":0}
        x=distribute(n,self.r);self.assertEqual(x["retained_enterprise_residual"],-20);self.assertEqual(x["household_capital_mixed_allocation"],0)
    def test_unfinanced_transfer(self):
        r=self.run_path((replace(self.period,income_rule=replace(self.r,public_transfer=1000)),))
        self.assertGreater(r["periods"][0]["income"]["public_allocation_gap"],0)
        self.assertIsNone(r["government_deficit"])
    def test_envelope(self):
        r=self.run_path((replace(self.period,income_rule=replace(self.r,envelope_share=.5)),))
        self.assertAlmostEqual(r["next_envelope"],50)
        self.assertAlmostEqual(r["periods"][0]["income"]["outside_basic_price_envelope"],50)
    def test_bad_distribution(self):
        with self.assertRaisesRegex(ValueError,"DISTRIBUTION_SHARE"):self.run_path((replace(self.period,income_rule=replace(self.r,foreign_distribution_share=.8)),))
    def test_no_lookahead(self):
        a=self.run_path()
        b=self.run_path((self.period,replace(self.period,income_rule=replace(self.r,public_transfer=100))))
        self.assertEqual(a["periods"][0],b["periods"][0])
    def test_replay(self):self.assertEqual(self.run_path(),self.run_path())
    def test_no_actual_claims(self):
        r=self.run_path()
        for k in ("actual_disposable_income","actual_savings","government_deficit","gdp","employment"):self.assertIsNone(r[k])
    def test_no_double_spend(self):
        r=self.run_path(initial=0)
        self.assertAlmostEqual(r["periods"][0]["budget"]["domestic"],0)
        self.assertGreater(r["periods"][0]["income"]["next_basic_price_envelope"],0)
    def test_signed_tax(self):
        x=distribute({"compensation":0,"gross_surplus_mixed":0,"other_net_production_taxes":-10,"valuation_bridge":5},self.r)
        self.assertAlmostEqual(x["public_allocation_gap"],14.6)
        self.assertAlmostEqual(x["allocation_residual"],0)
