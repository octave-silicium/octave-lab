import unittest
from dataclasses import replace
from fractions import Fraction as F
from pipeline.economic_transition import simulate,assess,allocation,valuation
from pipeline.economic_ramp_pilot import cases,audit
from pipeline.economic_physical_pilot import make,TASK_PREFIX
from pipeline.economic_investigation import Investigation,FirmTransition,assemble,verify_replay
from pipeline.economic_core import Graph,Scope,Coverage,canonical,digest
from pipeline.economic_prospective import model_pins
from test_economic_prospective import fixture

class Fake:
    manifest={"task_statements":{"url":"fixture","sha256":"a"*64}}
    def profile(self,code):return {"tasks":[{"task":{"label":TASK_PREFIX,"source":"task_statements","source_row":2,"id":"fixture:physical"}}]}

class RampTests(unittest.TestCase):
    def setUp(self):self.p,_=make(Fake());self.ref,self.phases,self.b,self.alts=cases(self.p)
    def sim(self,p):return simulate(self.p,self.ref,self.phases,p)["result"]
    def test_mix(self):
        q=self.sim(self.alts[1])["quarters"][2]
        self.assertEqual(q["reference_cohort_fraction"],"4/5");self.assertEqual(q["sales"],2875)
        self.assertEqual(q["allocated_production_seconds"],720000)
    def test_no_double_cohort(self):
        q=self.alts[1].quarters[2]
        with self.assertRaisesRegex(ValueError,"MIX_CONSERVATION"):allocation(replace(q,phase_mix=(("reference",125),("robot",25))))
    def test_predeployment(self):
        p=self.alts[1];q=replace(p.quarters[0],phase="mixed",phase_mix=(("reference",100),("robot",25)))
        with self.assertRaisesRegex(ValueError,"PRE_DEPLOYMENT"):self.sim(replace(p,quarters=(q,*p.quarters[1:])))
    def test_same_payroll(self):
        a=self.sim(self.alts[0]);b=self.sim(self.alts[1])
        self.assertEqual([q["payroll_eur"] for q in a["quarters"]],[q["payroll_eur"] for q in b["quarters"]])
        self.assertGreater(b["quarters"][2]["active_production_seconds"],a["quarters"][2]["active_production_seconds"])
    def test_capex(self):
        x=assess(self.p,self.ref,self.phases,self.b,self.alts[1])["result"];y=assess(self.p,self.ref,self.phases,self.b,self.alts[2])["result"]
        self.assertEqual(F(x["incremental_unlevered_npv_eur"])-F(y["incremental_unlevered_npv_eur"]),F(10000)/F(102,100))
    def test_financing(self):
        x=assess(self.p,self.ref,self.phases,self.b,self.alts[1])["result"];y=assess(self.p,self.ref,self.phases,self.b,self.alts[3])["result"]
        self.assertEqual(x["incremental_unlevered_npv_eur"],y["incremental_unlevered_npv_eur"])
        self.assertEqual(y["funding_status_both"][1],"UNFUNDED_SHORTFALL")
    def test_audit(self):self.assertEqual(len(audit(self.p)["cases"]),5)
    def test_investigation(self):
        g,ss,paths,inter,fs=fixture()
        s=replace(self.ref[1].scope,period_end="2027-12-31")
        g=Graph(g.requirements,entities=tuple(g.entities.values()),evidence=tuple(g.evidence.values()),parameters=tuple(replace(p,scope=s) for p in g.parameters.values()),claims=tuple(replace(c,scope=s) for c in g.claims.values()),assertions=tuple(g.assertions.values()))
        ss=tuple(replace(t,scope=s,step_unit="quarter",horizons=("8 quarters",)) for t in ss)
        args=(ss,paths,inter,fs)
        rows=tuple(Coverage(k,i,"PENDING_QUALIFICATION","fixture only") for k,ids in g.requirements.groups.items() for i in sorted(ids))
        inv=Investigation("ramp:inv",1,"Question","decision",("baseline","alternative"),"loss","synthetic",g.fingerprint,digest(canonical(model_pins())))
        item=FirmTransition(ss[2].key,self.p,self.ref,self.phases,self.b,self.alts[1])
        r=assemble(inv,g,rows,prospective=args,firm_transitions=(item,))
        self.assertEqual(r["manifest"]["firm_transitions"][0]["status"],"CONDITIONAL_NOT_PROPAGATED")
        self.assertTrue(verify_replay(r,inv,g,rows,prospective=args,firm_transitions=(item,)))
        with self.assertRaisesRegex(ValueError,"FIRM_SCOPE_HORIZON"):assemble(inv,g,rows,prospective=(tuple(replace(t,step_unit="month") for t in ss),paths,inter,fs),firm_transitions=(item,))
