"""G4 v0.7g: controlled finance-capital-work scenario comparison.
Modeled perimeter only; no empirical maturity, full balance sheet or observed employment.
"""
from dataclasses import dataclass,replace
from fractions import Fraction as F
from .economic_core import require,words,canonical,digest
from .economic_shared_state import amount
from .economic_operating_path import operating_path

@dataclass(frozen=True)
class BankScenario:
    id:str
    capital:str
    credit_limit:str
    evidence:str

def modeled_balance(state,bank,allowances,capital_receipt,branch_firms,capital_proxy,*,as_of):
    """Financial positions plus attributed productive capital, not full accounting equity."""
    by={a["id"]:a for a in capital_receipt["result"]["assets"]}
    owned={a.id:F(0) for a in state.actors}
    for v in list(capital_receipt["result"]["periods"][-1]["active_vintages"])+capital_receipt["result"]["pending"]:
        owned[branch_firms[by[v["asset"]]["branch"]]]+=F(str(v["carrying_value"]))*1000000
    memo=sum((amount(a.value) for a in allowances),F(0))
    rows={}
    for a in state.actors:
        pos=state.positions
        A=sum((amount(p.stock) for p in pos if p.holder==a.id),F(0))
        E=sum((amount(p.stock) for p in pos if p.issuer==a.id and p.instrument=="EQUITY"),F(0))
        D=sum((amount(p.stock) for p in pos if p.issuer==a.id and p.instrument!="EQUITY"),F(0))
        dep=sum((amount(p.stock) for p in pos if p.holder==a.id and p.instrument=="DEPOSIT"),F(0))
        due=sum((amount(p.stock) for p in pos if p.issuer==a.id and p.instrument in {"LOAN","TRADE_PAYABLE","INTEREST_PAYABLE"} and p.due is not None and p.due<=as_of),F(0))
        future=sum((amount(p.stock) for p in pos if p.issuer==a.id and p.instrument in {"LOAN","TRADE_PAYABLE","INTEREST_PAYABLE"} and p.due is not None and p.due>as_of),F(0))
        unknown=sum((amount(p.stock) for p in pos if p.issuer==a.id and p.instrument in {"LOAN","TRADE_PAYABLE","INTEREST_PAYABLE"} and p.due is None),F(0))
        allowance=memo if a.id==bank else F(0)
        rows[a.id]={"financial_assets_gross":str(A),"non_equity_financial_liabilities":str(D),"issued_equity_claims":str(E),
                    "financial_net_position_gross":str(A-D-E),"productive_capital_proxy":str(owned[a.id]),"cash_deposits":str(dep),
                    "due_debt_gross":str(due),"future_debt_gross":str(future),"unknown_maturity_debt_gross":str(unknown),
                    "bank_allowance_memo":str(allowance),"modeled_assets_less_non_equity_liabilities_net_of_allowance":str(A+owned[a.id]-D-allowance),
                    "full_balance_sheet":None,"legal_solvency":None}
    require(sum((F(r["financial_net_position_gross"]) for r in rows.values()),F(0))==0,"FINANCIAL_MATCH")
    b=rows[bank];b["bank_capital_policy_proxy"]=str(capital_proxy)
    b["unreconciled_difference_policy_vs_modeled_net_assets"]=str(F(capital_proxy)-F(b["modeled_assets_less_non_equity_liabilities_net_of_allowance"]))
    return rows

def compare(state,bank,outside,household,government,branch_firms,steps,assets,initial_vintages,scenarios,*,hourly_compensation,reference_hours,noncapital_capacity,other_rwa,loan_weight,minimum_ratio,coverage,evidence,allowances=()):
    require(words(evidence) and type(scenarios) is tuple and 2<=len(scenarios)<=8 and all(isinstance(s,BankScenario) for s in scenarios),"SCENARIOS")
    require(len({s.id for s in scenarios})==len(scenarios) and all(words(s.id) and words(s.evidence) for s in scenarios),"SCENARIO_AXIS")
    require(set(hourly_compensation)==set(reference_hours)==set(branch_firms),"WORK_AXIS")
    rate={k:amount(v) for k,v in hourly_compensation.items()};hrs={k:amount(v) for k,v in reference_hours.items()}
    require(all(v>0 for v in (*rate.values(),*hrs.values())),"WORK_PARAMETERS")
    require(type(steps) is tuple and 1<=len(steps)<=24,"HORIZON")
    allrows={}
    for scenario in scenarios:
        rows=[];previous=[]
        for t in range(1,len(steps)+1):
            close,aa,receipt=operating_path(state,bank,outside,household,government,branch_firms,steps[:t],assets,initial_vintages,
                 noncapital_capacity=noncapital_capacity,capital_before=scenario.capital,other_rwa=other_rwa,loan_weight=loan_weight,
                 minimum_ratio=minimum_ratio,credit_limit=scenario.credit_limit,coverage=coverage,evidence=evidence,allowances=allowances)
            rr=receipt["result"];require(rr["periods"][:-1]==previous,"SCENARIO_PREFIX_DRIFT");previous=rr["periods"];r=previous[-1]
            labor={}
            for firm in r["firms"]:
                k=firm["branch"];wage=F(firm["wages_eur"]);h=wage/rate[k]
                labor[k]={"wage_bill_eur":str(wage),"assumed_hourly_compensation_eur":str(rate[k]),"conditional_paid_hours":str(h),
                          "reference_hours_per_fte":str(hrs[k]),"conditional_fte_equivalent":str(h/hrs[k]),"actual_employed_people":None}
            rows.append({"period":t,"source_receipt_sha256":receipt["sha256"],"balance":modeled_balance(close,bank,aa,rr["capital_receipt"],branch_firms,r["closing_capital_proxy"],as_of=close.period-1),
                 "credit_ceiling":r["credit_ceiling"],"investment_settled_eur":str(sum((F(p["delivered_eur"]) for p in r["projects"]),F(0))),
                 "capacity_reference_m_eur":r["capital"]["capacity"],"output_reference_m_eur":r["capital"]["allocation"]["feasible_branch_output"],
                 "conditional_work":labor,"household_consumption_eur":r["household_consumption_eur"],"bank_capital_proxy":r["closing_capital_proxy"]})
        allrows[scenario.id]=rows
    base=scenarios[0].id;diffs={}
    for s in scenarios[1:]:
        diffs[s.id]=[{"period":a["period"],"investment_delta_eur":str(F(b["investment_settled_eur"])-F(a["investment_settled_eur"])),
                       "conditional_hours_delta":{k:str(F(b["conditional_work"][k]["conditional_paid_hours"])-F(a["conditional_work"][k]["conditional_paid_hours"])) for k in branch_firms},
                       "output_delta_reference_m_eur":[y-x for x,y in zip(a["output_reference_m_eur"],b["output_reference_m_eur"])]} for a,b in zip(allrows[base],allrows[s.id])]
    result={"status":"CONDITIONAL_FINANCE_CAPITAL_WORK_SCENARIOS","publication":"BLOCK_PUBLICATION","reference_scenario":base,"scenario_parameters":[{"id":s.id,"capital":s.capital,"credit_limit":s.credit_limit,"evidence":s.evidence} for s in scenarios],"scenarios":allrows,"differences":diffs,
           "actual_jobs":None,"actual_gdp":None,"actual_regulatory_capital":None,"limits":["fixed hourly compensation and reference hours convert wage bills to conditional paid-hour equivalents, not employment demand or headcounts",
             "representative actors, no labor complementarity, hiring/friction, wage response or causal identification",
             "modeled assets and obligations only, productive asset attribution by representative branch, issued equity claims separated from debt, unobserved balances not plugged",
             "bank policy capital proxy is not reconciled regulatory equity; residual explicitly exposed, no full accounts or empirical calibration",
             "prefix replay from identical initial state, only declared bank capital/limit varied; no probabilistic inference"]}
    return {"result":result,"sha256":digest(canonical(result))}
