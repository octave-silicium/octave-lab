"""Post-exit and make/buy bridge, using the existing market contract."""
from dataclasses import replace
from .economic_market import run,trajectory,InternalProduction,Seller,Policy
from .economic_market_dynamics_pilot import plans
from .economic_market_pilot import cases
from .economic_physical_pilot import make
from .work_graph import build

def audit(process):
    d=replace(plans(process)[1],id="market-dynamics:extended",quarters=10)
    trace=trajectory(d);assert trace==trajectory(d)
    ms=cases(process)
    m=ms[1]
    exit=run(m,("B",))
    entrant=Seller("D",m.sellers[0].reference,m.sellers[2].alternative,0,12)
    entry_market=replace(m,id="market:post-exit-entry",sellers=m.sellers+(entrant,),policies=m.policies+(Policy("D",True,10000,0,False,0),))
    entry=run(entry_market,("B",))
    control=run(replace(entry_market,ownership=(("A","group-AC"),("B","B"),("C","group-AC"),("D","D"))),("B",))
    # Same internal quantity, comparable manual or automated internal process.
    internal=ms[4];ref=internal.sellers[0].reference;auto=internal.sellers[0].alternative
    manual=run(replace(internal,id="market:make-manual",internal_production=InternalProduction("A",ref,"Fictif: nouvelle cohorte dédiée chez les clients, indépendance des ressources, coût complet récurrent de la cohorte; pas de prix de vente interne.")))
    automated=run(replace(internal,id="market:make-auto",internal_production=InternalProduction("A",auto,"Fictif: nouvelle cohorte dédiée chez les clients, indépendance des ressources, coût complet récurrent de la cohorte; pas de prix de vente interne.")))
    r={"fixture":"W002_MARKET_BOUNDARY","extended_trajectory":trace,"cases":{"exit":exit,"entry":entry,"control_consolidation":control,"external_only":run(ms[2]),"internal_unqualified":run(internal),"internal_manual":manual,"internal_automated":automated},"publication":"BLOCK_PUBLICATION","scientific_gate_promoted":False}
    return r
if __name__=="__main__":
    import json
    p,_=make(build());print(json.dumps(audit(p),ensure_ascii=False,indent=2))
