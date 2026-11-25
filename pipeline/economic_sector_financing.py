"""G4 v0.7d: conditional borrower cash/debt ledger coupled to delivered capital.
Single synthetic borrower pool, fixed reference prices; no bank equilibrium."""
import math
from dataclasses import dataclass,replace,asdict
from .economic_sector_capital import path,finite,words,balance
from .economic_sector_structural import require
from .economic_core import canonical,digest

@dataclass(frozen=True)
class Funding:
    equity_injection:float
    debt_ceiling:float
    new_credit_limit:float
    interest_rate:float
    principal_fraction:float # of opening principal not already overdue
    cash_reserve:float
    surplus_to_cash:float # signed operating surplus proxy, realized at close
    other_operating_cash:float # explicit signed adjustment, close
    evidence:str

def funded_path(periods,assets,initial_vintages,investments,policies,*,borrower,initial_cash,initial_debt,noncapital_capacity,period_unit,evidence):
    require(isinstance(periods,tuple) and 1<=len(periods)<=24 and isinstance(policies,tuple) and len(periods)==len(policies),"HORIZON")
    require(words(evidence) and borrower in periods[0].structure.codes,"BORROWER")
    require(all(finite(x) and x>=0 for x in (initial_cash,initial_debt)),"INITIAL_FINANCE")
    require(isinstance(assets,tuple) and assets and len({a.id for a in assets})==len(assets),"ASSETS")
    by={a.id:a for a in assets};idx=periods[0].structure.codes.index(borrower)
    require(isinstance(investments,tuple) and len({i.id for i in investments})==len(investments),"ORDERS")
    # Reuse capital input validation even when no financing is available.
    for i in investments:
        require(i.asset in by and by[i.asset].branch==borrower and words(i.id) and words(i.evidence) and type(i.period) is int and 1<=i.period<=len(periods) and type(i.lag) is int and 1<=i.lag<=120 and finite(i.units) and i.units>0,"ORDER_SCOPE")
    cash=float(initial_cash);debt=float(initial_debt);interest_arrears=0.;principal_overdue=0.;operating_arrears=0.
    approved=[];rows=[]
    for t,(p,f) in enumerate(zip(periods,policies),1):
        require(words(f.evidence) and all(finite(x) and x>=0 for x in (f.equity_injection,f.debt_ceiling,f.new_credit_limit,f.cash_reserve)),"FUNDING")
        require(all(finite(x) and 0<=x<=1 for x in (f.interest_rate,f.principal_fraction,f.surplus_to_cash)) and finite(f.other_operating_cash),"RATES")
        oc,od,oi,op,oo=cash,debt,interest_arrears,principal_overdue,operating_arrears
        cash+=f.equity_injection
        operating_paid=min(cash,operating_arrears);cash-=operating_paid;operating_arrears-=operating_paid
        interest=od*f.interest_rate
        interest_due=oi+interest;interest_paid=min(cash,interest_due);cash-=interest_paid;interest_arrears=interest_due-interest_paid
        principal_due=op+(od-op)*f.principal_fraction
        principal_paid=min(cash,principal_due);cash-=principal_paid;debt-=principal_paid;principal_overdue=principal_due-principal_paid
        blocked=operating_arrears>1e-10 or interest_arrears>1e-10 or principal_overdue>1e-10
        available_cash=max(0.,cash-f.cash_reserve)
        credit=0. if blocked else min(f.new_credit_limit,max(0.,f.debt_ceiling-debt))
        orders=[i for i in investments if i.period==t]
        wanted=math.fsum(i.units*by[i.asset].acquisition_price for i in orders)
        ceiling=0. if blocked else available_cash+credit
        fraction=min(1.,ceiling/wanted) if wanted else 0.
        current=[replace(i,units=i.units*fraction) for i in orders if fraction>0]
        approved.extend(current)
        # Prefix replay only: later periods and later commitments never enter current allocation.
        cap=path(periods[:t],assets,initial_vintages,tuple(approved),noncapital_capacity=noncapital_capacity,period_unit=period_unit,evidence=evidence)["result"]
        row=cap["periods"][-1];acquired=row["investment_acquired"]
        balance(acquired,min(acquired,ceiling),"ACQUISITION_FINANCE")
        cash_used=min(available_cash,acquired);draw=max(0.,acquired-cash_used)
        require(draw<=credit+1e-9*max(1,credit),"CREDIT_LIMIT")
        cash-=cash_used;debt+=draw
        gross_surplus=row["allocation"]["feasible_branch_output"][idx]*p.structure.surplus[idx]
        operating_flow=gross_surplus*f.surplus_to_cash+f.other_operating_cash
        received=max(0.,operating_flow);loss=max(0.,-operating_flow)
        cash+=received;loss_paid=min(cash,loss);cash-=loss_paid;operating_arrears+=loss-loss_paid
        balance(cash,oc+f.equity_injection-operating_paid-interest_paid-principal_paid+draw-acquired+received-loss_paid,"CASH_BALANCE")
        balance(debt,od+draw-principal_paid,"DEBT_BALANCE")
        balance(interest_arrears,oi+interest-interest_paid,"INTEREST_BALANCE")
        balance(principal_overdue,op+(od-op)*f.principal_fraction-principal_paid,"PRINCIPAL_OVERDUE")
        balance(operating_arrears,oo-operating_paid+loss-loss_paid,"OPERATING_ARREARS")
        require(all(math.isfinite(x) and x>=-1e-10 for x in (cash,debt,interest_arrears,principal_overdue,operating_arrears)) and principal_overdue<=debt+1e-9,"FINANCE_NONNEGATIVE")
        rows.append({"period":t,"opening_cash":oc,"opening_debt":od,"equity_injection":f.equity_injection,"interest_accrued":interest,"interest_paid":interest_paid,"principal_due":principal_due,"principal_paid":principal_paid,"old_operating_arrears_paid":operating_paid,"investment_blocked_by_arrears":blocked,"investment_requested":wanted,"investment_financially_approved":wanted*fraction,"investment_acquired":acquired,"unfinanced_investment":wanted*(1-fraction),"approved_but_undelivered":max(0.,wanted*fraction-acquired),"cash_used_for_acquisition":cash_used,"new_debt_draw":draw,"operating_surplus_proxy":gross_surplus,"net_operating_cash_proxy":operating_flow,"operating_cash_received":received,"operating_loss_paid":loss_paid,"closing_cash":cash,"closing_debt":debt,"closing_interest_arrears":interest_arrears,"closing_principal_overdue":principal_overdue,"closing_operating_arrears":operating_arrears,"debt_ceiling_breach":max(0.,debt-f.debt_ceiling),"reserve_shortfall":max(0.,f.cash_reserve-cash),"capital":row,"policy":asdict(f)})
    result={"status":"CONDITIONAL_FINANCED_CAPITAL_PATH","publication":"BLOCK_PUBLICATION","borrower":borrower,"period_unit":period_unit,"periods":rows,"pending":cap["pending"],"evidence":evidence,"actual_default":None,"actual_profit":None,"gdp":None,"employment":None,"limitations":["single synthetic borrower pool, no lending sector or counterparty balance sheet","operating cash proxy is assumed share of branch gross surplus plus explicit adjustment, not measured cash flow; no double deduction of depreciation","equity and credit limits exogenous; no equity ownership dilution, loan maturity schedule, collateral, bank risk or endogenous rate","cash waterfall operating arrears then interest then principal; principal overdue included in debt, no compounding interest arrears","new credit drawn only on served investment after opening service and reserve; no funding of operating arrears; reserve may be breached by losses or debt service","no insolvency/liquidation, other liabilities, full balance sheet, taxes or price/income feedback; no empirical admission"]}
    return {"result":result,"sha256":digest(canonical(result))}
