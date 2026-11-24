import unittest
from dataclasses import replace
from pipeline.economic_physical_pilot import make,variants,audit,TASK_PREFIX
from pipeline.economic_transform import evaluate,compare_design
from pipeline.economic_contributions import Submission,Input,intake
from pipeline.economic_operations import process_pin

class Fake:
    manifest={"task_statements":{"url":"fixture","sha256":"a"*64}}
    def profile(self,code):return {"tasks":[{"task":{"label":TASK_PREFIX,"source":"task_statements","source_row":2,"id":"fixture:physical-task"}}]}

class PhysicalTests(unittest.TestCase):
    def setUp(self):
        self.p,self.t=make(Fake());self.b,self.alts=variants(self.p)
    def test_physical_anchor(self):
        self.assertEqual(self.p.steps[0].action.modality.value,"PHYSICAL");self.assertEqual(len(self.p.steps),6)
    def test_same_engine(self):
        r=audit(self.p,self.t);self.assertEqual(len(r["alternatives"]),5)
    def test_robot_human_zero(self):
        r=evaluate(self.p,*self.alts[1])["result"];self.assertEqual(r["event_receipt"]["result"]["human_service_seconds"],0)
    def test_instrument_constraint(self):
        a=evaluate(self.p,*self.alts[1])["result"]["event_receipt"]["result"];b=evaluate(self.p,*self.alts[2])["result"]["event_receipt"]["result"]
        self.assertGreater(b["completed_cases"],a["completed_cases"])
    def test_critical_veto(self):
        p,s,d=self.alts[-1];r=compare_design(self.p,self.b[1],self.b[2],p,s,d)["result"];self.assertFalse(r["quality_comparable"]);self.assertIsNone(r["delta"])
    def sub(self):
        return Submission("contrib:sample",1,process_pin(self.p),"alias","contrôle industriel","FR","2026-01-01","2026-01-31","atelier fictif","INTERNAL_REVIEW_ONLY",True,True,"exemple", (Input("1","measure","DESCRIPTION","Mesure après positionnement"),Input("2","measure","MEASUREMENT","Cycle moyen","s","300",12,"chronométrage","b"*64)))
    def test_contribution_pending(self):
        r=intake(self.p,self.sub());self.assertEqual(r["status"],"PENDING_INDEPENDENT_REVIEW");self.assertFalse(r["measurement_qualified"]);self.assertFalse(r["automatic_graph_promotion"])
    def test_no_consent(self):
        with self.assertRaisesRegex(ValueError,"CONSENT_RIGHTS"):intake(self.p,replace(self.sub(),consent_internal=False))
    def test_no_measurement_evidence(self):
        s=self.sub()
        with self.assertRaisesRegex(ValueError,"MEASUREMENT_METADATA"):intake(self.p,replace(s,entries=(replace(s.entries[1],evidence_sha256=None),)))
    def test_unknown_step(self):
        s=self.sub()
        with self.assertRaisesRegex(ValueError,"ENTRY"):intake(self.p,replace(s,entries=(replace(s.entries[0],step_id="unknown"),)))
