"""G4 v0.7g3a: unified period replay with a deliberately narrow real-cash closure.
One representative firm per branch, one bank, one household buyer/worker pool,
no intermediate inputs/imports/taxes. Exact financial ledger; float capital kernel.
"""
from dataclasses import dataclass,replace,asdict
from fractions import Fraction as F
from .economic_core import require,words,canonical,digest
from .economic_shared_state import State,Position,Event,Project,amount,apply,advance,run_funding,validate_transversal_coverage
from .economic_shared_settlement import settle,Allowance,Discharge
from .economic_sector_capital import path,finite

@dataclass(frozen=True)
class IntegratedStep:
    production:object
    projects:tuple
    orders:tuple
    interest_rate:str
    recognition:str
    transfers:tuple=()
    discharges:tuple=()
    evidence:str="scenario"

def accrue(state,bank,rate,*,evidence):
    """Simple interest on opening gross principal, including overdue principal.
    No interest-on-interest, no origination-period charge, due now."""
    require(words(evidence),"INTEREST_EVIDENCE")
    r=amount(rate);require(r<=1,"INTEREST_RATE")
    tag="interest:"+str(state.period)
    require(tag not in state.processed_event_ids,"REPLAYED_EVENT")
    pos=state.stocks();rows=[];total=F(0)
    for p in state.positions:
        if p.instrument!="LOAN":continue
        require(p.holder==bank and p.due is not None,"LOAN_SCOPE")
        x=amount(p.stock)*r
        k=("INTEREST_PAYABLE",bank,p.issuer,state.period)
        if x:pos[k]=pos.get(k,F(0))+x
        rows.append({"principal_key":list(p.key),"interest":str(x)})
        total+=x
    close=replace(state,positions=tuple(Position(*k[:3],str(v),k[3]) for k,v in pos.items() if v),processed_event_ids=state.processed_event_ids+(tag,))
    close.net_financial_positions()
    result={"opening_sha256":state.fingerprint,"closing_sha256":close.fingerprint,"rate":str(r),"interest_accrued":str(total),"rows":rows,"evidence":evidence}
    return close,{"result":result,"sha256":digest(canonical(result))}

def integrated_path(state,bank,outside,household,branch_firms,steps,assets,initial_vintages,*,noncapital_capacity,capital_before,other_rwa,loan_weight,minimum_ratio,credit_limit,coverage,allowances=(),evidence):
    require(isinstance(state,State) and state.period==0 and words(evidence),"INITIAL_PERIOD")
    require(type(steps) is tuple and 1<=len(steps)<=24 and all(isinstance(x,IntegratedStep) for x in steps),"HORIZON")
    cov=validate_transversal_coverage(coverage)
    ids={a.id:a for a in state.actors};codes=steps[0].production.structure.codes
    require(isinstance(branch_firms,dict) and set(branch_firms)==set(codes) and len(set(branch_firms.values()))==len(codes),"BRANCH_FIRMS")
    firms=set(branch_firms.values())
    require(household in ids and ids[household].kind=="HOUSEHOLD" and outside in ids and ids[outside].kind=="EXTERNAL" and bank in ids and ids[bank].kind=="BANK","ACTOR_ROLES")
    require(not firms&{bank,outside,household} and all(a in ids and ids[a].kind=="FIRM" and ids[a].sector==k for k,a in branch_firms.items()),"BRANCH_MAPPING")
    by={a.id:a for a in assets};require(len(by)==len(assets),"ASSETS")
    K=amount(capital_before);base=amount(other_rwa);w=amount(loan_weight);ratio=amount(minimum_ratio);limit=amount(credit_limit)
    require(w>0 and 0<ratio<=1,"BANK_POLICY")
    cur=state;aa=allowances;rows=[];periods=[];approved=[];seen=set();previous=None
    gross=lambda st:sum((amount(p.stock) for p in st.positions if p.instrument=="LOAN" and p.holder==bank),F(0))
    dep=lambda a:("DEPOSIT",a,bank,None)
    tol=lambda x:max(F(1,1000000),abs(x)*F(1,100000000000))
    for t,step in enumerate(steps,1):
        require(words(step.evidence) and type(step.transfers) is tuple and all(isinstance(e,Event) and e.kind=="DEPOSIT_TRANSFER" and e.bank==bank for e in step.transfers),"TRANSFERS")
        s=step.production.structure
        require(s.codes==codes and s.origin=="SYNTHETIC","STRUCTURE_SCOPE")
        require(all(v==0 for m in (s.domestic,s.imported) for row in m for v in row) and all(v==0 for v in (*s.other_tax,*s.bridge)),"REAL_CASH_CLOSURE")
        require(all(v==int(i==j) for i,row in enumerate(s.shares) for j,v in enumerate(row)),"IDENTITY_SHARES")
        require(all(0<=x<=1 for x in s.wage) and all(0<=x<=1 for x in s.surplus),"NONNEGATIVE_INCOME")
        require(type(step.projects) is tuple and all(isinstance(p,Project) for p in step.projects),"PROJECTS")
        require(type(step.orders) is tuple and len(step.orders)==len(step.projects) and len({p.id for p in step.projects})==len(step.projects) and len({p.firm for p in step.projects})==len(step.projects),"ORDER_AXIS")
        od={i.id:i for i in step.orders}
        require(set(od)=={p.id for p in step.projects} and not seen&set(od),"DUPLICATE_OR_UNMAPPED_ORDER")
        seen|=set(od)
        buyers={p.firm for p in step.projects};suppliers={p.supplier for p in step.projects}
        require(not buyers&suppliers,"RESERVATION_ROLE_OVERLAP")
        for p in step.projects:
            i=od[p.id];require(p.bank==bank and i.period==t and i.asset in by and finite(i.units) and i.units>0,"ORDER_SCOPE")
            a=by[i.asset];require(branch_firms.get(a.branch)==p.firm and branch_firms.get(a.product)==p.supplier,"PROJECT_MAPPING")
            require(p.owner is None or p.owner in ids and ids[p.owner].kind=="INVESTOR","OWNER_SCOPE")
            require(amount(p.requested)==F(str(i.units))*F(str(a.acquisition_price))*1000000,"PRICE_MAPPING")
        opening=cur;before=K
        cur,trans=apply(cur,step.transfers)
        cur,interest=accrue(cur,bank,step.interest_rate,evidence=step.evidence)
        cur,aa,settled=settle(cur,bank,outside,aa,step.discharges,recognition=step.recognition,evidence=step.evidence)
        K+=F(interest["result"]["interest_accrued"])-F(settled["result"]["net_impairment_expense_proxy"])
        risk=base+w*gross(cur);head=max(F(0),(K/ratio-risk)/w);cap=min(head,limit)
        # Explicit conservative policy: no fresh borrowing by a firm with any overdue liability.
        overdue={p.issuer for p in cur.positions if p.instrument in {"LOAN","TRADE_PAYABLE","INTEREST_PAYABLE"} and p.due is not None and p.due<=cur.period}
        limited=tuple(replace(p,debt_cap="0") if p.firm in overdue else p for p in step.projects)
        _,reservation=run_funding(cur,limited,{bank:cap},coverage)
        funding={p["id"]:p for p in reservation["result"]["funding"]["result"]["projects"]}
        # Other final demand is household consumption, funded only from pre-sale deposits.
        desired=[F(str(x))*1000000 for x in s.final];require(all(x>=0 for x in desired),"DEMAND")
        budget=cur.stocks().get(dep(household),F(0));want=sum(desired,F(0))
        demand_scale=min(F(1),budget/want) if want else F(1)
        demand=[x*demand_scale for x in desired]
        periods.append(replace(step.production,structure=replace(s,final=tuple(float(x/1000000) for x in demand))))
        for p in limited:
            i=od[p.id];a=by[i.asset];reserved=amount(funding[p.id]["paid_acquisition"])
            if reserved:approved.append(replace(i,units=float(reserved/(F(str(a.acquisition_price))*1000000))))
        cp=path(tuple(periods),assets,initial_vintages,tuple(approved),noncapital_capacity=noncapital_capacity,period_unit=state.step_unit.upper(),evidence=evidence)
        caprows=cp["result"]["periods"]
        if previous is not None:require(caprows[:-1]==previous,"PREFIX_DRIFT")
        previous=caprows;row=caprows[-1]
        deliveries={d["id"]:d for d in row["investment_orders"]};events=[];projects=[];sales={a:F(0) for a in firms}
        def emit(id,kind,actor,cp,x,due=None):
            if x:events.append(Event(id,cur.period,kind,actor,cp,bank,str(x),step.evidence,due))
        for p in limited:
            f=funding[p.id];reserved=amount(f["paid_acquisition"]);d=deliveries.get(p.id)
            model=F(str(d["acquisition_value"]))*1000000 if d else F(0)
            require(0<=model<=reserved+tol(reserved),"OVERDELIVERY");paid=min(model,reserved)
            src={k:amount(v)*paid/reserved if reserved else F(0) for k,v in f["sources"].items()}
            require(sum(src.values())==paid,"SOURCE_BALANCE")
            emit("cap:"+p.id+":equity","EQUITY_SUBSCRIPTION",p.owner,p.firm,src["EQUITY"])
            emit("cap:"+p.id+":loan","LOAN_ORIGINATION",p.firm,bank,src["DEBT"],p.loan_due)
            emit("cap:"+p.id+":sale","DEPOSIT_TRANSFER",p.firm,p.supplier,paid)
            sales[p.supplier]+=paid
            projects.append({"id":p.id,"firm":p.firm,"requested_eur":p.requested,"reserved_eur":str(reserved),"delivered_eur":str(paid),"model_delivery_eur":str(model),"rounding_residual_eur":str(model-paid),"sources":{k:str(v) for k,v in src.items()},"commission_period":d["commission_period"] if d else None})
        household_paid=F(0)
        for i,k in enumerate(codes):
            model=F(str(row["other_final_served"][i]))*1000000
            require(0<=model<=demand[i]+tol(demand[i]),"CONSUMPTION_OVERDELIVERY")
            paid=min(model,demand[i]);household_paid+=paid;sales[branch_firms[k]]+=paid
            emit("consumption:"+str(t)+":"+k,"DEPOSIT_TRANSFER",household,branch_firms[k],paid)
        require(household_paid<=budget,"HOUSEHOLD_BUDGET")
        cur,salesreceipt=apply(cur,tuple(events));events=[];firm_rows=[]
        for i,k in enumerate(codes):
            a=branch_firms[k];rev=sales[a];model=F(str(row["allocation"]["feasible_branch_output"][i]))*1000000
            require(abs(rev-model)<=tol(model),"OUTPUT_SALES_RECONCILIATION")
            wage=rev*F(str(s.wage[i]));emit("wage:"+str(t)+":"+k,"DEPOSIT_TRANSFER",a,household,wage)
            firm_rows.append({"firm":a,"branch":k,"sales_eur":str(rev),"wages_eur":str(wage),"gross_operating_cash_proxy_eur":str(rev-wage),"output_model_eur":str(model),"output_sales_residual_eur":str(model-rev)})
        cur,wagereceipt=apply(cur,tuple(events))
        endrisk=base+w*gross(cur);draw=sum((F(p["sources"]["DEBT"]) for p in projects),F(0));require(draw<=cap and endrisk==risk+w*draw,"RWA_RECONCILIATION")
        modeltotal=F(str(row["investment_acquired"]))*1000000
        delivered=sum((F(p["delivered_eur"]) for p in projects),F(0))
        require(abs(modeltotal-delivered)<=tol(modeltotal),"CAPITAL_RECONCILIATION")
        # Total deposits change only through loan creation and bank debt/interest receipts.
        deposits=lambda st:sum((amount(p.stock) for p in st.positions if p.instrument=="DEPOSIT"),F(0))
        require(deposits(cur)==deposits(opening)+draw-F(settled["result"]["bank_receipts"]),"DEPOSIT_PERIOD_IDENTITY")
        cur.net_financial_positions()
        rows.append({"period":t,"opening_sha256":opening.fingerprint,"closing_sha256":cur.fingerprint,"opening_capital_proxy":str(before),"closing_capital_proxy":str(K),"rwa_proxy":str(endrisk),"credit_ceiling":str(cap),"overdue_credit_veto":sorted(overdue),"interest":interest,"settlement":settled,"exogenous_transfers":trans,"reservation":reservation,"projects":projects,"capital":row,"sales":salesreceipt,"wages":wagereceipt,"firms":firm_rows,"household_budget_eur":str(budget),"household_desired_eur":str(want),"household_consumption_eur":str(household_paid),"household_closing_deposits_eur":str(cur.stocks().get(dep(household),F(0))),"deposits_closing_eur":str(deposits(cur)),"investment_residual_eur":str(modeltotal-delivered),"cash_by_actor":{a:str(cur.stocks().get(dep(a),F(0))) for a in sorted(ids) if a!=bank}})
        cur=advance(cur)
    result={"status":"SYNTHETIC_INTEGRATED_FINANCE_CAPITAL_CASH_PATH","publication":"BLOCK_PUBLICATION","opening_sha256":state.fingerprint,"closing_sha256":cur.fingerprint,"coverage":cov,"periods":rows,"capital_receipt":cp,"actual_gdp":None,"actual_profit":None,"actual_employment":None,
            "limitations":["one bank, one representative firm per branch, household buyer/wage pool, no domestic intermediate inputs, imports, taxes or valuation bridge",
                           "explicit opening transfers and demand, fixed prices, sequential reservation, no endogenous investment choice; no automatic cash inflow from unsold output",
                           "simple interest on opening gross principal, bullet maturities, no compounding; accrual income proxy, impairment memo; no full bank balance sheet or regulatory capital",
                           "household wages recycled next period, no savings decision, no external export demand; gross operating cash proxy not profit or GDP",
                           "capital path prefix replay from initial vintages, partial delivery allowed, no backorder, no multiple firms per branch or factor complementarity"]}
    return cur,aa,{"result":result,"sha256":digest(canonical(result))}
