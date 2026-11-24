"""W001 event test: synthetic cases and service times; official source anchors only candidate process."""
from dataclasses import replace
from .economic_core import Scope
from .economic_operations import process_pin
from .economic_events import *
from .invoice_pilot import make
from .work_graph import build

def fixture(process):
    scope=Scope("W001 synthetic desk","FR","synthetic not representative","2026-01-01","2026-01-01","not monetized")
    H=4*3600
    pools=(Pool("clerk","HUMAN",(Server("c1",((0,H),)),)),Pool("review","HUMAN",(Server("r1",((0,3600),(5400,H))),)),Pool("machine","MACHINE",(Server("m1",((0,H),)),)))
    def build_case(i,assisted=False,burst=False,stress=False,redesign=False):
        exc=i%5==0 or stress and i%2==0
        path=("extract","match","check","exception","escalate") if exc else ("extract","match","check","accept")
        d={"extract":(("clerk",360),),"match":(("clerk",240),),"check":(("review",180),),"accept":(("clerk",60),),"exception":(("review",360),),"escalate":(("review",120),)}
        if assisted:d.update(extract=(("machine",60),("clerk",60)),match=(("clerk",120),))
        if redesign:d.update(check=(("review",90),),exception=(("review",240),),escalate=(("review",60),))
        es=[]
        for step in path:
            vs=tuple(Visit(k,t+(30 if i%3==0 else 0)) for k,t in d[step])
            es.append(Execution(step,vs))
            if stress and step=="check" and i%3==0:es.append(Execution(step,vs,True))
        return Case("case-%03d"%i,0 if burst else i*180,tuple(es),not(stress and i%7==0))
    def plan(label,**kw):
        return Schedule("w001:event-"+label,1,label,scope,"Correct control disposition including correct escalation, not payment",process_pin(process),H,98,100,pools,tuple(build_case(i,**kw) for i in range(60)),"Synthetic 60 cases, scripted durations, exception and correctness labels, no empirical calibration; empty start, 4 hours.")
    return plan("baseline"),plan("assisted",assisted=True),plan("redesign",assisted=True,redesign=True),plan("stress",assisted=True,stress=True),plan("burst-baseline",burst=True),plan("burst-assisted",assisted=True,burst=True)

METRICS=("arrivals","completed_cases","correct_completed_cases","unfinished_cases","waiting_cases","in_service_cases","quality_completed","quality_assigned_cohort","human_service_seconds","mean_completed_elapsed_seconds","p90_completed_elapsed_seconds","total_wait_case_seconds","time_weighted_mean_cases_in_system","planned_rework_executions","rework_visits_started")
def audit(process):
    from .economic_terminology import present
    b,a,r,s,bb,ba=fixture(process);rows={}
    for x,y in ((b,a),(b,r),(b,s),(bb,ba)):
        rec=compare(process,x,process,y);assert replay(rec,process,x,process,y)
        z=rec["result"]
        rows[y.label]={"baseline":{k:z["baseline"]["result"][k] for k in METRICS},"alternative":{k:z["alternative"]["result"][k] for k in METRICS},"quality_comparable":z["quality_comparable"],"delta":z["delta"],"paired_completed":z["paired_completed"],"sha256":rec["sha256"]}
    return {"fixture":"W001_SCRIPTED_SYNTHETIC","process_sha256":process_pin(process),"comparisons":rows,"terminology_example":present(simulate(process,a)["result"],METRICS),"scientific_gate_promoted":False,"publication":"BLOCK_PUBLICATION"}
if __name__=="__main__":
    import json
    process,_=make(build());print(json.dumps(audit(process),ensure_ascii=False,indent=2))
