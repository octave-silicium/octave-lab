"""One fictional service market with three competitors; not a real market definition."""
from dataclasses import replace
from .economic_market import Market,Seller,Policy,run
from .economic_firm_pilot import fixture
from .economic_physical_pilot import make
from .work_graph import build

def cases(process):
    b,bc,alts,_=fixture(process)
    ref=(*b,bc);alt=(*alts[2][0],alts[2][1]);alt2=(*alts[3][0],alts[3][1])
    ss=tuple(Seller(k,ref,alt2 if k=="C" else alt,12) for k in ("A","B","C"))
    def plan(name,adopters=(),rho=10000,elasticity=10000,internal=0,sat=72,pref=0,markdown=0):
        ps=tuple(Policy(s.id,s.id in adopters,rho,markdown if s.id in adopters else 0,s.id not in adopters,pref if s.id not in adopters else 0) for s in ss)
        return Market("market:"+name,1,"Marché fictif fermé de rapports de contrôle dimensionnel comparables, trois fournisseurs, même cohorte temporelle et géographique",ss,elasticity,sat,2,internal,ps,"Fictif, production de cohortes déjà engagée, coûts moyens de trésorerie par rapport correct, règle de prix et allocation non estimées, aucun coût d'internalisation ni surplus consommateur calculé.")
    return (plan("reference"),plan("first-mover",("A",)),plan("diffusion",("A","B","C")),plan("low-demand",("A","B","C"),elasticity=0),plan("internalization",("A","B","C"),internal=12),plan("human-preference",("A",),pref=3000),plan("retain-gain",("A",),rho=0),plan("saturation",("A","B","C"),elasticity=40000,sat=40))

def audit(process):
    out={}
    for m in cases(process):
        r=run(m);assert r==run(m);out[m.id]=r
    from .economic_terminology import present
    keys=("potential_demand","external_demand","internalized_units","price_induced_demand_change","fixed_basket_price_index","volume_hhi","cash_surplus_delta_eur","paid_hours_delta")
    return {"fixture":"W002_MARKET_SYNTHETIC","cases":out,"terminology":present(out["market:first-mover"]["result"],keys),"scientific_gate_promoted":False,"publication":"BLOCK_PUBLICATION"}

if __name__=="__main__":
    import json
    p,_=make(build());print(json.dumps(audit(p),ensure_ascii=False,indent=2))
