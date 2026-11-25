"""G4 v0.5c. Lagged rules over existing G4 dynamic allocation.
Behavioral scenarios, NOT estimated investment, optimization or equilibrium.
"""
import math
from dataclasses import dataclass,replace,asdict
from .economic_sector_structural import state,validate,require
from .economic_sector_capacity_dynamics import trajectory,CapacityOrder,nonnegative
from .economic_core import canonical,digest

@dataclass(frozen=True)
class CapacityRule:
    branch:str
    persistence:int
    lag:int
    expand_gap:float       # (unconstrained need - capacity)/capacity
    retire_utilization:float
    step:float             # absolute flow capacity per period
    floor:float
    ceiling:float
    retirement_signal:str  # DEMAND_CONFIRMED or UTILIZATION_ONLY
    evidence:str

@dataclass(frozen=True)
class SubstitutionRule:
    imported_product:str
    domestic_product:str
    buyer_branch:str
    persistence:int
    lag:int
    step:float             # imported input coefficient shifted per decision
    max_shift:float
    evidence:str

def finite(x):
    return type(x) in (int,float) and math.isfinite(x)
def positive_int(x):
    return type(x) is int and 1<=x<=24
def words(x):
    return isinstance(x,str) and bool(x.strip())

def adapt(periods,initial_capacity,initial_stock,capacity_rules=(),substitution_rules=(),*,period_unit,evidence):
    require(isinstance(periods,tuple) and 1<=len(periods)<=24,"ADAPT_HORIZON")
    require(words(evidence),"EVIDENCE")
    codes=periods[0].structure.codes;n=len(codes);idx={c:i for i,c in enumerate(codes)}
    cap0=nonnegative(initial_capacity,n,"CAPACITY")
    nonnegative(initial_stock,n,"STOCK")
    require(isinstance(capacity_rules,tuple) and isinstance(substitution_rules,tuple),"RULES")
    require(len({r.branch for r in capacity_rules})==len(capacity_rules),"DUPLICATE_CAPACITY_RULE")
    # Unique buyer/import pair: no overlapping withdrawal of the same input coefficient.
    require(len({(r.imported_product,r.buyer_branch) for r in substitution_rules})==len(substitution_rules),"DUPLICATE_SUBSTITUTION_RULE")
    for r in capacity_rules:
        require(r.branch in idx and positive_int(r.persistence) and positive_int(r.lag) and words(r.evidence),"CAPACITY_RULE")
        require(all(finite(x) for x in (r.expand_gap,r.retire_utilization,r.step,r.floor,r.ceiling)) and r.expand_gap>0 and 0<=r.retire_utilization<1 and r.step>0 and 0<=r.floor<=cap0[idx[r.branch]]<=r.ceiling and r.retirement_signal in ("DEMAND_CONFIRMED","UTILIZATION_ONLY"),"CAPACITY_RULE_RANGE")
    for r in substitution_rules:
        require(all(k in idx for k in (r.imported_product,r.domestic_product,r.buyer_branch)) and positive_int(r.persistence) and positive_int(r.lag) and words(r.evidence),"SUBSTITUTION_RULE")
        require(finite(r.step) and finite(r.max_shift) and 0<r.step<=r.max_shift<=1,"SUBSTITUTION_RANGE")
    cap_orders=[];sub_orders=[];effective=[];decisions=[]
    counts={r.branch:[0,0] for r in capacity_rules}
    scounts={i:0 for i in range(len(substitution_rules))}
    # Replay bounded prefixes through v0.5b. Decisions use only completed periods;
    # no future state, deliveries or demand are inspected by the rule.
    for t,p in enumerate(periods,1):
        s=p.structure
        require(s.codes==codes and s.origin==periods[0].structure.origin,"COMPARABILITY")
        validate(s)
        B=[list(row) for row in s.domestic];M=[list(row) for row in s.imported]
        commissioned=[]
        for o in sub_orders:
            if o["effective"]<=t:
                r=substitution_rules[o["rule"]];i=idx[r.imported_product];j=idx[r.buyer_branch];k=idx[r.domestic_product]
                M[i][j]-=o["shift"];B[k][j]+=o["shift"]
                require(M[i][j]>=0,"SUBSTITUTION_INSUFFICIENT_INPUT")
                if o["effective"]==t:commissioned.append(o)
        st=replace(s,domestic=tuple(map(tuple,B)),imported=tuple(map(tuple,M)))
        validate(st)
        effective.append(replace(p,structure=st))
        out=trajectory(tuple(effective),cap0,initial_stock,tuple(cap_orders),period_unit=period_unit,evidence=evidence)["result"]
        row=out["periods"][-1];need=state(st)["g"];cap=row["capacity"];actual=row["feasible_branch_output"]
        bound={ (b["kind"],b["code"]) for tier in row["tiers"] if tier["fraction"]<1-1e-9 for b in tier["binding"]}
        for r in capacity_rules:
            j=idx[r.branch];c=cap[j];q=need[j];u=actual[j]/c if c>0 else None
            # Expanding nonbinding capacity cannot solve the identified shortage.
            expand=("BRANCH",r.branch) in bound and q-c>r.expand_gap*max(c,1e-12)
            retire=c>r.floor and u is not None and u<r.retire_utilization and (r.retirement_signal=="UTILIZATION_ONLY" or q<c*r.retire_utilization)
            counter=counts[r.branch];counter[0]=counter[0]+1 if expand else 0;counter[1]=counter[1]+1 if retire else 0
            pending=any(o.branch==r.branch and o.placed+o.lag>t for o in cap_orders)
            reason="NO_TRIGGER";delta=0.
            if pending:reason="PENDING"
            elif counter[0]>=r.persistence:
                delta=min(r.step,r.ceiling-c);reason="EXPAND" if delta>0 else "CEILING"
            elif counter[1]>=r.persistence:
                delta=-min(r.step,c-r.floor);reason="RETIRE" if delta<0 else "FLOOR"
            if delta:
                cap_orders.append(CapacityOrder(t,r.lag,r.branch,delta,r.evidence));counts[r.branch]=[0,0]
            decisions.append({"period":t,"kind":"CAPACITY","branch":r.branch,"reason":reason,"delta":delta,"effective":t+r.lag if delta else None,"need":q,"capacity":c,"utilization":u,"binding":("BRANCH",r.branch) in bound})
        for i,r in enumerate(substitution_rules):
            trigger=("IMPORT",r.imported_product) in bound
            scounts[i]=scounts[i]+1 if trigger else 0
            previous=[o for o in sub_orders if o["rule"]==i];pending=any(o["effective"]>t for o in previous)
            used=math.fsum(o["shift"] for o in previous)
            remaining=min(r.max_shift-used,st.imported[idx[r.imported_product]][idx[r.buyer_branch]])
            shift=0.;reason="NO_TRIGGER"
            if pending:reason="PENDING"
            elif scounts[i]>=r.persistence:
                shift=min(r.step,max(0.,remaining));reason="SUBSTITUTE" if shift>1e-14 else "LIMIT"
                if shift<=1e-14:shift=0.
            if shift:
                sub_orders.append({"rule":i,"placed":t,"effective":t+r.lag,"shift":shift});scounts[i]=0
            decisions.append({"period":t,"kind":"SUBSTITUTION","rule":i,"reason":reason,"shift":shift,"effective":t+r.lag if shift else None})
    # Include decisions placed in final period as pending, with no look-ahead.
    out=trajectory(tuple(effective),cap0,initial_stock,tuple(cap_orders),period_unit=period_unit,evidence=evidence)["result"]
    result={"status":"CONDITIONAL_ADAPTIVE_RULE_PATH","publication":"BLOCK_PUBLICATION","dynamic":out,"decisions":decisions,
      "capacity_rules":[asdict(r) for r in capacity_rules],"substitution_rules":[asdict(r) for r in substitution_rules],
      "substitution_orders":sub_orders,"pending_substitution":[o for o in sub_orders if o["effective"]>len(periods)],
      "limitations":["bounded behavioral rules, no estimation or optimal anticipation","capacity steps are output-flow units, not CAPEX, no investment financing","substitution assumes identical reference-price input value and technical equivalence, no transition cost, reversible policy not modeled","no new demand, prices or observed employment inferred","prefix replay limited to 24 periods"]}
    return {"result":result,"sha256":digest(canonical(result))}
