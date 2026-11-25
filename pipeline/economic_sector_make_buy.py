"""G4 v0.4b: recurring make/buy accounting, synthetic only.
External suppliers' costs stay in a separate G3 consolidated ledger; never add to G4.
"""
from dataclasses import dataclass,replace
from fractions import Fraction as F
from .economic_core import canonical,digest
from .economic_market import run
from .economic_firm import ledger
from .economic_transform import compare_design
from .economic_sector_structural import state,compare,validate
from .economic_sector_market_bridge import require,positive

@dataclass(frozen=True)
class Allocation:
    category:str
    origin:str
    product:str
    share:str

@dataclass(frozen=True)
class MakeBuyMapping:
    service:str
    buyer:str
    reference_price_eur:str
    periods:int
    cohorts:str
    allocations:tuple
    evidence:str
    status:str="SYNTHETIC_CONDITIONAL"

def internal_ledger(m,r):
    x=r["result"]; i=m.internal_production
    if x["internalized_units"]==0:
        require(i is None,"INTERNAL_SCOPE")
        return {"payroll":F(0),"costs":{},"capital":F(0),"transition":F(0),"cash":F(0),"paid":0,"unused":0}
    require(i is not None and x["internalization_status"]=="CONDITIONAL_REPLAY","INTERNAL_UNQUALIFIED")
    s=next(s for s in m.sellers if s.id==i.reference_seller)
    bp,bs,bd,bc=s.reference;ip,ins,ind,inc=i.process
    op=compare_design(bp,bs,bd,ip,ins,ind)
    require(op["sha256"]==x["internal_production"]["operation_sha256"],"REPLAY")
    l=ledger(op["result"]["alternative"],replace(inc,max_sales=x["internalized_units"],price_cents_per_sale=0))
    require(l["sales"]==x["internalized_units"] and F(l["cash_cost_eur"])==F(x["internal_production"]["cash_cost_eur"]),"LEDGER")
    costs={"running":F(l["machine_running_eur"]),"intake":F(l["intake_eur"]),"error":F(l["error_cost_eur"])}
    costs.update({"fixed:"+k:F(v) for k,v in l["fixed_cash_costs_eur"].items()})
    pay=F(l["payroll_eur"]);cash=F(l["cash_cost_eur"])
    require(pay+sum(costs.values())==cash,"COST_COVERAGE")
    return {"payroll":pay,"costs":costs,"capital":F(inc.investment_cents,100),"transition":F(inc.transition_cents,100),"cash":cash,"paid":l["paid_human_seconds"],"unused":l["unsold_correct_outputs"]}

def bridge(base,before,after,m):
    require(base.origin=="SYNTHETIC" and m.status=="SYNTHETIC_CONDITIONAL","ADMISSION")
    require(m.service in base.codes and m.buyer in base.codes and m.service!=m.buyer,"AXIS")
    require(isinstance(m.evidence,str) and m.evidence.strip(),"EVIDENCE")
    require(before.definition==after.definition and before.sellers==after.sellers and before.policies==after.policies and before.ownership==after.ownership,"MATCHED_MARKET")
    require(type(m.periods) is int and 0<m.periods<=10000,"PERIOD")
    p=positive(m.reference_price_eur,"PRICE"); n=positive(m.cohorts,"COHORTS")
    require(n<=10**9 and p<=10**9,"SCALE")
    for s in before.sellers:
        require(all(v[3].periods_per_year==m.periods and v[1].horizon*m.periods<=366*86400 for v in (s.reference,s.alternative)),"NATIVE_PERIOD")
    for market in (before,after):
        if market.internal_production:
            v=market.internal_production.process
            require(v[3].periods_per_year==m.periods and v[1].horizon*m.periods<=366*86400,"NATIVE_PERIOD")
    a,b=run(before),run(after);x,z=a["result"],b["result"]
    require(x["scope"]==z["scope"] and x["output_contract"]==z["output_contract"],"OUTPUT_CONTRACT")
    require(x["potential_demand"]==z["potential_demand"] and x["unserved"]==z["unserved"]==0,"MATCHED_FULFILMENT")
    require(all(F(r["baseline_price_eur"])==p for r in x["sellers"]+z["sellers"]),"REFERENCE_PRICE")
    u,v=internal_ledger(before,a),internal_ledger(after,b)
    cats=set(u["costs"])|set(v["costs"]);weights={k:F(0) for k in cats};seen=set()
    for row in m.allocations:
        key=(row.category,row.origin,row.product)
        require(key not in seen and row.category in cats and row.product in base.codes and row.origin in ("DOMESTIC","IMPORTED"),"ALLOCATION")
        seen.add(key);weights[row.category]+=positive(row.share,"SHARE")
    require(all(w==1 for w in weights.values()),"ALLOCATION_COVERAGE")
    # All recurring nonpayroll components mapped as CI under explicit synthetic valuation assumptions.
    # Internal output is ancillary, not a new sale or new final use.
    factor=n*m.periods/10**6; capfactor=n/10**6
    ref=state(base);j=base.codes.index(m.buyer);i=base.codes.index(m.service);g=ref["g"][j]
    require(g>0,"BUYER_OUTPUT")
    B=[list(r) for r in base.domestic];M=[list(r) for r in base.imported];w=list(base.wage);k=list(base.surplus)
    # Check all baseline mapped flows jointly, including possible overlap with the external service.
    oldD={i:p*x["sales"]*factor};newD={i:p*z["sales"]*factor};oldM={};newM={}
    for row in m.allocations:
        dest=base.codes.index(row.product);share=F(row.share)
        d0,d1=(oldD,newD) if row.origin=="DOMESTIC" else (oldM,newM)
        d0[dest]=d0.get(dest,F(0))+u["costs"].get(row.category,F(0))*share*factor
        d1[dest]=d1.get(dest,F(0))+v["costs"].get(row.category,F(0))*share*factor
    for old,new,arr,orig in [(oldD,newD,B,base.domestic),(oldM,newM,M,base.imported)]:
        for ix in set(old)|set(new):
            require(float(old.get(ix,0))<=orig[ix][j]*g+1e-9,"BASE_COVERAGE")
            arr[ix][j]+=float(new.get(ix,0)-old.get(ix,0))/g
    pay0=u["payroll"]*factor;pay1=v["payroll"]*factor
    require(float(pay0)<=base.wage[j]*g+1e-9,"PAYROLL_COVERAGE")
    dw=float(pay1-pay0)/g;w[j]+=dw
    dd=sum(newD.values())-sum(oldD.values());dm=sum(newM.values())-sum(oldM.values())
    k[j]-=float(dd+dm)/g+dw
    t=replace(base,domestic=tuple(map(tuple,B)),imported=tuple(map(tuple,M)),wage=tuple(w),surplus=tuple(k))
    validate(t);r=compare(base,t)
    def consolidated(y,l):
        seller_pay=sum(F(row["payroll_eur"]) for row in y["sellers"])
        seller_non=sum(F(row["nonpayroll_eur"]) for row in y["sellers"])
        external=F(y["external_purchase_spend_eur"])
        buyer=external+l["cash"];seller= seller_pay+seller_non
        require(buyer+seller-external==F(y["direct_chain_cash_cost_eur"]),"CHAIN_CASH")
        return {"external_transfer_eur":str(external),"buyer_cash_eur":str(buyer),"seller_cash_cost_eur":str(seller),"consolidated_cash_cost_eur":str(seller+l["cash"]),"consolidated_payroll_eur":str(seller_pay+l["payroll"]),"paid_hours":y["direct_chain_paid_hours"],"active_hours":y["direct_chain_active_hours"],"external_unsold":y["unsold_correct_outputs"],"internal_unused":l["unused"]}
    out={"status":"SYNTHETIC_MAKE_BUY_CONDITIONAL","publication":"BLOCK_PUBLICATION","receipts":{"before":a["sha256"],"after":b["sha256"]},"quantities":{"total":x["potential_demand"],"external_before":x["sales"],"external_after":z["sales"],"internal_before":x["internalized_units"],"internal_after":z["internalized_units"]},"direct_chain":{"before":consolidated(x,u),"after":consolidated(z,v)},"recurring_buyer_reference_mEUR":{"external_delta":str(p*(z["sales"]-x["sales"])*factor),"domestic_inputs_delta":str(dd),"imported_inputs_delta":str(dm),"payroll_delta":str(pay1-pay0),"gross_surplus_residual_at_base_output":str(-dd-dm-pay1+pay0)},"capital_separate_mEUR":{"investment_delta":str((v["capital"]-u["capital"])*capfactor),"transition_delta":str((v["transition"]-u["transition"])*capfactor)},"sector":r,"assumptions":{"factor_mEUR_per_eur_period":str(factor),"allocations":[row.__dict__ for row in m.allocations],"evidence":m.evidence},"limitations":["recurring buyer-side coefficients only; seller ledger separate, not added","G3 payroll assumed D1, running and other cash costs assumed CI at reference prices","internal activity assumed ancillary to unchanged buyer product contract","unsold/unused cohorts charged in G3, stocks not mapped to G4","capital and transition kept separate; no GFCF or depreciation forecast","no empirical scaling, employment or realized output"]}
    return {"result":out,"sha256":digest(canonical(out))}
