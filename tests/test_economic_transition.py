import unittest
from dataclasses import replace
from fractions import Fraction as F
from pipeline.economic_transition import *
from pipeline.economic_transition_pilot import fixture,audit
from pipeline.economic_physical_pilot import make,TASK_PREFIX
class Fake:
    manifest={"task_statements":{"url":"fixture","sha256":"a"*64}}
    def profile(self,code):return {"tasks":[{"task":{"label":TASK_PREFIX,"source":"task_statements","source_row":2,"id":"fixture:physical"}}]}
class TransitionTests(unittest.TestCase):
    def setUp(self):self.p,_=make(Fake());self.ref,self.phases,self.b,self.alts=fixture(self.p)
    def sim(self,p):return simulate(self.p,self.ref,self.phases,p)["result"]
    def mod(self,p,i,**kw):return replace(p,quarters=tuple(replace(q,**kw) if q.index==i else q for q in p.quarters))
    def test_anticipation(self):
        a=self.sim(self.alts[0]);self.assertEqual(a["quarters"][1]["phase"],"reference");self.assertEqual(a["quarters"][1]["frozen_hires"],1)
    def test_attrition(self):
        a=self.sim(self.alts[0]);self.assertEqual(a["ending_headcount"],0);self.assertEqual(a["cumulative_layoffs"],0);self.assertEqual(a["cumulative_frozen_hires"],2)
    def test_retention(self):
        a=self.sim(self.alts[1]);self.assertEqual(a["ending_headcount"],1);self.assertGreater(a["quarters"][-1]["redeployed_seconds"],0);self.assertGreater(F(a["quarters"][-1]["payroll_eur"]),0)
    def test_stock(self):
        a=self.sim(self.b)
        for q in a["quarters"]:self.assertEqual(q["headcount"],q["opening_headcount"]+q["hires"]-q["quits"]-q["layoffs"]-q["other_exits"])
    def test_receivable(self):
        q=self.sim(self.b)["quarters"];self.assertEqual(F(q[0]["collections_eur"]),F(q[0]["revenue_eur"])/2);self.assertEqual(F(q[1]["collections_eur"]),F(q[0]["receivables_eur"])+F(q[1]["revenue_eur"])/2)
    def test_debt(self):self.assertEqual(self.sim(self.alts[0])["closing_debt_eur"],"15000")
    def test_shortfall(self):self.assertGreater(F(self.sim(self.alts[2])["funding_gap_at_sampled_dates_eur"]),0)
    def test_insufficient_staff(self):
        with self.assertRaisesRegex(ValueError,"PAID_CAPACITY"):self.sim(self.mod(self.b,1,quit_j=1,quit_s=1))
    def test_overhire(self):
        with self.assertRaisesRegex(ValueError,"HIRING_BUDGET"):self.sim(self.mod(self.alts[0],2,hire_j=1))
    def test_invalid_exit(self):
        with self.assertRaisesRegex(ValueError,"STOCK_FLOW"):self.sim(self.mod(self.b,1,quit_j=2))
    def test_debt_overpayment(self):
        with self.assertRaisesRegex(ValueError,"DEBT_OVERPAYMENT"):self.sim(self.mod(self.b,1,principal_repaid_cents=100))
    def test_invalid_milestone(self):
        with self.assertRaisesRegex(ValueError,"MILESTONES"):self.sim(replace(self.alts[0],production_quarter=1))
    def test_promotion_training(self):
        with self.assertRaisesRegex(ValueError,"PROMOTION_TRAINING"):self.sim(self.mod(self.b,4,training_seconds=0))
    def test_comparison(self):
        r=compare(self.p,self.ref,self.phases,self.b,self.alts[0])["result"];self.assertEqual(r["headcount_gap"],-2);self.assertEqual(r["hires_gap"],-2);self.assertEqual(r["layoffs_gap"],0)
    def test_replay(self):self.assertEqual(self.sim(self.alts[0]),self.sim(self.alts[0]))
    def test_audit(self):self.assertEqual(len(audit(self.p)["comparisons"]),3)
