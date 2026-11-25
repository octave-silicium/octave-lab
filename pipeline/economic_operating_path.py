"""G4 v0.7g3b: pre-funded intermediate purchases, domestic taxes and loan instalments. Restricted synthetic closure; no equilibrium or observed GDP."""
from dataclasses import dataclass,replace,asdict
from fractions import Fraction as F
from .economic_core import require,words,canonical,digest
from .economic_shared_state import State,Position,Event,Project,amount,apply,advance,run_funding,validate_transversal_coverage
from .economic_shared_settlement import settle,Allowance,Discharge
from .economic_sector_capital import path,finite

from .economic_integrated_path import accrue
from .economic_sector_structural import state as unconstrained

@dataclass(frozen=True)
class OperatingStep:
    production:object
    projects:tuple
    orders:tuple
    interest_rate:str
    recognition:str
    transfers:tuple=()
    discharges:tuple=()
    evidence:str="scenario"
    amortization:tuple=() # (project id, ((absolute due, share), ...))

def operating_path(state,bank,outside,household,government,branch_firms,steps,assets,initial_vintages,*,noncapital_capacity,capital_before,other_rwa,loan_weight,minimum_ratio,credit_limit,coverage,allowances=(),evidence):
    require(isinstance(state,State) and state.period==0 and words(evidence),"INITIAL_PERIOD")
    require(type(steps) is tuple and 1<=len(steps)<=24 and all(isinstance(x,OperatingStep) for x in steps),"HORIZON")
    cov=validate_transversal_coverage(coverage)
    ids={a.id:a for a in state.actors};codes=steps[0].production.structure.codes
    require(isinstance(branch_firms,dict) and set(branch_firms)==set(codes) and len(set(branch_firms.values()))==len(codes),"BRANCH_FIRMS")
    firms=set(branch_firms.values())
    require(household in ids and ids[household].kind=="HOUSEHOLD" and outside in ids and ids[outside].kind=="EXTERNAL" and bank in ids and ids[bank].kind=="BANK","ACTOR_ROLES")
    require(government in ids and ids[government].kind=="GOVERNMENT","GOVERNMENT")
    require(not firms&{bank,outside,household,government} and all(a in ids and ids[a].kind=="FIRM" and ids[a].sector==k for k,a in branch_firms.items()),"BRANCH_MAPPING")
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
        require(all(v==0 for v in s.bridge) and all(0<=v<=1 for v in s.other_tax),"TAX_AND_VALUATION_SCOPE")
        require(all(v==int(i==j) for i,row in enumerate(s.shares) for j,v in enumerate(row)),"IDENTITY_SHARES")
        require(all(0<=x<=1 for x in s.wage) and all(0<=x<=1 for x in s.surplus),"NONNEGATIVE_INCOME")
        require(type(step.projects) is tuple and all(isinstance(p,Project) for p in step.projects),"PROJECTS")
        require(type(step.orders) is tuple and len(step.orders)==len(step.projects) and len({p.id for p in step.projects})==len(step.projects) and len({p.firm for p in step.projects})==len(step.projects),"ORDER_AXIS")
        od={i.id:i for i in step.orders}
        require(set(od)=={p.id for p in step.projects} and not seen&set(od),"DUPLICATE_OR_UNMAPPED_ORDER")
        seen|=set(od)
        require(type(step.amortization) is tuple and len(dict(step.amortization))==len(step.amortization),"AMORTIZATION_AXIS")
        schedules=dict(step.amortization)
        require(set(schedules)<=set(od),"AMORTIZATION_PROJECT")
        for p in step.projects:
            if p.id not in schedules:continue
            parts=schedules[p.id]
            require(type(parts) is tuple and parts and "DEBT" in p.order and all(type(d) is int and d>cur.period and amount(v)>0 for d,v in parts),"AMORTIZATION_DUE")
            require(len({d for d,v in parts})==len(parts) and sum((amount(v) for d,v in parts),F(0))==1 and max(d for d,v in parts)==p.loan_due,"AMORTIZATION_SHARES")
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
        # Reserve gross intermediate purchases from opening cash after the full cash contribution.
        # No same-period sales, new investment borrowing or household wages finance inputs.
        reserved_cash={a:F(0) for a in firms}
        trial_orders=[]
        trial_demand=list(demand)
        for p in limited:
            f=funding[p.id];reserved_cash[p.firm]+=amount(f["sources"]["CASH"])
            i=od[p.id];a=by[i.asset];trial_demand[codes.index(a.product)]+=amount(f["paid_acquisition"])
        req=unconstrained(replace(s,final=tuple(float(x/1000000) for x in trial_demand)))
        needs={}
        scales=[F(1)]
        for j,k in enumerate(codes):
            a=branch_firms[k]
            coeff=sum((F(str(s.domestic[i][j])) for i in range(len(codes)) if i!=j),F(0))+sum((F(str(s.imported[i][j])) for i in range(len(codes))),F(0))
            need=F(str(req["g"][j]))*1000000*coeff
            # Tiny outward buffer only for positive requirements; no artificial cash charge.
            if need:need+=tol(need)
            funds=max(F(0),cur.stocks().get(dep(a),F(0))-reserved_cash[a])
            needs[a]={"unconstrained_external_inputs_eur":str(need),"available_prefunding_eur":str(funds)}
            if need:scales.append(funds/need)
        alpha=min(scales)
        demand=[x*alpha for x in demand]
        periods.append(replace(step.production,structure=replace(s,final=tuple(float(x/1000000) for x in demand))))
        for p in limited:
            i=od[p.id];a=by[i.asset];reserved=amount(funding[p.id]["paid_acquisition"])
            if reserved and alpha:approved.append(replace(i,units=float(reserved*alpha/(F(str(a.acquisition_price))*1000000))))
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
            for due,share in schedules.get(p.id,((p.loan_due,"1"),)):
                emit("cap:"+p.id+":loan:"+str(due),"LOAN_ORIGINATION",p.firm,bank,src["DEBT"]*amount(share),due)
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
        # Execute intermediate purchases before final sales, with independent gross cash limits.
        # Self-use is an internal resource flow, never a fictitious payment.
        finale=tuple(events);events=[];inputs={a:F(0) for a in firms};internal={a:F(0) for a in firms};inputrows=[]
        for j,k in enumerate(codes):
            buyer=branch_firms[k];out=F(str(row["allocation"]["feasible_branch_output"][j]))*1000000
            for i,h in enumerate(codes):
                supplier=branch_firms[h];x=out*F(str(s.domestic[i][j]))
                if x:
                    if i==j:internal[buyer]+=x
                    else:
                        emit("input:"+str(t)+":"+k+":"+h,"DEPOSIT_TRANSFER",buyer,supplier,x);inputs[buyer]+=x;sales[supplier]+=x
                    inputrows.append({"buyer":buyer,"supplier":supplier,"product":h,"kind":"SELF_USE" if i==j else "DOMESTIC","value_eur":str(x)})
                im=out*F(str(s.imported[i][j]))
                if im:
                    emit("import:"+str(t)+":"+k+":"+h,"DEPOSIT_TRANSFER",buyer,outside,im);inputs[buyer]+=im
                    inputrows.append({"buyer":buyer,"supplier":outside,"product":h,"kind":"IMPORT","value_eur":str(im)})
        for a in firms:require(inputs[a]<=max(F(0),cur.stocks().get(dep(a),F(0))-reserved_cash[a]),"GROSS_INPUT_LIQUIDITY")
        cur,inputreceipt=apply(cur,tuple(events));cur,salesreceipt=apply(cur,finale);events=[];firm_rows=[]
        for i,k in enumerate(codes):
            a=branch_firms[k];rev=sales[a];model=F(str(row["allocation"]["feasible_branch_output"][i]))*1000000
            require(abs(rev+internal[a]-model)<=tol(model),"OUTPUT_SALES_RECONCILIATION")
            # Output-based wage and production-tax accrual, settle from cash; fail closed on numerical shortfall.
            wage=model*F(str(s.wage[i]));tax=model*F(str(s.other_tax[i]))
            emit("wage:"+str(t)+":"+k,"DEPOSIT_TRANSFER",a,household,wage)
            emit("tax:"+str(t)+":"+k,"DEPOSIT_TRANSFER",a,government,tax)
            gross_cash=rev-inputs[a]-wage-tax
            require(abs(gross_cash-model*F(str(s.surplus[i])))<=tol(model),"OPERATING_SURPLUS_RECONCILIATION")
            firm_rows.append({"firm":a,"branch":k,"sales_eur":str(rev),"self_use_eur":str(internal[a]),"intermediate_cash_cost_eur":str(inputs[a]),"wages_eur":str(wage),"production_tax_eur":str(tax),"gross_operating_cash_proxy_eur":str(gross_cash),"output_model_eur":str(model),"output_sales_residual_eur":str(model-rev-internal[a])})
        cur,wagereceipt=apply(cur,tuple(events))
        endrisk=base+w*gross(cur);draw=sum((F(p["sources"]["DEBT"]) for p in projects),F(0));require(draw<=cap and endrisk==risk+w*draw,"RWA_RECONCILIATION")
        modeltotal=F(str(row["investment_acquired"]))*1000000
        delivered=sum((F(p["delivered_eur"]) for p in projects),F(0))
        require(abs(modeltotal-delivered)<=tol(modeltotal),"CAPITAL_RECONCILIATION")
        # Total deposits change only through loan creation and bank debt/interest receipts.
        deposits=lambda st:sum((amount(p.stock) for p in st.positions if p.instrument=="DEPOSIT"),F(0))
        require(deposits(cur)==deposits(opening)+draw-F(settled["result"]["bank_receipts"]),"DEPOSIT_PERIOD_IDENTITY")
        cur.net_financial_positions()
        rows.append({"period":t,"opening_sha256":opening.fingerprint,"closing_sha256":cur.fingerprint,"opening_capital_proxy":str(before),"closing_capital_proxy":str(K),"rwa_proxy":str(endrisk),"credit_ceiling":str(cap),"overdue_credit_veto":sorted(overdue),"interest":interest,"settlement":settled,"exogenous_transfers":trans,"reservation":reservation,"projects":projects,"capital":row,"input_prefunding_scale":str(alpha),"input_prefunding":needs,"input_flows":inputrows,"input_receipt":inputreceipt,"sales":salesreceipt,"wages_and_taxes":wagereceipt,"firms":firm_rows,"household_budget_eur":str(budget),"household_desired_eur":str(want),"household_consumption_eur":str(household_paid),"government_deposits_eur":str(cur.stocks().get(dep(government),F(0))),"household_closing_deposits_eur":str(cur.stocks().get(dep(household),F(0))),"deposits_closing_eur":str(deposits(cur)),"investment_residual_eur":str(modeltotal-delivered),"cash_by_actor":{a:str(cur.stocks().get(dep(a),F(0))) for a in sorted(ids) if a!=bank}})
        cur=advance(cur)
    result={"status":"SYNTHETIC_OPERATING_FINANCE_CAPITAL_PATH","publication":"BLOCK_PUBLICATION","opening_sha256":state.fingerprint,"closing_sha256":cur.fingerprint,"coverage":cov,"periods":rows,"capital_receipt":cp,"actual_gdp":None,"actual_profit":None,"actual_employment":None,
            "limitations":["one bank, one firm per branch, household buyer/wage pool; external imports and nonnegative production tax, no valuation bridge",
                           "explicit opening transfers and demand, fixed prices, sequential reservation, no endogenous investment choice; no automatic cash inflow from unsold output",
                           "simple interest on opening gross principal, explicit instalment shares or bullet maturities, no compounding; accrual income proxy, impairment memo; no full bank balance sheet or regulatory capital",
                           "household wages recycled next period, no savings decision, no external export demand; gross operating cash proxy not profit or GDP",
                           "capital prefix replay, partial delivery, no inventories or backorder; common liquidity scaling of all final uses is conservative, not optimized; input purchases paid upfront out of own cash, no working capital credit; no tax on profits or household income"]}
    return cur,aa,{"result":result,"sha256":digest(canonical(result))}
