import unittest
from dataclasses import replace
from fractions import Fraction as F
from pipeline.economic_market import run,allocate
from pipeline.economic_market_pilot import cases,audit
from pipeline.economic_physical_pilot import make,TASK_PREFIX
class Fake:
    manifest={"task_statements":{"url":"fixture","sha256":"a"*64}}
    def profile(self,code):return {"tasks":[{"task":{"label":TASK_PREFIX,"source":"task_statements","source_row":2,"id":"fixture:physical"}}]}
class MarketTests(unittest.TestCase):
    def setUp(self):self.p,_=make(Fake());self.ms=cases(self.p)
    def r(self,i):return run(self.ms[i])["result"]
    def test_zero_shock(self):
        r=self.r(0);self.assertEqual(r["sales"],36);self.assertEqual(r["price_induced_demand_change"],0);self.assertEqual(r["cash_surplus_delta_eur"],"0");self.assertEqual([x["sales"] for x in r["sellers"]],[12,12,12])
    def test_capacity_redistribution(self):self.assertEqual(allocate(10,{"a":F(9),"b":F(1)},{"a":2,"b":10}),{"a":2,"b":8})
    def test_capacity_shortage(self):self.assertEqual(allocate(10,{"a":F(1),"b":F(1)},{"a":2,"b":3}),{"a":2,"b":3})
    def test_tie(self):self.assertEqual(allocate(3,{"b":F(1),"a":F(1)},{"a":10,"b":10}),{"a":2,"b":1})
    def test_share_conservation(self):
        for m in self.ms:
            r=run(m)["result"];self.assertEqual(sum(F(x["share_reallocation_component"]) for x in r["sellers"]),0);self.assertEqual(r["sales"]+r["unserved"]+r["internalized_units"],r["potential_demand"])
    def test_no_rebound(self):self.assertEqual(self.r(3)["potential_demand"],36)
    def test_internalized(self):self.assertEqual(self.r(4)["external_demand"],self.r(2)["potential_demand"]-12)
    def test_invalid_internalization(self):
        with self.assertRaisesRegex(ValueError,"INTERNALIZATION_VOLUME"):run(replace(self.ms[0],internalized_units=100))
    def test_price_floor(self):
        m=self.ms[0];p=replace(m.policies[0],price_adjustment_cents=-1200)
        with self.assertRaisesRegex(ValueError,"NONPOSITIVE_PRICE"):run(replace(m,policies=(p,*m.policies[1:])))
    def test_human_preference(self):
        self.assertGreaterEqual(self.r(5)["sellers"][1]["sales"],self.r(1)["sellers"][1]["sales"])
    def test_price_retention(self):self.assertEqual(self.r(6)["fixed_basket_price_index"],"1")
    def test_saturation(self):self.assertLessEqual(self.r(7)["potential_demand"],40)
    def test_no_employment_inference(self):self.assertIsNone(self.r(2)["employment_effect"])
    def test_replay(self):self.assertEqual(run(self.ms[1]),run(self.ms[1]))
    def test_audit(self):self.assertEqual(len(audit(self.p)["cases"]),8)
