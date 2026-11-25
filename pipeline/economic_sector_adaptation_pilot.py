"""Illustrative adaptive paths; exact hand-derived expected outcomes."""
from dataclasses import replace
from .economic_sector_structural import Structure
from .economic_sector_capacity_dynamics import Period
from .economic_sector_adaptation import CapacityRule,SubstitutionRule,adapt

def audit():
    s=Structure(("A","B"),((0,.5),(0,0)),((0,0),(0,.2)),((1,0),(0,1)),(.5,.1),(0,0),(0,0),(.5,.2),(100,100),"SYNTHETIC")
    p=Period(s,(0,20),(("A","B"),),"Synthetic homogeneous products")
    short=replace(p,deliveries=(0,10))
    low=replace(p,structure=replace(s,final=(30,30)))
    rule=CapacityRule("A",1,2,.01,.6,30,60,200,"DEMAND_CONFIRMED","Hypothetical management rule")
    naive=replace(rule,retirement_signal="UTILIZATION_ONLY")
    sub=SubstitutionRule("B","A","B",1,1,.1,.2,"Hypothetical technical equivalence at fixed reference price")
    cases={}
    specs=[
        ("persistent_capacity_gap",(p,)*5,(120,100),(rule,),(),[160,160,200,200,200]),
        ("temporary_demand_then_overshoot",(p,p,low,low,low,p),(120,100),(rule,),(),[160,160,60,60,60,160]),
        ("import_shortage_confirmed",(short,short,p,p,p),(150,100),(rule,),(),[100,100,200,200,200]),
        ("import_shortage_naive",(short,short,p,p,p),(150,100),(naive,),(),[100,100,160,160,200]),
        ("substitution_without_expansion",(short,)*5,(150,100),(),(sub,),[100,187.5,187.5,187.5,187.5]),
        ("substitution_with_expansion",(short,)*5,(150,100),(rule,),(sub,),[100,187.5,187.5,200,200])]
    for name,ps,cap,rs,ss,expected in specs:
        receipt=adapt(ps,cap,(0,0),rs,ss,period_unit="QUARTER",evidence="Synthetic scenario; no empirical estimates")
        result=receipt["result"];rows=result["dynamic"]["periods"]
        served=[sum(r["served_final"]) for r in rows]
        assert all(abs(a-b)<1e-7 for a,b in zip(served,expected)),(name,served,expected)
        cases[name]={"sha256":receipt["sha256"],"served":served,"expected":expected,
          "requested":[sum(r["served_final"])+sum(r["unserved_final"]) for r in rows],
          "capacity_A":[r["capacity"][0] for r in rows],"idle_A":[r["idle_capacity"][0] for r in rows],
          "closing_import_stock_B":[r["closing_stock"][1] for r in rows],
          "decisions":result["decisions"],"substitution_orders":result["substitution_orders"],
          "cumulative_unserved":result["dynamic"]["cumulative_unserved_final"]}
    return {"status":"SYNTHETIC_ADAPTIVE_RULE_AUDIT","publication":"BLOCK_PUBLICATION","cases":cases,"verification":"Analytical expected trajectories compared to G4 replay; not empirical calibration"}

if __name__=="__main__":
    import json
    print(json.dumps(audit(),indent=2))
