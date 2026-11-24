"""G3.2 v0.2 — scripted discrete-event simulation (integer seconds).
Non-preemptive, sequential visits per case, parallel identical servers within a pool.
Strict FIFO reservation (no backfill). Synthetic/conditional only, no calibrated distributions.
"""
from dataclasses import dataclass,asdict
from collections import defaultdict
from fractions import Fraction
from heapq import heappush,heappop
from pathlib import Path
from .economic_core import require,words,identity,sha,unique,canonical,digest,Scope
from .economic_operations import process_pin,native_paths

MAX_CASES=10000
MAX_VISITS=200000
MAX_SECONDS=366*86400

@dataclass(frozen=True)
class Server:
    id:str
    windows:tuple # disjoint [start,end) integer-second availability

@dataclass(frozen=True)
class Pool:
    id:str
    kind:str
    servers:tuple

@dataclass(frozen=True)
class Visit:
    pool:str
    seconds:int

@dataclass(frozen=True)
class Execution:
    step:str
    visits:tuple
    # A repeat is a full re-execution of the immediately preceding nonterminal step.
    rework:bool=False

@dataclass(frozen=True)
class Case:
    id:str
    arrival:int
    executions:tuple
    correct:bool

@dataclass(frozen=True)
class Schedule:
    id:str
    revision:int
    label:str
    scope:Scope
    output_contract:str
    process_sha256:str
    horizon:int
    quality_floor_num:int
    quality_floor_den:int
    pools:tuple
    cases:tuple
    assumption_note:str
    @property
    def key(self):return identity(self.id,self.revision)

def model_pins():
    d=Path(__file__).resolve().parent
    return {n:digest((d/n).read_bytes()) for n in ("economic_events.py","economic_operations.py","economic_core.py","work_process.py","work_actions.py")}

def integer(x,lo,hi):return type(x) is int and lo<=x<=hi

def validate(process,schedule):
    schedule.key
    require(isinstance(schedule.scope,Scope) and all(words(x) for x in (schedule.label,schedule.output_contract,schedule.assumption_note)),"SCHEDULE_FIELDS")
    require(schedule.process_sha256==process_pin(process),"PROCESS_PIN")
    require(integer(schedule.horizon,1,MAX_SECONDS),"HORIZON")
    require(integer(schedule.quality_floor_den,1,1000000) and integer(schedule.quality_floor_num,0,schedule.quality_floor_den),"QUALITY_FLOOR")
    require(isinstance(schedule.pools,tuple) and 0<len(schedule.pools)<=100,"POOLS")
    pools=unique(schedule.pools,lambda x:x.id)
    servers={}
    for k,p in pools.items():
        require(words(k) and p.kind in {"HUMAN","MACHINE","SERVICE"} and isinstance(p.servers,tuple) and 0<len(p.servers)<=100,"POOL")
        ss=unique(p.servers,lambda s:s.id)
        for sid,s in ss.items():
            require(words(sid) and isinstance(s.windows,tuple) and len(s.windows)<=1000,"SERVER")
            last=0
            for w in s.windows:
                require(isinstance(w,tuple) and len(w)==2 and integer(w[0],last,MAX_SECONDS) and integer(w[1],w[0]+1,MAX_SECONDS),"CALENDAR")
                last=w[1]
            servers[(k,sid)]=s
    require(isinstance(schedule.cases,tuple) and len(schedule.cases)<=MAX_CASES,"CASE_LIMIT")
    cases=unique(schedule.cases,lambda c:c.id)
    routes=native_paths(process);flat={};used=set();count=0;rework=0
    for cid,c in cases.items():
        require(words(cid) and integer(c.arrival,0,schedule.horizon-1) and type(c.correct) is bool and isinstance(c.executions,tuple) and bool(c.executions),"CASE")
        route=[];visits=[];previous=None;repeats=0
        for e in c.executions:
            require(type(e.rework) is bool and isinstance(e.visits,tuple) and bool(e.visits),"EXECUTION")
            if e.rework:
                require(previous==e.step and e.step not in process.terminals and repeats<10,"REWORK_EDGE")
                repeats+=1;rework+=1
            else:
                route.append(e.step);repeats=0
            previous=e.step
            for v in e.visits:
                require(v.pool in pools and integer(v.seconds,1,MAX_SECONDS),"VISIT")
                visits.append((e.step,e.rework,v));count+=1
                require(count<=MAX_VISITS,"VISIT_LIMIT")
        require(tuple(route) in routes,"ROUTE")
        used.add(tuple(route));flat[cid]=visits
    return pools,servers,cases,flat,routes-used,rework

def quantile(values,num,den):
    if not values:return None
    v=sorted(values);return v[(len(v)*num+den-1)//den-1]

def simulate(process,schedule):
    pools,servers,cases,flat,unused_routes,planned_rework=validate(process,schedule)
    H=schedule.horizon
    # Event order: completions before arrivals at equal time, then stable insertion order.
    events=[];seq=0
    def emit(t,kind,cid,index):
        nonlocal seq
        seq+=1;heappush(events,(t,kind,seq,cid,index))
    for cid,c in sorted(cases.items(),key=lambda x:(x[1].arrival,x[0])):emit(c.arrival,1,cid,0)
    free={k:0 for k in servers};last_start=defaultdict(int);blocked=set()
    assignments=[];completed={};waits=defaultdict(int);busy=defaultdict(int);service=defaultdict(int);pending={}
    def slot(s,ready,duration):
        for start,end in s.windows:
            t=max(start,ready)
            if t+duration<=end:return t
        return None
    def request(cid,index,ready):
        step,rework,v=flat[cid][index];pool=v.pool
        candidates=[]
        if pool not in blocked:
            for sid in sorted(s.id for s in pools[pool].servers):
                k=(pool,sid);t=slot(servers[k],max(ready,free[k],last_start[pool]),v.seconds)
                if t is not None:candidates.append((t,sid))
        if not candidates:
            blocked.add(pool);waits[pool]+=H-ready
            pending[cid]={"state":"WAITING_NO_SLOT","pool":pool,"step":step}
            return
        start,sid=min(candidates);end=start+v.seconds
        last_start[pool]=start;free[(pool,sid)]=end
        w=max(0,min(start,H)-ready);b=max(0,min(end,H)-min(start,H))
        waits[pool]+=w;busy[(pool,sid)]+=b;service[cid]+=b
        assignments.append({"case":cid,"visit_index":index,"step":step,"rework":rework,"pool":pool,"server":sid,"ready":ready,"start":start,"end":end,"wait_within_horizon":w,"service_within_horizon":b})
        pending[cid]={"state":"WAITING" if start>=H else "IN_SERVICE","pool":pool,"step":step}
        if end<=H:emit(end,0,cid,index)
    while events:
        t,kind,_,cid,index=heappop(events)
        if kind==0:
            if index+1==len(flat[cid]):
                completed[cid]=t;pending.pop(cid,None)
            elif t<H:request(cid,index+1,t)
            else:
                step,_,v=flat[cid][index+1];pending[cid]={"state":"WAITING","pool":v.pool,"step":step}
        else:request(cid,index,t)
    require(len(completed)+len(pending)==len(cases),"CASE_CONSERVATION")
    good=sum(cases[c].correct for c in completed);n=len(cases);done=len(completed)
    quality=Fraction(good,done) if done else None;planned=Fraction(sum(c.correct for c in cases.values()),n) if n else None
    floor=Fraction(schedule.quality_floor_num,schedule.quality_floor_den)
    elapsed=[completed[c]-cases[c].arrival for c in completed]
    rows=[];human=0
    for k,p in sorted(pools.items()):
        available=sum(max(0,min(end,H)-start) for s in p.servers for start,end in s.windows if start<H)
        used=sum(busy[(k,s.id)] for s in p.servers)
        require(0<=used<=available,"RESOURCE_CONSERVATION")
        if p.kind=="HUMAN":human+=used
        rows.append({"resource":k,"kind":p.kind,"available_seconds":available,"busy_seconds":used,"idle_available_seconds":available-used,"utilization":str(Fraction(used,available)) if available else None,"queue_case_seconds":waits[k],"unfinished_waiting_cases":sum(r["pool"]==k and r["state"].startswith("WAITING") for r in pending.values())})
    wip=sum(completed.get(c,H)-job.arrival for c,job in cases.items())
    require(wip==sum(waits.values())+sum(service.values()),"TIME_CONSERVATION")
    result={"schedule_ref":schedule.key,"label":schedule.label,"scope":asdict(schedule.scope),"output_contract":schedule.output_contract,"horizon_seconds":H,"arrivals":n,"completed_cases":done,"correct_completed_cases":good,"incorrect_completed_cases":done-good,"unfinished_cases":n-done,"waiting_cases":sum(r["state"].startswith("WAITING") for r in pending.values()),"in_service_cases":sum(r["state"]=="IN_SERVICE" for r in pending.values()),"quality_completed":str(quality) if quality is not None else None,"quality_assigned_cohort":str(planned) if planned is not None else None,"quality_floor":str(floor),"quality_gate":"PASS_CONDITIONAL" if quality is not None and planned is not None and min(quality,planned)>=floor else "BLOCK_QUALITY_OR_EMPTY","human_service_seconds":human,"mean_completed_elapsed_seconds":str(Fraction(sum(elapsed),done)) if done else None,"p90_completed_elapsed_seconds":quantile(elapsed,90,100),"total_wait_case_seconds":sum(waits.values()),"time_weighted_mean_cases_in_system":str(Fraction(wip,H)),"planned_rework_executions":planned_rework,"rework_visits_started":sum(a["rework"] and a["start"]<H for a in assignments),"resource_rows":rows,"completed_case_ids":sorted(completed),"unfinished":dict(sorted(pending.items())),"completion_seconds":dict(sorted(completed.items())),"assignments":assignments,"unrepresented_native_routes":[list(r) for r in sorted(unused_routes)],"input_sha256":digest(canonical(asdict(schedule))),"process_sha256":schedule.process_sha256,"model_versions":model_pins(),"assumption_note":schedule.assumption_note,"status":"CONDITIONAL_SCRIPTED_EVENTS","queue_policy":"FIFO_RESERVATION_NO_BACKFILL","employment_effect":None,"cash_savings":None,"publication":"BLOCK_PUBLICATION"}
    return {"result":result,"sha256":digest(canonical(result))}

def compare(bp,base,ap,alternative):
    require(base.scope==alternative.scope and base.output_contract==alternative.output_contract and base.horizon==alternative.horizon and Fraction(base.quality_floor_num,base.quality_floor_den)==Fraction(alternative.quality_floor_num,alternative.quality_floor_den) and sorted((c.id,c.arrival) for c in base.cases)==sorted((c.id,c.arrival) for c in alternative.cases),"COMPARISON_COHORT")
    a=simulate(bp,base);b=simulate(ap,alternative);x=a["result"];y=b["result"]
    ok=x["quality_gate"]==y["quality_gate"]=="PASS_CONDITIONAL" and Fraction(y["quality_assigned_cohort"])>=Fraction(x["quality_assigned_cohort"]) and Fraction(y["quality_completed"])>=Fraction(x["quality_completed"])
    matched=sorted(set(x["completed_case_ids"])&set(y["completed_case_ids"]))
    paired=None
    if ok and matched:
        paired={"count":len(matched),"mean_elapsed_delta_seconds":str(Fraction(sum(y["completion_seconds"][c]-x["completion_seconds"][c] for c in matched),len(matched))),"selection_warning":"Only cases completed in both scenarios; not whole cohort."}
    delta={k:y[k]-x[k] for k in ("completed_cases","correct_completed_cases","unfinished_cases","human_service_seconds","total_wait_case_seconds")} if ok else None
    r={"baseline":a,"alternative":b,"quality_comparable":ok,"delta":delta,"paired_completed":paired,"interpretation":"Conditional scripted cohort, not real performance or staffing recommendation.","publication":"BLOCK_PUBLICATION"}
    return {"result":r,"sha256":digest(canonical(r))}

def replay(expected,bp,base,ap,alternative):
    require(expected==compare(bp,base,ap,alternative),"EVENT_REPLAY")
    return True
