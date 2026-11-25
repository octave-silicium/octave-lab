import unittest
from dataclasses import replace
from fractions import Fraction as F
from pipeline.economic_market import trajectory,run
from pipeline.economic_market_dynamics_pilot import plans,audit
from pipeline.economic_physical_pilot import make,TASK_PREFIX
from pipeline.economic_investigation import Investigation,MarketTrajectory,assemble,verify_replay
from pipeline.economic_core import Graph,Coverage,canonical,digest
from pipeline.economic_prospective import model_pins
from test_economic_prospective import fixture

class Fake:
    manifest={"task_statements":{"url":"fixture","sha256":"a"*64}}
    def profile(self,code):return {"tasks":[{"task":{"label":TASK_PREFIX,"source":"task_statements","source_row":2,"id":"fixture:physical"}}]}

class DynamicsTests(unittest.TestCase):
    def setUp(self):self.p,_=make(Fake());self.ds=plans(self.p)
    def r(self,i):return trajectory(self.ds[i])["result"]
    def test_no_shock(self):
        r=self.r(0);self.assertEqual(list(r["adoption_quarters"].values()),[None,None,None]);self.assertTrue(all(q["sales"]==4500 for q in r["quarters"]))
    def test_adoption(self):self.assertEqual(self.r(1)["adoption_quarters"]["A"],1)
    def test_credit_constraint(self):
        r=self.r(1);self.assertTrue(any(x["seller"]=="B" and x["reason"]=="CREDIT_CONSTRAINT" for x in r["decisions"]))
    def test_funded(self):self.assertIsNotNone(self.r(2)["adoption_quarters"]["B"])
    def test_cessation(self):
        r=self.r(1);q=r["cessation_quarters"]["B"];self.assertIsNotNone(q)
        if q<len(r["quarters"]):self.assertIn("B",r["quarters"][q]["market"]["result"]["unavailable_sellers"])
    def test_unavailable(self):
        r=run(self.ds[0].market,("B",))["result"];self.assertEqual(r["sellers"][1]["sales"],0);self.assertIsNone(r["sellers"][1]["price_eur"]);self.assertIsNone(r["fixed_basket_price_index"]);self.assertIsNotNone(r["matched_available_basket_index"])
    def test_all_unavailable(self):
        r=run(self.ds[0].market,("A","B","C"))["result"];self.assertEqual(r["sales"],0);self.assertEqual(r["unserved"],36);self.assertIsNone(r["matched_available_basket_index"])
    def test_conservation(self):
        for q in self.r(1)["quarters"]:
            r=q["market"]["result"];self.assertEqual(r["potential_demand"],r["sales"]+r["unserved"]+r["internalized_units"]);self.assertEqual(sum(x["sales"] for x in q["seller_finances"]),q["sales"])
    def test_no_future_sales(self):
        r=self.r(1)
        for k,n in r["cessation_quarters"].items():
            if n:
                for q in r["quarters"][n:]:self.assertEqual(next(x for x in q["seller_finances"] if x["seller"]==k)["sales"],0)
    def test_bad_strategy(self):
        d=self.ds[1]
        with self.assertRaisesRegex(ValueError,"STRATEGY"):trajectory(replace(d,strategies=(replace(d.strategies[0],credit_limit_cents=-1),*d.strategies[1:])))
    def test_replay(self):self.assertEqual(self.r(1),self.r(1))
    def test_investigation(self):
        g,ss,paths,inter,fs=fixture();s=replace(self.ds[0].market.sellers[0].reference[1].scope,period_end="2027-12-31")
        g=Graph(g.requirements,entities=tuple(g.entities.values()),evidence=tuple(g.evidence.values()),parameters=tuple(replace(p,scope=s) for p in g.parameters.values()),claims=tuple(replace(c,scope=s) for c in g.claims.values()),assertions=tuple(g.assertions.values()))
        ss=tuple(replace(t,scope=s,step_unit="quarter",horizons=("8 quarters",)) for t in ss);args=(ss,paths,inter,fs)
        rows=tuple(Coverage(k,i,"PENDING_QUALIFICATION","fixture only") for k,ids in g.requirements.groups.items() for i in sorted(ids))
        inv=Investigation("market:inv",1,"Question","decision",("baseline","alternative"),"loss","synthetic",g.fingerprint,digest(canonical(model_pins())))
        item=MarketTrajectory(ss[2].key,self.ds[1]);r=assemble(inv,g,rows,prospective=args,market_trajectories=(item,))
        self.assertEqual(r["manifest"]["market_trajectories"][0]["status"],"CONDITIONAL_NOT_PROPAGATED")
        self.assertTrue(verify_replay(r,inv,g,rows,prospective=args,market_trajectories=(item,)))
    def test_audit(self):self.assertEqual(len(audit(self.p)["cases"]),3)
