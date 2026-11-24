"""G3.2 v0.4b: finite-horizon DAG dispatch, atomic simultaneous resources.
Scripted scenarios only; no optimization, stochastic inference or mid-task failure.
"""
from dataclasses import dataclass,asdict
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from .economic_core import require,words,identity,unique,digest,canonical,Scope
from .economic_operations import process_pin,native_paths
from .economic_events import Pool,integer,MAX_SECONDS

@dataclass(frozen=True)
class Task:
    id:str
    step:str
    parents:tuple
    seconds:int
    resources:tuple # (pool id, integer count); all held for entire operation

@dataclass(frozen=True)
class Job:
    id:str
    arrival:int
    priority:int # smaller first
    kind:str # PRODUCTION or AUDIT
    tasks:tuple
    correct:bool|None
    due:int|None=None

@dataclass(frozen=True)
class Plan:
    id:str
    revision:int
    scope:Scope
    output_contract:str
    process_sha256:str
    horizon:int
    policy:str
    pools:tuple
    jobs:tuple
    quality_floor_num:int
    quality_floor_den:int
    assumptions:str
    @property
    def key(self):return identity(self.id,self.revision)

def validate(process,plan):
    plan.key
    require(isinstance(plan.scope,Scope) and words(plan.output_contract) and words(plan.assumptions) and plan.process_sha256==process_pin(process),"PLAN_SCOPE_PIN")
    require(integer(plan.horizon,1,MAX_SECONDS) and plan.policy in {"READY_FIFO","PRIORITY_FIRST"},"POLICY_HORIZON")
    require(integer(plan.quality_floor_den,1,1000000) and integer(plan.quality_floor_num,0,plan.quality_floor_den),"QUALITY_FLOOR")
    require(isinstance(plan.pools,tuple) and 0<len(plan.pools)<=50,"POOLS")
    pools=unique(plan.pools,lambda x:x.id);servers={}
    for k,p in pools.items():
        require(isinstance(p,Pool) and words(k) and p.kind in {"HUMAN","MACHINE","SERVICE"} and isinstance(p.servers,tuple) and 0<len(p.servers)<=50,"POOL")
        for sid,s in unique(p.servers,lambda x:x.id).items():
            require(words(sid) and isinstance(s.windows,tuple) and len(s.windows)<=100,"SERVER")
            last=0
            for w in s.windows:
                require(isinstance(w,tuple) and len(w)==2 and integer(w[0],last,MAX_SECONDS) and integer(w[1],w[0]+1,MAX_SECONDS),"CALENDAR")
                last=w[1]
            servers[(k,sid)]=s.windows
    require(isinstance(plan.jobs,tuple) and len(plan.jobs)<=500,"JOBS")
    jobs=unique(plan.jobs,lambda j:j.id);native=native_paths(process);all_tasks={};total=0
    for jid,j in jobs.items():
        require(words(jid) and integer(j.arrival,0,plan.horizon-1) and integer(j.priority,0,1000) and j.kind in {"PRODUCTION","AUDIT"} and isinstance(j.tasks,tuple) and 0<len(j.tasks)<=50,"JOB")
        require((j.kind=="PRODUCTION" and type(j.correct) is bool and j.due is None) or (j.kind=="AUDIT" and j.correct is None and integer(j.due,j.arrival+1,plan.horizon)),"JOB_OUTCOME")
        tasks=unique(j.tasks,lambda t:t.id);total+=len(tasks);require(total<=5000,"TASK_LIMIT")
        ancestors={}
        def visit(k,active):
            require(k not in active,"CYCLE")
            if k in ancestors:return ancestors[k]
            t=tasks[k];a=set(t.parents)
            for p in t.parents:a|=visit(p,active|{k})
            ancestors[k]=a;return a
        for k,t in tasks.items():
            require(words(k) and words(t.step) and isinstance(t.parents,tuple) and len(t.parents)==len(set(t.parents)) and set(t.parents)<=tasks.keys() and integer(t.seconds,1,MAX_SECONDS) and isinstance(t.resources,tuple) and bool(t.resources),"TASK")
            rr=unique(t.resources,lambda x:x[0])
            require(all(pool in pools and integer(row[1],1,len(pools[pool].servers)) for pool,row in rr.items()),"RESOURCE_DEMAND")
        for k in tasks:visit(k,set())
        if j.kind=="PRODUCTION":
            # A native exclusive route is selected explicitly. Parallel subtasks are allowed
            # within a step. All tasks of each preceding step must finish before any next step.
            matched=[]
            for path in native:
                if set(path)!={t.step for t in tasks.values()}:continue
                ix={s:i for i,s in enumerate(path)}
                if all(ix[tasks[a].step]<=ix[t.step] for t in tasks.values() for a in ancestors[t.id]) and all(all(u.id in ancestors[t.id] for u in tasks.values() if ix[u.step]<ix[t.step]) for t in tasks.values()):
                    matched.append(path)
            require(len(matched)==1,"NATIVE_ROUTE_OR_DEPENDENCY")
        else:require(all(t.step=="periodic-audit" for t in tasks.values()),"AUDIT_STEP")
        all_tasks.update({(jid,k):t for k,t in tasks.items()})
    return pools,servers,jobs,all_tasks

def simulate(process,plan):
    pools,servers,jobs,tasks=validate(process,plan);H=plan.horizon
    now=0;finish={};started={};ready_since={};running={};free={k:0 for k in servers};trace=[];busy=defaultdict(int);ready_wait=defaultdict(int)
    # Calendar starts, arrivals, completions; at each time dispatch eligible tasks.
    times={0,H}|{j.arrival for j in jobs.values()}|{a for ws in servers.values() for a,b in ws if a<H}
    pending=set(tasks)
    def find(t):
        chosen=[]
        for pool,n in sorted(t.resources):
            available=[k for k,ws in sorted(servers.items()) if k[0]==pool and free[k]<=now and any(a<=now and now+t.seconds<=b for a,b in ws)]
            if len(available)<n:return None
            chosen.extend(available[:n])
        return chosen
    while times:
        now=min(times);times.remove(now)
        for k,end in list(running.items()):
            if end==now:finish[k]=end;del running[k]
        if now>=H:break
        ready=[]
        for k in sorted(pending):
            jid,_=k;t=tasks[k];j=jobs[jid]
            if j.arrival<=now and all((jid,p) in finish for p in t.parents):
                ready_since.setdefault(k,now);ready.append(k)
        def rank(k):
            return ((jobs[k[0]].priority,) if plan.policy=="PRIORITY_FIRST" else ())+(ready_since[k],jobs[k[0]].arrival,k)
        for k in sorted(ready,key=rank):
            t=tasks[k];chosen=find(t)
            if chosen is None:continue
            end=now+t.seconds;pending.remove(k);started[k]=now;running[k]=end
            if end<=H:times.add(end)
            occupied=min(end,H)-now;ready_wait[k]=now-ready_since[k]
            for server in chosen:
                free[server]=end;busy[server]+=occupied
            trace.append({"job":k[0],"task":k[1],"step":t.step,"kind":jobs[k[0]].kind,"ready":ready_since[k],"start":now,"end":end,"resources":[list(s) for s in chosen],"occupied_seconds":occupied})
    for k in pending:
        if k in ready_since:ready_wait[k]=H-ready_since[k]
    require(len(finish)+len(running)+len(pending)==len(tasks),"TASK_CONSERVATION")
    complete={}
    for jid,j in jobs.items():
        keys=[(jid,t.id) for t in j.tasks]
        if all(k in finish for k in keys):complete[jid]=max(finish[k] for k in keys)
    production=[j for j in jobs.values() if j.kind=="PRODUCTION"];audits=[j for j in jobs.values() if j.kind=="AUDIT"]
    done=[j for j in production if j.id in complete];good=sum(j.correct for j in done)
    assigned=sum(j.correct for j in production)
    q=Fraction(good,len(done)) if done else None;qa=Fraction(assigned,len(production)) if production else None;floor=Fraction(plan.quality_floor_num,plan.quality_floor_den)
    rows=[];human=0;audit_human=0
    for k,p in sorted(pools.items()):
        avail=sum(max(0,min(b,H)-a) for server,ws in servers.items() if server[0]==k for a,b in ws if a<H)
        used=sum(v for server,v in busy.items() if server[0]==k)
        require(0<=used<=avail,"RESOURCE_CONSERVATION")
        if p.kind=="HUMAN":
            human+=used
            audit_human+=sum(r["occupied_seconds"]*sum(s[0]==k for s in r["resources"]) for r in trace if r["kind"]=="AUDIT")
        rows.append({"pool":k,"kind":p.kind,"available_seconds":avail,"used_seconds":used,"idle_available_seconds":avail-used})
    # Independent trace checks: precedence, calendars and no overlapping allocations.
    by_server=defaultdict(list)
    for r in trace:
        k=(r["job"],r["task"]);t=tasks[k]
        require(all(finish[(k[0],p)]<=r["start"] for p in t.parents),"PRECEDENCE")
        for s in r["resources"]:
            key=tuple(s);require(any(a<=r["start"] and r["end"]<=b for a,b in servers[key]),"CALENDAR_TRACE")
            by_server[key].append((r["start"],r["end"]))
    for spans in by_server.values():
        spans.sort();require(all(a[1]<=b[0] for a,b in zip(spans,spans[1:])),"OVERLAP")
    elapsed=[complete[j.id]-j.arrival for j in done]
    audit_on_time=sum(j.id in complete and complete[j.id]<=j.due for j in audits)
    r={"plan_ref":plan.key,"policy":plan.policy,"horizon_seconds":H,"arrivals":len(production),"completed_cases":len(done),"correct_completed_cases":good,"unfinished_cases":len(production)-len(done),"quality_completed":str(q) if q is not None else None,"quality_assigned_cohort":str(qa) if qa is not None else None,"quality_gate":"PASS_CONDITIONAL" if q is not None and qa is not None and min(q,qa)>=floor else "BLOCK_QUALITY_OR_EMPTY","human_service_seconds":human,"audit_human_seconds":audit_human,"production_human_seconds":human-audit_human,"audit_due_count":len(audits),"audit_on_time_count":audit_on_time,"audit_missed_count":len(audits)-audit_on_time,"mean_completed_elapsed_seconds":str(Fraction(sum(elapsed),len(elapsed))) if elapsed else None,"total_ready_task_wait_seconds":sum(ready_wait.values()),"resource_rows":rows,"completion_seconds":dict(sorted(complete.items())),"task_states":{"completed":len(finish),"running":len(running),"not_started":len(pending)},"trace":trace,"input_sha256":digest(canonical(asdict(plan))),"model_versions":{n:digest((Path(__file__).parent/n).read_bytes()) for n in ("economic_parallel.py","economic_events.py","economic_operations.py","economic_core.py","work_process.py","work_actions.py")},"process_sha256":plan.process_sha256,"assumptions":plan.assumptions,"deployment":"BLOCK_DEPLOYMENT_UNQUALIFIED","publication":"BLOCK_PUBLICATION"}
    return {"result":r,"sha256":digest(canonical(r))}

def compare(process,a,b):
    require(a.scope==b.scope and a.output_contract==b.output_contract and a.horizon==b.horizon and Fraction(a.quality_floor_num,a.quality_floor_den)==Fraction(b.quality_floor_num,b.quality_floor_den) and sorted((j.id,j.arrival,j.priority) for j in a.jobs if j.kind=="PRODUCTION")==sorted((j.id,j.arrival,j.priority) for j in b.jobs if j.kind=="PRODUCTION"),"COMPARISON_SCOPE")
    x=simulate(process,a);y=simulate(process,b);u=x["result"];v=y["result"]
    ok=u["quality_gate"]==v["quality_gate"]=="PASS_CONDITIONAL" and Fraction(v["quality_completed"])>=Fraction(u["quality_completed"]) and Fraction(v["quality_assigned_cohort"])>=Fraction(u["quality_assigned_cohort"])
    # Does not replace the criticality gates of economic_transform; no deployment recommendation.
    r={"baseline":x,"alternative":y,"quality_comparable":ok,"delta":{k:v[k]-u[k] for k in ("completed_cases","unfinished_cases","human_service_seconds","audit_human_seconds")} if ok else None,"audit_obligations_met_both":u["audit_missed_count"]==v["audit_missed_count"]==0,"criticality_comparison":"NOT_IMPLEMENTED_IN_THIS_CONTRACT","publication":"BLOCK_PUBLICATION"}
    return {"result":r,"sha256":digest(canonical(r))}
