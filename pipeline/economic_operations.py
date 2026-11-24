"""G3.2 v0.1: deterministic divisible-flow capacity envelope, not a queue simulator.
Every numeric input is an explicit G3 assumption. Exact rational arithmetic.
"""
from dataclasses import dataclass,asdict
from fractions import Fraction
from pathlib import Path
from collections import defaultdict
from .economic_core import require,words,texts,identity,canonical,digest,unique,Scope
from .work_process import Process

@dataclass(frozen=True)
class Resource:
    id:str
    kind:str
    available_hours_ref:str
    overhead_hours_ref:str

@dataclass(frozen=True)
class StepLoad:
    step_id:str
    resource_minutes:tuple  # (resource id, parameter ref); all positive loads explicit
    nonlabor_cost_ref:str  # EUR per visit, excludes resource payroll and fixed cost

@dataclass(frozen=True)
class Route:
    id:str
    steps:tuple
    share_ref:str
    correct_disposition_ref:str  # conditional fraction of correctly resolved/routed cases

@dataclass(frozen=True)
class Plan:
    id:str
    revision:int
    label:str
    scope:Scope
    output_contract:str
    process_sha256:str
    demand_ref:str
    minimum_quality_ref:str
    resources:tuple
    step_loads:tuple
    routes:tuple
    assumptions:str
    @property
    def key(self):return identity(self.id,self.revision)

def process_pin(process):
    require(isinstance(process,Process),"PROCESS_REQUIRED")
    # work action may have a Decimal duration; never use it as a scenario assumption silently.
    import json
    return digest(canonical(json.loads(json.dumps(asdict(process),default=str))))

def model_pin():
    here=Path(__file__).resolve().parent
    return {name:digest((here/name).read_bytes()) for name in ("economic_operations.py","economic_core.py","work_process.py","work_actions.py")}

def native_paths(process):
    children=defaultdict(list)
    for t in process.transitions:children[t.origin].append(t.target)
    paths=[]
    def visit(s,path):
        require(len(paths)<1000,"ROUTE_BUDGET")
        path=path+(s,)
        if s in process.terminals:paths.append(path)
        else:
            for child in children[s]:visit(child,path)
    visit(process.entry,())
    return set(paths)

def run(graph,process,plan):
    plan.key
    require(isinstance(plan.scope,Scope) and words(plan.label) and words(plan.output_contract) and words(plan.assumptions),"PLAN_FIELDS")
    require(plan.process_sha256==process_pin(process),"PROCESS_PIN")
    seen=set()
    def p(key,unit):
        require(key in graph.parameters,"PARAMETER_REF")
        x=graph.parameters[key];q=x.quantity
        require(x.scope==plan.scope and x.basis=="ASSUMPTION" and q.unit==unit and q.value is not None and q.value>=0 and q.lower is None,"PARAMETER_SCOPE_UNIT_OR_BASIS")
        seen.add(key)
        return Fraction(q.value)
    demand=p(plan.demand_ref,"UNIT");minimum=p(plan.minimum_quality_ref,"FRACTION")
    rr=unique(plan.resources,lambda x:x.id)
    require(bool(rr) and all(words(k) and r.kind in {"HUMAN","MACHINE","SERVICE"} for k,r in rr.items()),"RESOURCE")
    available={};overhead={}
    for k,r in rr.items():
        available[k]=p(r.available_hours_ref,"HOUR")*60
        overhead[k]=p(r.overhead_hours_ref,"HOUR")*60
        require(overhead[k]<=available[k],"OVERHEAD_EXCEEDS_CAPACITY")
    loads=unique(plan.step_loads,lambda x:x.step_id)
    require(set(loads)=={s.id for s in process.steps},"STEP_COVERAGE")
    times={};costs={}
    for k,s in loads.items():
        mapping=unique(s.resource_minutes,lambda x:x[0])
        require(bool(mapping) and set(mapping)<=rr.keys(),"STEP_RESOURCE")
        times[k]={r:p(pair[1],"MINUTE_PER_UNIT") for r,pair in mapping.items()}
        require(any(v>0 for v in times[k].values()),"ZERO_STEP_WORK")
        costs[k]=p(s.nonlabor_cost_ref,"EUR_PER_UNIT")
    routes=unique(plan.routes,lambda r:r.id)
    require(bool(routes) and len(routes)==len({r.steps for r in routes.values()}) and {r.steps for r in routes.values()}==native_paths(process),"ROUTE_COVERAGE")
    total_share=Fraction(0);quality=Fraction(0);per_resource=defaultdict(Fraction);per_step=defaultdict(Fraction);varcost=Fraction(0);route_results=[]
    for k,r in sorted(routes.items()):
        share=p(r.share_ref,"FRACTION");good=p(r.correct_disposition_ref,"FRACTION")
        total_share+=share;quality+=share*good
        for step in r.steps:
            per_step[step]+=share
            for res,minutes in times[step].items():per_resource[res]+=share*minutes
            varcost+=share*costs[step]
        route_results.append({"route":k,"steps":list(r.steps),"share":str(share),"correct_disposition_fraction":str(good)})
    require(total_share==1,"ROUTE_SHARES")
    caps={k:(available[k]-overhead[k])/v for k,v in per_resource.items() if v>0}
    require(bool(caps),"NO_WORKLOAD")
    cap=min(caps.values());processed=min(demand,cap)
    good=processed*quality
    resource_rows=[];labor=Fraction(0);labor_intensity=Fraction(0);fixed_labor=Fraction(0)
    for k,r in sorted(rr.items()):
        per=per_resource[k];used=overhead[k]+processed*per
        require(used<=available[k],"RESOURCE_CONSERVATION")
        if r.kind=="HUMAN":
            labor+=used/60;labor_intensity+=per/60;fixed_labor+=overhead[k]/60
        resource_rows.append({"resource":k,"kind":r.kind,"minutes_per_case":str(per),"available_hours":str(available[k]/60),"overhead_hours":str(overhead[k]/60),"used_hours":str(used/60),"unused_hours":str((available[k]-used)/60),"utilization":str(used/available[k]) if available[k]>0 else None,"capacity_cases":str(caps[k]) if k in caps else None})
    return {"plan_ref":plan.key,"label":plan.label,"scope":asdict(plan.scope),"output_contract":plan.output_contract,"quality_floor":str(minimum),"quality":str(quality),"quality_gate":"PASS_CONDITIONAL" if quality>=minimum else "BLOCK_QUALITY","demand_cases":str(demand),"capacity_upper_bound_cases":str(cap),"processed_cases_envelope":str(processed),"unserved_demand_cases":str(demand-processed),"correct_dispositions_envelope":str(good),"incorrect_dispositions_envelope":str(processed-good),"human_hours":str(labor),"fixed_human_overhead_hours":str(fixed_labor),"marginal_human_hours_per_case":str(labor_intensity),"human_hours_per_correct_disposition":str(labor/good) if good>0 else None,"nonlabor_variable_eur":str(processed*varcost),"nonlabor_eur_per_case":str(varcost),"binding_resources":sorted(k for k,v in caps.items() if v==cap),"demand_binding":demand<=cap,"resource_rows":resource_rows,"route_rows":route_results,"step_visits_per_case":{k:str(v) for k,v in sorted(per_step.items())},"parameter_refs":sorted(seen),"assumptions":plan.assumptions,"process_sha256":plan.process_sha256,"graph_sha256":graph.fingerprint,"model_versions":model_pin(),"status":"CONDITIONAL_DIVISIBLE_FLOW_UPPER_BOUND","employment_effect":None,"queue_delay":None,"cash_savings":None,"publication":"BLOCK_PUBLICATION"}

def compare(graph,baseline_process,baseline,alternative_process,alternative):
    require(baseline.scope==alternative.scope and baseline.output_contract==alternative.output_contract and baseline.minimum_quality_ref==alternative.minimum_quality_ref and baseline.demand_ref==alternative.demand_ref,"COMPARISON_SCOPE")
    a=run(graph,baseline_process,baseline);b=run(graph,alternative_process,alternative)
    comparable=a["quality_gate"]==b["quality_gate"]=="PASS_CONDITIONAL" and Fraction(b["quality"])>=Fraction(a["quality"])
    delta={}
    if comparable:
        for k in ("capacity_upper_bound_cases","processed_cases_envelope","correct_dispositions_envelope","human_hours","nonlabor_variable_eur","unserved_demand_cases"):
            delta[k]=str(Fraction(b[k])-Fraction(a[k]))
    out={"baseline":a,"alternative":b,"quality_comparable":comparable,"delta":delta if comparable else None,"decision":"CONDITIONAL_COMPARISON" if comparable else "BLOCK_QUALITY_COMPARISON","interpretation":"Differences of coherent capacity envelopes, not realized production, headcount or cash savings."}
    return {"result":out,"sha256":digest(canonical(out))}

def replay(expected,graph,baseline_process,baseline,alternative_process,alternative):
    require(expected==compare(graph,baseline_process,baseline,alternative_process,alternative),"OPERATIONS_REPLAY")
    return True
