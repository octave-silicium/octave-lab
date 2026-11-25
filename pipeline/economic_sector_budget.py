"""G4 v0.6b: closed nominal household-use envelope at reference basic-price valuation.
Capped CES-style expenditure rule, not a fitted demand system or disposable-income account.
"""
import math
from dataclasses import dataclass,replace,asdict
from .economic_sector_structural import validate,require,state
from .economic_sector_prices import price,checked
from .economic_core import canonical,digest

@dataclass(frozen=True)
class HouseholdBasket:
    domestic:tuple
    imported:tuple
    evidence:str

@dataclass(frozen=True)
class BudgetPolicy:
    resources:float       # nominal envelope, not observed disposable income
    reserve_share:float   # exogenous minimum fraction unspent
    elasticity:float      # common CES substitution elasticity
    domestic_cap:tuple    # multiples of base quantities, >=1
    imported_cap:tuple
    final_import_price:tuple
    evidence:str

def allocation(weights,prices,budget,caps,sigma):
    # Unconstrained CES expenditure shares: w_i p_i^(1-sigma).
    # With caps, allocate residual proportionally among uncapped goods.
    # Zero benchmark weight means no new product demand.
    score=[w*math.exp((1-sigma)*math.log(p)) for w,p in zip(weights,prices)]
    require(all(math.isfinite(x) for x in score),"SCORE")
    limits=[w*p*m for w,p,m in zip(weights,prices,caps)]
    require(all(math.isfinite(x) for x in limits),"SATURATION_VALUE")
    active={i for i,x in enumerate(score) if x>0};spend=[0.]*len(weights);remaining=budget
    for _ in range(len(weights)+1):
        if not active or remaining<=0:break
        total=math.fsum(score[i] for i in sorted(active))
        hits=[i for i in sorted(active) if remaining*(score[i]/total)>limits[i]]
        if not hits:
            for i in sorted(active):spend[i]=remaining*(score[i]/total)
            remaining=0.;break
        for i in hits:spend[i]=limits[i]
        remaining=max(0.,remaining-math.fsum(spend[i] for i in hits))
        active.difference_update(hits)
    spent=math.fsum(spend)
    require(spent<=budget+1e-10*max(1,budget),"BUDGET_EXCEEDED")
    q=tuple(x/p for x,p in zip(spend,prices))
    require(all(x<=w*m+1e-10*max(1,w*m) for x,w,m in zip(q,weights,caps)),"SATURATION_EXCEEDED")
    return q,tuple(spend)

def budgeted(base,scenario,price_policy,basket,budget):
    validate(base);validate(scenario)
    require(base.codes==scenario.codes and base.origin==scenario.origin,"COMPARABILITY")
    n=len(base.codes)
    require(isinstance(basket.evidence,str) and basket.evidence.strip(),"BASKET_EVIDENCE")
    require(isinstance(budget.evidence,str) and budget.evidence.strip(),"BUDGET_EVIDENCE")
    hd=checked(basket.domestic,n,0,1e15,"HOUSEHOLD_DOMESTIC")
    hi=checked(basket.imported,n,0,1e15,"HOUSEHOLD_IMPORT")
    require(all(x<=a and x<=b for x,a,b in zip(hd,base.final,scenario.final)),"HOUSEHOLD_COVERAGE")
    weights=hd+hi;reference=math.fsum(weights)
    require(reference>0,"EMPTY_BASKET")
    resources=checked((budget.resources,),1,0,1e15,"RESOURCES")[0]
    save=checked((budget.reserve_share,),1,0,1,"RESERVE")[0]
    sigma=checked((budget.elasticity,),1,0,10,"SUBSTITUTION_ELASTICITY")[0]
    caps=checked(budget.domestic_cap,n,1,100,"DOMESTIC_CAP")+checked(budget.imported_cap,n,1,100,"IMPORT_CAP")
    ip=checked(budget.final_import_price,n,1e-6,1000,"FINAL_IMPORT_PRICE")
    pr=price(base,scenario,price_policy)["result"]
    pp=pr["product_price"];prices=pp+ip
    spendable=resources*(1-save)
    q,spend=allocation(weights,prices,spendable,caps,sigma)
    dh,ih=q[:n],q[n:]
    other=tuple(y-h for y,h in zip(scenario.final,hd))
    final=tuple(o+h for o,h in zip(other,dh))
    # Other domestic final uses (government, investment, exports, etc.) fixed in volume.
    result=price(base,replace(scenario,final=final),price_policy)["result"]
    require(all(abs(a-b)<=1e-12 for a,b in zip(result["product_price"],pp)),"PRICE_REPLAY")
    dom_spend=math.fsum(spend[:n]);imp_spend=math.fsum(spend[n:])
    spent=math.fsum(spend);unspent=max(0.,resources-spent)
    require(abs(resources-dom_spend-imp_spend-unspent)<=1e-10*max(1,resources),"HOUSEHOLD_BUDGET")
    require(unspent+1e-10*max(1,resources)>=resources*save,"RESERVE_FLOOR")
    other_nominal=math.fsum(a*b for a,b in zip(pp,other))
    require(abs(result["nominal"]["domestic_final"]-dom_spend-other_nominal)<=1e-9*max(1,result["nominal"]["domestic_final"]),"DOMESTIC_USE_SPLIT")
    nacc=result["nominal"]
    extended= nacc["domestic_final"]+imp_spend
    total_imp=nacc["intermediate_imports"]+imp_spend
    require(abs(extended-total_imp-nacc["gross_value_added"]-nacc["valuation_bridge"])<=1e-9*max(1,extended),"EXTENDED_ACCOUNT")
    fixed_basket_cost=math.fsum(w*p for w,p in zip(weights,prices))
    out={"status":"CONDITIONAL_HOUSEHOLD_BUDGET_ALLOCATION","publication":"BLOCK_PUBLICATION","codes":base.codes,
      "basket":asdict(basket),"budget_policy":asdict(budget),"reference_household_spend":reference,
      "fixed_reference_basket_cost":fixed_basket_cost,"fixed_basket_price_effect":fixed_basket_cost-reference,
      "budget":{"resources":resources,"spendable":spendable,"domestic":dom_spend,"direct_import":imp_spend,"unspent":unspent,"minimum_reserve":resources*save,"additional_unspent":max(0.,unspent-resources*save)},
      "domestic_household_volume":dh,"imported_household_volume":ih,"domestic_household_spend":spend[:n],"imported_household_spend":spend[n:],
      "other_domestic_final_volume":other,"other_domestic_final_nominal":other_nominal,
      "household_volume_change":math.fsum(q)-reference,"domestic_household_volume_change":tuple(a-b for a,b in zip(dh,hd)),
      "imported_household_volume_change":tuple(a-b for a,b in zip(ih,hi)),
      "extended_nominal_scope":{"domestic_final_plus_household_direct_imports":extended,"intermediate_plus_household_direct_imports":total_imp,"gross_value_added":nacc["gross_value_added"],"valuation_bridge":nacc["valuation_bridge"]},
      "sector":result,"actual_disposable_income":None,"actual_savings":None,"cpi":None,"gdp":None,"employment":None,
      "limitations":["budget is a nominal basic-price use envelope, not disposable income or purchaser-price spending","unspent envelope is not measured household saving","common CES substitution parameter and caps assumed, no estimated elasticities or welfare claims","other final imports excluded; household direct imports separate from intermediate imports","no endogenous income, fiscal transfers, credit, constraints of supply, new products or household heterogeneity"]}
    return {"result":out,"sha256":digest(canonical(out))}
