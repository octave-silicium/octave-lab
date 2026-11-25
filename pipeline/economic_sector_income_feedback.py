"""G4 v0.6c: explicitly lagged income-allocation feedback, not institutional national accounts."""
import math
from dataclasses import dataclass,replace,asdict
from .economic_sector_structural import require,validate
from .economic_sector_prices import price,checked
from .economic_sector_budget import budgeted
from .economic_core import canonical,digest

@dataclass(frozen=True)
class IncomeRule:
    social_share:float
    foreign_wage_share:float  # fraction of D1 after social allocation
    capital_consumption_share:float # assumed share of nonnegative gross surplus/mixed
    domestic_distribution_share:float # share of remainder allocated to resident households
    foreign_distribution_share:float
    direct_tax_rate:float
    public_transfer:float # fixed nominal allocation, not actual benefits
    envelope_share:float # proxy disposable resources allocated to basic-price envelope
    evidence:str

@dataclass(frozen=True)
class Period:
    structure:object
    price_policy:object
    budget_policy:object # resources field ignored, replaced from previous receipt
    income_rule:IncomeRule
    evidence:str

def distribute(nominal,rule):
    require(isinstance(rule.evidence,str) and rule.evidence.strip(),"INCOME_EVIDENCE")
    social,fw,cc,dist,foreign,tax,env=checked((rule.social_share,rule.foreign_wage_share,rule.capital_consumption_share,rule.domestic_distribution_share,rule.foreign_distribution_share,rule.direct_tax_rate,rule.envelope_share),7,0,1,"INCOME_SHARES")
    require(dist+foreign<=1,"DISTRIBUTION_SHARE")
    tr=checked((rule.public_transfer,),1,0,1e15,"TRANSFER")[0]
    w=nominal["compensation"];k=nominal["gross_surplus_mixed"];t=nominal["other_net_production_taxes"];h=nominal["valuation_bridge"]
    require(all(math.isfinite(x) for x in (w,k,t,h)) and w>=0,"INCOME_SCOPE")
    social_flow=w*social;foreign_wage=(w-social_flow)*fw;resident_wage=w-social_flow-foreign_wage
    # Losses stay with enterprise residual, not invented negative distributions.
    reserve=max(0.,k)*cc;net=k-reserve
    hh_capital=max(0.,net)*dist;foreign_capital=max(0.,net)*foreign;retained=net-hh_capital-foreign_capital
    gross_hh=resident_wage+hh_capital;direct=gross_hh*tax
    available=gross_hh-direct+tr
    public_pool=social_flow+t+direct
    public_residual=public_pool-tr
    # Signed valuation bridge deliberately unassigned. Negative public residual
    # is a gap within this allocation only; not a government deficit or financed debt.
    foreign_total=foreign_wage+foreign_capital
    assigned=available+public_residual+reserve+retained+foreign_total+h
    require(abs(assigned-w-k-t-h)<=1e-9*max(1,abs(w)+abs(k)+abs(t)+abs(h)),"ALLOCATION_BALANCE")
    envelope=available*env
    return {"D1":w,"gross_surplus_mixed":k,"other_net_production_taxes":t,"unassigned_valuation_bridge":h,
      "resident_wage":resident_wage,"social_allocation":social_flow,"foreign_wage":foreign_wage,
      "assumed_capital_consumption_reserve":reserve,"residual_after_reserve":net,"household_capital_mixed_allocation":hh_capital,
      "foreign_capital_allocation":foreign_capital,"retained_enterprise_residual":retained,"direct_tax":direct,"transfer":tr,
      "household_resources_proxy":available,"public_allocation_pool":public_pool,"public_allocation_residual":public_residual,
      "public_allocation_gap":max(0.,-public_residual),"foreign_allocation":foreign_total,
      "next_basic_price_envelope":envelope,"outside_basic_price_envelope":available-envelope,"allocation_residual":assigned-w-k-t-h}

def feedback(base,basket,periods,initial_envelope,*,period_unit,evidence):
    validate(base)
    require(isinstance(periods,tuple) and 1<=len(periods)<=120 and period_unit in ("MONTH","QUARTER","YEAR"),"HORIZON")
    require(isinstance(evidence,str) and evidence.strip(),"EVIDENCE")
    initial=checked((initial_envelope,),1,0,1e15,"INITIAL_ENVELOPE")[0]
    resources=initial;rows=[]
    for i,p in enumerate(periods,1):
        require(p.structure.codes==base.codes and p.structure.origin==base.origin and isinstance(p.evidence,str) and p.evidence.strip(),"COMPARABILITY")
        policy=replace(p.budget_policy,resources=resources)
        receipt=budgeted(base,p.structure,p.price_policy,basket,policy);b=receipt["result"]
        flow=distribute(b["sector"]["nominal"],p.income_rule)
        nxt=flow["next_basic_price_envelope"]
        require(math.isfinite(nxt) and 0<=nxt<=1e15,"NEXT_ENVELOPE")
        rows.append({"period":i,"input_envelope":resources,"budget":b["budget"],"household_volume_change":b["household_volume_change"],
          "domestic_household_volume":b["domestic_household_volume"],"imported_household_volume":b["imported_household_volume"],
          "nominal":b["sector"]["nominal"],"reference_price_volume":b["sector"]["reference_price_volume"],
          "income":flow,"income_rule":asdict(p.income_rule),"budget_receipt":receipt["sha256"],"evidence":p.evidence})
        resources=nxt
    result={"status":"CONDITIONAL_LAGGED_INCOME_ALLOCATION","publication":"BLOCK_PUBLICATION","period_unit":period_unit,"codes":base.codes,
      "initial_envelope":initial,"periods":rows,"next_envelope":resources,"evidence":evidence,
      "actual_disposable_income":None,"actual_savings":None,"government_deficit":None,"gdp":None,"employment":None,
      "limitations":["allocation of production-side income only; not institutional accounts or measured disposable income",
      "D1 includes employer social contributions; social share assumed; other taxes signed; valuation bridge unassigned",
      "gross surplus includes mixed income; reserve and distributions assumed, no actual ownership or depreciation",
      "public residual not fiscal balance, excludes public spending, debt and full tax/transfers; gap not automatically financed",
      "outside envelope and non-spending are not observed savings; no wealth, credit, capacity rationing or equilibrium",
      "one-period lag, homogeneous aggregate household, exogenous allocation rules and other final demand"]}
    return {"result":result,"sha256":digest(canonical(result))}
