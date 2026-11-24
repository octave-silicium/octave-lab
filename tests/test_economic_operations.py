import unittest
from dataclasses import replace
from fractions import Fraction
from pipeline.economic_operations import *
from pipeline.economic_operations_pilot import fixture,audit
from pipeline.invoice_pilot import make,CODE,TASK_PREFIX

class FakeONet:
    manifest={"task_statements":{"url":"fixture","sha256":"a"*64}}
    def profile(self,code):
        return {"tasks":[{"task":{"label":TASK_PREFIX,"source":"task_statements","source_row":2,"id":"fixture:task"}}]}

class OperationTests(unittest.TestCase):
    def setUp(self):
        self.process,_=make(FakeONet());self.g,self.plans=fixture(self.process)
        self.base,self.ai,self.stress,self.redesign,self.bh,self.ah=self.plans
    def runplan(self,p):return run(self.g,self.process,p)
    def test_shared_resource_bottleneck(self):
        a=self.runplan(self.base);b=self.runplan(self.ai)
        self.assertEqual(a["binding_resources"],["clerk"])
        self.assertEqual(b["binding_resources"],["review"])
        self.assertEqual(Fraction(a["capacity_upper_bound_cases"]),Fraction(2000,3))
        self.assertEqual(Fraction(b["capacity_upper_bound_cases"]),Fraction(18000,23))
    def test_demand_bound_and_redesign(self):
        a=self.runplan(self.redesign);self.assertEqual(a["processed_cases_envelope"],"1000")
        self.assertTrue(a["demand_binding"])
    def test_high_demand(self):
        a=self.runplan(self.ai);b=self.runplan(self.ah)
        self.assertEqual(a["capacity_upper_bound_cases"],b["capacity_upper_bound_cases"])
        self.assertGreater(Fraction(b["unserved_demand_cases"]),Fraction(a["unserved_demand_cases"]))
    def test_quality_blocks_delta(self):
        r=compare(self.g,self.process,self.base,self.process,self.stress)["result"]
        self.assertFalse(r["quality_comparable"]);self.assertIsNone(r["delta"])
    def test_conservation(self):
        for p in self.plans:
            r=self.runplan(p)
            self.assertEqual(Fraction(r["correct_dispositions_envelope"])+Fraction(r["incorrect_dispositions_envelope"]),Fraction(r["processed_cases_envelope"]))
            self.assertEqual(Fraction(r["processed_cases_envelope"])+Fraction(r["unserved_demand_cases"]),Fraction(r["demand_cases"]))
            for row in r["resource_rows"]:
                self.assertEqual(Fraction(row["used_hours"])+Fraction(row["unused_hours"]),Fraction(row["available_hours"]))
    def test_route_omission(self):
        with self.assertRaisesRegex(ValueError,"ROUTE_COVERAGE"):self.runplan(replace(self.base,routes=self.base.routes[:1]))
    def test_wrong_shares(self):
        r=self.base.routes
        with self.assertRaisesRegex(ValueError,"ROUTE_SHARES"):self.runplan(replace(self.base,routes=(r[0],replace(r[1],share_ref=r[0].share_ref))))
    def test_process_pin(self):
        with self.assertRaisesRegex(ValueError,"PROCESS_PIN"):self.runplan(replace(self.base,process_sha256="0"*64))
    def test_wrong_unit(self):
        with self.assertRaisesRegex(ValueError,"PARAMETER_SCOPE_UNIT_OR_BASIS"):self.runplan(replace(self.base,demand_ref=self.base.minimum_quality_ref))
    def test_incompatible_demand(self):
        with self.assertRaisesRegex(ValueError,"COMPARISON_SCOPE"):compare(self.g,self.process,self.base,self.process,self.ah)
    def test_no_employment_inference(self):
        r=self.runplan(self.ai);self.assertIsNone(r["employment_effect"]);self.assertIsNone(r["cash_savings"]);self.assertIsNone(r["queue_delay"])
    def test_replay(self):
        r=compare(self.g,self.process,self.base,self.process,self.ai)
        self.assertTrue(replay(r,self.g,self.process,self.base,self.process,self.ai))
        with self.assertRaisesRegex(ValueError,"OPERATIONS_REPLAY"):replay(r,self.g,self.process,self.base,self.process,self.redesign)
    def test_no_adoption_identity(self):
        r=compare(self.g,self.process,self.base,self.process,self.base)["result"]
        self.assertTrue(all(Fraction(v)==0 for v in r["delta"].values()))
    def test_audit(self):
        r=audit(self.process);self.assertEqual(len(r["cases"]),4)
