import unittest
from fractions import Fraction as F
from dataclasses import replace
from pipeline.economic_market import run,trajectory,InternalProduction
from pipeline.economic_market_boundary_pilot import audit
from pipeline.economic_market_dynamics_pilot import plans
from pipeline.economic_market_pilot import cases
from pipeline.economic_physical_pilot import make,TASK_PREFIX

class Fake:
    manifest={"task_statements":{"url":"fixture","sha256":"a"*64}}
    def profile(self,code):return {"tasks":[{"task":{"label":TASK_PREFIX,"source":"task_statements","source_row":2,"id":"fixture:physical"}}]}

class BoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p,_=make(Fake());cls.a=audit(cls.p);cls.ms=cases(cls.p)
    def r(self,k):return self.a["cases"][k]["result"]
    def test_post_exit(self):
        r=self.a["extended_trajectory"]["result"];self.assertEqual(r["cessation_quarters"]["B"],8)
        for q in r["quarters"][8:]:
            self.assertIn("B",q["market"]["result"]["unavailable_sellers"])
            b=next(s for s in q["seller_finances"] if s["seller"]=="B")
            self.assertEqual(b["sales"],0);self.assertEqual(b["status"],"CEASED_SUPPLY")
            self.assertIn("debt",b["unresolved_at_cessation"])
    def test_entry(self):
        r=self.r("entry");d=next(s for s in r["sellers"] if s["seller"]=="D")
        self.assertEqual(d["baseline_sales"],0);self.assertGreater(d["sales"],0);self.assertEqual(d["baseline_paid_seconds"],0)
        self.assertEqual(r["baseline_sales"],36)
    def test_ownership(self):
        a=self.r("entry");b=self.r("control_consolidation")
        self.assertEqual(a["sales"],b["sales"]);self.assertEqual(a["volume_hhi"],b["volume_hhi"])
        self.assertGreater(F(b["control_group_volume_hhi"]),F(a["control_group_volume_hhi"]))
    def test_bad_ownership(self):
        with self.assertRaisesRegex(ValueError,"OWNERSHIP_COVERAGE"):run(replace(self.ms[0],ownership=(("A","group"),)))
    def test_internal(self):
        for k in ("internal_manual","internal_automated"):
            r=self.r(k);i=r["internal_production"]
            self.assertEqual(i["fulfilled_units"],12)
            self.assertEqual(r["potential_demand"],r["sales"]+i["fulfilled_units"]+r["unserved"])
            self.assertEqual(F(r["direct_chain_cash_cost_eur"]),sum(F(s["payroll_eur"])+F(s["nonpayroll_eur"]) for s in r["sellers"])+F(i["cash_cost_eur"]))
            self.assertEqual(F(r["buyer_direct_cash_outlay_eur"]),F(r["market_revenue_eur"])+F(i["cash_cost_eur"]))
    def test_internal_hours(self):
        a=self.r("internal_manual");b=self.r("internal_automated")
        self.assertEqual(a["sales"],b["sales"]);self.assertGreater(F(a["direct_chain_paid_hours"]),F(b["direct_chain_paid_hours"]))
    def test_unknown_not_zero(self):
        a=self.r("internal_unqualified");self.assertIsNone(a["direct_chain_cash_cost_eur"]);self.assertIsNone(a["direct_chain_paid_hours"])
    def test_internal_zero(self):
        m=self.ms[0];i=InternalProduction("A",m.sellers[0].reference,"fixture")
        with self.assertRaisesRegex(ValueError,"INTERNAL_CONTRACT"):run(replace(m,internal_production=i))
    def test_internal_capacity(self):
        m=self.ms[2];i=InternalProduction("A",m.sellers[0].reference,"fixture")
        with self.assertRaisesRegex(ValueError,"INTERNAL_CAPACITY"):run(replace(m,internalized_units=24,internal_production=i))
    def test_no_markup_or_rent(self):
        for k,v in self.a["cases"].items():
            for r in v["result"]["sellers"]:
                self.assertIsNone(r["marginal_cost_markup"]);self.assertIsNone(r["economic_rent"])
    def test_replay(self):self.assertEqual(self.a,audit(self.p))
