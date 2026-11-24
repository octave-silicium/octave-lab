"""W002 conditional financial scenarios; price is for inspection service, not value of part."""
from dataclasses import replace
from .economic_firm import Economics,ResourceCost,assess
from .economic_physical_pilot import make,variants
from .work_graph import build
from .economic_operations import process_pin

def fixture(process):
    base,alts=variants(process)
    def cfg(name,scenario,capex=0,transition=0,paid=7200,license=0,sales=36,price=1200,opening=2500000):
        p,s,d=scenario
        return Economics("firm:"+name,1,s.key,price,sales,50,5000,tuple(ResourceCost(pool.id,paid if pool.kind=="HUMAN" else 0,4000 if pool.kind=="HUMAN" else 0,{"gauge":800,"software":200,"robot":500}.get(pool.id,0)) for pool in s.pools),(("overhead",3000),("license_maintenance",license)),100000,capex,transition,0,500,5,800,opening,"Fictif: prestation de contrôle par rapport correct vendu, cohortes indépendantes répétées 500 fois/an, pas de report des dossiers inachevés, encaissement immédiat, EUR nominaux constants, hors impôt/dette/BFR. Aucun coût d'opportunité ou redéploiement monétisé.")
    def release(scenario):
        p,s,d=scenario
        s=replace(s,id=s.id+"-paid-release",pools=tuple(replace(pool,servers=tuple(replace(v,windows=()) for v in pool.servers)) if pool.kind=="HUMAN" else pool for pool in s.pools))
        return p,s,replace(d,id=d.id+"-paid-release")
    digital=alts[0];robot=alts[1];robot2=alts[2];rel=release(robot);rel2=release(robot2)
    return base,cfg("baseline",base),((digital,cfg("digital",digital,500000,100000,license=500)),(robot,cfg("robot-retain",robot,4000000,200000,license=1000)),(rel,cfg("robot-release",rel,4000000,200000,paid=0,license=1000)),(rel2,cfg("robot-two-instruments",rel2,5500000,250000,paid=0,license=1500))),cfg

def audit(process):
    b,bc,alts,cfg=fixture(process);rows={}
    fields=("sales","correct_outputs","paid_human_seconds","active_human_seconds","revenue_eur","payroll_eur","cash_cost_eur","cash_operating_surplus_eur","accounting_operating_result_eur","cost_per_correct_output_eur","annual_cash_surplus_eur","npv_eur","funding_gap_at_sampled_dates_eur")
    metrics=("incremental_npv_eur","incremental_revenue_eur","incremental_cash_surplus_eur","incremental_accounting_result_eur","payroll_saving_eur","active_human_seconds_released","max_incremental_investment_at_zero_npv_eur","sustained_payback_year")
    for scenario,ac in alts:
        r=assess(process,b[1],b[2],bc,*scenario,ac);assert r==assess(process,b[1],b[2],bc,*scenario,ac)
        z=r["result"];rows[ac.id]={"baseline":{k:z["baseline"][k] for k in fields},"alternative":{k:z["alternative"][k] for k in fields},"comparison":{k:z[k] for k in metrics},"receipt_sha256":r["sha256"]}
    # Demand-constrained comparison: same sales ceiling of 23, even if output is 36.
    s,ac=alts[-1];r=assess(process,b[1],b[2],replace(bc,max_sales=23),*s,replace(ac,max_sales=23))
    z=r["result"];rows["limited_sales"]={"baseline":{k:z["baseline"][k] for k in fields},"alternative":{k:z["alternative"][k] for k in fields},"comparison":{k:z[k] for k in metrics},"receipt_sha256":r["sha256"]}
    from .economic_terminology import present
    return {"fixture":"W002_FIRM_SYNTHETIC","process_sha256":process_pin(process),"cases":rows,"terminology":present(z,metrics),"scientific_gate_promoted":False,"publication":"BLOCK_PUBLICATION"}
if __name__=="__main__":
    import json
    p,_=make(build());print(json.dumps(audit(p),ensure_ascii=False,indent=2))
