import unittest
from dataclasses import replace
from fractions import Fraction as F
from pipeline.economic_skills import *
from pipeline.economic_skills_pilot import fixture,audit
from pipeline.economic_physical_pilot import make,TASK_PREFIX
class Fake:
    manifest={"task_statements":{"url":"fixture","sha256":"a"*64}}
    def profile(self,code):return {"tasks":[{"task":{"label":TASK_PREFIX,"source":"task_statements","source_row":2,"id":"fixture:physical"}]}
class SkillsTests(unittest.TestCase):
    def setUp(self):self.p,_=make(Fake());self.ref,self.phases,self.b,self.alts=fixture(self.p)
    def ev(self,x):return evaluate(self.p,self.ref,self.phases,*x)["result"]
    def mod(self,s,i,**kw):return replace(s,quarters=tuple(replace(q,**kw) if q.index==i else q for q in s.quarters))
    def test_freeze(self):
        r=self.ev(self.b);self.assertEqual(r["ending_experts"],0);self.assertEqual(r["total_expert_shortfall_hours"],"550")
    def test_renew(self):
        r=self.ev(self.alts[0]);self.assertEqual(r["ending_experts"],1);self.assertEqual(r["total_promotions"],1);self.assertEqual(r["skill_rows"][4]["promoted"],1)
    def test_fast(self):
        r=self.ev(self.alts[1]);self.assertEqual(r["skill_rows"][3]["promoted"],1);self.assertEqual(r["total_expert_shortfall_hours"],"0")
    def test_early(self):
        p,s=self.alts[0]
        with self.assertRaisesRegex(ValueError,"PREMATURE_QUALIFICATION"):self.ev((p,self.mod(s,3,assessments_passed=("new",))))
    def test_mentor(self):
        p,s=self.alts[0];l=replace(s.quarters[1].learning[0],mentor_seconds=0)
        with self.assertRaisesRegex(ValueError,"MENTOR_REQUIREMENT"):self.ev((p,self.mod(s,2,learning=(l,))))
    def test_capacity(self):
        p,s=self.alts[0]
        with self.assertRaisesRegex(ValueError,"PERSON_TIME_CAPACITY"):self.ev((p,self.mod(s,2,production=(("j",900000),("s",900000)))))
    def test_production_reconcile(self):
        p,s=self.alts[0]
        with self.assertRaisesRegex(ValueError,"TRANSITION_SKILL_RECONCILIATION"):self.ev((p,self.mod(s,1,production=())))
    def test_duplicate_hire(self):
        p,s=self.alts[0]
        with self.assertRaisesRegex(ValueError,"SKILL_HIRE"):self.ev((p,self.mod(s,2,hires=(("j","JUNIOR"),))))
    def test_finance_zero_rate(self):
        x=self.ev(self.b);v=valuation(x,0)
        self.assertEqual(F(v["npv_eur"]),sum(F(q["start_eur"])+F(q["end_eur"]) for q in v["flows"])+F(v["terminal_eur"]))
    def test_finance_debt_excluded(self):
        p,s=self.b;q=tuple(replace(x,debt_draw_cents=0,principal_repaid_cents=0) for x in p.quarters)
        self.assertEqual(valuation(self.ev(self.b),200),valuation(self.ev((replace(p,quarters=q),s)),200))
    def test_terminal(self):
        x=self.ev(self.b);a=valuation(x,0);b=valuation(x,0,settle_trade=False)
        self.assertEqual(F(a["npv_eur"])-F(b["npv_eur"]),F(a["terminal_eur"]))
    def test_threshold(self):
        r=compare_skills(self.p,self.ref,self.phases,*self.b,*self.alts[0])["result"];self.assertGreater(F(r["incremental_discounted_expert_hours"]),0);self.assertGreater(F(r["expert_hour_break_even_eur"]),0)
    def test_replay(self):
        self.assertEqual(self.ev(self.alts[1]),self.ev(self.alts[1]))
    def test_audit(self):self.assertEqual(len(audit(self.p)["sensitivity"]),6)
