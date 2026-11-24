import unittest
from dataclasses import replace
from pipeline.economic_transform import *
from pipeline.economic_transform_pilot import variants,audit
from pipeline.invoice_pilot import make,TASK_PREFIX
class Fake:
    manifest={"task_statements":{"url":"fixture","sha256":"a"*64}}
    def profile(self,code):return {"tasks":[{"task":{"label":TASK_PREFIX,"source":"task_statements","source_row":2,"id":"fixture:task"}}]}
class TransformTests(unittest.TestCase):
    def setUp(self):
        self.p,_=make(Fake());self.b,self.bd,self.alts=variants(self.p)
    def eval(self,i):
        p,s,d=self.alts[i];return evaluate(self.p,p,s,d)["result"]
    def test_fusion(self):
        self.assertEqual(len(self.p.steps),6);self.assertEqual(self.eval(0)["step_count"],4)
    def test_authorization_separate(self):
        r=self.eval(1);self.assertGreater(r["human_authorization_started_cases"],0);self.assertGreater(r["human_verification_started_cases"],0)
    def test_sample(self):
        r=self.eval(2);self.assertEqual(r["human_authorization_started_cases"],0);self.assertGreater(r["human_verification_started_cases"],0)
    def test_autonomy(self):
        r=self.eval(3);self.assertEqual(r["human_touched_cases"],0);self.assertEqual(r["event_receipt"]["result"]["human_service_seconds"],0);self.assertTrue(all(x["accountable_actor"] for x in r["role_map"]))
    def test_critical_veto(self):
        p,s,d=self.alts[4];r=compare_design(self.p,self.b,self.bd,p,s,d)["result"];self.assertFalse(r["quality_comparable"]);self.assertIsNone(r["delta"])
    def test_human_not_perfect(self):
        r=evaluate(self.p,self.p,self.b,self.bd)["result"];self.assertEqual(r["event_receipt"]["result"]["quality_assigned_cohort"],"59/60")
    def test_unknown_legal(self):
        self.assertEqual(self.eval(3)["deployment"],"BLOCK_DEPLOYMENT_UNQUALIFIED")
    def test_missing_change(self):
        p,s,d=self.alts[0]
        with self.assertRaisesRegex(ValueError,"CHANGE_COVERAGE"):evaluate(self.p,p,s,replace(d,changes=d.changes[:-1]))
    def test_missing_role(self):
        p,s,d=self.alts[0]
        with self.assertRaisesRegex(ValueError,"ROLE_COVERAGE"):evaluate(self.p,p,s,replace(d,roles=d.roles[:-1]))
    def test_wrong_role_pool(self):
        p,s,d=self.alts[0];r=replace(d.roles[0],verification=("review",))
        with self.assertRaisesRegex(ValueError,"ROLE_VISITS"):evaluate(self.p,p,s,replace(d,roles=(r,*d.roles[1:])))
    def test_missing_quality(self):
        p,s,d=self.alts[0]
        with self.assertRaisesRegex(ValueError,"QUALITY_COVERAGE"):evaluate(self.p,p,s,replace(d,quality=d.quality[:-1]))
    def test_risk_cohort(self):
        p,s,d=self.alts[0];q=replace(d.quality[0],criticality="STANDARD")
        with self.assertRaisesRegex(ValueError,"RISK_COHORT"):compare_design(self.p,self.b,self.bd,p,s,replace(d,quality=(q,*d.quality[1:])))
    def test_audit(self):self.assertEqual(len(audit(self.p)["alternatives"]),5)
