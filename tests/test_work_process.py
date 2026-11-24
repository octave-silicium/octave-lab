import unittest
from dataclasses import replace
from pipeline.work_process import Process,Step,Transition
from pipeline.invoice_pilot import make
class FakeGraph:
    manifest={"task_statements":{"url":"https://example.org/fixture","sha256":"a"*64}}
    def profile(self,code):
        return {"tasks":[{"task":{"label":"Check figures, postings, and documents (fixture)","source":"task_statements","source_row":2,"id":"fixture:task"}}]}
class ProcessTests(unittest.TestCase):
    def test_proposed_no_inferred_metrics(self):
        p,t=make(FakeGraph())
        self.assertEqual(p.audit()["steps"],6)
        self.assertIsNone(p.audit()["duration_estimate"])
        self.assertTrue(p.audit()["human_review_required"])
    def test_unknown_dependency(self):
        p,_=make(FakeGraph())
        with self.assertRaisesRegex(ValueError,"MISSING_INPUT"):
            replace(p,external_inputs=("facture",))
    def test_cycle(self):
        p,_=make(FakeGraph())
        with self.assertRaisesRegex(ValueError,"CYCLE"):
            replace(p,transitions=p.transitions+(Transition("check","extract","retry"),))
    def test_dead_end(self):
        p,_=make(FakeGraph())
        with self.assertRaisesRegex(ValueError,"DEAD_END"):
            replace(p,transitions=p.transitions[:-1])
