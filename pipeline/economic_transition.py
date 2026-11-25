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
    phase_mix:tuple=() # (phase, number of complete sequential cohorts); empty = legacy single phase

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

def allocation(q):
    if not q.phase_mix:return ((q.phase,q.repeats),)
    require(q.phase=="mixed" and isinstance(q.phase_mix,tuple) and len(q.phase_mix)>=2,"MIX_CONTRACT")
    require(all(isinstance(x,tuple) and len(x)==2 and words(x[0]) and integer(x[1],1,10000) for x in q.phase_mix),"MIX_ROWS")
    require(len({x[0] for x in q.phase_mix})==len(q.phase_mix) and sum(x[1] for x in q.phase_mix)==q.repeats,"MIX_CONSERVATION")
    return q.phase_mix

def validate(plan,phases):
    plan.key;w=plan.workforce
    require(words(plan.assumptions) and all(integer(x,0,100000) for x in (w.junior,w.senior)) and integer(w.seconds_per_person,1,92*86400) and all(money(x) for x in (w.junior_cents_per_hour,w.senior_cents_per_hour,plan.opening_cash_cents,plan.opening_receivable_cents,plan.opening_payable_cents,plan.opening_debt_cents)),"PLAN")
    require(all(integer(x,0,10000) for x in (plan.collection_next_quarter_bp,plan.supplier_next_quarter_bp,plan.quarterly_interest_bp)),"RATES")
    require(isinstance(plan.quarters,tuple) and 1<=len(plan.quarters)<=120,"HORIZON")
    dates=(plan.anticipation_quarter,plan.decision_quarter,plan.investment_quarter,plan.production_quarter)
    require(all(x is None for x in dates) or (all(integer(x,1,len(plan.quarters)) for x in dates) and list(dates)==sorted(dates)),"MILESTONES")
    for i,q in enumerate(plan.quarters,1):
        require(q.index==i and integer(q.repeats,1,10000) and all(k in phases for k,n in allocation(q)),"QUARTER")
        require(all(integer(getattr(q,k),0,100000) for k in ("budgeted_hires","frozen_hires","hire_j","hire_s","quit_j","quit_s","layoff_j","layoff_s","other_j","other_s","promote")),"WORKFORCE_FLOW")
        require(q.hire_j+q.hire_s+q.frozen_hires<=q.budgeted_hires,"HIRING_BUDGET")
        require(all(integer(x,0,10**12) for x in (q.training_seconds,q.redeployed_seconds)) and all(money(getattr(q,k)) for k in ("training_cents","exit_cents","capex_cents","transition_cents","debt_draw_cents","principal_repaid_cents")),"QUARTER_COST")
        require(all(k=="reference" for k,n in allocation(q)) if plan.production_quarter is None or i<plan.production_quarter else True,"PRE_DEPLOYMENT")
    if plan.investment_quarter is not None:require(plan.quarters[plan.investment_quarter-1].capex_cents>0,"INVESTMENT_MILESTONE")

def cash_step(cash,ar,ap,debt,revenue,supplier,payroll,collection_bp,supplier_bp,interest_bp,draw,repayment,start_cost):
    """Shared exact cash and trade-credit bridge; all monetary inputs in cents."""
    require(all(x>=0 for x in (ar,ap,debt,revenue,supplier,payroll,draw,repayment,start_cost)),"CASH_INPUT")
    require(all(integer(x,0,10000) for x in (collection_bp,supplier_bp,interest_bp)),"RATES")
    new_ar=revenue*F(collection_bp,10000);new_ap=supplier*F(supplier_bp,10000)
    collected=ar+revenue-new_ar;paid_supplier=ap+supplier-new_ap
    require(ar+revenue==collected+new_ar and ap+supplier==paid_supplier+new_ap,"WORKING_CAPITAL_CONSERVATION")
    new_debt=debt+draw
    require(repayment<=new_debt,"DEBT_OVERPAYMENT")
    interest=new_debt*F(interest_bp,10000)
    cash_start=cash+draw-start_cost
    operating=collected-paid_supplier-payroll
    closing=cash_start+operating-interest-repayment
    require(operating==revenue-supplier-payroll-(new_ar-ar)+(new_ap-ap),"CASH_ACCRUAL_BRIDGE")
    return {"cash":closing,"ar":new_ar,"ap":new_ap,"debt":new_debt-repayment,"cash_start":cash_start,"interest":interest,"operating":operating,"collected":collected,"paid_supplier":paid_supplier}

def simulate(base,reference,phases,plan):
    # Each phase is a process, event schedule, design, financial configuration.
    # Quality-gated replay; no supplied aggregate productivity or revenue accepted.
    require("reference" in phases and phases["reference"]==reference,"REFERENCE_PHASE")
    validate(plan,phases)
    rp,rs,rd,rc=reference
    require(rp==base,"REFERENCE_PROCESS")
    cache={};pins={}
    for key in sorted({k for q in plan.quarters for k,n in allocation(q)}):
        p,s,d,c=phases[key]
        op=compare_design(base,rs,rd,p,s,d)
        require(op["result"]["quality_comparable"],"BLOCK_OPERATIONAL_QUALITY")
        require(c.max_sales==rc.max_sales and c.price_cents_per_sale==rc.price_cents_per_sale,"PRICE_DEMAND_SCOPE")
        require({k for k,v in c.fixed_cash_costs}=={k for k,v in rc.fixed_cash_costs},"FIXED_CATEGORY_COMPARABILITY")
        l=ledger(op["result"]["alternative"],c)
        e=op["result"]["alternative"]["result"]["event_receipt"]["result"]
        cache[key]=(l,e);pins[key]=op["sha256"]
    w=plan.workforce;j=w.junior;s=w.senior
    cash=F(plan.opening_cash_cents);ar=F(plan.opening_receivable_cents);ap=F(plan.opening_payable_cents);debt=F(plan.opening_debt_cents)
    min_cash=cash;rows=[]
    eur=lambda x:str(F(x)/100)
    for q in plan.quarters:
        mix=allocation(q)
        require(sum(cache[k][1]["horizon_seconds"]*n for k,n in mix)<=90*86400,"QUARTER_TIME")
        def total(field):return sum(F(cache[k][0][field])*n for k,n in mix)
        sales=int(total("sales"));unfinished=int(total("unfinished_cases"))
        # One cohort assigned exactly once; no simultaneous execution across cohorts.
        phase_rows=[{"phase":k,"cohorts":n,"sales":cache[k][0]["sales"]*n,"paid_production_seconds":cache[k][0]["paid_human_seconds"]*n,"operation_sha256":pins[k]} for k,n in mix]
        oj,os=j,s;outj=q.quit_j+q.layoff_j+q.other_j;outs=q.quit_s+q.layoff_s+q.other_s
        require(outj+q.promote<=j and outs<=s,"STOCK_FLOW")
        # Start-of-quarter flows: no fractional people or promotion of new hires.
        j=j-outj-q.promote+q.hire_j;s=s-outs+q.promote+q.hire_s
        require(j+s==oj+os+q.hire_j+q.hire_s-outj-outs,"HEADCOUNT_CONSERVATION")
        paid=(j+s)*w.seconds_per_person
        production_required=int(total("paid_human_seconds"))
        active=int(total("active_human_seconds"))
        require(active<=production_required and production_required+q.training_seconds+q.redeployed_seconds<=paid,"PAID_CAPACITY")
        require(q.promote==0 or q.training_seconds>0,"PROMOTION_TRAINING")
        payroll=F((j*w.junior_cents_per_hour+s*w.senior_cents_per_hour)*w.seconds_per_person,3600)
        revenue=total("revenue_eur")*100
        supplier=(total("cash_cost_eur")-total("payroll_eur"))*100
        require(supplier>=0,"NONPAYROLL")
        step=cash_step(cash,ar,ap,debt,revenue,supplier,payroll,plan.collection_next_quarter_bp,plan.supplier_next_quarter_bp,plan.quarterly_interest_bp,q.debt_draw_cents,q.principal_repaid_cents,q.capex_cents+q.transition_cents+q.exit_cents+q.training_cents)
        cash,ar,ap,debt=(step[k] for k in ("cash","ar","ap","debt"))
        cash_start,operating,interest,collected,paid_supplier=(step[k] for k in ("cash_start","operating","interest","collected","paid_supplier"))
        min_cash=min(min_cash,cash_start,cash)
        rows.append({"quarter":q.index,"phase":q.phase,"opening_headcount":oj+os,"headcount":j+s,"junior":j,"senior":s,"hires":q.hire_j+q.hire_s,"quits":q.quit_j+q.quit_s,"layoffs":q.layoff_j+q.layoff_s,"other_exits":q.other_j+q.other_s,"promotions":q.promote,"budgeted_hires":q.budgeted_hires,"frozen_hires":q.frozen_hires,"unfilled_nonfrozen_budget":q.budgeted_hires-q.frozen_hires-q.hire_j-q.hire_s,"paid_seconds":paid,"active_production_seconds":active,"allocated_production_seconds":production_required,"training_seconds":q.training_seconds,"redeployed_seconds":q.redeployed_seconds,"unallocated_paid_seconds":paid-production_required-q.training_seconds-q.redeployed_seconds,"sales":sales,"unfinished":unfinished,"phase_mix":phase_rows,"reference_cohort_fraction":str(F(sum(n for k,n in mix if k=="reference"),q.repeats)),"revenue_eur":eur(revenue),"payroll_eur":eur(payroll),"nonpayroll_cost_eur":eur(supplier),"accrual_surplus_before_depreciation_eur":eur(revenue-supplier-payroll),"collections_eur":eur(collected),"supplier_payments_eur":eur(paid_supplier),"receivables_eur":eur(ar),"payables_eur":eur(ap),"net_trade_working_capital_eur":eur(ar-ap),"capex_eur":eur(q.capex_cents),"transition_eur":eur(q.transition_cents),"training_cost_eur":eur(q.training_cents),"exit_cost_eur":eur(q.exit_cents),"debt_draw_eur":eur(q.debt_draw_cents),"principal_repayment_eur":eur(q.principal_repaid_cents),"interest_eur":eur(interest),"closing_debt_eur":eur(debt),"cash_after_start_transactions_eur":eur(cash_start),"closing_cash_eur":eur(cash),"operating_cash_flow_eur":eur(operating)})
    r={"plan_ref":plan.key,"quarters":rows,"ending_headcount":j+s,"cumulative_hires":sum(x["hires"] for x in rows),"cumulative_layoffs":sum(x["layoffs"] for x in rows),"cumulative_frozen_hires":sum(x["frozen_hires"] for x in rows),"closing_cash_eur":eur(cash),"closing_debt_eur":eur(debt),"funding_gap_at_sampled_dates_eur":eur(max(F(0),-min_cash)),"funding_status":"UNFUNDED_SHORTFALL" if min_cash<0 else "NO_SHORTFALL_AT_SAMPLED_DATES","phase_pins":pins,"input_sha256":digest(canonical({"plan":asdict(plan),"phase_economics":{k:asdict(phases[k][3]) for k in pins}})),"model_versions":{n:digest((Path(__file__).parent/n).read_bytes()) for n in ("economic_transition.py","economic_firm.py","economic_transform.py","economic_events.py","economic_operations.py","economic_core.py")},"assumptions":plan.assumptions,"status":"CONDITIONAL_NOT_EMPIRICAL","publication":"BLOCK_PUBLICATION"}
    return {"result":r,"sha256":digest(canonical(r))}

def compare(base,reference,phases,a,b):
    require(a.workforce==b.workforce and (a.opening_cash_cents,a.opening_receivable_cents,a.opening_payable_cents,a.opening_debt_cents,a.collection_next_quarter_bp,a.supplier_next_quarter_bp,a.quarterly_interest_bp)==(b.opening_cash_cents,b.opening_receivable_cents,b.opening_payable_cents,b.opening_debt_cents,b.collection_next_quarter_bp,b.supplier_next_quarter_bp,b.quarterly_interest_bp) and [(q.index,q.repeats) for q in a.quarters]==[(q.index,q.repeats) for q in b.quarters],"COMPARISON_SCOPE")
    x=simulate(base,reference,phases,a);y=simulate(base,reference,phases,b)
    u=x["result"];v=y["result"]
    r={"baseline":x,"alternative":y,"headcount_gap":v["ending_headcount"]-u["ending_headcount"],"hires_gap":v["cumulative_hires"]-u["cumulative_hires"],"layoffs_gap":v["cumulative_layoffs"]-u["cumulative_layoffs"],"quarterly_gaps":[{"quarter":i["quarter"],"headcount_gap":k["headcount"]-i["headcount"],"hires_gap":k["hires"]-i["hires"],"payroll_saving_eur":str(F(i["payroll_eur"])-F(k["payroll_eur"]))} for i,k in zip(u["quarters"],v["quarters"])],"interpretation":"Conditional differences of declared trajectories, not causal estimates or individual job losses.","publication":"BLOCK_PUBLICATION"}
    return {"result":r,"sha256":digest(canonical(r))}

def valuation(receipt,quarterly_discount_bp,terminal_asset_cents=0,settle_trade=True):
    """Unlevered finite-horizon value, reused by skill and investigation adapters."""
    require(integer(quarterly_discount_bp,0,10000) and money(terminal_asset_cents) and type(settle_trade) is bool,"VALUATION_PARAMETERS")
    rows=receipt["result"]["quarters"];rate=1+F(quarterly_discount_bp,10000)
    flows=[];value=F(0)
    for q in rows:
        i=q["quarter"]
        start=-sum(F(q[x]) for x in ("capex_eur","transition_eur","training_cost_eur","exit_cost_eur"))
        end=F(q["operating_cash_flow_eur"])
        value+=start/rate**(i-1)+end/rate**i
        flows.append({"quarter":i,"start_eur":str(start),"end_eur":str(end)})
    terminal=F(terminal_asset_cents,100)
    if settle_trade:terminal+=F(rows[-1]["receivables_eur"])-F(rows[-1]["payables_eur"])
    value+=terminal/rate**len(rows)
    return {"npv_eur":str(value),"flows":flows,"terminal_eur":str(terminal),"quarterly_discount_bp":quarterly_discount_bp,"settle_trade":settle_trade,"terminal_asset_cents":terminal_asset_cents,"scope":"Unlevered before tax, no ongoing enterprise value, excludes debt draw, repayment and interest; expert work not monetized."}

def assess(base,reference,phases,a,b,rate=200,terminal_assets=(0,0)):
    receipt=compare(base,reference,phases,a,b);x=receipt["result"]
    u=valuation(x["baseline"],rate,terminal_assets[0]);v=valuation(x["alternative"],rate,terminal_assets[1])
    r={"transition_comparison":receipt,"baseline_valuation":u,"alternative_valuation":v,"incremental_unlevered_npv_eur":str(F(v["npv_eur"])-F(u["npv_eur"])),"funding_status_both":[x[k]["result"]["funding_status"] for k in ("baseline","alternative")],"valuation_status":"CONDITIONAL_NOT_EMPIRICAL","publication":"BLOCK_PUBLICATION"}
    return {"result":r,"sha256":digest(canonical(r))}
