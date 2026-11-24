"""W002 skills: same robot adoption and market, different recruitment/learning paths."""
from dataclasses import replace
from .economic_skills import *
from .economic_transition_pilot import fixture as transition_fixture
from .economic_physical_pilot import make
from .work_graph import build

def fixture(process):
    ref,phases,b,alts=transition_fixture(process)
    template=alts[0]
    # Reset all movements; they are compiled from named synthetic slots.
    template=replace(template,quarters=tuple(replace(q,budgeted_hires=1 if q.index==2 else 0,frozen_hires=0,hire_j=0,hire_s=0,quit_j=0,quit_s=0,other_j=0,other_s=0,layoff_j=0,layoff_s=0,promote=0,training_seconds=0,redeployed_seconds=0,training_cents=0) for q in template.quarters))
    def scenario(name,hire,fast=False):
        rule=Rule(2 if fast else 3,20*3600 if fast else 30*3600,80*3600 if fast else 120*3600,2500)
        qs=[];ts=[]
        for t in template.quarters:
            i=t.index;learn=hire and i in ((2,3) if fast else (2,3,4))
            qs.append(SkillQuarter(i,(("new","JUNIOR"),) if i==2 and hire else (), (("j","QUIT"),) if i==4 else (("s","OTHER"),) if i==5 else (),("new",) if hire and i==(4 if fast else 5) else (), (Learning("new",10*3600,40*3600,"s",10*3600),) if learn else (), (("j",900000),) if i<=2 else (), (300 if i==4 else 125)*3600))
            ts.append(replace(t,frozen_hires=1 if i==2 and not hire else 0,training_cents=50000 if learn else 0))
        plan=replace(template,id="skills-finance:"+name,quarters=tuple(ts))
        skill=SkillPlan("skills:"+name,1,(("j","JUNIOR"),("s","SENIOR")),rule,tuple(qs),"Fictif: même processus W002 et ventes, expertise distincte demandée 125 h/trimestre (300 au T4), formation et évaluation hypothétiques, aucune valeur économique du service expert présumée.")
        return plan,skill
    return ref,phases,scenario("freeze",False),(scenario("renew",True),scenario("accelerated",True,True))

def audit(process):
    ref,phases,b,alts=fixture(process);out={}
    for a in alts:
        r=compare_skills(process,ref,phases,*b,*a);assert r==compare_skills(process,ref,phases,*b,*a)
        x=r["result"];out[a[1].id]={"result":x,"sha256":r["sha256"]}
    # Sensitivity: compare the same paths at three discount rates; compare
    # a matched capex stress in both paths (same investment), no probabilities.
    sensitivity=[]
    for rate in (0,200,500):
        for a in alts:
            x=compare_skills(process,ref,phases,*b,*a,rate=rate)["result"]
            sensitivity.append({"quarterly_rate_bp":rate,"alternative":a[1].id,"incremental_npv_eur":x["incremental_unlevered_npv_eur"],"expert_hour_break_even_eur":x["expert_hour_break_even_eur"]})
    from .economic_terminology import present
    return {"fixture":"W002_SKILLS_SYNTHETIC","comparisons":out,"sensitivity":sensitivity,"terminology":present(out[alts[0][1].id]["result"]["alternative"]["result"],("ending_experts","total_expert_shortfall_hours","total_expert_served_hours","total_promotions")),"scientific_gate_promoted":False,"publication":"BLOCK_PUBLICATION"}
if __name__=="__main__":
    import json
    p,_=make(build());print(json.dumps(audit(p),ensure_ascii=False,indent=2))
