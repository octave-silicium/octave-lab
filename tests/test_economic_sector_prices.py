import unittest
from dataclasses import replace
from pipeline.economic_sector_structural import Structure
from pipeline.economic_sector_prices import PricePolicy,DemandPolicy,price

class PricesTests(unittest.TestCase):
    def setUp(self):
        self.s=Structure(("A","B"),((0,.5),(0,0)),((0,0),(0,.2)),((1,0),(0,1)),(.5,.1),(0,0),(0,0),(.5,.2),(100,100),"SYNTHETIC")
        self.t=replace(self.s,wage=(.4,.1),surplus=(.6,.2))
        self.p=PricePolicy((1,1),(1,1),(1,1),(1,1),(1,1),"synthetic")
    def run_case(self,t=None,p=None,d=None):
        return price(self.s,t or self.t,p or self.p,d)["result"]
    def test_identity(self):
        r=self.run_case(self.s);self.assertTrue(all(abs(v-1)<1e-13 for v in r["branch_price"]));self.assertAlmostEqual(r["nominal"]["gross_value_added"],180)
    def test_full_pass_through(self):
        r=self.run_case();self.assertAlmostEqual(r["branch_price"][0],.9);self.assertAlmostEqual(r["branch_price"][1],.95)
        self.assertAlmostEqual(r["unit_surplus_change"][0],0)
    def test_retention(self):
        r=self.run_case(p=replace(self.p,pass_through=(0,0)))
        self.assertEqual(r["branch_price"],(1,1));self.assertAlmostEqual(r["unit_gross_surplus"][0],.6)
    def test_partial(self):
        r=self.run_case(p=replace(self.p,pass_through=(.5,.5)))
        self.assertAlmostEqual(r["branch_price"][0],.95);self.assertAlmostEqual(r["branch_price"][1],.9875)
        self.assertAlmostEqual(r["unit_gross_surplus"][0],.55)
    def test_import_inflation(self):
        r=self.run_case(self.s,replace(self.p,import_price=(1,1.5)))
        self.assertAlmostEqual(r["branch_price"][1],1.1);self.assertAlmostEqual(r["nominal"]["intermediate_imports"],30)
    def test_elasticity_one(self):
        r=self.run_case(d=DemandPolicy((1,1),(1,1),(10,10),"synthetic"))
        self.assertAlmostEqual(r["nominal"]["domestic_final"],200)
        self.assertGreater(r["reference_price_volume"]["domestic_final"],200)
    def test_saturation(self):
        r=self.run_case(d=DemandPolicy((5,5),(1,1),(1.02,1.02),"synthetic"))
        self.assertAlmostEqual(r["reference_price_volume"]["domestic_final"],204)
    def test_nonresponsive(self):
        r=self.run_case(d=DemandPolicy((5,5),(0,0),(10,10),"synthetic"))
        self.assertEqual(r["final_volume_equivalent"],(100,100))
    def test_nominal_balance(self):
        r=self.run_case();a=r["nominal"]
        self.assertAlmostEqual(a["domestic_final"],a["gross_value_added"]+a["intermediate_imports"]+a["valuation_bridge"])
    def test_price_volume(self):
        r=self.run_case(d=DemandPolicy((2,2),(1,1),(10,10),"synthetic"));a=r["final_value_decomposition"]
        self.assertAlmostEqual(a["volume"]+a["price_at_scenario_volume"],a["nominal_change"])
    def test_invalid_policy(self):
        with self.assertRaisesRegex(ValueError,"PASS_THROUGH"):self.run_case(p=replace(self.p,pass_through=(2,1)))
    def test_nonpositive(self):
        s=replace(self.s,wage=(0,.1),surplus=(1,.2))
        # Branch A base cost is only 0.5; zero price needs a different reference with zero surplus.
        b=replace(self.s,wage=(1,.1),surplus=(0,.2))
        with self.assertRaisesRegex(ValueError,"NONPOSITIVE_PRICE"):price(b,s,self.p)
    def test_mixed_product(self):
        s=replace(self.s,shares=((.8,.1),(.2,.9)))
        t=replace(s,wage=(.4,.1),surplus=(.6,.2))
        r=price(s,t,self.p)["result"];self.assertAlmostEqual(r["product_price"][0],.8*r["branch_price"][0]+.2*r["branch_price"][1])
    def test_replay(self):
        self.assertEqual(self.run_case(),self.run_case())
    def test_null_claims(self):
        r=self.run_case();self.assertIsNone(r["gdp"]);self.assertIsNone(r["employment"]);self.assertIsNone(r["cpi"])
