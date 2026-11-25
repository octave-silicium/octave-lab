"""Common economic state v0.1: exact, closed synthetic financial sub-ledger.
Shared contract, not a seventh engine or a full balance sheet.
"""
from dataclasses import dataclass, asdict, replace
from fractions import Fraction as F
from pathlib import Path
import json
from .economic_core import canonical, digest, require, words, identity

KINDS={"FIRM","BANK","HOUSEHOLD","INVESTOR","GOVERNMENT","CENTRAL_BANK","EXTERNAL","WORKER"}
INSTRUMENTS={"DEPOSIT","LOAN","EQUITY","TRADE_PAYABLE","INTEREST_PAYABLE"}
STEPS={"month","quarter","year"}

def amount(x):
    require(type(x) in (str,int,F),"EXACT_AMOUNT")
    try: v=F(x)
    except (ValueError,ZeroDivisionError): raise ValueError("EXACT_AMOUNT")
    require(v>=0,"NEGATIVE_AMOUNT")
    return v

@dataclass(frozen=True)
class Actor:
    id:str
    kind:str
    sector:str|None=None
    geography:str|None=None
    group:str|None=None
    size:str|None=None
    revision:int=1
    def __post_init__(self):
        identity(self.id,self.revision)
        require(self.kind in KINDS and all(v is None or words(v) for v in (self.sector,self.geography,self.group,self.size)),"ACTOR")

@dataclass(frozen=True)
class Position:
    instrument:str
    holder:str
    issuer:str
    stock:str
    due:int|None=None
    def __post_init__(self):
        require(self.instrument in INSTRUMENTS and self.holder!=self.issuer,"POSITION")
        require(self.due is None or (type(self.due) is int and self.due>=0),"DUE")
        require(self.instrument not in {"EQUITY","DEPOSIT"} or self.due is None,"NONMATURITY")
        object.__setattr__(self,"stock",str(amount(self.stock)))
    @property
    def key(self): return self.instrument,self.holder,self.issuer,self.due

def sortkey(k): return (*k[:3],-1 if k[3] is None else k[3])

@dataclass(frozen=True)
class State:
    actors:tuple
    positions:tuple
    period:int
    step_unit:str
    scope:str
    evidence:str
    currency:str="EUR"
    basis:str="NOMINAL_SYNTHETIC"
    processed_event_ids:tuple=()
    def __post_init__(self):
        require(type(self.actors) is tuple and self.actors and all(isinstance(a,Actor) for a in self.actors),"ACTORS")
        ids={a.id:a for a in self.actors}
        require(len(ids)==len(self.actors),"DUPLICATE_ACTOR")
        require(type(self.positions) is tuple and all(isinstance(p,Position) for p in self.positions),"POSITIONS")
        require(len({p.key for p in self.positions})==len(self.positions),"DUPLICATE_POSITION")
        require(type(self.period) is int and self.period>=0 and self.step_unit in STEPS and words(self.scope) and words(self.evidence),"SCOPE_TIME")
        require(self.currency=="EUR" and self.basis=="NOMINAL_SYNTHETIC","SYNTHETIC_EUR_ONLY")
        require(type(self.processed_event_ids) is tuple and all(words(x) for x in self.processed_event_ids) and len(set(self.processed_event_ids))==len(self.processed_event_ids),"EVENT_HISTORY")
        object.__setattr__(self,"processed_event_ids",tuple(sorted(self.processed_event_ids)))
        for p in self.positions:
            require(p.holder in ids and p.issuer in ids,"UNKNOWN_COUNTERPARTY")
            require(p.instrument!="DEPOSIT" or ids[p.issuer].kind=="BANK","DEPOSIT_ISSUER")
        object.__setattr__(self,"actors",tuple(sorted(self.actors,key=lambda a:a.id)))
        object.__setattr__(self,"positions",tuple(sorted((p for p in self.positions if amount(p.stock)),key=lambda p:sortkey(p.key))))
    @property
    def fingerprint(self): return digest(canonical(asdict(self)))
    def stocks(self): return {p.key:amount(p.stock) for p in self.positions}
    def net_financial_positions(self):
        v={a.id:F(0) for a in self.actors}
        for p in self.positions: v[p.holder]+=amount(p.stock);v[p.issuer]-=amount(p.stock)
        require(sum(v.values())==0,"COUNTERPARTY_BALANCE")
        return v
    def due_stock(self):
        # Contractual maturity bucket, not a default or a clearing input.
        return {"matured":[asdict(p) for p in self.positions if p.due is not None and p.due<=self.period],
                "unknown_maturity":[asdict(p) for p in self.positions if p.instrument in {"LOAN","TRADE_PAYABLE","INTEREST_PAYABLE"} and p.due is None]}

@dataclass(frozen=True)
class Event:
    id:str
    period:int
    kind:str
    actor:str
    counterparty:str
    bank:str
    value:str
    evidence:str
    due:int|None=None
    def __post_init__(self):
        require(words(self.id) and words(self.evidence) and type(self.period) is int,"EVENT")
        require(self.kind in {"DEPOSIT_TRANSFER","LOAN_ORIGINATION","LOAN_REPAYMENT","EQUITY_SUBSCRIPTION"},"EVENT_KIND")
        require(self.due is None or (type(self.due) is int and self.due>=0),"DUE")
        require(self.kind in {"LOAN_ORIGINATION","LOAN_REPAYMENT"} or self.due is None,"EVENT_DUE")
        object.__setattr__(self,"value",str(amount(self.value)))

def apply(state,events):
    """Replay a single period; reject whole batch on a negative position."""
    require(isinstance(state,State) and type(events) is tuple and all(isinstance(e,Event) for e in events),"EVENTS")
    require(len({e.id for e in events})==len(events),"DUPLICATE_EVENT")
    require(not set(state.processed_event_ids)&{e.id for e in events},"REPLAYED_EVENT")
    ids={a.id:a for a in state.actors}; opening=state.stocks(); pos=opening.copy(); ledger=[]
    for e in events:
        require(e.period==state.period,"EVENT_PERIOD")
        require(e.actor in ids and e.counterparty in ids and e.bank in ids and e.actor!=e.counterparty,"EVENT_ACTORS")
        require(ids[e.bank].kind=="BANK" and e.actor!=e.bank,"SETTLEMENT_BANK")
        x=amount(e.value);dep=lambda a:("DEPOSIT",a,e.bank,None)
        if e.kind=="DEPOSIT_TRANSFER":
            require(e.counterparty!=e.bank,"CROSS_BANK_OR_BANK_INCOME_UNSUPPORTED")
            legs=[(dep(e.actor),-x),(dep(e.counterparty),x)]
        elif e.kind=="EQUITY_SUBSCRIPTION":
            require(e.counterparty!=e.bank and ids[e.counterparty].kind=="FIRM","EQUITY_ISSUER")
            legs=[(dep(e.actor),-x),(dep(e.counterparty),x),(("EQUITY",e.actor,e.counterparty,None),x)]
        else:
            require(e.counterparty==e.bank and ids[e.actor].kind=="FIRM","LOAN_PARTIES")
            if e.kind=="LOAN_ORIGINATION":
                require(e.due is not None and e.due>state.period,"NEW_LOAN_MATURITY")
            sign=1 if e.kind=="LOAN_ORIGINATION" else -1
            legs=[(dep(e.actor),sign*x),(("LOAN",e.bank,e.actor,e.due),sign*x)]
        for k,d in legs:
            pos[k]=pos.get(k,F(0))+d
            require(pos[k]>=0,"INSUFFICIENT_POSITION")
        ledger.append({"event":asdict(e),"legs":[{"key":list(k),"delta":str(d)} for k,d in legs]})
    closing=replace(state,positions=tuple(Position(k[0],k[1],k[2],str(v),k[3]) for k,v in pos.items() if v),processed_event_ids=state.processed_event_ids+tuple(e.id for e in events))
    totals={}
    for row in ledger:
        for leg in row["legs"]:
            k=tuple(leg["key"]);totals[k]=totals.get(k,F(0))+F(leg["delta"])
    for k in set(opening)|set(pos)|set(totals):
        require(pos.get(k,F(0))==opening.get(k,F(0))+totals.get(k,F(0)),"STOCK_FLOW")
    closing.net_financial_positions()
    result={"status":"SYNTHETIC_SHARED_STATE","publication":"BLOCK_PUBLICATION","opening_sha256":state.fingerprint,
            "closing_sha256":closing.fingerprint,"period":state.period,"events":ledger,
            "net_financial_positions":{k:str(v) for k,v in closing.net_financial_positions().items()}}
    return closing,{"result":result,"sha256":digest(canonical(result))}

def advance(state):
    """Time only; no implicit interest, repayment, write-off or cash creation."""
    require(isinstance(state,State),"STATE")
    return replace(state,period=state.period+1)

@dataclass(frozen=True)
class Project:
    id:str
    firm:str
    supplier:str
    bank:str
    owner:str|None
    requested:str
    reserve:str
    equity_cap:str
    debt_cap:str
    order:tuple
    partial:bool
    loan_due:int|None
    evidence:str
    def __post_init__(self):
        require(words(self.id) and words(self.evidence) and type(self.partial) is bool,"PROJECT")
        require(type(self.order) is tuple and len(set(self.order))==len(self.order) and set(self.order)<={"CASH","EQUITY","DEBT"},"FUNDING_ORDER")
        for k in ("requested","reserve","equity_cap","debt_cap"):object.__setattr__(self,k,str(amount(getattr(self,k))))
        require("EQUITY" not in self.order or self.owner is not None,"OWNER")
        require("DEBT" not in self.order or type(self.loan_due) is int,"PROJECT_MATURITY")

def fund_projects(state,projects,bank_limits):
    """Explicit sequential allocation; order is a scenario assumption.
    Funding commitments are caps, not observed credit or optimal decisions.
    Immediate paid purchase only; no productive service/quantity inferred.
    """
    require(type(projects) is tuple and all(isinstance(p,Project) for p in projects),"PROJECTS")
    require(len({p.id for p in projects})==len(projects),"DUPLICATE_PROJECT")
    ids={a.id:a for a in state.actors}
    require(isinstance(bank_limits,dict) and all(k in ids and ids[k].kind=="BANK" for k in bank_limits),"BANK_LIMITS")
    caps={k:amount(v) for k,v in bank_limits.items()};remaining=caps.copy();cur=state;all_events=[];rows=[]
    for p in projects:
        require(p.firm in ids and ids[p.firm].kind=="FIRM" and p.supplier in ids and p.bank in ids and ids[p.bank].kind=="BANK","PROJECT_PARTIES")
        require(len({p.firm,p.supplier,p.bank})==3 and (p.owner is None or p.owner in ids and p.owner not in {p.firm,p.bank,p.supplier}),"PROJECT_COUNTERPARTY")
        require("DEBT" not in p.order or p.bank in remaining and p.loan_due>state.period,"BANK_CAP_OR_MATURITY")
        dep=lambda a:cur.stocks().get(("DEPOSIT",a,p.bank,None),F(0))
        available={"CASH":max(F(0),dep(p.firm)-amount(p.reserve)),
                   "EQUITY":min(amount(p.equity_cap),dep(p.owner)) if p.owner else F(0),
                   "DEBT":min(amount(p.debt_cap),remaining.get(p.bank,F(0)))}
        want=amount(p.requested);left=want;used={k:F(0) for k in available}
        for k in p.order:
            used[k]=min(left,available[k]);left-=used[k]
        if left and not p.partial: used={k:F(0) for k in used}
        paid=sum(used.values());ev=[]
        def emit(kind,actor,counterparty,value,due=None):
            if value:ev.append(Event(p.id+":"+kind,state.period,kind,actor,counterparty,p.bank,str(value),p.evidence,due))
        emit("EQUITY_SUBSCRIPTION",p.owner,p.firm,used["EQUITY"])
        emit("LOAN_ORIGINATION",p.firm,p.bank,used["DEBT"],p.loan_due)
        emit("DEPOSIT_TRANSFER",p.firm,p.supplier,paid)
        cur,_=apply(cur,tuple(ev));all_events.extend(ev)
        if used["DEBT"]:remaining[p.bank]-=used["DEBT"]
        require(paid<=want and paid==sum(used.values()),"FUNDING_IDENTITY")
        rows.append({"id":p.id,"firm":p.firm,"requested":str(want),"paid_acquisition":str(paid),
                     "unfunded":str(want-paid),"sources":{k:str(v) for k,v in used.items()},
                     "productive_capacity_added":None,"actual_credit_granted":None})
    replay,receipt=apply(state,tuple(all_events))
    require(replay.fingerprint==cur.fingerprint,"BATCH_REPLAY")
    result={"status":"CONDITIONAL_MULTI_SOURCE_FUNDING","publication":"BLOCK_PUBLICATION",
            "opening_sha256":state.fingerprint,"closing_sha256":cur.fingerprint,"project_order":[p.id for p in projects],
            "projects":rows,"bank_caps_initial":{k:str(v) for k,v in caps.items()},
            "bank_caps_remaining":{k:str(v) for k,v in remaining.items()},"ledger":receipt,
            "limitations":["single settlement bank per payment; no interbank transfer","explicit cash balances, finite owner funds, exogenous credit ceilings; no endogenous allocation",
                           "paid acquisition is not an asset service, delivery verification or value added","no full balance sheet, reserves, risk weights, ownership shares, legal default, or empirical admission"]}
    return cur,{"result":result,"sha256":digest(canonical(result))}

def validate_transversal_coverage(rows,root=None):
    """New state-contract runs must account for each AC; legacy receipts unchanged."""
    root=Path(root) if root is not None else Path(__file__).resolve().parents[1]/"governance"
    raw=(root/"transversal_enrichment_v1.json").read_bytes();reg=json.loads(raw)
    require(reg["status"]=="USER_APPROVED_REQUIREMENTS_METHOD_PENDING","AC_REGISTRY_STATUS")
    expected={e["id"] for e in reg["entries"]}
    require(expected=={f"AC{i:02}" for i in range(1,28)},"AC_REGISTRY_DRIFT")
    require(type(rows) is tuple and all(isinstance(r,dict) for r in rows),"AC_ROWS")
    require(len(rows)==len(expected) and {r.get("id") for r in rows}==expected,"AC_COVERAGE")
    allowed={"PENDING_QUALIFICATION","HYPOTHESIS_ONLY","NOT_APPLICABLE_JUSTIFIED","BLOCKED_MISSING_DATA","BLOCKED_METHOD_OR_RIGHTS"}
    for r in rows:
        require(r.get("disposition") in allowed and words(r.get("reason")),"AC_DISPOSITION")
        require(r["disposition"]!="HYPOTHESIS_ONLY" or words(r.get("evidence_ref")),"AC_EVIDENCE")
    return {"registry_sha256":digest(raw),"entries":len(rows),"scientific_coverage_validated":False,"publication":"BLOCK_PUBLICATION",
            "rows":sorted(rows,key=lambda r:r["id"])}


def run_funding(state,projects,bank_limits,coverage):
    """Governed entry point; raw ledger functions remain low-level primitives."""
    audit=validate_transversal_coverage(coverage)
    close,receipt=fund_projects(state,projects,bank_limits)
    result={"status":"CONDITIONAL_GOVERNED_FUNDING","publication":"BLOCK_PUBLICATION","funding":receipt,"coverage":audit}
    return close,{"result":result,"sha256":digest(canonical(result))}
