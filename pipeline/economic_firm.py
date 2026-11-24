"""G3.3 v0.1 — bounded, conditional process-service economics in nominal EUR.
No market inference, headcount inference, financing, tax or working capital.
Inputs are explicitly synthetic integer cents, seconds and whole repeated periods.
"""
from dataclasses import dataclass,asdict
from fractions import Fraction as F
from pathlib import Path
from .economic_core import require,words,identity,unique,canonical,digest
from .economic_events import integer
from .economic_transform import compare_design

@dataclass(frozen=True)
class ResourceCost:
    pool:str
    paid_seconds:int # HUMAN payroll only; may include idle/other work allocated here
    payroll_cents_per_hour:int
    running_cents_per_hour:int # MACHINE/SERVICE only

@dataclass(frozen=True)
class Economics:
    id:str
    revision:int
    schedule_ref:str
    price_cents_per_sale:int
    max_sales:int
    receipt_cents_per_arrival:int # consumption on entry, including unfinished cases
    defect_cents_per_incorrect_completion:int
    resources:tuple
    fixed_cash_costs:tuple # (unique named category, cents per repeated period)
    common_depreciation_cents_per_year:int
    investment_cents:int
    transition_cents:int
    residual_cents:int
    periods_per_year:int
    years:int
    discount_basis_points:int
    opening_cash_cents:int
    assumptions:str
    @property
    def key(self):return identity(self.id,self.revision)

def money(x):return integer(x,0,10**12)
def eur(cents):return str(F(cents,100))
def ledger(receipt,config):
    config.key
    d=receipt["result"];e=d["event_receipt"]["result"]
    require(config.schedule_ref==e["schedule_ref"] and words(config.assumptions),"SCHEDULE_REF")
    require(all(money(x) for x in (config.price_cents_per_sale,config.receipt_cents_per_arrival,config.defect_cents_per_incorrect_completion,config.common_depreciation_cents_per_year,config.investment_cents,config.transition_cents,config.residual_cents,config.opening_cash_cents)),"MONEY")
    require(integer(config.max_sales,0,e["arrivals"]) and integer(config.periods_per_year,1,10000) and integer(config.years,1,30) and integer(config.discount_basis_points,0,10000) and config.residual_cents<=config.investment_cents,"FINANCIAL_RANGE")
    require(config.periods_per_year*e["horizon_seconds"]<=366*86400,"REPEAT_TIME")
    rows=unique(config.resources,lambda x:x.pool)
    pools=unique(e["resource_rows"],lambda x:x["resource"])
    require(set(rows)==set(pools),"COST_POOL_COVERAGE")
    payroll=F(0);running=F(0);paid=0;human_used=0;resource_ledger=[]
    for k,p in sorted(pools.items()):
        c=rows[k];avail=F(p["available_seconds"]);used=F(p["busy_seconds"])
        require(integer(c.paid_seconds,0,10**9) and money(c.payroll_cents_per_hour) and money(c.running_cents_per_hour),"RESOURCE_COST")
        if p["kind"]=="HUMAN":
            require(c.paid_seconds>=avail and c.running_cents_per_hour==0,"PAID_TIME_OR_DOUBLE_COUNT")
            pay=F(c.paid_seconds*c.payroll_cents_per_hour,3600);run=F(0);paid+=c.paid_seconds;human_used+=used
        else:
            require(c.paid_seconds==0 and c.payroll_cents_per_hour==0,"NONHUMAN_PAYROLL")
            pay=F(0);run=used*c.running_cents_per_hour/3600
        payroll+=pay;running+=run
        resource_ledger.append({"pool":k,"kind":p["kind"],"used_seconds":str(used),"paid_seconds":c.paid_seconds,"payroll_eur":eur(pay),"running_eur":eur(run)})
    require(human_used==e["human_service_seconds"],"HUMAN_TIME_RECONCILIATION")
    fixed=unique(config.fixed_cash_costs,lambda x:x[0])
    require(all(words(k) and money(v[1]) for k,v in fixed.items()),"FIXED_COST")
    fixed_cash=sum(v[1] for v in fixed.values())
    good=e["correct_completed_cases"];sold=min(good,config.max_sales);bad=e["incorrect_completed_cases"]
    revenue=F(sold*config.price_cents_per_sale)
    intake=F(e["arrivals"]*config.receipt_cents_per_arrival)
    error=F(bad*config.defect_cents_per_incorrect_completion)
    cash_cost=payroll+running+intake+error+fixed_cash
    cash=revenue-cash_cost
    annual_dep=F(config.common_depreciation_cents_per_year)+F(config.investment_cents-config.residual_cents,config.years)
    dep_period=annual_dep/config.periods_per_year
    accounting=cash-dep_period;annual_cash=cash*config.periods_per_year
    initial=-(config.investment_cents+config.transition_cents)
    flows=[F(initial)]+[annual_cash+(config.residual_cents if y==config.years else 0) for y in range(1,config.years+1)]
    rate=F(config.discount_basis_points,10000)
    npv=sum(v/(1+rate)**i for i,v in enumerate(flows))
    cash_balance=[];bal=F(config.opening_cash_cents)
    for v in flows:bal+=v;cash_balance.append(bal)
    require(accounting+dep_period==cash and sum([payroll,running,intake,error,F(fixed_cash)])==cash_cost,"LEDGER_CONSERVATION")
    return {"economics_ref":config.key,"schedule_ref":config.schedule_ref,"correct_outputs":good,"sales":sold,"unsold_correct_outputs":good-sold,"unfinished_cases":e["unfinished_cases"],"paid_human_seconds":paid,"active_human_seconds":int(human_used),"paid_not_in_process_seconds":str(paid-human_used),"resource_ledger":resource_ledger,"fixed_cash_costs_eur":{k:eur(v[1]) for k,v in sorted(fixed.items())},"revenue_eur":eur(revenue),"payroll_eur":eur(payroll),"machine_running_eur":eur(running),"intake_eur":eur(intake),"error_cost_eur":eur(error),"fixed_cash_eur":eur(fixed_cash),"cash_cost_eur":eur(cash_cost),"depreciation_eur":eur(dep_period),"full_scoped_cost_eur":eur(cash_cost+dep_period),"cash_operating_surplus_eur":eur(cash),"accounting_operating_result_eur":eur(accounting),"cost_per_correct_output_eur":eur((cash_cost+dep_period)/good) if good else None,"cost_per_sale_eur":eur((cash_cost+dep_period)/sold) if sold else None,"price_floor_at_fixed_activity_eur":eur((cash_cost+dep_period)/sold) if sold else None,"annual_cash_surplus_eur":eur(annual_cash),"annual_depreciation_eur":eur(annual_dep),"cash_flows_eur":[eur(v) for v in flows],"npv_eur":eur(npv),"minimum_cash_balance_eur":eur(min(cash_balance)),"funding_gap_at_sampled_dates_eur":eur(max(F(0),-min(cash_balance))),"accounting_scope":"Period expense model; not inventory accounting or company-wide profit. Existing depreciation explicit; transition expense at time zero excluded from recurring result.","assumptions":config.assumptions,"employment_effect":None,"deployment":"BLOCK_DEPLOYMENT_UNQUALIFIED"}

def assess(base,bs,bd,bc,alt,ats,ad,ac):
    # Always recompute the actual operation receipts; do not accept fabricated summary dicts.
    op=compare_design(base,bs,bd,alt,ats,ad)
    x=op["result"];require(x["quality_comparable"],"BLOCK_OPERATIONAL_QUALITY")
    require(bc.periods_per_year==ac.periods_per_year and bc.years==ac.years and bc.discount_basis_points==ac.discount_basis_points and bc.opening_cash_cents==ac.opening_cash_cents and bc.max_sales==ac.max_sales,"FINANCIAL_COMPARABILITY")
    require({k for k,v in bc.fixed_cash_costs}=={k for k,v in ac.fixed_cash_costs},"FIXED_CATEGORY_COMPARABILITY")
    a=ledger(x["baseline"],bc);b=ledger(x["alternative"],ac)
    flows=[F(v)-F(u) for u,v in zip(a["cash_flows_eur"],b["cash_flows_eur"])]
    rate=F(ac.discount_basis_points,10000);npv=sum(v/(1+rate)**i for i,v in enumerate(flows))
    require(npv==F(b["npv_eur"])-F(a["npv_eur"]),"NPV_CONSERVATION")
    cumulative=F(0);balances=[]
    for v in flows:cumulative+=v;balances.append(cumulative)
    # First recovery sustained through final sampled year; not interpolated.
    payback=next((i for i in range(len(balances)) if all(x>=0 for x in balances[i:])),None)
    initial_extra=F(ac.investment_cents-bc.investment_cents,100)
    result={"baseline":a,"alternative":b,"operation_sha256":op["sha256"],"incremental_cash_flows_eur":[str(v) for v in flows],"incremental_npv_eur":str(npv),"incremental_investment_eur":str(initial_extra),"max_incremental_investment_at_zero_npv_eur":str(initial_extra+npv),"sustained_payback_year":payback,"payroll_saving_eur":str(F(a["payroll_eur"])-F(b["payroll_eur"])),"active_human_seconds_released":a["active_human_seconds"]-b["active_human_seconds"],"incremental_revenue_eur":str(F(b["revenue_eur"])-F(a["revenue_eur"])),"incremental_cash_surplus_eur":str(F(b["cash_operating_surplus_eur"])-F(a["cash_operating_surplus_eur"])),"incremental_accounting_result_eur":str(F(b["accounting_operating_result_eur"])-F(a["accounting_operating_result_eur"])),"model_sha256":digest(Path(__file__).read_bytes()),"input_sha256":digest(canonical([asdict(bc),asdict(ac)])),"status":"CONDITIONAL_NOT_EMPIRICAL","publication":"BLOCK_PUBLICATION"}
    return {"result":result,"sha256":digest(canonical(result))}
