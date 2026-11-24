"""W001 conditional demonstrator. All numerical assumptions are synthetic, not model benchmarks."""
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from .economic_core import *
from .economic_operations import Resource,StepLoad,Route,Plan,process_pin,compare,replay
from .invoice_pilot import make
from .work_graph import build

def fixture(process):
    scope=Scope("W001 synthetic invoice control desk","FR","hypothetical, not representative","2026-01-01","2026-01-31","nominal EUR illustrative")
    ev=Evidence("w001:assumptions",1,"ASSUMPTION","Synthetic demonstration only","fixture in economic_operations_pilot.py",digest(b"W001 operational scenario assumptions v1"),"v1","2026-11-24",None,"INTERNAL_ONLY","ASSUMED")
    params={}
    def p(id,unit,value):
        x=Parameter("w001:"+id,1,scope,Quantity(Decimal(str(value)),unit),"ASSUMPTION",(ev.key,),id)
        if x.key in params:require(params[x.key]==x,"FIXTURE_DUPLICATE")
        params[x.key]=x
        return x.key
    demand=p("demand","UNIT",1000);high=p("high-demand","UNIT",2000)
    floor=p("quality-floor","FRACTION","0.98")
    zero=p("zero-hours","HOUR",0);zero_cost=p("zero-cost","EUR_PER_UNIT",0)
    clerk=p("clerk-hours","HOUR",120);review=p("review-hours","HOUR",60);machine=p("machine-hours","HOUR",200)
    common=(Resource("clerk","HUMAN",clerk,zero),Resource("review","HUMAN",review,zero),Resource("machine","MACHINE",machine,zero))
    def plan(name,minutes,share="0.2",quality="0.99",d=demand,ai=False,overhead=0):
        res=common if not overhead else (common[0],replace(common[1],overhead_hours_ref=p(name+"-overhead","HOUR",overhead)),common[2])
        steps=[]
        for s,loads in minutes.items():
            cost=p(name+"-"+s+"-cost","EUR_PER_UNIT","0.10") if ai and s=="extract" else zero_cost
            steps.append(StepLoad(s,tuple((r,p(name+"-"+s+"-"+r,"MINUTE_PER_UNIT",v)) for r,v in loads.items()),cost))
        routes=(Route("normal",("extract","match","check","accept"),p(name+"-normal-share","FRACTION",Decimal(1)-Decimal(share)),p(name+"-normal-quality","FRACTION",quality)),Route("exception",("extract","match","check","exception","escalate"),p(name+"-exception-share","FRACTION",share),p(name+"-exception-quality","FRACTION",quality)))
        return Plan("w001:"+name,1,name,scope,"Correct control disposition including correctly escalated anomalies; excludes payment and resolution",process_pin(process),d,floor,res,tuple(steps),routes,"All times, capacities, route shares, quality and costs assumed, no measured performance.")
    base_load={"extract":{"clerk":6},"match":{"clerk":4},"check":{"review":3},"accept":{"clerk":1},"exception":{"review":6},"escalate":{"review":2}}
    ai_load={**base_load,"extract":{"machine":1,"clerk":1},"match":{"clerk":2}}
    redesign={**ai_load,"check":{"review":1.5},"exception":{"review":4},"escalate":{"review":1}}
    baseline=plan("baseline",base_load)
    assisted=plan("assisted",ai_load,ai=True)
    stress=plan("stress",ai_load,share="0.5",quality="0.96",ai=True,overhead=5)
    improved=plan("redesign",redesign,ai=True)
    baseline_high=replace(baseline,id="w001:baseline-high",label="baseline high demand",demand_ref=high)
    assisted_high=replace(assisted,id="w001:assisted-high",label="assisted high demand",demand_ref=high)
    graph=Graph(Requirements(),evidence=(ev,),parameters=tuple(params.values()))
    return graph,(baseline,assisted,stress,improved,baseline_high,assisted_high)

def audit(process):
    g,plans=fixture(process)
    baseline,assisted,stress,improved,bh,ah=plans
    rows={}
    for a,b in ((baseline,assisted),(baseline,stress),(baseline,improved),(bh,ah)):
        receipt=compare(g,process,a,process,b)
        assert replay(receipt,g,process,a,process,b)
        r=receipt["result"]
        fields=("capacity_upper_bound_cases","processed_cases_envelope","human_hours","quality","binding_resources","nonlabor_variable_eur")
        rows[b.label]={"baseline":{k:r["baseline"][k] for k in fields},"alternative":{k:r["alternative"][k] for k in fields},"quality_comparable":r["quality_comparable"],"delta":r["delta"],"receipt_sha256":receipt["sha256"]}
    return {"fixture":"W001_SYNTHETIC_ONLY","process_ref":process.id+"@"+str(process.revision),"process_sha256":process_pin(process),"cases":rows,"scientific_gate_promoted":False,"publication":"BLOCK_PUBLICATION"}

if __name__=="__main__":
    import json
    process,task=make(build())
    print(json.dumps(audit(process),indent=2))
