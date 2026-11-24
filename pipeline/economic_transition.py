"""G3.3 v0.2a: quarterly conditional workforce and liquidity trajectories.
One scoped service business, explicit staffing flows, no endogenous hiring or legal advice.
"""
from dataclasses import dataclass,asdict
from fractions import Fraction as F
from pathlib import Path
from .economic_core import require,words,identity,canonical,digest
from .economic_events import integer
from .economic_firm import ledger,money
from .economic_transform import compare_design

@dataclass(frozen=True)
class Workforce:
    junior:int
    senior:int
    seconds_per_person:int
    junior_cents_per_hour:int
    senior_cents_per_hour:int

@dataclass(frozen=True)
class Quarter:
    index:int
    phase:str
    repeats:int
    budgeted_hires:int
    frozen_hires:int
    hire_j:int
    hire_s:int
    quit_j:int
    quit_s:int
    layoff_j:int
    layoff_s:int
    other_j:int
    other_s:int
    promote:int
    training_seconds:int
    redeployed_seconds:int
    training_cents:int
    exit_cents:int
    capex_cents:int
    transition_cents:int
    debt_draw_cents:int
    principal_repaid_cents:int

@dataclass(frozen=True)
class Plan:
    id:str
    revision:int
    workforce:Workforce
    opening_cash_cents:int
    opening_receivable_cents:int
    opening_payable_cents:int
    opening_debt_cents:int
    collection_next_quarter_bp:int
    supplier_next_quarter_bp:int
    quarterly_interest_bp:int
    anticipation_quarter:int|None
    decision_quarter:int|None
    investment_quarter:int|None
    production_quarter:int|None
    quarters:tuple
    assumptions:str
    @property
    def key(self):return identity(self.id,self.revision)

def validate(plan,phases):
    plan.key;w=plan.workforce
    require(words(plan.assumptions) and all(integer(x,0,100000) for x in (w.junior,w.senior)) and integer(w.seconds_per_person,1,92*86400) and all(money(x) for x in (w.junior_cents_per_hour,w.senior_cents_per_hour,plan.opening_cash_cents,plan.opening_receivable_cents,plan.opening_payable_cents,plan.opening_debt_cents)),"PLAN")
    require(all(integer(x,0,10000) for x in (plan.collection_next_quarter_bp,plan.supplier_next_quarter_bp,plan.quarterly_interest_bp)),"RATES")
    require(isinstance(plan.quarters,tuple) and 1<=len(plan.quarters)<=120,"HORIZON")
    dates=(plan.anticipation_quarter,plan.decision_quarter,plan.investment_quarter,plan.production_quarter)
    require(all(x is None for x in dates) or (all(integer(x,1,len(plan.quarters)) for x in dates) and list(dates)==sorted(dates)),"MILESTONES")
    for i,q in enumerate(plan.quarters,1):
        require(q.index==i and q.phase in phases and integer(q.repeats,1,10000),"QUARTER")
        require(all(integer(getattr(q,k),0,100000) for k in ("budgeted_hires","frozen_hires","hire_j","hire_s","quit_j","quit_s","layoff_j","layoff_s","other_j","other_s","promote")),"WORKFORCE_FLOW")
        require(q.hire_j+q.hire_s+q.frozen_hires<=q.budgeted_hires,"HIRING_BUDGET")
        require(all(integer(x,0,10**12) for x in (q.training_seconds,q.redeployed_seconds)) and all(money(getattr(q,k)) for k in ("training_cents","exit_cents","capex_cents","transition_cents","debt_draw_cents","principal_repaid_cents")),"QUARTER_COST")
        require((q.phase=="reference") if plan.production_quarter is None or i<plan.production_quarter else True,"PRE_DEPLOYMENT")
    if plan.investment_quarter is not None:require(plan.quarters[plan.investment_quarter-1].capex_cents>0,"INVESTMENT_MILESTONE")

def simulate(base,reference,phases,plan):
    # Each phase is a process, event schedule, design, financial configuration.
    # Quality-gated replay; no supplied aggregate productivity or revenue accepted.
    require("reference" in phases and phases["reference"]==reference,"REFERENCE_PHASE")
    validate(plan,phases)
    rp,rs,rd,rc=reference
    require(rp==base,"REFERENCE_PROCESS")
    cache={};pins={}
    for key in sorted({q.phase for q in plan.quarters}):
        p,s,d,c=phases[key]
        op=compare_design(base,rs,rd,p,s,d)
        require(op["result"]["quality_comparable"],"BLOCK_OPERATIONAL_QUALITY")
        require(c.max_sales==rc.max_sales and c.price_cents_per_sale==rc.price_cents_per_sale,"PRICE_DEMAND_SCOPE")
        l=ledger(op["result"]["alternative"],c)
        e=op["result"]["alternative"]["result"]["event_receipt"]["result"]
        cache[key]=(l,e);pins[key]=op["sha256"]
    w=plan.workforce;j=w.junior;s=w.senior
    cash=F(plan.opening_cash_cents);ar=F(plan.opening_receivable_cents);ap=F(plan.opening_payable_cents);debt=F(plan.opening_debt_cents)
    min_cash=cash;rows=[]
    eur=lambda x:str(F(x)/100)
    for q in plan.quarters:
        l,e=cache[q.phase];n=q.repeats
        require(n*e["horizon_seconds"]<=90*86400,"QUARTER_TIME")
        oj,os=j,s;outj=q.quit_j+q.layoff_j+q.other_j;outs=q.quit_s+q.layoff_s+q.other_s
        require(outj+q.promote<=j and outs<=s,"STOCK_FLOW")
        # Start-of-quarter flows: no fractional people or promotion of new hires.
        j=j-outj-q.promote+q.hire_j;s=s-outs+q.promote+q.hire_s
        require(j+s==oj+os+q.hire_j+q.hire_s-outj-outs,"HEADCOUNT_CONSERVATION")
        paid=(j+s)*w.seconds_per_person
        production_required=l["paid_human_seconds"]*n
        active=l["active_human_seconds"]*n
        require(active<=production_required and production_required+q.training_seconds+q.redeployed_seconds<=paid,"PAID_CAPACITY")
        require(q.promote==0 or q.training_seconds>0,"PROMOTION_TRAINING")
        payroll=F((j*w.junior_cents_per_hour+s*w.senior_cents_per_hour)*w.seconds_per_person,3600)
        revenue=F(l["revenue_eur"])*100*n
        supplier=(F(l["cash_cost_eur"])-F(l["payroll_eur"]))*100*n
        require(supplier>=0,"NONPAYROLL")
        # All scoped non-payroll recurrent costs are assumed eligible for payment lag.
        new_ar=revenue*F(plan.collection_next_quarter_bp,10000)
        new_ap=supplier*F(plan.supplier_next_quarter_bp,10000)
        collected=ar+revenue-new_ar;paid_supplier=ap+supplier-new_ap
        require(ar+revenue==collected+new_ar and ap+supplier==paid_supplier+new_ap,"WORKING_CAPITAL_CONSERVATION")
        oc,od,oa,opay=cash,debt,ar,ap
        debt+=q.debt_draw_cents
        require(q.principal_repaid_cents<=debt,"DEBT_OVERPAYMENT")
        interest=debt*F(plan.quarterly_interest_bp,10000)
        cash_start=cash+q.debt_draw_cents-q.capex_cents-q.transition_cents-q.exit_cents-q.training_cents
        operating=collected-paid_supplier-payroll
        cash=cash_start+operating-interest-q.principal_repaid_cents
        debt-=q.principal_repaid_cents;ar=new_ar;ap=new_ap
        require(debt==od+q.debt_draw_cents-q.principal_repaid_cents,"DEBT_CONSERVATION")
        require(cash==oc+q.debt_draw_cents-q.capex_cents-q.transition_cents-q.exit_cents-q.training_cents+collected-paid_supplier-payroll-interest-q.principal_repaid_cents,"CASH_CONSERVATION")
        require(operating==revenue-supplier-payroll-(ar-oa)+(ap-opay),"CASH_ACCRUAL_BRIDGE")
        min_cash=min(min_cash,cash_start,cash)
        rows.append({"quarter":q.index,"phase":q.phase,"opening_headcount":oj+os,"headcount":j+s,"junior":j,"senior":s,"hires":q.hire_j+q.hire_s,"quits":q.quit_j+q.quit_s,"layoffs":q.layoff_j+q.layoff_s,"other_exits":q.other_j+q.other_s,"promotions":q.promote,"budgeted_hires":q.budgeted_hires,"frozen_hires":q.frozen_hires,"unfilled_nonfrozen_budget":q.budgeted_hires-q.frozen_hires-q.hire_j-q.hire_s,"paid_seconds":paid,"active_production_seconds":active,"allocated_production_seconds":production_required,"training_seconds":q.training_seconds,"redeployed_seconds":q.redeployed_seconds,"unallocated_paid_seconds":paid-production_required-q.training_seconds-q.redeployed_seconds,"sales":l["sales"]*n,"unfinished":l["unfinished_cases"]*n,"revenue_eur":eur(revenue),"payroll_eur":eur(payroll),"nonpayroll_cost_eur":eur(supplier),"accrual_surplus_before_depreciation_eur":eur(revenue-supplier-payroll),"collections_eur":eur(collected),"supplier_payments_eur":eur(paid_supplier),"receivables_eur":eur(ar),"payables_eur":eur(ap),"net_trade_working_capital_eur":eur(ar-ap),"capex_eur":eur(q.capex_cents),"transition_eur":eur(q.transition_cents),"training_cost_eur":eur(q.training_cents),"exit_cost_eur":eur(q.exit_cents),"debt_draw_eur":eur(q.debt_draw_cents),"principal_repayment_eur":eur(q.principal_repaid_cents),"interest_eur":eur(interest),"closing_debt_eur":eur(debt),"cash_after_start_transactions_eur":eur(cash_start),"closing_cash_eur":eur(cash),"operating_cash_flow_eur":eur(operating)})
    r={"plan_ref":plan.key,"quarters":rows,"ending_headcount":j+s,"cumulative_hires":sum(x["hires"] for x in rows),"cumulative_layoffs":sum(x["layoffs"] for x in rows),"cumulative_frozen_hires":sum(x["frozen_hires"] for x in rows),"closing_cash_eur":eur(cash),"closing_debt_eur":eur(debt),"funding_gap_at_sampled_dates_eur":eur(max(F(0),-min_cash)),"funding_status":"UNFUNDED_SHORTFALL" if min_cash<0 else "NO_SHORTFALL_AT_SAMPLED_DATES","phase_pins":pins,"input_sha256":digest(canonical({"plan":asdict(plan),"phase_economics":{k:asdict(phases[k][3]) for k in pins}})),"model_versions":{n:digest((Path(__file__).parent/n).read_bytes()) for n in ("economic_transition.py","economic_firm.py","economic_transform.py","economic_events.py","economic_operations.py","economic_core.py")},"assumptions":plan.assumptions,"status":"CONDITIONAL_NOT_EMPIRICAL","publication":"BLOCK_PUBLICATION"}
    return {"result":r,"sha256":digest(canonical(r))}

def compare(base,reference,phases,a,b):
    require(a.workforce==b.workforce and (a.opening_cash_cents,a.opening_receivable_cents,a.opening_payable_cents,a.opening_debt_cents,a.collection_next_quarter_bp,a.supplier_next_quarter_bp,a.quarterly_interest_bp)==(b.opening_cash_cents,b.opening_receivable_cents,b.opening_payable_cents,b.opening_debt_cents,b.collection_next_quarter_bp,b.supplier_next_quarter_bp,b.quarterly_interest_bp) and [(q.index,q.repeats) for q in a.quarters]==[(q.index,q.repeats) for q in b.quarters],"COMPARISON_SCOPE")
    x=simulate(base,reference,phases,a);y=simulate(base,reference,phases,b)
    u=x["result"];v=y["result"]
    r={"baseline":x,"alternative":y,"headcount_gap":v["ending_headcount"]-u["ending_headcount"],"hires_gap":v["cumulative_hires"]-u["cumulative_hires"],"layoffs_gap":v["cumulative_layoffs"]-u["cumulative_layoffs"],"quarterly_gaps":[{"quarter":i["quarter"],"headcount_gap":k["headcount"]-i["headcount"],"hires_gap":k["hires"]-i["hires"],"payroll_saving_eur":str(F(i["payroll_eur"])-F(k["payroll_eur"]))} for i,k in zip(u["quarters"],v["quarters"])],"interpretation":"Conditional differences of declared trajectories, not causal estimates or individual job losses.","publication":"BLOCK_PUBLICATION"}
    return {"result":r,"sha256":digest(canonical(r))}
