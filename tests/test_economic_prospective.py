import unittest
from dataclasses import replace
from decimal import Decimal
from pipeline.economic_core import *
from pipeline.economic_prospective import *
from pipeline.economic_investigation import Investigation,assemble,verify_replay
from pipeline.economic_calculations import Calculation,calculate

S=Scope("synthetic invoice service","FR","fictional","2026-01-01","2027-12-31","nominal EUR")
def fixture():
    ev=Evidence("p:assume",1,"ASSUMPTION","fixture","assumption","a"*64,"synthetic","2026-11-24",None,"INTERNAL_ONLY","ASSUMED")
    nat=Evidence("p:native",1,"NATIVE_SOURCE","synthetic fixture only","state","b"*64,"synthetic","2026-11-24",None,"INTERNAL_ONLY","DESCRIPTIVE_ONLY")
    p=Parameter("p:adopt",1,S,Quantity(Decimal("0.5"),"FRACTION"),"ASSUMPTION",(ev.key,),"scenario adoption assumption")
    initial=Claim("p:initial",1,"OBSERVATION","Synthetic initial state (test only)","decision",S,None,(nat.key,),(),"test fixture not real data","fictional","other state","measure",())
    nodes=[Entity("p:"+k,1,t,k,"fixture") for k,t in [("tech","TECHNOLOGY"),("task","ACTION"),("process","PROCESS"),("firm","FIRM"),("market","MARKET"),("actor","ACTOR"),("shock2","TECHNOLOGY")]]
    links=[("tech","task",0,"NEGATIVE"),("task","process",None,"UNKNOWN"),("process","firm",1,"POSITIVE"),("tech","firm",2,"NEGATIVE"),("firm","market",1,"UNKNOWN"),("market","tech",1,"UNKNOWN"),("shock2","firm",1,"UNKNOWN")]
    claims=[initial];edges=[]
    for i,(a,b,lag,direction) in enumerate(links):
        c=Claim("p:claim:"+str(i),1,"MECHANISM_HYPOTHESIS","candidate "+a+" to "+b,"decision",S,None,(ev.key,),("M010",),"hypothesis only","not measured","rival","test",())
        claims.append(c);edges.append(Assertion("p:edge:"+str(i),1,"p:"+a+"@1","p:"+b+"@1","CAUSAL_HYPOTHESIS",c.key,"if conditions hold",lag,direction))
    g=Graph(Requirements(),entities=nodes,evidence=(ev,nat),parameters=(p,),claims=claims,assertions=edges)
    baseline=Trajectory("p:baseline",1,"NO_SHOCK",None,"comparison",S,(initial.key,),(),(),(),("short","long"),"month","fixed boundary",("hours","cost"),"unknown","measure")
    noad=replace(baseline,id="p:noad",mode="NO_ADOPTION",baseline_ref=baseline.key,shock_refs=(nodes[0].key,),assumption_refs=(p.key,))
    adopted=replace(noad,id="p:adopted",mode="CONDITIONAL",shock_refs=(nodes[0].key,nodes[-1].key),intervention_refs=(nodes[2].key,))
    def branch(id,sc,shock,indices,code="MISSING_EVIDENCE"):
        cs=[];prior=initial.key
        for i in indices:
            cs.append(Context(nodes[5].key,(prior,),(p.key,),"UNKNOWN","candidate only"))
            prior=edges[i].claim_ref
        return Branch("p:"+id,1,sc.key,shock,tuple(edges[i].key for i in indices),tuple(cs),code,"test stop")
    paths=(branch("no",noad,nodes[0].key,(),"NO_ADOPTION"),branch("long",adopted,nodes[0].key,(0,1,2)),branch("short",adopted,nodes[0].key,(3,)),branch("second",adopted,nodes[-1].key,(6,)),branch("loop",adopted,nodes[0].key,(3,4,5),"DEPTH_LIMIT"))
    interactions=(Interaction("p:interaction",1,"COMPENSATING",(paths[1].key,paths[2].key),claims[1].key,"rival effects","measure hours and price separately"),)
    fs=tuple((f,(baseline.key,) if i==0 else (noad.key,) if i==1 else (adopted.key,) if i==4 else (),"fixture scope only") for i,f in enumerate(families()))
    return g,(baseline,noad,adopted),paths,interactions,fs
class ProspectiveTests(unittest.TestCase):
    def test_contract_and_replay(self):
        g,*args=fixture();b=build(g,*args);r=b["result"]
        self.assertEqual(b,build(g,*args))
        self.assertEqual(b,json.loads(canonical(b)))
        self.assertEqual(len(r["families"]),10)
        self.assertEqual(len(r["scenarios"]),3)
        self.assertEqual(len(r["paths"]),5)
        self.assertTrue(all(set(g.requirements.scenario_fields)<=set(s) for s in r["scenarios"]))
        self.assertTrue(all(set(g.requirements.path_fields)<=set(s) for p in r["paths"] for s in p["steps"]))
        self.assertIsNone(r["comparison"]["total_effect"]);self.assertFalse(r["comparison"]["path_sum_allowed"])
        self.assertEqual(len(r["convergences"]),1)
        self.assertEqual(len(r["convergences"][0]["paths"]),3)
        self.assertTrue(r["frontier"])
        self.assertTrue(all(s["magnitude_or_unknown"] is None for p in r["paths"] for s in p["steps"]))
    def test_order_and_feedback(self):
        g,*args=fixture();r=build(g,*args)["result"];by={p["path_ref"]:p for p in r["paths"]}
        self.assertEqual([s["path_order"] for s in by["p:long@1"]["steps"]],[1,2,3])
        self.assertIsNone(by["p:long@1"]["steps"][-1]["elapsed_model_steps"])
        self.assertEqual(by["p:loop@1"]["steps"][-1]["elapsed_model_steps"],4)
        self.assertTrue(by["p:loop@1"]["truncated"])
        self.assertEqual(by["p:no@1"]["steps"],[])
    def test_missing_shock(self):
        g,s,p,i,f=fixture()
        with self.assertRaisesRegex(ValueError,"UNTRACED_SHOCK"):build(g,s,tuple(x for x in p if x.id!="p:second"),i,f)
    def test_no_shock(self):
        g,s,p,i,f=fixture()
        with self.assertRaisesRegex(ValueError,"NULL_SHOCK"):build(g,(replace(s[0],shock_refs=s[1].shock_refs),*s[1:]),p,i,f)
    def test_no_adoption(self):
        g,s,p,i,f=fixture()
        bad=replace(p[0],assertion_refs=p[2].assertion_refs,contexts=p[2].contexts)
        with self.assertRaisesRegex(ValueError,"NO_ADOPTION_TRANSMISSION"):build(g,s,(bad,*p[1:]),i,f)
    def test_false_stop(self):
        g,s,p,i,f=fixture()
        with self.assertRaisesRegex(ValueError,"FALSE_NO_ONWARD_LINK"):build(g,s,(p[0],replace(p[1],stop_code="NO_ONWARD_LINK"),*p[2:]),i,f)
    def test_assumption_scope(self):
        g,s,p,i,f=fixture()
        with self.assertRaisesRegex(ValueError,"PATH_ASSUMPTION"):build(g,s,(p[0],replace(p[1],contexts=(replace(p[1].contexts[0],assumption_refs=("p:missing@1",)),*p[1].contexts[1:])),*p[2:]),i,f)
    def test_actor(self):
        g,s,p,i,f=fixture()
        with self.assertRaisesRegex(ValueError,"AFFECTED_ACTOR"):build(g,s,(p[0],replace(p[1],contexts=(replace(p[1].contexts[0],actor_ref="p:tech@1"),*p[1].contexts[1:])),*p[2:]),i,f)
    def test_chain(self):
        g,s,p,i,f=fixture()
        with self.assertRaisesRegex(ValueError,"PATH_CLAIM_CHAIN"):build(g,s,(p[0],replace(p[1],contexts=(p[1].contexts[0],replace(p[1].contexts[1],input_claim_refs=("p:initial@1",)),p[1].contexts[2])),*p[2:]),i,f)
    def test_baseline_comparability(self):
        g,s,p,i,f=fixture()
        with self.assertRaisesRegex(ValueError,"BASELINE_COMPARABILITY"):build(g,(s[0],s[1],replace(s[2],comparison_metrics=("other",))),p,i,f)
    def test_family_missing(self):
        g,s,p,i,f=fixture()
        with self.assertRaisesRegex(ValueError,"FAMILY_COVERAGE"):build(g,s,p,i,f[:-1])
    def test_inverse(self):
        g,*args=fixture();b=build(g,*args)
        r=inverse(b,"p:firm@1",(Rival("p:long@1","test bottleneck"),Rival("p:short@1","test direct adoption")))
        self.assertFalse(r["causal_inference"]);self.assertEqual(r["unassessed_paths"],["p:second@1"])
        with self.assertRaisesRegex(ValueError,"RIVAL_TESTS"):inverse(b,"p:firm@1",(Rival("p:long@1","test"),))
    def test_manifest(self):
        g,*args=fixture();rows=tuple(Coverage(k,i,"PENDING_QUALIFICATION","fixture") for k,ids in g.requirements.groups.items() for i in sorted(ids))
        inv=Investigation("p:inv",1,"Question","decision",("baseline","alternative"),"loss","synthetic",g.fingerprint,digest(canonical(model_pins())))
        result=assemble(inv,g,rows,prospective=args)
        self.assertTrue(verify_replay(result,inv,g,rows,prospective=args))
        with self.assertRaisesRegex(ValueError,"MODEL_PIN_MISMATCH"):assemble(replace(inv,model_sha256="c"*64),g,rows,prospective=args)

class CalculationDirectTests(unittest.TestCase):
    def case(self,op,u,v,out,x,y,z):
        e=Evidence("calc:a",1,"ASSUMPTION","fixture","case","a"*64,"fixture","2026-11-24",None,"INTERNAL_ONLY","ASSUMED")
        a=Parameter("calc:x",1,S,Quantity(Decimal(x),u),"ASSUMPTION",(e.key,),"numerator")
        b=Parameter("calc:y",1,S,Quantity(Decimal(y),v),"ASSUMPTION",(e.key,),"denominator")
        c=Claim("calc:c",1,"CONDITIONAL_SCENARIO","fixture","decision",S,Quantity(Decimal(z),out),(e.key,),("M010",),"synthetic","not measured","rival","test",(),(a.key,b.key))
        return Graph(Requirements(),evidence=(e,),parameters=(a,b),claims=(c,)),Calculation("calc:receipt",1,op,(a.key,b.key),c.key)
    def test_labor_cost(self):
        g,c=self.case("LABOR_COST","HOUR","EUR_PER_HOUR","EUR","10","25","250");self.assertEqual(calculate(g,c)["result"],"250")
    def test_variable_cost(self):
        g,c=self.case("VARIABLE_COST","EUR_PER_UNIT","UNIT","EUR","0.25","100","25");self.assertEqual(Decimal(calculate(g,c)["result"]),Decimal("25"))
    def test_unit_cost(self):
        g,c=self.case("UNIT_COST","EUR","UNIT","EUR_PER_UNIT","25","100","0.25");self.assertEqual(calculate(g,c)["result"],"0.25")
    def test_throughput(self):
        g,c=self.case("THROUGHPUT","UNIT","HOUR","UNIT_PER_HOUR","100","10","10");self.assertEqual(calculate(g,c)["result"],"10")
    def test_zero_denominator(self):
        g,c=self.case("THROUGHPUT","UNIT","HOUR","UNIT_PER_HOUR","100","0","0")
        with self.assertRaisesRegex(ValueError,"ZERO_DENOMINATOR"):calculate(g,c)
