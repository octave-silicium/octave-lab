import unittest
from dataclasses import replace
from pipeline.economic_sector_structural import Structure
from pipeline.economic_sector_capital import Asset,Vintage,Investment,Period,path

class CapitalTests(unittest.TestCase):
    def setUp(self):
        self.s=Structure(("A","B"),((0,0),(0,0)),((0,0),(0,0)),((1,0),(0,1)),(.5,.5),(0,0),(0,0),(.5,.5),(100,80),"SYNTHETIC")
        self.a=Asset("machine","A","B",2,10,0,0,10,"synthetic")
        self.v=Vintage("machine",10,0,20)
        self.p=Period(self.s,(None,None),(("A","B"),),(1,),"synthetic")
        self.i=Investment("order","machine",1,5,2,"synthetic")
    def run_case(self,ps=None,a=None,v=None,orders=(),noncap=(0,100)):
        return path(ps or (self.p,)*4,(a or self.a,),v if v is not None else (self.v,),orders,noncapital_capacity=noncap,period_unit="YEAR",evidence="synthetic")["result"]
    def test_reference(self):
        r=self.run_case()
        for p in r["periods"]:
            self.assertEqual(p["capacity"],[100,100])
            self.assertAlmostEqual(sum(p["other_final_served"]),180)
            self.assertAlmostEqual(p["closing_active_value"],20)
    def test_lag(self):
        r=self.run_case(orders=(self.i,));p=r["periods"]
        self.assertEqual([x["capacity"][0] for x in p],[100,100,150,150])
        self.assertEqual([x["closing_wip_value"] for x in p],[10,10,0,0])
        self.assertAlmostEqual(p[2]["closing_active_value"],30)
    def test_investment_rationing(self):
        r=self.run_case(orders=(self.i,),noncap=(0,45));p=r["periods"][0]
        self.assertAlmostEqual(p["investment_acquired"],5)
        self.assertAlmostEqual(p["investment_orders"][0]["acquired_units"],2.5)
        self.assertAlmostEqual(sum(p["other_final_served"])+p["investment_acquired"],sum(p["allocation"]["served_final"]))
        self.assertAlmostEqual(r["periods"][2]["capacity"][0],125)
    def test_no_self_creation(self):
        a=replace(self.a,product="A")
        r=self.run_case(a=a,v=(),orders=(self.i,),noncap=(0,100))
        self.assertTrue(all(p["capacity"][0]==0 for p in r["periods"]))
        self.assertEqual(r["periods"][0]["investment_acquired"],0)
    def test_priority(self):
        p=replace(self.p,tiers=(("A",),("B",)))
        r=self.run_case((p,),orders=(self.i,),noncap=(0,45))
        self.assertAlmostEqual(r["periods"][0]["other_final_served"][0],100)
        self.assertAlmostEqual(r["periods"][0]["investment_acquired"],5)
    def test_efficiency_decay_not_book(self):
        r=self.run_case(a=replace(self.a,efficiency_decay=.1))
        self.assertAlmostEqual(r["periods"][1]["capacity"][0],90)
        self.assertEqual(r["periods"][1]["closing_active_value"],20)
    def test_book_decay_not_efficiency(self):
        r=self.run_case(a=replace(self.a,book_decay=.1))
        self.assertEqual(r["periods"][1]["capacity"][0],100)
        self.assertAlmostEqual(r["periods"][1]["closing_active_value"],16.2)
    def test_retirement_writeoff(self):
        r=self.run_case(a=replace(self.a,life=2,book_decay=.1))
        self.assertAlmostEqual(r["periods"][1]["retirement_writeoff"],16.2)
        self.assertEqual(r["periods"][2]["capacity"][0],0)
        self.assertEqual(r["periods"][1]["retired_units_by_asset"]["machine"],10)
    def test_zero_book_live_asset(self):
        r=self.run_case(v=(replace(self.v,carrying_value=0),))
        self.assertEqual(r["periods"][0]["capacity"][0],100)
    def test_exogenous_obsolescence(self):
        p=replace(self.p,efficiency_factor=(.5,))
        r=self.run_case((p,self.p))
        self.assertEqual([x["capacity"][0] for x in r["periods"]],[50,100])
    def test_pending_end(self):
        r=self.run_case((self.p,),orders=(self.i,))
        self.assertEqual(r["pending"][0]["due"],3)
        self.assertEqual(r["periods"][0]["closing_wip_value"],10)
    def test_no_instant_commission(self):
        with self.assertRaisesRegex(ValueError,"INVESTMENT"):self.run_case(orders=(replace(self.i,lag=0),))
    def test_duplicate_order(self):
        with self.assertRaisesRegex(ValueError,"DUPLICATE_INVESTMENT"):self.run_case(orders=(self.i,self.i))
    def test_invalid_age(self):
        with self.assertRaisesRegex(ValueError,"VINTAGE"):self.run_case(v=(replace(self.v,age=10),))
    def test_replay_and_null_claims(self):
        a=self.run_case(orders=(self.i,));self.assertEqual(a,self.run_case(orders=(self.i,)))
        self.assertIsNone(a["actual_ccf"]);self.assertIsNone(a["financing"])
    def test_no_empirical_admission(self):
        p=replace(self.p,structure=replace(self.s,origin="PINNED_2022_CONDITIONAL"))
        with self.assertRaisesRegex(ValueError,"SYNTHETIC_ONLY"):self.run_case((p,))
