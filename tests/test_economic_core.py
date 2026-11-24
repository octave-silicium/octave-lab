import unittest
from dataclasses import replace
from decimal import Decimal
from pipeline.economic_core import *
S=Scope("synthetic firm","FR","fictional scope","2026-01-01","2026-12-31","nominal EUR 2026")
def example():
    req=Requirements()
    ev=Evidence("fixture:assumption",1,"ASSUMPTION","synthetic fixture","case 1","a"*64,"fixture-v1","2026-11-24",None,"INTERNAL_ONLY","ASSUMED")
    p=Parameter("fixture:time",1,S,Quantity(Decimal("66"),"MINUTE_PER_UNIT"),"ASSUMPTION",(ev.key,),"human time conditional")
    c=Claim("fixture:claim",1,"CONDITIONAL_SCENARIO","Illustrative 66 minutes","capacity",S,p.quantity,(ev.key,),("M010",),"declared scenario","not observed","different adoption","revise when measured",(),(p.key,))
    a=Entity("fixture:action",1,"ACTION","Document extraction","synthetic")
    b=Entity("fixture:process",1,"PROCESS","Invoice control","synthetic")
    edge=Assertion("fixture:edge",1,a.key,b.key,"SCENARIO",c.key,"quality fixed",0,"UNKNOWN")
    return req,ev,p,c,a,b,edge
def graph():
    r,e,p,c,a,b,edge=example()
    return Graph(r,entities=(a,b),evidence=(e,),parameters=(p,),claims=(c,),assertions=(edge,))
class CoreTests(unittest.TestCase):
    def test_registry_and_reproducibility(self):
        g=graph()
        self.assertEqual(len(g.requirements.mechanisms),64)
        self.assertEqual(g.fingerprint,graph().fingerprint)
        self.assertEqual(len(g.neighbors("fixture:process@1","in")["assertions"]),1)
        self.assertEqual(g.neighbors("fixture:process@1","out")["assertions"],[])
        self.assertFalse(g.neighbors("fixture:process@1")["inferred_causality"])
    def test_revision_exact_and_contradictions(self):
        r,e,p,c,a,b,edge=example()
        g=Graph(r,entities=(a,b),evidence=(e,),parameters=(p,),claims=(c,replace(c,revision=2,statement="Alternative scenario")),assertions=(edge,))
        self.assertEqual(len(g.claims),2)
        with self.assertRaisesRegex(ValueError,"EDGE_REFERENCE"):Graph(r,entities=(a,replace(b,revision=2)),evidence=(e,),parameters=(p,),claims=(c,),assertions=(edge,))
    def test_no_fake_observation(self):
        r,e,p,c,*_=example()
        with self.assertRaisesRegex(ValueError,"OBSERVATION_BLOCKED"):Graph(r,evidence=(e,),claims=(replace(c,claim_type="OBSERVATION",parameter_refs=()),))
        with self.assertRaisesRegex(ValueError,"CLAIM_TYPE_SCOPE"):replace(c,claim_type="CAUSAL_ESTIMATE")
    def test_unknown_no_numeric(self):
        r,e,p,c,*_=example()
        with self.assertRaisesRegex(ValueError,"UNKNOWN_NOT_ZERO"):replace(p,basis="UNKNOWN")
        p=replace(p,basis="UNKNOWN",quantity=Quantity(None,"MINUTE_PER_UNIT"))
        with self.assertRaisesRegex(ValueError,"UNKNOWN_DEPENDENCY"):Graph(r,evidence=(e,),parameters=(p,),claims=(c,))
    def test_restricted_no_numeric(self):
        r,e,p,c,*_=example()
        e=replace(e,rights="RESTRICTED")
        with self.assertRaisesRegex(ValueError,"NUMERIC_EVIDENCE_BLOCKED"):Graph(r,evidence=(e,),parameters=(p,),claims=(c,))
    def test_cycles_in_provenance(self):
        r,e,p,c,*_=example()
        with self.assertRaisesRegex(ValueError,"PROVENANCE_CYCLE"):Graph(r,evidence=(e,),parameters=(p,),claims=(replace(c,dependency_refs=(c.key,)),))
    def test_coverage_and_no_certification(self):
        g=graph()
        entries=[Coverage(k,i,"PENDING_QUALIFICATION","Not evaluated in this fixture") for k,ids in g.requirements.groups.items() for i in sorted(ids)]
        self.assertEqual(validate_coverage(g,entries)["entries"],110)
        with self.assertRaisesRegex(ValueError,"COVERAGE_MISSING"):validate_coverage(g,entries[:-1])
        with self.assertRaisesRegex(ValueError,"QUALIFICATION_GATE"):Coverage("mechanism","M001","APPLIED_QUALIFIED","not supported",("fixture:claim@1",))
    def test_quantity_strict(self):
        with self.assertRaisesRegex(ValueError,"NUMERIC"):Quantity(0.1,"FRACTION")
        with self.assertRaisesRegex(ValueError,"RATIO_RANGE"):Quantity(Decimal("101"),"PERCENT")
        with self.assertRaisesRegex(ValueError,"BOUNDS"):Quantity(Decimal("1"),"EUR",lower=Decimal("2"),upper=Decimal("3"))

    def test_structural_path_order_not_delay(self):
        from pipeline.economic_paths import Scenario,Path,trace
        g=graph();s=Scenario("fixture:scenario",1,None,"synthetic",("fixture:time@1",),("future",),"bounded","unknown","measurement")
        p=Path(s.key,"fixture:action@1",("fixture:edge@1",),"No qualified onward link")
        result=trace(g,s,p)
        self.assertEqual(result["steps"][0]["order"],1)
        self.assertEqual(result["steps"][0]["elapsed_model_steps"],0)
        self.assertIsNone(result["computed_effect"])
        with self.assertRaisesRegex(ValueError,"DISCONTINUITY"):trace(g,s,replace(p,shock_entity="fixture:process@1"))
    def test_no_zero_lag_feedback(self):
        from pipeline.economic_paths import Scenario,Path,trace
        r,e,p,c,a,b,edge=example()
        back=replace(edge,id="fixture:back",origin=b.key,target=a.key)
        g=Graph(r,entities=(a,b),evidence=(e,),parameters=(p,),claims=(c,),assertions=(edge,back))
        s=Scenario("fixture:scenario",1,None,"synthetic",(p.key,),("future",),"bounded","unknown","measurement")
        path=Path(s.key,a.key,(edge.key,back.key),"stop")
        with self.assertRaisesRegex(ValueError,"FEEDBACK"):trace(g,s,path)
        g=Graph(r,entities=(a,b),evidence=(e,),parameters=(p,),claims=(c,),assertions=(edge,replace(back,delay_steps=1)))
        self.assertEqual(trace(g,s,path)["steps"][-1]["elapsed_model_steps"],1)
