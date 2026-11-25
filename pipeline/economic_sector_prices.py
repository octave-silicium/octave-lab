"""G4 v0.6a: fixed-mix cost-price propagation, nominal accounting and partial demand response.
No price equilibrium, observed elasticities, CPI, GDP or causal forecasts."""
import math
from dataclasses import dataclass,replace,asdict
from .economic_sector_structural import validate,state,require,vec,mv,mm,solve,close
from .economic_core import canonical,digest

@dataclass(frozen=True)
class PricePolicy:
    pass_through:tuple  # branch share of cost change passed to selling prices [0,1]
    import_price:tuple  # imported product price relatives
    wage_price:tuple    # compensation per unit of labor-equivalent requirement, relative
    tax_price:tuple     # multiplier on other net production taxes
    bridge_price:tuple  # multiplier on signed valuation bridge
    evidence:str

@dataclass(frozen=True)
class DemandPolicy:
    elasticity:tuple    # nonnegative own-price elasticity magnitude
    responsive_share:tuple # fraction of baseline domestic final demand responsive
    max_multiple:tuple  # saturation limit of responsive component relative to its reference
    evidence:str

def trans(a):return tuple(zip(*a))
def checked(v,n,lo,hi,why):
    require(isinstance(v,tuple) and len(v)==n and all(type(x) in (int,float) and math.isfinite(x) and lo<=x<=hi for x in v),why)
    return tuple(float(x) for x in v)

def price(base,scenario,policy,demand=None):
    """Compare scenario against reference-price unit account in base.
    Branch output price = 1 + pass-through*(scenario cost - base cost).
    Base cost excludes gross surplus/mixed income. Scenario surplus is residual
    at current prices, not an independently imposed target markup.
    """
    require(base.codes==scenario.codes and base.origin==scenario.origin,"COMPARABILITY")
    validate(base);validate(scenario)
    n=len(base.codes);require(isinstance(policy.evidence,str) and policy.evidence.strip(),"EVIDENCE")
    rho=checked(policy.pass_through,n,0,1,"PASS_THROUGH")
    imp=checked(policy.import_price,n,1e-6,1000,"IMPORT_PRICE")
    wage=checked(policy.wage_price,n,0,1000,"WAGE_PRICE")
    tax=checked(policy.tax_price,n,0,1000,"TAX_PRICE")
    bridge=checked(policy.bridge_price,n,0,1000,"BRIDGE_PRICE")
    # product price = fixed product output shares weighted branch prices.
    D=scenario.shares;B=scenario.domestic;M=scenario.imported
    T=mm(trans(B),trans(D))
    # Solve changes in branch prices, with upstream effects priced at fixed mix.
    P=tuple(tuple(rho[i]*x for x in row) for i,row in enumerate(T))
    contraction=max(math.fsum(row) for row in P)
    require(contraction<1,"PRICE_CONTRACTION")
    wc=tuple(a*b for a,b in zip(scenario.wage,wage))
    tc=tuple(a*b for a,b in zip(scenario.other_tax,tax))
    hc=tuple(a*b for a,b in zip(scenario.bridge,bridge))
    mc=mv(trans(M),imp)
    direct=tuple(math.fsum(col)+mc[i]+wc[i]+tc[i]+hc[i]-(1-base.surplus[i]) for i,col in enumerate(zip(*B)))
    shock=tuple(a*b for a,b in zip(rho,direct))
    # Infinity-norm Neumann bound (row sums); existing quantity solver uses L1.
    term=shock;delta=term
    for iteration in range(1,10001):
        term=mv(P,term);delta=tuple(a+b for a,b in zip(delta,term))
        tail=max(abs(v) for v in term)*contraction/(1-contraction)
        if tail<=1e-13:break
    else:raise ValueError("PRICE_CONVERGENCE")
    pb=tuple(1+x for x in delta);pp=mv(trans(D),pb)
    require(all(math.isfinite(x) and x>0 for x in pb+pp),"NONPOSITIVE_PRICE")
    dc=mv(trans(B),pp)
    cost=tuple(a+b+c+d+e for a,b,c,d,e in zip(dc,mc,wc,tc,hc))
    surplus=tuple(a-b for a,b in zip(pb,cost))
    require(close(delta,tuple(r*(c-(1-k)) for r,c,k in zip(rho,cost,base.surplus)),1e-10),"PRICE_RESIDUAL")
    require(close(tuple(k-b for k,b in zip(surplus,base.surplus)),tuple(-(1-r)*(c-(1-k)) for r,c,k in zip(rho,cost,base.surplus)),1e-10),"SURPLUS_RESIDUAL")
    y0=scenario.final;y=y0
    if demand is not None:
        require(isinstance(demand.evidence,str) and demand.evidence.strip(),"DEMAND_EVIDENCE")
        eps=checked(demand.elasticity,n,0,20,"ELASTICITY")
        share=checked(demand.responsive_share,n,0,1,"RESPONSIVE_SHARE")
        ceiling=checked(demand.max_multiple,n,1,100,"SATURATION")
        y=tuple(v*((1-s)+s*min(m,math.exp(min(math.log(m),-e*math.log(p))))) for v,s,m,e,p in zip(y0,share,ceiling,eps,pp))
    ref=state(base);vol=state(replace(scenario,final=y))
    g=vol["g"];q=vol["q"]
    # Aggregate nominal product and branch output agree via fixed shares.
    output_product=math.fsum(a*b for a,b in zip(pp,q))
    output_branch=math.fsum(a*b for a,b in zip(pb,g))
    require(abs(output_product-output_branch)<=1e-9*max(1,abs(output_product)),"OUTPUT_VALUATION")
    final_nominal=math.fsum(a*b for a,b in zip(pp,y))
    imports=math.fsum(a*b for a,b in zip(mc,g))
    compensation=math.fsum(a*b for a,b in zip(wc,g))
    other_tax=math.fsum(a*b for a,b in zip(tc,g))
    valuation_bridge=math.fsum(a*b for a,b in zip(hc,g))
    gross_surplus=math.fsum(a*b for a,b in zip(surplus,g))
    va=compensation+other_tax+gross_surplus
    require(abs(final_nominal-va-imports-valuation_bridge)<=1e-9*max(1,abs(final_nominal)),"NOMINAL_BALANCE")
    # Exact additive price/quantity decomposition at fixed reference basket.
    # Relative to base final quantities; separate exogenous scenario demand from induced demand.
    volume_effect=math.fsum(y)-math.fsum(base.final)
    price_effect=math.fsum((p-1)*v for p,v in zip(pp,y))
    require(abs(final_nominal-math.fsum(base.final)-volume_effect-price_effect)<=1e-9*max(1,abs(final_nominal)),"PRICE_VOLUME")
    direct_price=shock;network_price=tuple(a-b for a,b in zip(delta,direct_price))
    result={"status":"CONDITIONAL_COST_PRICE_DEMAND","publication":"BLOCK_PUBLICATION","codes":base.codes,
      "branch_price":pb,"product_price":pp,"unit_cost":cost,"unit_gross_surplus":surplus,
      "direct_branch_price_effect":direct_price,"network_branch_price_effect":network_price,
      "cost_change":tuple(a-(1-b) for a,b in zip(cost,base.surplus)),
      "unit_surplus_change":tuple(a-b for a,b in zip(surplus,base.surplus)),
      "reference_final":base.final,"scenario_final_before_price_response":y0,"final_volume_equivalent":y,
      "price_induced_final_change":tuple(a-b for a,b in zip(y,y0)),
      "final_value_decomposition":{"volume":volume_effect,"price_at_scenario_volume":price_effect,"nominal_change":final_nominal-math.fsum(base.final)},
      "nominal":{"gross_output":output_branch,"domestic_final":final_nominal,"intermediate_imports":imports,"compensation":compensation,"other_net_production_taxes":other_tax,"valuation_bridge":valuation_bridge,"gross_surplus_mixed":gross_surplus,"gross_value_added":va},
      "reference_price_volume":{"gross_output":math.fsum(q),"domestic_final":math.fsum(y)},
      "base_reference":{"gross_output":math.fsum(ref["q"]),"domestic_final":math.fsum(base.final),"compensation":math.fsum(ref["wage"]),"gross_surplus_mixed":math.fsum(ref["surplus"]),"gross_value_added":math.fsum(ref["va"])},
      "price_tail_bound":tail,"price_iterations":iteration,"price_policy":asdict(policy),"demand_policy":asdict(demand) if demand else None,
      "actual_output":None,"employment":None,"gdp":None,"cpi":None,"net_profit":None,
      "limitations":["branch homogeneous price relatives across secondary products; fixed product shares","cost pass-through rule is assumed, not competition equilibrium or estimated markup","gross surplus/mixed residual includes capital consumption, not net profit","own-price elasticities and responsive shares assumed; no cross-price, income, budget or capacity feedback","reference-price quantities are value equivalents, not physical units; no final import or purchaser-price household basket"]}
    return {"result":result,"sha256":digest(canonical(result))}
