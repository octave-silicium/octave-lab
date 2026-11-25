"""G4 v0.7g2: exact settlement of due claims in a closed one-bank ledger.
Acyclic network or existing regular pari-passu clearing. Not insolvency law or IFRS 9.
"""
from dataclasses import dataclass,replace
from fractions import Fraction as F
from .economic_core import require,words,canonical,digest
from .economic_shared_state import State,Position,Event,amount,apply,advance,sortkey,run_funding,validate_transversal_coverage
from .economic_financial_network import clear

DEBT={"LOAN","TRADE_PAYABLE","INTEREST_PAYABLE"}

@dataclass(frozen=True)
class Allowance:
    key:tuple
    value:str
    def __post_init__(self):
        require(type(self.key) is tuple and len(self.key)==4,"ALLOWANCE_KEY")
        object.__setattr__(self,"value",str(amount(self.value)))

@dataclass(frozen=True)
class Discharge:
    key:tuple
    value:str
    evidence:str
    def __post_init__(self):
        require(type(self.key) is tuple and len(self.key)==4 and words(self.evidence),"DISCHARGE")
        object.__setattr__(self,"value",str(amount(self.value)))

def settle(state,bank,outside,allowances=(),discharges=(),*,recognition,evidence):
    require(isinstance(state,State) and words(evidence),"STATE")
    ids={a.id:a for a in state.actors}
    require(bank in ids and ids[bank].kind=="BANK" and outside in ids and ids[outside].kind=="EXTERNAL" and outside!=bank,"BANK_OUTSIDE")
    require(sum(a.kind=="BANK" for a in state.actors)==1,"ONE_BANK_ONLY")
    require(all(p.instrument!="DEPOSIT" or p.issuer==bank for p in state.positions),"SETTLEMENT_SCOPE")
    require(all(p.issuer!=bank for p in state.positions if p.instrument in DEBT),"BANK_DEBTOR_UNSUPPORTED")
    require(all(p.issuer!=outside for p in state.positions if p.instrument in DEBT),"OUTSIDE_DEBTOR_UNSUPPORTED")
    require(all(p.holder==bank for p in state.positions if p.instrument=="LOAN"),"LOAN_HOLDER")
    require(all(p.holder==bank for p in state.positions if p.instrument=="INTEREST_PAYABLE"),"INTEREST_HOLDER")
    rate=amount(recognition);require(rate<=1,"RECOGNITION")
    pos=state.stocks();opening=pos.copy();codes=tuple(a.id for a in state.actors if a.id!=outside)
    require(len(codes)<=30,"NETWORK_SIZE")
    ix={a:i for i,a in enumerate(codes)}
    due=[p for p in state.positions if p.instrument in DEBT]
    require(all(p.due is not None for p in due),"UNKNOWN_MATURITY")
    due=[p for p in due if p.due<=state.period]
    def memo(items,typ):
        require(type(items) is tuple and all(isinstance(x,typ) for x in items),"MEMO")
        require(len({x.key for x in items})==len(items),"DUPLICATE_MEMO")
        m={x.key:amount(x.value) for x in items}
        require(all(k in opening and k[0] in DEBT and k[1]==bank and v<=opening[k] for k,v in m.items()),"MEMO_SCOPE")
        return m
    old=memo(allowances,Allowance);cancel=memo(discharges,Discharge)
    require(set(cancel)<={p.key for p in due},"DISCHARGE_NOT_DUE")
    tag="settlement:"+str(state.period)
    require(tag not in state.processed_event_ids,"REPLAYED_EVENT")
    dep=lambda a:("DEPOSIT",a,bank,None)
    liquidity={a:opening.get(dep(a),F(0)) if a!=bank else F(0) for a in codes}
    outgoing={a:[] for a in codes};indegree={a:0 for a in codes}
    for p in due:
        outgoing[p.issuer].append(p)
        if p.holder!=outside:indegree[p.holder]+=1
    queue=sorted(a for a in codes if indegree[a]==0);order=[]
    while queue:
        a=queue.pop(0);order.append(a)
        for p in outgoing[a]:
            if p.holder!=outside:
                indegree[p.holder]-=1
                if indegree[p.holder]==0:queue.append(p.holder);queue.sort()
    shares={};net=liquidity.copy();external_paid=F(0);bank_paid=F(0)
    if len(order)==len(codes):
        method="ACYCLIC_TOPOLOGICAL"
        for a in order:
            total=sum((amount(p.stock) for p in outgoing[a]),F(0))
            ratio=min(F(1),net[a]/total) if total else F(0)
            for p in outgoing[a]:
                x=amount(p.stock)*ratio;shares[p.key]=x;net[a]-=x
                if p.holder==outside:external_paid+=x
                else:net[p.holder]+=x
    else:
        method="REGULAR_SIMULTANEOUS"
        n=len(codes);L=[[F(0)]*n for _ in codes];o=[F(0)]*n
        for p in due:
            x=amount(p.stock);i=ix[p.issuer]
            if p.holder==outside:o[i]+=x
            else:L[i][ix[p.holder]]+=x
        c=clear(codes,L,o,[liquidity[a] for a in codes],evidence=evidence)["result"]
        for p in due:
            i=ix[p.issuer];total=sum(L[i])+o[i];shares[p.key]=amount(p.stock)*F(c["payments"][i])/total
        net={a:F(v) for a,v in zip(codes,c["remaining_liquidity"])}
        external_paid=sum(map(F,c["external_paid"]),F(0))
    lines=[];closing_allowance={};loss=F(0)
    for p in due:
        k=p.key;x=shares[k];remaining=opening[k]-x;d=cancel.get(k,F(0))
        require(d<=remaining,"DISCHARGE_EXCEEDS_UNPAID")
        pos[k]=remaining-d
        if p.holder==bank:
            bank_paid+=x
            new=pos[k]*rate
            loss+=new-old.get(k,F(0))+d
            if new:closing_allowance[k]=new
        lines.append({"key":list(k),"opening_due":str(opening[k]),"paid":str(x),"unpaid_before_discharge":str(remaining),"discharged":str(d),"closing_gross":str(pos[k]),"opening_allowance":str(old.get(k,F(0))) if p.holder==bank else None,"closing_allowance":str(closing_allowance.get(k,F(0))) if p.holder==bank else None})
    for k,v in old.items():
        if k not in shares and v:closing_allowance[k]=v
    for a,v in net.items():
        if a!=bank:pos[dep(a)]=v
    pos[dep(outside)]=opening.get(dep(outside),F(0))+external_paid
    require(net[bank]==bank_paid,"BANK_RECEIPTS")
    deposits=lambda m:sum((v for k,v in m.items() if k[0]=="DEPOSIT"),F(0))
    require(deposits(opening)-deposits(pos)==bank_paid,"DEPOSIT_EXTINCTION")
    require(all(v>=0 for v in pos.values()),"NEGATIVE_SETTLEMENT")
    close=replace(state,positions=tuple(Position(*k[:3],str(v),k[3]) for k,v in pos.items() if v),processed_event_ids=state.processed_event_ids+(tag,))
    close.net_financial_positions()
    aa=tuple(Allowance(k,str(v)) for k,v in sorted(closing_allowance.items(),key=lambda kv:sortkey(kv[0])))
    result={"status":"SYNTHETIC_SETTLEMENT","publication":"BLOCK_PUBLICATION","method":method,"period":state.period,
        "opening_sha256":state.fingerprint,"closing_sha256":close.fingerprint,"claims":lines,"bank_receipts":str(bank_paid),
        "external_receipts":str(external_paid),"deposits_extinguished":str(bank_paid),"net_impairment_expense_proxy":str(loss),
        "allowance_opening":str(sum(old.values(),F(0))),"allowance_closing":str(sum(closing_allowance.values(),F(0))),
        "explicit_discharge":str(sum(cancel.values(),F(0))),"discharge_evidence":[{"key":list(d.key),"evidence":d.evidence} for d in discharges],
        "actual_default":None,"actual_regulatory_capital":None,
        "limits":["one bank only, bank/outside cannot be debtors, simultaneous net clearing in regular cycles only; no intraday funding",
                  "all matured claims pari passu, no legal priority or bankruptcy; unpaid persists unless explicit contractual discharge",
                  "allowance memo not a bilateral position, no automatic write-off or IFRS 9 ECL; interest already accrued, settlement not new income"]}
    require(loss==sum(closing_allowance.values(),F(0))-sum(old.values(),F(0))+sum(cancel.values(),F(0)),"ALLOWANCE_IDENTITY")
    return close,aa,{"result":result,"sha256":digest(canonical(result))}

@dataclass(frozen=True)
class Step:
    transfers:tuple
    projects:tuple
    recognition:str
    discharges:tuple=()
    evidence:str="scenario"

def finance_path(state,bank,outside,steps,*,capital_before,other_rwa,loan_weight,minimum_ratio,credit_limit,coverage,allowances=()):
    """Sequential finance-only replay. Operating transfers are cash, not inferred profits."""
    require(type(steps) is tuple and 1<=len(steps)<=24 and all(isinstance(s,Step) for s in steps),"HORIZON")
    cov=validate_transversal_coverage(coverage)
    K=amount(capital_before);base=amount(other_rwa);w=amount(loan_weight);ratio=amount(minimum_ratio);limit=amount(credit_limit)
    require(w>0 and 0<ratio<=1,"BANK_POLICY")
    cur=state;aa=allowances;rows=[]
    for step in steps:
        require(words(step.evidence) and type(step.transfers) is tuple and all(isinstance(e,Event) and e.kind=="DEPOSIT_TRANSFER" and e.bank==bank for e in step.transfers),"OPERATING_TRANSFERS")
        require(type(step.projects) is tuple and all(p.bank==bank for p in step.projects),"PROJECT_BANK")
        before=K;cur,op=apply(cur,step.transfers)
        cur,aa,s=settle(cur,bank,outside,aa,step.discharges,recognition=step.recognition,evidence=step.evidence)
        K-=F(s["result"]["net_impairment_expense_proxy"])
        gross=lambda st:sum((amount(p.stock) for p in st.positions if p.instrument=="LOAN" and p.holder==bank),F(0))
        risk=base+w*gross(cur);head=max(F(0),(K/ratio-risk)/w);cap=min(head,limit)
        cur,fr=run_funding(cur,step.projects,{bank:cap},coverage)
        endrisk=base+w*gross(cur)
        require(endrisk<=risk+w*cap,"RWA_CAP")
        rows.append({"period":cur.period,"opening_capital_proxy":str(before),"closing_capital_proxy":str(K),
            "rwa_before_funding_proxy":str(risk),"rwa_after_funding_proxy":str(endrisk),"credit_ceiling":str(cap),
            "capital_shortfall_proxy":str(max(F(0),ratio*endrisk-K)),"operating_transfers":op,"settlement":s,"funding":fr,
            "closing_state_sha256":cur.fingerprint})
        cur=advance(cur)
    result={"status":"SYNTHETIC_MULTI_PERIOD_FINANCE","publication":"BLOCK_PUBLICATION","opening_sha256":state.fingerprint,
            "closing_sha256":cur.fingerprint,"coverage":cov,"periods":rows,
            "limits":["gross loans fixed risk weight plus exogenous other RWA, not regulatory capital or balance sheet",
                      "capital proxy includes impairment/discharge only; no interest accrual, bank profit, taxes or dividends",
                      "operating transfers exogenous, paid projects not productive delivery, no real-sector feedback; each period credit cap resets by assumption"]}
    return cur,aa,{"result":result,"sha256":digest(canonical(result))}
