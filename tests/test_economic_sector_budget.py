import unittest
from dataclasses import replace
from pipeline.economic_sector_structural import Structure
from pipeline.economic_sector_prices import PricePolicy
from pipeline.economic_sector_budget import HouseholdBasket,BudgetPolicy,budgeted,allocation

class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.s=Structure(("A","B"),((0,.5),(0,0)),((0,0),(0,.2)),((1,0),(0,1)),(.5,.1),(0,0),(0,0),(.5,.2),(100,100),"SYNTHETIC")
        self.t=replace(self.s,wage=(.4,.1),surplus=(.6,.2))
        self.p=PricePolicy((1,1),(1,1),(1,1),(1,1),(1,1),"synthetic")
        self.h=HouseholdBasket((40,40),(20,0),"synthetic")
        self.b=BudgetPolicy(100,0,1,(10,10),(10,10),(1,1),"synthetic")
    def run_case(self,s=None,b=None,h=None):
        return budgeted(self.s,s or self.t,self.p,h or self.h,b or self.b)["result"]
    def test_identity(self):
        r=self.run_case(self.s)
        self.assertAlmostEqual(r["budget"]["domestic"],80)
        self.assertAlmostEqual(r["budget"]["direct_import"],20)
        self.assertAlmostEqual(r["sector"]["nominal"]["domestic_final"],200)
    def test_budget(self):
        r=self.run_case()
        self.assertAlmostEqual(sum(r["budget"][k] for k in ("domestic","direct_import","unspent")),100)
        self.assertAlmostEqual(r["domestic_household_volume"][0],40/.9)
        self.assertAlmostEqual(r["domestic_household_volume"][1],40/.95)
    def test_cross_price(self):
        q,_=allocation((50,50),(.5,1),100,(10,10),2)
        self.assertAlmostEqual(q[0],400/3);self.assertAlmostEqual(q[1],100/3)
    def test_complement_fixed_mix(self):
        q,_=allocation((50,50),(.5,1),100,(10,10),0)
        self.assertAlmostEqual(q[0],200/3);self.assertAlmostEqual(q[1],200/3)
    def test_reserve(self):
        r=self.run_case(b=replace(self.b,reserve_share=.2))
        self.assertAlmostEqual(r["budget"]["unspent"],20)
    def test_all_saturated(self):
        r=self.run_case(b=replace(self.b,domestic_cap=(1,1),imported_cap=(1,1)))
        self.assertAlmostEqual(r["budget"]["additional_unspent"],6)
    def test_redistribution_after_cap(self):
        q,sp=allocation((50,50),(.5,1),100,(1,10),2)
        self.assertAlmostEqual(q[0],50);self.assertAlmostEqual(sp[1],75)
    def test_zero_resources(self):
        r=self.run_case(b=replace(self.b,resources=0))
        self.assertEqual(r["domestic_household_volume"],(0,0))
        self.assertEqual(r["other_domestic_final_volume"],(60,60))
    def test_zero_weight(self):
        self.assertEqual(self.run_case()["imported_household_volume"][1],0)
    def test_import_price(self):
        r=self.run_case(b=replace(self.b,final_import_price=(2,1),elasticity=2))
        self.assertLess(r["budget"]["direct_import"],20)
    def test_coverage(self):
        with self.assertRaisesRegex(ValueError,"HOUSEHOLD_COVERAGE"):self.run_case(h=replace(self.h,domestic=(110,40)))
    def test_invalid_budget(self):
        with self.assertRaisesRegex(ValueError,"RESOURCES"):self.run_case(b=replace(self.b,resources=-1))
    def test_invalid_sigma(self):
        with self.assertRaisesRegex(ValueError,"SUBSTITUTION_ELASTICITY"):self.run_case(b=replace(self.b,elasticity=-1))
    def test_extended_identity(self):
        a=self.run_case()["extended_nominal_scope"]
        self.assertAlmostEqual(a["domestic_final_plus_household_direct_imports"],a["intermediate_plus_household_direct_imports"]+a["gross_value_added"]+a["valuation_bridge"])
    def test_null_and_replay(self):
        r=self.run_case();self.assertIsNone(r["actual_disposable_income"]);self.assertIsNone(r["actual_savings"]);self.assertEqual(r,self.run_case())
