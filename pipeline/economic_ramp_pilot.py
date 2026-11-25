"""G3.3 integration demonstration. No independent simulator: call transition/valuation."""
from dataclasses import replace
from .economic_transition import assess,simulate
from .economic_transition_pilot import fixture
from .economic_physical_pilot import make
from .work_graph import build

def cases(process):
    ref,phases,b,alts=fixture(process)
    # Keep two employees through the transition to isolate timing.
    # Explicit quarterly staffing unchanged. Mixed operation is sequential cohorts.
    a=alts[0]
    def neutral(q):return replace(q,budgeted_hires=0,frozen_hires=0,hire_j=0,hire_s=0,quit_j=0,quit_s=0,other_j=0,other_s=0,layoff_j=0,layoff_s=0,promote=0,training_seconds=0,redeployed_seconds=0,training_cents=0)
    b=replace(b,id="ramp:reference",quarters=tuple(neutral(q) for q in b.quarters))
    a=replace(a,id="ramp:immediate",quarters=tuple(neutral(q) for q in a.quarters))
    def mix(q,n):return replace(q,phase="mixed",phase_mix=(("reference",q.repeats-n),("robot",n)))
    ramp=replace(a,id="ramp:gradual",quarters=tuple(mix(q,25) if q.index==3 else mix(q,75) if q.index==4 else q for q in a.quarters))
    expensive=replace(ramp,id="ramp:capex-stress",quarters=tuple(replace(q,capex_cents=q.capex_cents+1000000) if q.index==2 else q for q in ramp.quarters))
    unfunded=replace(ramp,id="ramp:unfunded",quarters=tuple(replace(q,debt_draw_cents=0,principal_repaid_cents=0) for q in ramp.quarters))
    return ref,phases,b,(a,ramp,expensive,unfunded)

def audit(process):
    ref,phases,b,alts=cases(process);out={}
    for a in alts:
        r=assess(process,ref,phases,b,a);assert r==assess(process,ref,phases,b,a)
        x=r["result"];t=x["transition_comparison"]["result"]["alternative"]["result"]
        out[a.id]={"npv_delta_eur":x["incremental_unlevered_npv_eur"],"funding_gap_eur":t["funding_gap_at_sampled_dates_eur"],"quarters":[{k:q[k] for k in ("quarter","sales","headcount","phase_mix","active_production_seconds","allocated_production_seconds","payroll_eur","closing_cash_eur")} for q in t["quarters"]],"sha256":r["sha256"]}
    # Matched lower demand per cohort in both reference and alternative, no endogenous prices.
    reduced={k:(p,s,d,replace(c,max_sales=18)) for k,(p,s,d,c) in phases.items()}
    r=assess(process,reduced["reference"],reduced,b,alts[1])
    z=r["result"];t=z["transition_comparison"]["result"]["alternative"]["result"]
    out["matched_lower_demand"]={"npv_delta_eur":z["incremental_unlevered_npv_eur"],"funding_gap_eur":t["funding_gap_at_sampled_dates_eur"],"sales_per_quarter":t["quarters"][0]["sales"],"sha256":r["sha256"]}
    return {"fixture":"W002_RAMP_INTEGRATED","cases":out,"scientific_gate_promoted":False,"publication":"BLOCK_PUBLICATION"}
if __name__=="__main__":
    import json
    p,_=make(build());print(json.dumps(audit(p),ensure_ascii=False,indent=2))
