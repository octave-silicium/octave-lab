import unittest
from dataclasses import replace
from pipeline.economic_events import *
from pipeline.economic_events_pilot import fixture,audit,METRICS
from pipeline.economic_terminology import present
from pipeline.invoice_pilot import make,TASK_PREFIX

class Fake:
    manifest={"task_statements":{"url":"fixture","sha256":"a"*64}}
    def profile(self,code):return {"tasks":[{"task":{"label":TASK_PREFIX,"source":"task_statements","source_row":2,"id":"fixture:task"}}]}

class EventTests(unittest.TestCase):
    def setUp(self):
        self.p,_=make(Fake());self.b,self.a,self.r,self.s,self.bb,self.ba=fixture(self.p)
    def sim(self,p):return simulate(self.p,p)["result"]
    def simple(self,arrivals=(0,0),windows=((0,100),),h=100,servers=1):
        pool=Pool("human","HUMAN",tuple(Server("s"+str(i),windows) for i in range(servers)))
        e=tuple(Execution(k,(Visit("human",10),)) for k in ("extract","match","check","accept"))
        return replace(self.b,pools=(pool,),horizon=h,cases=tuple(Case(str(i),t,e,True) for i,t in enumerate(arrivals)))
    def test_one_case_exact(self):
        r=self.sim(self.simple((0,)));self.assertEqual(r["completion_seconds"],{"0":40});self.assertEqual(r["total_wait_case_seconds"],0);self.assertEqual(r["human_service_seconds"],40)
    def test_two_cases_shared_server(self):
        r=self.sim(self.simple());self.assertEqual(r["completion_seconds"],{"0":70,"1":80});self.assertEqual(r["total_wait_case_seconds"],70)
    def test_parallel_servers(self):
        r=self.sim(self.simple(servers=2));self.assertEqual(r["completion_seconds"],{"0":40,"1":40});self.assertEqual(r["total_wait_case_seconds"],0)
    def test_calendar_gap(self):
        r=self.sim(self.simple((0,),((0,15),(30,100))));self.assertEqual(r["completion_seconds"],{"0":60});self.assertEqual(r["total_wait_case_seconds"],20)
    def test_censored_in_service(self):
        r=self.sim(self.simple((0,),((0,100),),h=15));self.assertEqual(r["completed_cases"],0);self.assertEqual(r["in_service_cases"],1);self.assertEqual(r["human_service_seconds"],15)
    def test_no_slot(self):
        r=self.sim(self.simple((0,),((0,5),),h=15));self.assertEqual(r["waiting_cases"],1);self.assertEqual(r["total_wait_case_seconds"],15)
    def test_completion_at_boundary(self):
        r=self.sim(self.simple((0,),h=40));self.assertEqual(r["completed_cases"],1)
    def test_empty_cohort(self):
        r=self.sim(self.simple(()));self.assertIsNone(r["quality_completed"]);self.assertIsNone(r["mean_completed_elapsed_seconds"])
    def test_conservation(self):
        for p in (self.b,self.a,self.r,self.s,self.bb,self.ba):
            r=self.sim(p);self.assertEqual(r["arrivals"],r["completed_cases"]+r["unfinished_cases"]);self.assertEqual(r["unfinished_cases"],r["waiting_cases"]+r["in_service_cases"])
            for x in r["resource_rows"]:self.assertEqual(x["available_seconds"],x["busy_seconds"]+x["idle_available_seconds"])
    def test_quality_and_rework(self):
        r=compare(self.p,self.b,self.p,self.s)["result"];self.assertFalse(r["quality_comparable"]);self.assertIsNone(r["delta"]);self.assertGreater(r["alternative"]["result"]["planned_rework_executions"],0)
    def test_rework_invalid(self):
        p=self.simple((0,));c=p.cases[0];bad=replace(c,executions=(replace(c.executions[0],rework=True),*c.executions[1:]))
        with self.assertRaisesRegex(ValueError,"REWORK_EDGE"):self.sim(replace(p,cases=(bad,)))
    def test_route_invalid(self):
        p=self.simple((0,));c=p.cases[0]
        with self.assertRaisesRegex(ValueError,"ROUTE"):self.sim(replace(p,cases=(replace(c,executions=c.executions[1:]),)))
    def test_calendar_overlap(self):
        with self.assertRaisesRegex(ValueError,"CALENDAR"):self.sim(self.simple((0,),((0,20),(10,100))))
    def test_cohort_mismatch(self):
        with self.assertRaisesRegex(ValueError,"COMPARISON_COHORT"):compare(self.p,self.b,self.p,self.ba)
    def test_replay(self):
        x=compare(self.p,self.b,self.p,self.a);self.assertTrue(replay(x,self.p,self.b,self.p,self.a))
        with self.assertRaisesRegex(ValueError,"EVENT_REPLAY"):replay(x,self.p,self.b,self.p,self.r)
    def test_identity(self):
        r=compare(self.p,self.b,self.p,self.b)["result"];self.assertTrue(all(v==0 for v in r["delta"].values()))
    def test_terminology(self):
        r=present(self.sim(self.a),METRICS);self.assertEqual(len(r["items"]),len(METRICS))
        with self.assertRaisesRegex(ValueError,"UNEXPLAINED_METRIC"):present({"unknown":1},("unknown",))
    def test_audit(self):self.assertEqual(len(audit(self.p)["comparisons"]),4)
