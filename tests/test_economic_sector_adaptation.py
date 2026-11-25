import unittest
from dataclasses import replace
from pipeline.economic_sector_structural import Structure
from pipeline.economic_sector_capacity_dynamics import Period
from pipeline.economic_sector_adaptation import CapacityRule,SubstitutionRule,adapt

class AdaptationTests(unittest.TestCase):
    def setUp(self):
        self.s=Structure(("A","B"),((0,.5),(0,0)),((0,0),(0,.2)),((1,0),(0,1)),(.5,.1),(0,0),(0,0),(.5,.2),(100,100),"SYNTHETIC")
        self.p=Period(self.s,(0,20),(("A","B"),),"synthetic")
        self.r=CapacityRule("A",1,2,.01,.6,30,60,200,"DEMAND_CONFIRMED","synthetic")
        self.sub=SubstitutionRule("B","A","B",1,1,.1,.2,"synthetic equivalence")
    def run_path(self,ps=None,cap=(120,100),stock=(0,0),rules=(),subs=()):
        return adapt(ps or (self.p,)*5,cap,stock,rules,subs,period_unit="QUARTER",evidence="synthetic")["result"]
    def test_lag_expansion(self):
        r=self.run_path(rules=(self.r,));p=r["dynamic"]["periods"]
        self.assertEqual([x["capacity"][0] for x in p],[120,120,150,150,150])
        self.assertAlmostEqual(sum(p[2]["served_final"]),200)
    def test_no_duplicate_pending(self):
        r=self.run_path(rules=(self.r,))
        self.assertEqual(sum(x["reason"]=="EXPAND" for x in r["decisions"]),1)
        self.assertEqual(r["decisions"][1]["reason"],"PENDING")
    def test_persistence(self):
        r=self.run_path(rules=(replace(self.r,persistence=2),))
        self.assertEqual(r["decisions"][0]["reason"],"NO_TRIGGER")
        self.assertEqual(r["decisions"][1]["reason"],"EXPAND")
    def test_nonbinding_expansion(self):
        p=replace(self.p,deliveries=(0,10))
        r=self.run_path((p,)*4,cap=(150,100),rules=(self.r,))
        self.assertFalse(any(x["reason"]=="EXPAND" for x in r["decisions"]))
    def test_naive_retirement(self):
        p=replace(self.p,deliveries=(0,10))
        r=self.run_path((p,)*4,cap=(150,100),rules=(replace(self.r,retirement_signal="UTILIZATION_ONLY"),))
        self.assertEqual(r["decisions"][0]["reason"],"RETIRE")
        self.assertEqual(r["dynamic"]["periods"][2]["capacity"][0],120)
    def test_confirmed_not_retired_on_import_shortage(self):
        p=replace(self.p,deliveries=(0,10))
        r=self.run_path((p,)*4,cap=(150,100),rules=(self.r,))
        self.assertFalse(any(x["reason"]=="RETIRE" for x in r["decisions"]))
    def test_demand_contraction_retirement(self):
        p=replace(self.p,structure=replace(self.s,final=(30,30)))
        r=self.run_path((p,)*4,cap=(150,100),rules=(self.r,))
        self.assertEqual(r["decisions"][0]["reason"],"RETIRE")
    def test_substitution_lag(self):
        p=replace(self.p,deliveries=(0,10))
        r=self.run_path((p,)*4,cap=(200,100),subs=(self.sub,))
        self.assertEqual(r["substitution_orders"][0]["effective"],2)
        self.assertAlmostEqual(sum(r["dynamic"]["periods"][0]["served_final"]),100)
        self.assertAlmostEqual(sum(r["dynamic"]["periods"][1]["served_final"]),200)
    def test_substitution_limit(self):
        p=replace(self.p,deliveries=(0,0))
        r=self.run_path((p,)*5,cap=(200,100),subs=(self.sub,))
        self.assertAlmostEqual(sum(o["shift"] for o in r["substitution_orders"]),.2)
        self.assertAlmostEqual(sum(r["dynamic"]["periods"][2]["served_final"]),200)
    def test_new_bottleneck(self):
        p=replace(self.p,deliveries=(0,10))
        r=self.run_path((p,)*4,cap=(150,100),subs=(self.sub,))
        self.assertAlmostEqual(sum(r["dynamic"]["periods"][1]["served_final"]),187.5)
        self.assertEqual(r["dynamic"]["periods"][1]["tiers"][0]["binding"][0]["code"],"A")
    def test_no_lookahead(self):
        a=self.run_path(rules=(self.r,));p=replace(self.p,structure=replace(self.s,final=(1,1)))
        b=self.run_path((self.p,self.p,p,p,p),rules=(self.r,))
        self.assertEqual(a["decisions"][:2],b["decisions"][:2])
    def test_stock_and_replay(self):
        a=self.run_path(rules=(self.r,));b=self.run_path(rules=(self.r,))
        self.assertEqual(a,b)
        for row in a["dynamic"]["periods"]:self.assertAlmostEqual(row["flow_stock_residual"],0)
    def test_duplicate_rules(self):
        with self.assertRaisesRegex(ValueError,"DUPLICATE_CAPACITY_RULE"):self.run_path(rules=(self.r,self.r))
    def test_invalid_lag(self):
        with self.assertRaisesRegex(ValueError,"CAPACITY_RULE"):self.run_path(rules=(replace(self.r,lag=0),))
    def test_bounds(self):
        r=self.run_path(rules=(replace(self.r,ceiling=130),))
        self.assertEqual(r["dynamic"]["periods"][2]["capacity"][0],130)
    def test_insufficient_future_input(self):
        p=replace(self.p,deliveries=(0,10))
        s=replace(self.s,imported=((0,0),(0,.05)),surplus=(.5,.35))
        with self.assertRaisesRegex(ValueError,"SUBSTITUTION_INSUFFICIENT_INPUT"):
            self.run_path((p,replace(p,structure=s)),cap=(200,100),subs=(self.sub,))
