"""W002 eight-quarter transition, invented inputs, not actual workshop staffing."""
from dataclasses import replace
from .economic_transition import Workforce,Quarter,Plan,simulate,compare
from .economic_firm_pilot import fixture as firm_fixture
from .economic_physical_pilot import make
from .work_graph import build

def fixture(process):
    b,bc,alts,_=firm_fixture(process)
    reference=(*b,bc)
    p,s,d=alts[2][0];robot=(p,s,d,alts[2][1])
    phases={"reference":reference,"robot":robot}
    w=Workforce(1,1,900000,3000,4000)
    def q(i,phase="reference",**kw):
        defaults=dict(index=i,phase=phase,repeats=125,budgeted_hires=0,frozen_hires=0,hire_j=0,hire_s=0,quit_j=0,quit_s=0,layoff_j=0,layoff_s=0,other_j=0,other_s=0,promote=0,training_seconds=0,redeployed_seconds=0,training_cents=0,exit_cents=0,capex_cents=0,transition_cents=0,debt_draw_cents=0,principal_repaid_cents=0)
        return Quarter(**(defaults|kw))
    note="Scénario fictif, postes à temps partiel de 250 h/trimestre; mouvements au début de chaque trimestre; production répétée de cohortes indépendantes, dossiers inachevés transférés hors périmètre, sans coût explicite; aucune valeur de réaffectation incluse; encaissements/paiements restants le trimestre suivant, pas d'impôt ni stocks physiques; solde négatif = besoin non financé, pas continuation viable démontrée."
    def plan(name,qs,dates=(None,None,None,None)):
        return Plan("transition:"+name,1,w,2500000,0,0,0,5000,2500,200,*dates,tuple(qs),note)
    baseline=plan("reference",[q(1),q(2,budgeted_hires=1,hire_j=1),q(3,other_s=1),q(4,promote=1,training_seconds=18000,training_cents=50000),q(5,quit_j=1,budgeted_hires=1,hire_j=1),q(6),q(7),q(8)])
    def alt(name,mode,financed):
        qs=[q(1),q(2,budgeted_hires=1,frozen_hires=1,capex_cents=4000000,transition_cents=200000,debt_draw_cents=3500000 if financed else 0)]
        qs.append(q(3,"robot",other_s=1,redeployed_seconds=450000 if mode=="retain" else 0))
        qs.append(q(4,"robot",promote=1,training_seconds=18000,training_cents=50000,redeployed_seconds=450000 if mode=="retain" else 0) if mode=="retain" else q(4,"robot"))
        for i in range(5,9):
            extra={}
            if i==5 and mode=="attrition":extra={"quit_j":1,"budgeted_hires":1,"frozen_hires":1}
            if i==5 and mode=="retain":extra={"quit_s":1,"budgeted_hires":1,"hire_j":1}
            if mode=="retain":extra["redeployed_seconds"]=450000
            if financed:extra["principal_repaid_cents"]=500000
            qs.append(q(i,"robot",**extra))
        return plan(name,qs,(1,2,2,3))
    return reference,phases,baseline,(alt("attrition", "attrition",True),alt("retain","retain",True),alt("unfinanced","attrition",False))

def audit(process):
    ref,phases,b,alts=fixture(process);out={}
    for a in alts:
        r=compare(process,ref,phases,b,a);assert r==compare(process,ref,phases,b,a)
        x=r["result"];out[a.id]={"baseline":x["baseline"]["result"],"alternative":x["alternative"]["result"],"headcount_gap":x["headcount_gap"],"hires_gap":x["hires_gap"],"layoffs_gap":x["layoffs_gap"],"quarterly_gaps":x["quarterly_gaps"],"sha256":r["sha256"]}
    from .economic_terminology import present
    metrics=("ending_headcount","cumulative_hires","cumulative_layoffs","cumulative_frozen_hires","closing_cash_eur","closing_debt_eur","funding_gap_at_sampled_dates_eur")
    return {"fixture":"W002_TRANSITION_SYNTHETIC","comparisons":out,"terminology":present(out[alts[0].id]["alternative"],metrics),"publication":"BLOCK_PUBLICATION","scientific_gate_promoted":False}
if __name__=="__main__":
    import json
    p,_=make(build());print(json.dumps(audit(p),ensure_ascii=False,indent=2))
