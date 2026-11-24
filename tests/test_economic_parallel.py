import unittest
from dataclasses import replace
from pipeline.economic_parallel import *
from pipeline.economic_events import Server
from pipeline.economic_parallel_pilot import fixture,audit
from pipeline.economic_physical_pilot import make,TASK_PREFIX
class Fake:
    manifest={"task_statements":{"url":"fixture","sha256":"a"*64}}
    def profile(self,code):return {"tasks":[{"task":{"label":TASK_PREFIX,"source":"task_statements","source_row":2,"id":"fixture:physical"}}]}
class ParallelTests(unittest.TestCase):
    def setUp(self):
        self.p,_=make(Fake());self.b,self.alts=fixture(self.p)
    def sim(self,p):return simulate(self.p,p)["result"]
    def small(self,parallel=True):
        p=self.alts[1];j=p.jobs[0]
        return replace(p,jobs=(j,),horizon=1000)
    def test_join(self):
        r=self.sim(self.small());t={x["task"]:x for x in r["trace"]}
        self.assertEqual(t["metadata"]["start"],t["tolerance"]["start"])
        self.assertEqual(t["report"]["start"],max(t["metadata"]["end"],t["tolerance"]["end"]))
    def test_atomic_bundle(self):
        r=self.sim(self.small());t=r["trace"][0];self.assertEqual(sorted(x[0] for x in t["resources"]),["gauge","robot"])
    def test_calendar_joint_unavailable(self):
        p=self.small();p=replace(p,pools=tuple(replace(x,servers=(Server("g1",((100,1000),)),)) if x.id=="gauge" else x for x in p.pools))
        self.assertEqual(self.sim(p)["trace"][0]["start"],100)
    def test_cycle(self):
        p=self.small();j=p.jobs[0];t=replace(j.tasks[0],parents=("report",))
        with self.assertRaisesRegex(ValueError,"CYCLE"):self.sim(replace(p,jobs=(replace(j,tasks=(t,*j.tasks[1:])),)))
    def test_missing_join(self):
        p=self.small();j=p.jobs[0];t=replace(j.tasks[-1],parents=("metadata",))
        with self.assertRaisesRegex(ValueError,"NATIVE_ROUTE_OR_DEPENDENCY"):self.sim(replace(p,jobs=(replace(j,tasks=(*j.tasks[:-1],t)),)))
    def test_audit_separate(self):
        r=self.sim(self.alts[2]);self.assertEqual(r["arrivals"],24);self.assertEqual(r["audit_due_count"],2);self.assertGreater(r["audit_human_seconds"],0);self.assertEqual(r["production_human_seconds"],0)
    def test_priority(self):
        p=self.small();j=p.jobs[0];audit1=Job("audit-a",0,1,"AUDIT",(Task("review","periodic-audit",(),10,(("software",1),)),),None,1000)
        audit2=replace(audit1,id="audit-z",priority=0)
        pool=tuple(replace(x,servers=(Server("s1",((0,1000),)),)) if x.id=="software" else x for x in p.pools)
        p=replace(p,jobs=(audit1,audit2),pools=pool)
        self.assertEqual(self.sim(p)["trace"][0]["job"],"audit-a")
        self.assertEqual(self.sim(replace(p,policy="PRIORITY_FIRST"))["trace"][0]["job"],"audit-z")
    def test_censor(self):
        p=replace(self.small(),horizon=10);r=self.sim(p);self.assertEqual(r["task_states"]["running"],1);self.assertEqual(r["completed_cases"],0)
    def test_no_partial_reservation(self):
        p=self.small();p=replace(p,pools=tuple(replace(x,servers=(Server("g1",()),)) if x.id=="gauge" else x for x in p.pools))
        r=self.sim(p);self.assertEqual(r["trace"],[]);self.assertEqual(r["unfinished_cases"],1)
    def test_audit_missed(self):
        p=self.alts[2];p=replace(p,pools=tuple(replace(x,servers=(Server("o1",()),)) if x.id=="operator" else x for x in p.pools))
        r=self.sim(p);self.assertEqual(r["audit_missed_count"],2)
    def test_replay(self):
        self.assertEqual(compare(self.p,self.b,self.alts[0]),compare(self.p,self.b,self.alts[0]))
    def test_outage(self):
        a=self.sim(self.alts[3]);b=self.sim(self.alts[4]);self.assertLessEqual(b["completed_cases"],a["completed_cases"])
    def test_audit(self):self.assertEqual(len(audit(self.p)["alternatives"]),6)
