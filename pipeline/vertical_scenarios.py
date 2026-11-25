"""VERTICAL-001 V2a: exact conditional service-market scenario adapter.
Reuse G3 market allocation; evidence and assumptions stay separate.
Not a sector calibration, employment forecast or autonomous new economic engine.
"""
from dataclasses import dataclass,asdict,replace
from fractions import Fraction as F
from .economic_market import allocate
from .economic_core import require,canonical,digest

@dataclass(frozen=True)
class Case:
    id:str
    hours_per_unit:str
    extra_hours:str
    ai_cost_per_unit:str
    pass_through:str
    elasticity:str
    capacity:int
    paid_floor:str
    upfront_eur:str
    explanation:str

# Same normalized service output, hypothetical quality held constant, on-demand production.
# 1000 sales per quarter, 1 h/unit, 40 EUR/h, 20 EUR other inputs, 100 EUR price.
BASE=Case("reference","1","0","0","0","0",1000,"0","0","No change; no assumed adoption")
CASES=(BASE,
 Case("substitution","1/2","0","5","1","1",2000,"0","10000","Half the direct time, paid hours adjust, cost reduction passed to buyers"),
 Case("complementarity","3/4","150","5","1","4",2000,"0","10000","New human work plus strong price response"),
 Case("redesign","1/4","50","8","1","1",2500,"0","20000","Removed steps; residual coordination work, quality assumption unchanged"),
 Case("no_rebound","1/2","0","5","1","0",2000,"0","10000","Same substitution, no price-induced demand"),
 Case("retained_payroll","1/2","0","5","1","1",2000,"1000","10000","Same technology, paid hours initially retained"),
 Case("retain_margin","1/2","0","5","0","1",2000,"0","10000","Savings not passed to buyers"),
 Case("capacity_stress","3/4","150","5","1","4",1000,"0","10000","Complementarity constrained by capacity"))

def run(c):
    h,x,ai,rho,e,floor,upfront=map(F,(c.hours_per_unit,c.extra_hours,c.ai_cost_per_unit,c.pass_through,c.elasticity,c.paid_floor,c.upfront_eur))
    require(0<=h<=4 and 0<=x<=10000 and 0<=ai<=1000 and 0<=rho<=1 and 0<=e<=10 and 0<=floor<=10000 and 0<=upfront<=10**9,"SCENARIO_PARAMETER")
    require(type(c.capacity) is int and 0<=c.capacity<=10000,"CAPACITY")
    base_q=1000;base_h=F(1000);w=F(40);other=F(20);p0=F(100);fixed=F(10000)
    variable=w*h+other+ai
    # Price rule applies to direct variable cost only; fixed/extra labor not passed through.
    p=p0+rho*(variable-(w+other));require(p>0,"PRICE")
    desired=min(5000,max(0,int(base_q*(1-e*(p/p0-1))+F(1,2))))
    # Two identical hypothetical sellers; this is NOT an empirical concentration estimate.
    sales=allocate(desired,{"A":F(1),"B":F(1)},{"A":c.capacity//2,"B":c.capacity-c.capacity//2})
    q=sum(sales.values());active=q*h+x;paid=max(active,floor)
    payroll=paid*w;inputs=q*other;technology=q*ai;revenue=q*p
    surplus=revenue-payroll-inputs-technology-fixed
    base_surplus=base_q*p0-base_h*w-base_q*other-fixed
    delta=surplus-base_surplus
    require(revenue==payroll+inputs+technology+fixed+surplus,"VALUE_IDENTITY")
    require(revenue-base_q*p0==(q-base_q)*p0+q*(p-p0),"REVENUE_BRIDGE")
    # Three years, quarterly discount 2%, immediate investment; no tax/finance/depreciation.
    npv=-upfront+sum(delta/(1+F(1,50))**t for t in range(1,13))
    breakeven=(base_h-x)/h if h>0 and x<=base_h else None
    # Cash incidence bridge versus baseline; buyer expenditure is NOT consumer welfare.
    incidence={"labor_income_delta":payroll-base_h*w,"other_supplier_revenue_delta":inputs-base_q*other,
               "technology_supplier_revenue_delta":technology,"firm_cash_surplus_delta":delta}
    require(sum(incidence.values())==revenue-base_q*p0,"INCIDENCE_IDENTITY")
    return {"id":c.id,"assumptions":asdict(c),"quantity":q,"desired_quantity":desired,"unserved":desired-q,
            "price_eur":str(p),"direct_variable_cost_eur":str(variable),"active_hours":str(active),"paid_hours":str(paid),
            "paid_hours_delta":str(paid-base_h),"conditional_fte_at_400h":str(paid/400),"actual_jobs":None,
            "revenue_eur":str(revenue),"payroll_eur":str(payroll),"other_inputs_eur":str(inputs),"technology_cost_eur":str(technology),
            "fixed_cost_eur":str(fixed),"cash_surplus_eur":str(surplus),"cash_surplus_delta_eur":str(delta),"incremental_npv_eur":str(npv),
            "break_even_volume_for_baseline_active_hours":str(breakeven) if breakeven is not None else None,
            "break_even_volume_growth_pct":str(100*(breakeven/base_q-1)) if breakeven is not None else None,
            "incidence_eur":{k:str(v) for k,v in incidence.items()},"buyer_expenditure_delta_eur":str(revenue-base_q*p0),
            "baseline_basket_price_saving_eur":str(base_q*(p0-p)),"consumer_surplus":None,"economic_rent":None,
            "quality_status":"ASSUMED_EQUAL_NOT_TESTED","status":"CONDITIONAL_NOT_EMPIRICAL"}
def compare():
    rows=[run(c) for c in CASES]
    require(rows[0]["paid_hours_delta"]==rows[0]["cash_surplus_delta_eur"]=="0","ZERO_SHOCK")
    # Exposure-only comparator: direct time at baseline output, no demand, new work or payroll friction.
    for r,c in zip(rows,CASES):
        r["simple_direct_time_comparator_delta_hours"]=str(1000*(F(c.hours_per_unit)-1))
    sens=[{"elasticity":str(e),"pass_through":str(p),"paid_hours_delta":run(replace(CASES[1],elasticity=str(e),pass_through=str(p)))["paid_hours_delta"]}
          for e in (0,1,2,4,6,8,10) for p in (F(0),F(1,2),F(1))]
    result={"scenarios":rows,"sensitivity":sens,"scope":"Two identical fictional service suppliers, 1000 reference units per quarter; no NACE J extrapolation",
            "reference":{"sales":1000,"unit_price_eur":100,"hours_per_unit":1,"hourly_compensation_eur":40,"other_input_eur":20,"fixed_cost_eur":10000,"reference_hours_per_fte":400},
            "limits":["Assumed equal quality and homogeneous output, no independent process performance measurement.",
                      "Linear local demand bounded at 5000, not estimated; no macro demand feedback or strategic market equilibrium.",
                      "On-demand output, no inventory; extra hours fixed, paid floor imposed, no hiring, separations or headcount prediction.",
                      "Cash surplus before tax/depreciation/finance, upfront costs exogenous, no financing or full balance sheet.",
                      "Expenditure and scoped cash incidence are not welfare, rents or GDP; no separate attribution of capital income.",
                      "Only market allocation function reused from G3.4; operational and full finance engines not calibrated to sector."],
            "publication":"BLOCK_PUBLICATION"}
    return {"result":result,"sha256":digest(canonical(result))}
