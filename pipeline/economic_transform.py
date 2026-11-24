"""G3.2 v0.3: explicit structural alternatives and symmetric quality gates.
No legal clearance, no prediction. Reuses the event engine; sequential exclusive routes only.
"""
from dataclasses import dataclass,asdict
from fractions import Fraction
from pathlib import Path
from .economic_core import require,words,unique,digest,canonical,identity
from .economic_operations import process_pin
from .economic_events import simulate,compare

@dataclass(frozen=True)
class Change:
    before:tuple
    after:tuple
    reason:str

@dataclass(frozen=True)
class Roles:
    step:str
    execution:tuple
    verification:tuple
    authorization:tuple
    accountable_actor:str
    verification_condition:str

@dataclass(frozen=True)
class Quality:
    case_id:str
    criticality:str  # stable cohort characteristic
    correct:bool
    defect:str # NONE, NONCRITICAL, CRITICAL

@dataclass(frozen=True)
class Design:
    id:str
    revision:int
    label:str
    baseline_pin:str
    process_pin:str
    changes:tuple
    roles:tuple
    quality:tuple
    legal_status:str
    legal_context:str
    qualification_note:str
    fallback_note:str
    @property
    def key(self):return identity(self.id,self.revision)

def validate(base,process,schedule,design):
    design.key
    require(all(words(x) for x in (design.label,design.legal_context,design.qualification_note,design.fallback_note)),"DESIGN_FIELDS")
    require(design.baseline_pin==process_pin(base) and design.process_pin==process_pin(process)==schedule.process_sha256,"DESIGN_PIN")
    require(design.legal_status in {"UNKNOWN","ASSUMED_ALLOWED","ASSUMED_PROHIBITED"},"LEGAL_STATUS")
    old={s.id:s for s in base.steps};new={s.id:s for s in process.steps}
    require(base.scope==process.scope and set(base.external_inputs)==set(process.external_inputs),"INPUT_SCOPE")
    def terminal_outputs(p):return sorted(tuple(sorted(s.action.outputs)) for s in p.steps if s.id in p.terminals)
    require(terminal_outputs(base)==terminal_outputs(process),"OUTPUT_CONTRACT")
    a=[];b=[]
    for c in design.changes:
        require(isinstance(c.before,tuple) and isinstance(c.after,tuple) and bool(c.before or c.after) and words(c.reason),"CHANGE")
        a.extend(c.before);b.extend(c.after)
    require(len(a)==len(set(a)) and len(b)==len(set(b)) and set(a)==set(old) and set(b)==set(new),"CHANGE_COVERAGE")
    pools={p.id:p.kind for p in schedule.pools}
    roles=unique(design.roles,lambda r:r.step)
    require(set(roles)==set(new),"ROLE_COVERAGE")
    for r in roles.values():
        require(bool(r.execution or r.verification or r.authorization) and words(r.accountable_actor) and words(r.verification_condition),"ROLE_FIELDS")
        for group in (r.execution,r.verification,r.authorization):
            require(isinstance(group,tuple) and len(group)==len(set(group)) and set(group)<=pools.keys(),"ROLE_POOL")
    qs=unique(design.quality,lambda q:q.case_id)
    require(set(qs)=={c.id for c in schedule.cases},"QUALITY_COVERAGE")
    for c in schedule.cases:
        q=qs[c.id]
        require(q.criticality in {"STANDARD","HIGH"} and type(q.correct) is bool and q.correct==c.correct and q.defect in {"NONE","NONCRITICAL","CRITICAL"} and (q.defect=="NONE")==q.correct,"QUALITY_LABEL")
        for e in c.executions:
            r=roles[e.step]
            require({v.pool for v in e.visits}==set(r.execution+r.verification+r.authorization),"ROLE_VISITS")
    return roles,qs

def evaluate(base,process,schedule,design):
    roles,qs=validate(base,process,schedule,design)
    receipt=simulate(process,schedule);r=receipt["result"];completed=set(r["completed_case_ids"])
    critical=sum(q.defect=="CRITICAL" for q in qs.values())
    critical_done=sum(q.defect=="CRITICAL" and q.case_id in completed for q in qs.values())
    by_class={}
    for cls in ("STANDARD","HIGH"):
        cohort=[q for q in qs.values() if q.criticality==cls];done=[q for q in cohort if q.case_id in completed]
        by_class[cls]={"assigned":len(cohort),"assigned_correct":sum(q.correct for q in cohort),"completed":len(done),"completed_correct":sum(q.correct for q in done)}
    human_pools={p.id for p in schedule.pools if p.kind=="HUMAN"}
    cases_human={a["case"] for a in r["assignments"] if a["pool"] in human_pools and a["service_within_horizon"]>0}
    verified_human={a["case"] for a in r["assignments"] if a["pool"] in human_pools and a["pool"] in roles[a["step"]].verification and a["service_within_horizon"]>0}
    authorized_human={a["case"] for a in r["assignments"] if a["pool"] in human_pools and a["pool"] in roles[a["step"]].authorization and a["service_within_horizon"]>0}
    out={"design_ref":design.key,"label":design.label,"step_count":len(process.steps),"change_map":[asdict(c) for c in design.changes],"role_map":[asdict(x) for x in design.roles],"human_touched_cases":len(cases_human),"human_verification_started_cases":len(verified_human),"human_authorization_started_cases":len(authorized_human),"critical_defects_assigned":critical,"critical_defects_completed":critical_done,"quality_by_class":by_class,"legal_status":design.legal_status,"deployment":"BLOCK_DEPLOYMENT_UNQUALIFIED","technical_safety":"BLOCK_CRITICAL_DEFECT" if critical else "NO_CRITICAL_DEFECT_ASSIGNED_NOT_VALIDATED","event_receipt":receipt,"design_sha256":digest(canonical(asdict(design))),"model_sha256":digest(Path(__file__).read_bytes()),"publication":"BLOCK_PUBLICATION"}
    return {"result":out,"sha256":digest(canonical(out))}

def compare_design(base,bs,bd,alt,ats,ad):
    x=evaluate(base,base,bs,bd);y=evaluate(base,alt,ats,ad)
    require(sorted((q.case_id,q.criticality) for q in bd.quality)==sorted((q.case_id,q.criticality) for q in ad.quality),"RISK_COHORT")
    event=compare(base,bs,alt,ats)["result"]
    a=x["result"];b=y["result"]
    def nondegraded():
        for k,u in a["quality_by_class"].items():
            v=b["quality_by_class"][k]
            if u["assigned"] and Fraction(v["assigned_correct"],v["assigned"])<Fraction(u["assigned_correct"],u["assigned"]):return False
            # Cannot claim class comparability where either side has no completed cases.
            if u["assigned"] and (not u["completed"] or not v["completed"]):return False
            if u["completed"] and Fraction(v["completed_correct"],v["completed"])<Fraction(u["completed_correct"],u["completed"]):return False
        return True
    comparable=event["quality_comparable"] and a["critical_defects_assigned"]==b["critical_defects_assigned"]==0 and nondegraded()
    out={"baseline":x,"alternative":y,"quality_comparable":comparable,"delta":event["delta"] if comparable else None,"paired_completed":event["paired_completed"] if comparable else None,"deployment":"BLOCK_DEPLOYMENT_UNQUALIFIED","interpretation":"Symmetric conditional quality and criticality checks. No empirical superiority or legal authorization."}
    return {"result":out,"sha256":digest(canonical(out))}
