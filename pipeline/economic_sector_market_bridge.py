"""G3 -> G4 v0.4a. Scoped external transactions only; no automatic revenue scaling."""
from dataclasses import dataclass, replace
from fractions import Fraction as F
import math
from .economic_market import run
from .economic_core import canonical,digest
from .economic_sector_structural import state,compare,validate

def require(ok,why):
    if not ok: raise ValueError(why)
def positive(x,why):
    require(isinstance(x,(str,int,F)) and not isinstance(x,bool),why)
    try: v=F(x)
    except (ValueError,ZeroDivisionError): raise ValueError(why) from None
    require(v>0,why);return v

@dataclass(frozen=True)
class BuyerUse:
    # FINAL_DOMESTIC or INTERMEDIATE_DOMESTIC, buyer branch mandatory only for latter
    kind:str
    buyer:str|None
    before:int
    after:int

@dataclass(frozen=True)
class Mapping:
    product:str
    territory:str
    reference_year:int
    unit:str
    reference_price_eur:str
    periods_per_year:int
    cohort_weight:str
    uses:tuple
    mapping_evidence:str
    scale_evidence:str
    valuation_evidence:str
    closure:str="EXPLICIT_GROSS_SURPLUS_RESIDUAL"
    status:str="SYNTHETIC_CONDITIONAL"

def bridge(base,before,after,mapping,unavailable_before=(),unavailable_after=()):
    """Replays actual G3 markets. No caller supplied receipt; synthetic-only admission.
    Reference price is a common homogeneous basic price, not actual seller price.
    Cohort weight counts disjoint representative cohorts, not adoption probability.
    Final quantity translates to y; intermediate change to B per initial buyer output.
    For intermediate purchases, gross surplus is the explicitly assumed balancing item.
    """
    require(base.origin=="SYNTHETIC" and mapping.status=="SYNTHETIC_CONDITIONAL","ADMISSION")
    require(before.definition==after.definition and before.sellers==after.sellers,"MARKET_COMPARABILITY")
    require(before.ownership==after.ownership,"OWNERSHIP_COMPARABILITY")
    require(type(mapping.reference_year) is int and 1900<=mapping.reference_year<=2100 and mapping.unit=="EUR_MILLION_REFERENCE_BASIC_PRICE","VALUATION")
    require(all(isinstance(x,str) and x.strip() for x in (mapping.territory,mapping.mapping_evidence,mapping.scale_evidence,mapping.valuation_evidence)),"EVIDENCE")
    require(mapping.product in base.codes,"PRODUCT")
    require(type(mapping.periods_per_year) is int and 1<=mapping.periods_per_year<=10000,"PERIOD")
    p=positive(mapping.reference_price_eur,"REFERENCE_PRICE"); weight=positive(mapping.cohort_weight,"COHORT_WEIGHT")
    require(weight<=10**9 and p<=10**9,"SCALE_RANGE")
    require(mapping.closure=="EXPLICIT_GROSS_SURPLUS_RESIDUAL","CLOSURE")
    for s in before.sellers:
        require(mapping.periods_per_year*s.reference[1].horizon<=366*86400 and mapping.periods_per_year*s.alternative[1].horizon<=366*86400,"PERIOD_TIME")
    a,b=run(before,unavailable_before),run(after,unavailable_after)
    x,z=a["result"],b["result"]
    require(x["scope"]==z["scope"] and x["output_contract"]==z["output_contract"],"OUTPUT_CONTRACT")
    require(x["internalized_units"]==z["internalized_units"]==0,"INTERNALIZATION_REQUIRES_FULL_MAKE_BUY_BRIDGE")
    require(x["unserved"]==z["unserved"]==0,"UNSERVED_REQUIRES_SUPPLY_MODEL")
    # Only sold transactions are mapped; unsold output remains explicitly out of scope.
    require(all(F(row["baseline_price_eur"])==p for row in x["sellers"]+z["sellers"]),"HOMOGENEOUS_REFERENCE_PRICE")
    require(mapping.uses and len({(u.kind,u.buyer) for u in mapping.uses})==len(mapping.uses),"USE_DUPLICATE")
    for u in mapping.uses:
        require(type(u.before) is int and type(u.after) is int and u.before>=0 and u.after>=0,"USE_QUANTITY")
        require((u.kind=="FINAL_DOMESTIC" and u.buyer is None) or (u.kind=="INTERMEDIATE_DOMESTIC" and u.buyer in base.codes),"USE_CLASS")
    require(sum(u.before for u in mapping.uses)==x["sales"] and sum(u.after for u in mapping.uses)==z["sales"],"USE_RECONCILIATION")
    ref=state(base);i=base.codes.index(mapping.product); y=list(base.final); B=[list(r) for r in base.domestic]; k=list(base.surplus)
    factor=p*weight*mapping.periods_per_year/10**6
    flows=[]
    for u in mapping.uses:
        old=float(factor*u.before);new=float(factor*u.after);delta=new-old
        require(all(math.isfinite(v) for v in (old,new,delta)),"SCALE_FINITE")
        if u.kind=="FINAL_DOMESTIC":
            require(old<=base.final[i]+1e-9,"BASE_COVERAGE")
            y[i]+=delta
        else:
            j=base.codes.index(u.buyer);g=ref["g"][j]
            require(g>0 and old<=base.domestic[i][j]*g+1e-9,"BASE_COVERAGE")
            d=delta/g;B[i][j]+=d;k[j]-=d
        flows.append({"kind":u.kind,"buyer":u.buyer,"before_reference_mEUR":old,"after_reference_mEUR":new,"delta_reference_mEUR":delta})
    t=replace(base,final=tuple(y),domestic=tuple(tuple(r) for r in B),surplus=tuple(k))
    validate(t);r=compare(base,t)
    price_effect=sum(F(row["price_revenue_component_eur"]) for row in z["sellers"])-sum(F(row["price_revenue_component_eur"]) for row in x["sellers"])
    volume_effect=sum(F(row["volume_revenue_component_eur"]) for row in z["sellers"])-sum(F(row["volume_revenue_component_eur"]) for row in x["sellers"])
    nominal=F(z["market_revenue_eur"])-F(x["market_revenue_eur"])
    require(nominal==price_effect+volume_effect,"G3_REVENUE_IDENTITY")
    out={"status":"SYNTHETIC_G3_G4_CONDITIONAL","publication":"BLOCK_PUBLICATION","receipts":{"before":a["sha256"],"after":b["sha256"]},"market":{"before_sales":x["sales"],"after_sales":z["sales"],"nominal_delta_eur_per_cohort":str(nominal),"price_component_eur_per_cohort":str(price_effect),"volume_component_eur_per_cohort":str(volume_effect),"before_unsold":x["unsold_correct_outputs"],"after_unsold":z["unsold_correct_outputs"]},"mapping":{"product":mapping.product,"territory":mapping.territory,"reference_year":mapping.reference_year,"factor_mEUR_per_unit":str(factor),"closure":mapping.closure,"evidence":[mapping.mapping_evidence,mapping.scale_evidence,mapping.valuation_evidence]},"flows":flows,"sector":r,"limitations":["external sold transactions only; inventory production excluded","domestic origin assumed, no empirical representative scaling","no supplier cost or wage changes transferred automatically","intermediate buyer output used at baseline to set coefficients; endogenous output changes subsequently","price effects reported not propagated","gross surplus balancing assumption, not profit forecast","no internalization, unserved demand or actual capacity solution"]}
    return {"result":out,"sha256":digest(canonical(out))}
