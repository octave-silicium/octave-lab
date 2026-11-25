"""Dynamic extension of W002 market, not a new simulator."""
from dataclasses import replace
from .economic_market import Dynamics,Strategy,trajectory
from .economic_market_pilot import cases
from .economic_physical_pilot import make
from .work_graph import build

def plans(process):
    m=cases(process)[0]
    ss=(Strategy("A",6000000,0,1,0,6,500000,0),
        Strategy("B",1000000,0,2,100,8,500000,0),
        Strategy("C",6500000,0,3,100,8,500000,0))
    d=Dynamics("market-dynamics:constrained",1,m,ss,8,125,0,0,200, "Fictif: prix et volumes par cohorte, 125 cohortes indépendantes/trimestre, paie imputée au procédé, anticipation statique de surplus à partir du marché précédent, coût d'investissement et transition G3.3, réserve à l'adoption, crédit engagé plafonné, cessation de l'offre après déficit non financé. Pas de liquidation ni effectif déduit.")
    return (replace(d,id="market-dynamics:no-adoption",strategies=tuple(replace(s,earliest_adoption=0) for s in ss)),d,replace(d,id="market-dynamics:funded",strategies=tuple(replace(s,credit_limit_cents=5000000) if s.seller=="B" else s for s in ss)))

def audit(process):
    out={}
    for d in plans(process):
        r=trajectory(d);assert r==trajectory(d);out[d.id]=r
    return {"fixture":"W002_MARKET_DYNAMICS","cases":out,"scientific_gate_promoted":False,"publication":"BLOCK_PUBLICATION"}
if __name__=="__main__":
    import json
    p,_=make(build());print(json.dumps(audit(p),ensure_ascii=False,indent=2))
