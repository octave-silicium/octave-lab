"""G3.3 v0.2b1: conditional skill pipeline and dynamic unlevered valuation.
Synthetic named worker slots, not personal data or qualification certification.
"""
from dataclasses import dataclass,asdict,replace
from fractions import Fraction as F
from pathlib import Path
from .economic_core import require,words,identity,unique,canonical,digest
from .economic_events import integer
from .economic_firm import money
from .economic_transition import simulate,compare

@dataclass(frozen=True)
class Rule:
    min_quarters:int
    formal_seconds:int
    practice_seconds:int
    mentor_basis_points:int

@dataclass(frozen=True)
class Learning:
    worker:str
    formal_seconds:int
    practice_seconds:int
    mentor:str
    mentor_seconds:int

@dataclass(frozen=True)
class SkillQuarter:
    index:int
    hires:tuple # (id, JUNIOR/SENIOR)
    exits:tuple # (id, QUIT/LAYOFF/OTHER)
    assessments_passed:tuple # scripted assessment; only after prior learning
    learning:tuple
    production:tuple # (worker, seconds) allocated production time, not active time
    expert_demand_seconds:int # separate non-production activity

@dataclass(frozen=True)
class SkillPlan:
    id:str
    revision:int
    initial:tuple # (id, JUNIOR/SENIOR), prior learning not assumed
    rule:Rule
    quarters:tuple
    assumptions:str
    @property
    def key(self):return identity(self.id,self.revision)

def compile_plan(template,skills):
    skills.key;r=skills.rule;w=template.workforce
    require(words(skills.assumptions) and integer(r.min_quarters,1,120) and integer(r.formal_seconds,1,10**9) and integer(r.practice_seconds,1,10**9) and integer(r.mentor_basis_points,1,10000),"LEARNING_RULE")
    require(len(skills.quarters)==len(template.quarters) and isinstance(skills.initial,tuple) and len(skills.initial)<=1000,"SKILL_SCOPE")
    initial=unique(skills.initial,lambda x:x[0])
    require(all(words(k) and v[1] in {"JUNIOR","SENIOR"} for k,v in initial.items()),"INITIAL_ROLE")
    require(sum(v[1]=="JUNIOR" for v in initial.values())==w.junior and sum(v[1]=="SENIOR" for v in initial.values())==w.senior,"INITIAL_STOCK")
    people={k:{"role":v[1],"entered":1,"formal":0,"practice":0} for k,v in initial.items()};seen=set(people);rows=[];quarters=[]
    for q,t in zip(skills.quarters,template.quarters):
        require(q.index==t.index and integer(q.expert_demand_seconds,0,10**12),"SKILL_QUARTER")
        hires=unique(q.hires,lambda x:x[0]);exits=unique(q.exits,lambda x:x[0])
        require(all(k in people and v[1] in {"QUIT","LAYOFF","OTHER"} for k,v in exits.items()),"SKILL_EXIT")
        require(all(words(k) and k not in seen and v[1] in {"JUNIOR","SENIOR"} for k,v in hires.items()),"SKILL_HIRE")
        flows={k:0 for k in ("hire_j","hire_s","quit_j","quit_s","layoff_j","layoff_s","other_j","other_s")}
        for k,v in exits.items():
            flows[v[1].lower()+"_"+people[k]["role"][0].lower()]+=1;del people[k]
        require(len(q.assessments_passed)==len(set(q.assessments_passed)),"DUPLICATE_ASSESSMENT")
        eligible=sorted(k for k,p in people.items() if p["role"]=="JUNIOR" and q.index-p["entered"]>=r.min_quarters and p["formal"]>=r.formal_seconds and p["practice"]>=r.practice_seconds)
        require(set(q.assessments_passed)<=set(eligible),"PREMATURE_QUALIFICATION")
        for k in q.assessments_passed:people[k]["role"]="SENIOR"
        for k,v in hires.items():
            flows["hire_"+v[1][0].lower()]+=1;people[k]={"role":v[1],"entered":q.index,"formal":0,"practice":0};seen.add(k)
        require(len(people)<=1000,"WORKER_LIMIT")
        remaining={k:w.seconds_per_person for k in people}
        def use(k,n):
            require(k in remaining and integer(n,0,w.seconds_per_person) and n<=remaining[k],"PERSON_TIME_CAPACITY")
            remaining[k]-=n
        prod=unique(q.production,lambda x:x[0]);production=0
        for k,v in prod.items():use(k,v[1]);production+=v[1]
        training=0;practice=0;mentor=0
        for k,l in unique(q.learning,lambda x:x.worker).items():
            require(k in people and people[k]["role"]=="JUNIOR" and l.mentor in people and people[l.mentor]["role"]=="SENIOR","MENTOR_ROLE")
            require(all(integer(x,0,w.seconds_per_person) for x in (l.formal_seconds,l.practice_seconds,l.mentor_seconds)) and l.formal_seconds+l.practice_seconds>0 and l.mentor_seconds*10000>=l.practice_seconds*r.mentor_basis_points,"MENTOR_REQUIREMENT")
            use(k,l.formal_seconds+l.practice_seconds);use(l.mentor,l.mentor_seconds)
            people[k]["formal"]+=l.formal_seconds;people[k]["practice"]+=l.practice_seconds
            training+=l.formal_seconds+l.practice_seconds+l.mentor_seconds;practice+=l.practice_seconds;mentor+=l.mentor_seconds
        # The previous transition contract asks for positive current training
        # if promotion occurs. Reserve explicit assessment time instead of
        # fabricating new training. One hour per scripted passed assessment.
        assessment_seconds=0
        for k in q.assessments_passed:use(k,3600);assessment_seconds+=3600
        training+=assessment_seconds
        expert_available=sum(remaining[k] for k,p in people.items() if p["role"]=="SENIOR")
        served=min(q.expert_demand_seconds,expert_available)
        junior=sum(p["role"]=="JUNIOR" for p in people.values());senior=len(people)-junior
        require(production+training+served<=len(people)*w.seconds_per_person,"TOTAL_TIME")
        require(t.redeployed_seconds==0,"REDEPLOYMENT_DOUBLE_COUNT")
        quarters.append(replace(t,**flows,promote=len(q.assessments_passed),training_seconds=training,redeployed_seconds=served))
        rows.append({"quarter":q.index,"junior":junior,"senior":senior,"eligible_at_start":eligible,"promoted":len(q.assessments_passed),"practice_seconds":practice,"mentor_seconds":mentor,"assessment_seconds":assessment_seconds,"training_seconds":training,"production_seconds":production,"expert_available_seconds":expert_available,"expert_demand_seconds":q.expert_demand_seconds,"expert_served_seconds":served,"expert_shortfall_seconds":q.expert_demand_seconds-served,"workers":{k:dict(p) for k,p in sorted(people.items())}})
    return replace(template,quarters=tuple(quarters)),rows

def evaluate(base,reference,phases,template,skills):
    plan,rows=compile_plan(template,skills)
    receipt=simulate(base,reference,phases,plan);x=receipt["result"]
    for k,t in zip(rows,x["quarters"]):
        require((k["junior"],k["senior"],k["production_seconds"],k["training_seconds"],k["expert_served_seconds"])==(t["junior"],t["senior"],t["allocated_production_seconds"],t["training_seconds"],t["redeployed_seconds"]),"TRANSITION_SKILL_RECONCILIATION")
    r={"skills_ref":skills.key,"skill_rows":rows,"transition":receipt,"ending_experts":rows[-1]["senior"],"total_expert_shortfall_hours":str(F(sum(q["expert_shortfall_seconds"] for q in rows),3600)),"total_expert_served_hours":str(F(sum(q["expert_served_seconds"] for q in rows),3600)),"total_promotions":sum(q["promoted"] for q in rows),"skill_input_sha256":digest(canonical(asdict(skills))),"assumptions":skills.assumptions,"qualification":"SCRIPTED_NOT_CERTIFIED","publication":"BLOCK_PUBLICATION"}
    return {"result":r,"sha256":digest(canonical(r))}

def valuation(result,quarterly_discount_bp,terminal_asset_cents=0,settle_trade=True):
    from .economic_transition import valuation as value_transition
    v=value_transition(result["transition"],quarterly_discount_bp,terminal_asset_cents,settle_trade)
    rate=1+F(quarterly_discount_bp,10000)
    hours=sum(F(k["expert_served_seconds"],3600)/rate**k["quarter"] for k in result["skill_rows"])
    return {**v,"discounted_expert_hours":str(hours)}

def compare_skills(base,reference,phases,a,sa,b,sb,rate=200,terminal_assets=(0,0)):
    require(a.workforce==b.workforce and sa.initial==sb.initial and (a.opening_cash_cents,a.opening_receivable_cents,a.opening_payable_cents,a.opening_debt_cents,a.collection_next_quarter_bp,a.supplier_next_quarter_bp,a.quarterly_interest_bp)==(b.opening_cash_cents,b.opening_receivable_cents,b.opening_payable_cents,b.opening_debt_cents,b.collection_next_quarter_bp,b.supplier_next_quarter_bp,b.quarterly_interest_bp) and [(q.index,q.repeats) for q in a.quarters]==[(q.index,q.repeats) for q in b.quarters] and [q.expert_demand_seconds for q in sa.quarters]==[q.expert_demand_seconds for q in sb.quarters],"SKILL_COMPARABILITY")
    x=evaluate(base,reference,phases,a,sa);y=evaluate(base,reference,phases,b,sb)
    u=valuation(x["result"],rate,terminal_assets[0]);v=valuation(y["result"],rate,terminal_assets[1])
    delta=F(v["npv_eur"])-F(u["npv_eur"]);h=F(v["discounted_expert_hours"])-F(u["discounted_expert_hours"])
    r={"baseline":x,"alternative":y,"baseline_valuation":u,"alternative_valuation":v,"incremental_unlevered_npv_eur":str(delta),"incremental_discounted_expert_hours":str(h),"expert_hour_break_even_eur":str(max(F(0),-delta/h)) if h>0 else None,"funding_status_both":[z["result"]["transition"]["result"]["funding_status"] for z in (x,y)],"model_sha256":digest(Path(__file__).read_bytes()),"publication":"BLOCK_PUBLICATION"}
    return {"result":r,"sha256":digest(canonical(r))}
