"""G4 v0.7g3c1: local operating liquidity, capped supplier credit and working loans.
No inventory valuation, factoring or contract-level PD. Exact nominal ledger.
"""
from dataclasses import dataclass,replace
from fractions import Fraction as F
from math import nextafter,inf
from .economic_core import require,words,canonical,digest
from .economic_shared_state import Position,amount,sortkey

@dataclass(frozen=True)
class Facility:
    firm:str
    limit:str
    due:int
    evidence:str

@dataclass(frozen=True)
class TradeTerm:
    buyer:str
    supplier:str
    share:str
    outstanding_cap:str
    lag:int
    evidence:str

@dataclass(frozen=True)
class WorkingPolicy:
    facilities:tuple=()
    terms:tuple=()

def prepare(state,bank,firms,policy,cap,overdue):
    require(isinstance(policy,WorkingPolicy),"WORKING_POLICY")
    require(type(policy.facilities) is tuple and all(isinstance(x,Facility) for x in policy.facilities),"FACILITIES")
    require(type(policy.terms) is tuple and all(isinstance(x,TradeTerm) for x in policy.terms),"TRADE_TERMS")
    facilities={f.firm:f for f in policy.facilities};terms={(x.buyer,x.supplier):x for x in policy.terms}
    require(len(facilities)==len(policy.facilities) and len(terms)==len(policy.terms),"DUPLICATE_WORKING_TERM")
    requests={}
    for a,f in facilities.items():
        require(a in firms and type(f.due) is int and f.due>state.period and words(f.evidence),"FACILITY_SCOPE")
        requests[a]=F(0) if a in overdue else amount(f.limit)
    total=sum(requests.values(),F(0));envelope=min(cap,total)
    alloc={a:envelope*x/total if total else F(0) for a,x in requests.items()}
    edges={}
    for k,x in terms.items():
        require(x.buyer in firms and x.supplier in firms and x.buyer!=x.supplier and type(x.lag) is int and x.lag>=1 and words(x.evidence),"TRADE_SCOPE")
        share=amount(x.share);require(share<=1,"TRADE_SHARE")
        used=sum((amount(p.stock) for p in state.positions if p.instrument=="TRADE_PAYABLE" and p.issuer==x.buyer and p.holder==x.supplier),F(0))
        edges[k]=(share,max(F(0),amount(x.outstanding_cap)-used),state.period+x.lag)
    return facilities,alloc,edges,envelope

def deferred(edges,buyer,supplier,value):
    share,cap,due=edges.get((buyer,supplier),(F(0),F(0),None))
    return min(value*share,cap),due

def local_limits(s,codes,branch_firms,state,bank,reserved,alloc,edges,required):
    """Monotone gross prefunding cost. Bisection provides a conservative bound.
    Sellers offering deferred payment reserve full payroll/tax as well.
    """
    limits=[];details={}
    sellers={b for (a,b),(share,cap,due) in edges.items() if share and cap}
    for j,k in enumerate(codes):
        a=branch_firms[k]
        cash=max(F(0),state.stocks().get(("DEPOSIT",a,bank,None),F(0))-reserved[a])
        budget=cash+alloc.get(a,F(0))
        payroll=F(str(s.wage[j]))+F(str(s.other_tax[j])) if a in sellers else F(0)
        imports=sum((F(str(s.imported[i][j])) for i in range(len(codes))),F(0))
        def cost(g):
            result=g*(imports+payroll)
            for i,h in enumerate(codes):
                if i!=j:
                    x=g*F(str(s.domestic[i][j]));d,_=deferred(edges,a,branch_firms[h],x);result+=x-d
            return result
        hi=max(F(1),F(str(required[j]))*1000000+1)
        safe=max(F(0),budget-max(F(1,1000000),budget*F(1,100000000000))) if budget else F(0)
        if cost(hi)<=safe: bound=None
        else:
            lo=F(0)
            for _ in range(72):
                mid=(lo+hi)/2
                if cost(mid)<=safe:lo=mid
                else:hi=mid
            bound=max(0.,nextafter(float(lo/1000000),-inf))
        limits.append(bound)
        details[a]={"own_cash":str(cash),"working_credit_reserved":str(alloc.get(a,F(0))),"gross_prefunding_budget":str(budget),
                    "payroll_tax_prefunded":a in sellers,"branch_output_ceiling_reference_m_eur":bound}
    return tuple(limits),details,sellers

def invoice(state,items,*,evidence):
    require(words(evidence),"INVOICE_EVIDENCE")
    require(type(items) is tuple,"INVOICE_BATCH")
    ids={a.id:a for a in state.actors};pos=state.stocks();rows=[];tags=[]
    for id,buyer,supplier,value,due in items:
        require(words(id) and buyer in ids and supplier in ids and buyer!=supplier and ids[buyer].kind==ids[supplier].kind=="FIRM","INVOICE_PARTIES")
        require(type(due) is int and due>state.period,"INVOICE_DUE")
        x=amount(value);require(x>0,"INVOICE_VALUE")
        tag="invoice:"+id;require(tag not in state.processed_event_ids and tag not in tags,"REPLAYED_EVENT");tags.append(tag)
        key=("TRADE_PAYABLE",supplier,buyer,due);pos[key]=pos.get(key,F(0))+x
        rows.append({"event":tag,"key":list(key),"delta":str(x)})
    close=replace(state,positions=tuple(Position(*k[:3],str(v),k[3]) for k,v in pos.items() if v),processed_event_ids=state.processed_event_ids+tuple(tags))
    close.net_financial_positions()
    result={"opening_sha256":state.fingerprint,"closing_sha256":close.fingerprint,"invoices":rows,"cash_created":"0","evidence":evidence}
    return close,{"result":result,"sha256":digest(canonical(result))}

def trade_bfr(state,firms):
    out={}
    for a in sorted(firms):
        r=sum((amount(p.stock) for p in state.positions if p.instrument=="TRADE_PAYABLE" and p.holder==a),F(0))
        p=sum((amount(p.stock) for p in state.positions if p.instrument=="TRADE_PAYABLE" and p.issuer==a),F(0))
        out[a]={"trade_receivables":str(r),"trade_payables":str(p),"net_trade_claims":str(r-p),"inventory":None,"full_bfr":None}
    return out
