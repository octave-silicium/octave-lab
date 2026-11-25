"""G4 v0.7g1: shared-state maturity stress -> conditional credit -> served capital.
Single opening-period funding batch, no settlement of the counterfactual clearing.
"""
from dataclasses import dataclass, replace, asdict
from fractions import Fraction as F
from .economic_core import require, words, canonical, digest
from .economic_shared_state import State, Project, Event, amount, apply, run_funding
from .economic_financial_network import clear, credit_headroom
from .economic_sector_capital import path, finite

@dataclass(frozen=True)
class BankPolicy:
    bank:str
    capital:str
    existing_rwa:str
    minimum_ratio:str
    new_risk_weight:str
    credit_limit:str
    loss_recognition:str
    evidence:str

def maturity_stress(state,codes,outside,liquidity,*,evidence):
    require(isinstance(state,State) and type(codes) is tuple and len(set(codes))==len(codes) and codes,"STRESS_AXIS")
    ids={a.id:a for a in state.actors}
    require(outside in ids and ids[outside].kind=="EXTERNAL" and outside not in codes and set(codes)<=set(ids),"OUTSIDE")
    require(isinstance(liquidity,dict) and set(liquidity)==set(codes) and words(evidence),"LIQUIDITY_AXIS")
    n=len(codes);ix={k:i for i,k in enumerate(codes)}
    L=[[F(0) for _ in codes] for _ in codes];o=[F(0) for _ in codes]
    relevant=[]
    for p in state.positions:
        if p.instrument not in {"LOAN","TRADE_PAYABLE","INTEREST_PAYABLE"} or p.issuer not in ix:continue
        require(p.due is not None,"UNKNOWN_MATURITY")
        if p.due>state.period:continue
        require(p.holder in ix or p.holder==outside,"UNMAPPED_DUE_HOLDER")
        i=ix[p.issuer];x=amount(p.stock)
        if p.holder==outside:o[i]+=x
        else:L[i][ix[p.holder]]+=x
        relevant.append(asdict(p))
    clearing=clear(codes,L,o,[amount(liquidity[c]) for c in codes],evidence=evidence)
    result={"status":"COUNTERFACTUAL_MATURITY_STRESS","opening_sha256":state.fingerprint,"period":state.period,
            "outside":outside,"mapped_positions":relevant,"clearing":clearing,
            "settlement_booked":False,"liquidity_basis":"EXOGENOUS_SCENARIO_NOT_DEPOSITS"}
    return {"result":result,"sha256":digest(canonical(result))}

def stress_funding_capital(state,codes,outside,liquidity,policies,projects,periods,assets,initial_vintages,orders,*,noncapital_capacity,coverage,evidence):
    require(isinstance(state,State) and state.period==0 and words(evidence),"OPENING_PERIOD_ONLY")
    require(type(policies) is tuple and policies and all(isinstance(p,BankPolicy) for p in policies),"BANK_POLICIES")
    require(type(projects) is tuple and projects and all(isinstance(p,Project) for p in projects),"PROJECTS")
    require(len({p.id for p in projects})==len(projects) and len({p.firm for p in projects})==len(projects),"ONE_PROJECT_PER_FIRM")
    require(len({p.bank for p in policies})==len(policies),"DUPLICATE_BANK")
    ids={a.id:a for a in state.actors};by={a.id:a for a in assets};banks={p.bank:p for p in policies}
    require(all(b in ids and ids[b].kind=="BANK" and b in codes for b in banks),"BANK_MAPPING")
    firms={p.firm for p in projects};suppliers={p.supplier for p in projects};owners={p.owner for p in projects if p.owner is not None}
    require(not (firms&suppliers or firms&owners or suppliers&owners or set(banks)&(firms|suppliers|owners)),"ROLE_OVERLAP")
    require(type(orders) is tuple and len(orders)==len(projects) and {i.id for i in orders}=={p.id for p in projects},"ORDER_MAPPING")
    by_order={i.id:i for i in orders}
    require(all(p.firm in ids and p.supplier in ids and p.bank in banks and p.firm in codes for p in projects),"ACTOR_MAPPING")
    for p in projects:
        i=by_order[p.id];require(i.asset in by and i.period==1 and finite(i.units) and i.units>0,"ORDER_PERIOD")
        a=by[i.asset]
        require(ids[p.firm].sector==a.branch and ids[p.supplier].sector==a.product,"BRANCH_PRODUCT_MAPPING")
        # Unique supplier branch and identity product/branch share mapping required below.
        require(finite(a.acquisition_price) and a.acquisition_price>0,"PRICE")
        require(amount(p.requested)==F(str(i.units))*F(str(a.acquisition_price))*1000000,"EUR_REFERENCE_PRICE_MAPPING")
    require(type(periods) is tuple and periods and all(p.structure.origin=="SYNTHETIC" for p in periods),"SYNTHETIC_ONLY")
    # A supplier is a declared representative of the product branch, not an identified supplier share.
    for p in periods:
        require(all(v==int(i==j) for i,row in enumerate(p.structure.shares) for j,v in enumerate(row)),"IDENTITY_PRODUCT_BRANCH_ONLY")
    unit=state.step_unit.upper()
    stress=maturity_stress(state,codes,outside,liquidity,evidence=evidence)
    alloc={};headrooms={};limits={}
    for bank,b in banks.items():
        requests={p.firm:str(min(amount(p.requested),amount(p.debt_cap)) if "DEBT" in p.order else F(0)) for p in projects if p.bank==bank}
        require(requests,"BANK_WITHOUT_PROJECT")
        r=credit_headroom(stress["result"]["clearing"],bank,capital=b.capital,existing_rwa=b.existing_rwa,minimum_ratio=b.minimum_ratio,
             new_risk_weight=b.new_risk_weight,credit_limit=b.credit_limit,loss_recognition=b.loss_recognition,requests=requests,evidence=b.evidence)
        headrooms[bank]=r;alloc.update(r["result"]["approved"]);limits[bank]=r["result"]["approved_total"]
    limited=tuple(replace(p,debt_cap=str(min(amount(p.debt_cap),amount(alloc[p.firm])))) for p in projects)
    # Preview only; no financial state from this reservation is committed.
    _,preview=run_funding(state,limited,limits,coverage)
    funding=preview["result"]["funding"]["result"];by_funding={p["id"]:p for p in funding["projects"]}
    approved=[]
    for p in projects:
        i=by_order[p.id];a=by[i.asset];paid=amount(by_funding[p.id]["paid_acquisition"])
        if paid:approved.append(replace(i,units=float(paid/(F(str(a.acquisition_price))*1000000))))
    capital=path(periods,assets,initial_vintages,tuple(approved),noncapital_capacity=noncapital_capacity,period_unit=unit,evidence=evidence)
    deliveries={x["id"]:x for x in capital["result"]["periods"][0]["investment_orders"]}
    events=[];results=[]
    for p in projects:
        row=by_funding[p.id];reserved=amount(row["paid_acquisition"]);d=deliveries.get(p.id)
        modeled=F(str(d["acquisition_value"]))*1000000 if d else F(0)
        # Numerical bridge: cap tiny solver overshoots only within explicit tolerance, record residual.
        tolerance=max(F(1,1000000),reserved*F(1,100000000000))
        require(0<=modeled<=reserved+tolerance,"DELIVERY_EXCEEDS_RESERVATION")
        paid=min(reserved,modeled);residual=modeled-paid
        source={k:amount(v)*paid/reserved if reserved else F(0) for k,v in row["sources"].items()}
        require(sum(source.values())==paid,"SETTLEMENT_SOURCES")
        def emit(kind,actor,cp,x,due=None):
            if x:events.append(Event("delivery:"+p.id+":"+kind,state.period,kind,actor,cp,p.bank,str(x),p.evidence,due))
        emit("EQUITY_SUBSCRIPTION",p.owner,p.firm,source["EQUITY"])
        emit("LOAN_ORIGINATION",p.firm,p.bank,source["DEBT"],p.loan_due)
        emit("DEPOSIT_TRANSFER",p.firm,p.supplier,paid)
        results.append({"id":p.id,"firm":p.firm,"requested_eur":p.requested,"bank_ceiling_eur":alloc[p.firm],
             "reserved_eur":str(reserved),"delivered_model_eur":str(modeled),"settled_eur":str(paid),
             "rounding_residual_eur":str(residual),"unused_reservation_eur":str(reserved-paid),
             "financially_unfunded_eur":str(amount(p.requested)-reserved),"supply_unserved_eur":str(reserved-paid),
             "sources_eur":{k:str(v) for k,v in source.items()},"commission_period_model":d["commission_period"] if d else None})
    close,receipt=apply(state,tuple(events))
    for b in banks:
        drawn=sum((amount(r["sources_eur"]["DEBT"]) for r,p in zip(results,projects) if p.bank==b),F(0))
        require(drawn<=amount(limits[b]),"BANK_SETTLEMENT_CAP")
    total_paid=sum((amount(r["settled_eur"]) for r in results),F(0))
    total_residual=sum((amount(r["rounding_residual_eur"]) for r in results),F(0))
    model_total=F(str(capital["result"]["periods"][0]["investment_acquired"]))*1000000
    require(abs(total_paid+total_residual-model_total)<=max(F(1,1000000),abs(model_total)*F(1,100000000000)),"CAPITAL_SETTLEMENT_RECONCILIATION")
    result={"status":"SYNTHETIC_STRESS_FINANCE_CAPITAL_PATH","publication":"BLOCK_PUBLICATION","opening_sha256":state.fingerprint,
            "closing_sha256":close.fingerprint,"stress":stress,"headrooms":headrooms,"reservation":preview,
            "projects":results,"settlement":receipt,"capital":capital,"settled_total_eur":str(total_paid),
            "capital_aggregation_residual_eur":str(model_total-total_paid-total_residual),
            "actual_credit":None,"actual_loss":None,"actual_capacity":None,
            "limitations":["stress not settled or written off; no balance sheet/RWA update, liquidity exogenous, no arrears veto in investment",
                "one opening batch, one project per firm, disjoint firms/suppliers/owners, same-bank settlement, no rollover/reallocation of unused ceilings",
                "gross debt requests capped by project cost, not optimized net demand; pro-rata bank ceilings and sequential reservation; realized deliveries scale source shares",
                "explicit nominal EUR to synthetic fixed reference M EUR at identical price; identity product-branch and declared supplier representative; not real micro-macro mapping",
                "divisible physical delivery can be partial even when funding requires all-or-nothing; no later finance, price, operating cash or credit feedback; no empirical calibration"]}
    return close,{"result":result,"sha256":digest(canonical(result))}
