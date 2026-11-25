"""G3.4 v0.1. Conditional market accounting from replayed operations.
A defined single service, fixed cohort production, explicit price and allocation rules.
Not an estimated demand system, marginal-cost model or equilibrium solver.
"""
from dataclasses import dataclass,asdict,replace
from fractions import Fraction as F
from pathlib import Path
from .economic_core import require,words,identity,unique,canonical,digest
from .economic_events import integer
from .economic_firm import ledger
from .economic_transform import compare_design

@dataclass(frozen=True)
class Seller:
    id:str
    reference:tuple # process, schedule, design, economics
    alternative:tuple
    baseline_sales:int

@dataclass(frozen=True)
class Policy:
    seller:str
    adopted:bool
    pass_through_bp:int
    price_adjustment_cents:int
    human_provenance:bool
    preference_discount_bp:int # buyers' hypothetical effective price discount, not actual price

@dataclass(frozen=True)
class Market:
    id:str
    revision:int
    definition:str
    sellers:tuple
    demand_elasticity_bp:int # local linear response, absolute magnitude
    saturation_units:int
    substitution_power:int # sensitivity of allocation weights to relative effective prices
    internalized_units:int # explicit conditional quantity, not causal prediction
    policies:tuple
    assumptions:str
    @property
    def key(self):return identity(self.id,self.revision)

def allocate(demand,weights,caps):
    """Integer proportional allocation with capacity rationing and redistribution."""
    require(integer(demand,0,10**9) and set(weights)==set(caps) and all(v>0 for v in weights.values()) and all(integer(v,0,10**9) for v in caps.values()),"ALLOCATION_INPUT")
    out={k:0 for k in sorted(weights)};left=min(demand,sum(caps.values()))
    while left:
        active=[k for k in out if out[k]<caps[k]]
        require(bool(active),"ALLOCATION_CAPACITY")
        mass=sum(weights[k] for k in active)
        ideals={k:left*weights[k]/mass for k in active}
        # Fill capped participants first, then redistribute remaining demand.
        full=[k for k in active if ideals[k]>=caps[k]-out[k]]
        if full:
            for k in full:
                take=caps[k]-out[k];out[k]+=take;left-=take
            continue
        counts={k:int(ideals[k]) for k in active}
        for k,n in counts.items():out[k]+=n;left-=n
        for k in sorted(active,key=lambda k:(-(ideals[k]-counts[k]),k))[:left]:out[k]+=1
        left=0
    require(sum(out.values())==min(demand,sum(caps.values())) and all(out[k]<=caps[k] for k in out),"ALLOCATION_CONSERVATION")
    return out

def run(m):
    m.key
    require(words(m.definition) and words(m.assumptions) and 2<=len(m.sellers)<=100 and integer(m.demand_elasticity_bp,0,100000) and integer(m.saturation_units,1,10**9) and integer(m.substitution_power,0,4) and integer(m.internalized_units,0,10**9),"MARKET")
    sellers=unique(m.sellers,lambda s:s.id);policies=unique(m.policies,lambda p:p.seller)
    require(set(sellers)==set(policies),"SELLER_POLICY")
    baseline=sum(s.baseline_sales for s in sellers.values())
    require(0<baseline<=m.saturation_units,"BASELINE_DEMAND")
    prepared={};scope=None;contract=None;horizon=None;weights={};caps={};posted={}
    for k,s in sorted(sellers.items()):
        p=policies[k];require(words(k) and integer(s.baseline_sales,1,10**6) and type(p.adopted) is bool and type(p.human_provenance) is bool and integer(p.pass_through_bp,0,20000) and integer(p.price_adjustment_cents,-10**7,10**7) and integer(p.preference_discount_bp,0,9000),"POLICY")
        require(p.human_provenance or p.preference_discount_bp==0,"PREFERENCE_PROVENANCE")
        bp,bs,bd,bc=s.reference;ap,ats,ad,ac=s.alternative
        # Compare even a non-adopted variant only when selected; no unsupported quality transfer.
        target=(ap,ats,ad,ac) if p.adopted else s.reference
        tp,ts,td,tc=target
        op=compare_design(bp,bs,bd,tp,ts,td);require(op["result"]["quality_comparable"],"MARKET_QUALITY")
        if scope is None:scope=bs.scope;contract=bs.output_contract;horizon=bs.horizon
        require(bs.scope==scope and bs.output_contract==contract and bs.horizon==horizon,"MARKET_COMPARABILITY")
        require(bc.price_cents_per_sale>0 and bc.max_sales>=s.baseline_sales,"BASE_PRICE")
        require({x[0] for x in bc.fixed_cash_costs}=={x[0] for x in tc.fixed_cash_costs},"FIXED_CATEGORY_COMPARABILITY")
        bl=ledger(op["result"]["baseline"],bc);al=ledger(op["result"]["alternative"],tc)
        require(bl["correct_outputs"]>=s.baseline_sales and al["correct_outputs"]>0,"CAPACITY")
        # Accounting average cash production cost per correct output, not marginal cost.
        c0=F(bl["cash_cost_eur"])*100/bl["correct_outputs"];c1=F(al["cash_cost_eur"])*100/al["correct_outputs"]
        raw=bc.price_cents_per_sale+F(p.pass_through_bp,10000)*(c1-c0)+p.price_adjustment_cents
        require(raw>=1,"NONPOSITIVE_PRICE")
        price=int(raw+F(1,2));effective=price*F(10000-p.preference_discount_bp,10000)
        weights[k]=F(s.baseline_sales)*(F(bc.price_cents_per_sale)/effective)**m.substitution_power
        caps[k]=al["correct_outputs"];posted[k]=price
        prepared[k]=(s,p,op,bc,tc,c0,c1)
    # Fixed base-basket index of actual posted prices. Preference affects allocation only.
    spend0=sum(s.baseline_sales*s.reference[3].price_cents_per_sale for s in sellers.values())
    basket=sum(s.baseline_sales*posted[k] for k,s in sellers.items())
    ratio=F(basket,spend0)
    raw=baseline*(1-F(m.demand_elasticity_bp,10000)*(ratio-1))
    potential=min(m.saturation_units,max(0,int(raw+F(1,2))))
    require(m.internalized_units<=potential,"INTERNALIZATION_VOLUME")
    external=potential-m.internalized_units
    sold=allocate(external,weights,caps)
    total=sum(sold.values());unserved=external-total
    rows=[]
    for k,(s,p,op,bc,tc,c0,c1) in prepared.items():
        bl=ledger(op["result"]["baseline"],replace(bc,max_sales=s.baseline_sales))
        al=ledger(op["result"]["alternative"],replace(tc,max_sales=sold[k],price_cents_per_sale=posted[k]))
        # Entire production cohort charged, even unsold units.
        base_share=F(s.baseline_sales,baseline)
        share=F(sold[k],total) if total else F(0)
        market_volume_component=base_share*(total-baseline)
        share_component=sold[k]-base_share*total
        require(sold[k]-s.baseline_sales==market_volume_component+share_component,"SHARE_DECOMPOSITION")
        base_rev=F(bl["revenue_eur"]);rev=F(al["revenue_eur"])
        volume_revenue=F((sold[k]-s.baseline_sales)*bc.price_cents_per_sale,100)
        price_revenue=F(sold[k]*(posted[k]-bc.price_cents_per_sale),100)
        require(rev-base_rev==volume_revenue+price_revenue,"REVENUE_BRIDGE")
        rows.append({"seller":k,"adopted":p.adopted,"baseline_sales":s.baseline_sales,"sales":sold[k],"capacity":caps[k],"baseline_price_eur":str(F(bc.price_cents_per_sale,100)),"price_eur":str(F(posted[k],100)),"average_cost_before_eur":str(c0/100),"average_cost_after_eur":str(c1/100),"volume_change":sold[k]-s.baseline_sales,"market_volume_component":str(market_volume_component),"share_reallocation_component":str(share_component),"volume_share":str(share) if total else None,"price_revenue_component_eur":str(price_revenue),"volume_revenue_component_eur":str(volume_revenue),"baseline_revenue_eur":bl["revenue_eur"],"revenue_eur":al["revenue_eur"],"baseline_cash_surplus_eur":bl["cash_operating_surplus_eur"],"cash_surplus_eur":al["cash_operating_surplus_eur"],"baseline_paid_seconds":bl["paid_human_seconds"],"paid_seconds":al["paid_human_seconds"],"baseline_active_seconds":bl["active_human_seconds"],"active_seconds":al["active_human_seconds"],"operation_sha256":op["sha256"],"unsold_correct_outputs":al["unsold_correct_outputs"]})
    require(sum(F(r["share_reallocation_component"]) for r in rows)==0,"SHARE_CONSERVATION")
    require(total+unserved+m.internalized_units==potential,"MARKET_VOLUME_CONSERVATION")
    sumf=lambda k:sum(F(r[k]) for r in rows)
    revenue=sumf("revenue_eur");base_revenue=sumf("baseline_revenue_eur")
    require(revenue-base_revenue==sumf("price_revenue_component_eur")+sumf("volume_revenue_component_eur"),"MARKET_REVENUE")
    result={"market_ref":m.key,"definition":m.definition,"scope":asdict(scope),"output_contract":contract,"baseline_sales":baseline,"potential_demand":potential,"price_induced_demand_change":potential-baseline,"internalized_units":m.internalized_units,"external_demand":external,"sales":total,"unserved":unserved,"unsold_correct_outputs":sum(r["unsold_correct_outputs"] for r in rows),"fixed_basket_price_index":str(ratio),"fixed_basket_customer_saving_eur":str(F(spend0-basket,100)),"market_revenue_eur":str(revenue),"baseline_revenue_eur":str(base_revenue),"cash_surplus_delta_eur":str(sumf("cash_surplus_eur")-sumf("baseline_cash_surplus_eur")),"paid_hours_delta":str((sumf("paid_seconds")-sumf("baseline_paid_seconds"))/3600),"active_hours_delta":str((sumf("active_seconds")-sumf("baseline_active_seconds"))/3600),"baseline_volume_hhi":str(sum(F(s.baseline_sales,baseline)**2 for s in sellers.values())*10000),"volume_hhi":str(sum(F(r["sales"],total)**2 for r in rows)*10000) if total else None,"sellers":rows,"input_sha256":digest(canonical({"id":m.key,"definition":m.definition,"demand":[m.demand_elasticity_bp,m.saturation_units,m.substitution_power,m.internalized_units],"policies":[asdict(p) for p in m.policies],"seller_inputs":[{"id":s.id,"sales":s.baseline_sales,"baseline":asdict(s.reference[3]),"alternative":asdict(s.alternative[3]) if policies[s.id].adopted else None} for s in m.sellers],"assumptions":m.assumptions})),"model_versions":{n:digest((Path(__file__).parent/n).read_bytes()) for n in ("economic_market.py","economic_firm.py","economic_transform.py","economic_events.py","economic_operations.py","economic_core.py")},"assumptions":m.assumptions,"status":"CONDITIONAL_NOT_EMPIRICAL","employment_effect":None,"consumer_surplus":None,"value_added":None,"publication":"BLOCK_PUBLICATION"}
    return {"result":result,"sha256":digest(canonical(result))}
