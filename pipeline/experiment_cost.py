"""Cost and effort ledger. Measurements, allocations and assumptions remain distinct.
No observed labor cost is inferred from model runtime, and no missing cost is zero."""
from decimal import Decimal,InvalidOperation
from collections import defaultdict
import re
D=Decimal
ROLES={"operator","supervisor","reviewer"}
PHASES={"initial","supervision","correction","exception"}
DIRECT={"model_api","compute","other_variable"}
FIXED={"licenses","maintenance","integration_amortization"}
def number(v,positive=False):
    if not isinstance(v,str) or not re.fullmatch(r"\d{1,15}(?:\.\d{1,9})?",v):raise ValueError("DECIMAL_STRING_REQUIRED")
    n=D(v)
    if positive and n<=0:raise ValueError("POSITIVE_REQUIRED")
    return n
def evidence(r):
    if not isinstance(r.get("reference"),str) or not r["reference"].strip():raise ValueError("TRACE_REQUIRED")
def tagged(r,allowed):
    if not isinstance(r,dict) or r.get("basis") not in allowed:raise ValueError("BASIS")
    evidence(r)
    return number(r["value"])
def cost_ledger(case_ids,ledger):
    """One record per case, per-human intervals on common relative monotonic timeline.
    All monetary values EUR; time seconds; fixed annual allocations use declared volume."""
    if ledger.get("currency")!="EUR" or ledger.get("scope")!="DECLARED_PROCESS_BOUNDARY":raise ValueError("LEDGER_SCOPE")
    if not case_ids or len(case_ids)!=len(set(case_ids)):raise ValueError("CASE_IDS")
    records=ledger["cases"]
    if len(records)!=len(case_ids) or {r["id"] for r in records}!=set(case_ids):raise ValueError("LEDGER_COVERAGE")
    rates=ledger.get("hourly_rates",{})
    if not set(rates)<=ROLES:raise ValueError("ROLE")
    rates={k:tagged(v,{"ASSUMPTION","DOCUMENTED_RATE"}) for k,v in rates.items()}
    fixed=ledger.get("annual_fixed",{})
    if not set(fixed)<=FIXED:raise ValueError("FIXED_COMPONENT")
    fixed_values={k:tagged(v,{"ASSUMPTION","DOCUMENTED_COST"}) for k,v in fixed.items()}
    volume=ledger.get("annual_volume")
    if volume is not None:
        if volume.get("basis") not in {"ASSUMPTION","OBSERVED_VOLUME"}:raise ValueError("VOLUME_BASIS")
        evidence(volume);volume=number(volume["value"],True)
    fixed_per_case=sum(fixed_values.values(),D(0))/volume if set(fixed_values)==FIXED and volume is not None else None
    all_wall=[];all_human=[];all_labor=[];all_direct=[];all_error=[];all_full=[]
    phase_total=defaultdict(lambda:D(0));complete_phases=0
    for record in records:
        wall=None if record.get("wall_seconds") is None else tagged(record["wall_seconds"],{"MEASURED"})
        if wall is not None:all_wall.append(wall)
        intervals=record.get("human_intervals")
        labor=None
        if intervals is not None:
            if not isinstance(intervals,list) or record.get("human_time_complete") is not True:raise ValueError("HUMAN_TIME_COMPLETENESS")
            evidence(record)
            if wall is None:raise ValueError("WALL_REQUIRED")
            people=defaultdict(list);phases=defaultdict(lambda:D(0));role_time=defaultdict(lambda:D(0))
            for interval in intervals:
                evidence(interval)
                person=interval.get("person");role=interval.get("role");phase=interval.get("phase")
                if not isinstance(person,str) or not person or role not in ROLES or phase not in PHASES:raise ValueError("INTERVAL_ID")
                a,b=number(interval["start_seconds"]),number(interval["end_seconds"])
                if not a<b<=wall:raise ValueError("INTERVAL_RANGE")
                people[person].append((a,b))
                phases[phase]+=b-a;role_time[role]+=b-a
            for spans in people.values():
                spans.sort()
                if any(a[1]>b[0] for a,b in zip(spans,spans[1:])):raise ValueError("HUMAN_OVERLAP")
            human=sum(phases.values(),D(0));all_human.append(human);complete_phases+=1
            for phase,value in phases.items():phase_total[phase]+=value
            if set(role_time)<=set(rates):
                labor=sum((v*rates[k]/D(3600) for k,v in role_time.items()),D(0));all_labor.append(labor)
        direct=record.get("direct_costs",{})
        if not set(direct)<=DIRECT:raise ValueError("DIRECT_COMPONENT")
        direct_values={k:tagged(v,{"MEASURED","DOCUMENTED_COST","EXPLICIT_ZERO"}) for k,v in direct.items()}
        for k,v in direct.items():
            if v["basis"]=="EXPLICIT_ZERO" and direct_values[k]!=0:raise ValueError("ZERO_BASIS")
        variable=sum(direct_values.values(),D(0)) if set(direct_values)==DIRECT else None
        if variable is not None:all_direct.append(variable)
        error=record.get("error_cost")
        if error is not None:
            error_value=tagged(error,{"DOCUMENTED_COST","ASSUMPTION","EXPLICIT_ZERO"})
            if error["basis"]=="EXPLICIT_ZERO" and error_value!=0:raise ValueError("ZERO_BASIS")
            all_error.append(error_value)
        else:error_value=None
        if all(v is not None for v in (labor,variable,error_value,fixed_per_case)):
            all_full.append(labor+variable+error_value+fixed_per_case)
    n=len(case_ids)
    def metric(xs):
        return {"covered_cases":len(xs),"total":str(sum(xs,D(0))) if len(xs)==n else None}
    return {"scope":"DECLARED_MEASUREMENTS_AND_COST_ALLOCATION_NOT_AUTHENTICATED","cases":n,"wall_seconds":metric(all_wall),"human_person_seconds":metric(all_human),"human_seconds_by_phase":{p:str(phase_total[p]) for p in sorted(PHASES)} if complete_phases==n else None,"labor_cost_eur":metric(all_labor),"direct_variable_cost_eur":metric(all_direct),"error_cost_eur":metric(all_error),"fixed_cost_per_case_eur":str(fixed_per_case) if fixed_per_case is not None else None,"full_cost_eur":metric(all_full),"mean_full_cost_eur":str(sum(all_full,D(0))/n) if len(all_full)==n else None,"production_inference":False,"publication":"BLOCK_PUBLICATION"}
