"""G4 v0.5a: conditional capacity-constrained final allocation, not market equilibrium.
Nonnegative fixed-price Leontief requirements, proportional allocation within priority tiers.
No inventory, substitution, autonomous price or actual output claim.
"""
import math
from dataclasses import dataclass,replace
from .economic_sector_structural import validate,solve,state,vec,mv,add,sub,norm,require
from .economic_core import canonical,digest

@dataclass(frozen=True)
class Limits:
    branch:tuple # None or nonnegative M EUR reference-price output per period
    imported:tuple # None or nonnegative M EUR reference-price imported intermediate product
    tiers:tuple # partition of product codes; earlier tiers receive priority
    evidence:str
    origin:str="HYPOTHETICAL"

def bounds(a,n):
    require(len(a)==n,"LIMIT_AXIS")
    out=[]
    for v in a:
        require(v is None or (type(v) in (int,float) and math.isfinite(v) and v>=0),"LIMIT")
        out.append(v)
    return tuple(out)

def allocate(s,limits):
    A,c=validate(s);n=len(s.codes)
    require(limits.origin=="HYPOTHETICAL" and isinstance(limits.evidence,str) and limits.evidence.strip(),"LIMIT_EVIDENCE")
    bc=bounds(limits.branch,n);ic=bounds(limits.imported,n)
    require(isinstance(limits.tiers,tuple) and all(isinstance(t,tuple) and t for t in limits.tiers),"TIERS")
    flat=tuple(k for t in limits.tiers for k in t)
    require(len(flat)==n and set(flat)==set(s.codes),"TIER_PARTITION")
    requested=state(s);served=[0.]*n;used_b=[0.]*n;used_i=[0.]*n;rows=[]
    # For a tier, use its full demand vector, compute every required branch and imported product,
    # and choose the largest common fraction consistent with all remaining capacities.
    for tier in limits.tiers:
        y=tuple(s.final[i] if k in tier else 0. for i,k in enumerate(s.codes))
        q,tail,it=solve(A,y,c)
        g=mv(s.shares,q);im=mv(s.imported,g)
        # conservative upper bounds on requirements from the certified L1 Neumann tail.
        # D column sums 1; each row of M D <= max(M column-row coefficient).
        g_upper=[x+tail*max(s.shares[i]) if x>0 else x for i,x in enumerate(g)]
        # use nonzero tail bound for reachable rows even if truncated at zero
        # zero can be proven by graph reachability in the finite nonnegative system.
        reachable={i for i,x in enumerate(y) if x>0}
        for _ in range(n):
            nxt=reachable|{i for i in range(n) if any(A[i][j]>0 for j in reachable)}
            if nxt==reachable:break
            reachable=nxt
        g_upper=[x+(tail*max(s.shares[i][j] for j in reachable) if reachable else 0) for i,x in enumerate(g)]
        im_upper=[x+(tail*max(sum(s.imported[i][k]*s.shares[k][j] for k in range(n)) for j in reachable) if reachable else 0) for i,x in enumerate(im)]
        candidates=[(1.,"FULL",None)]
        for typ,cap,used,req in (("BRANCH",bc,used_b,g_upper),("IMPORT",ic,used_i,im_upper)):
            for i,(b,u,r) in enumerate(zip(cap,used,req)):
                if b is not None and r>0:candidates.append((max(0.,b-u)/r,typ,s.codes[i]))
        alpha=min(1.,min(x[0] for x in candidates))
        alpha=max(0.,alpha)
        # upper accounting of used capacities prevents earlier numerical truncation from
        # allocating the same tiny tail twice. Actual quantities independently replayed below.
        used_b=[u+alpha*r for u,r in zip(used_b,g_upper)]
        used_i=[u+alpha*r for u,r in zip(used_i,im_upper)]
        for i,k in enumerate(s.codes):served[i]+=alpha*y[i]
        binding=[{"kind":t,"code":k} for v,t,k in candidates if t!="FULL" and abs(v-alpha)<=1e-9*max(1,abs(alpha)) and alpha<1]
        rows.append({"products":tier,"fraction":alpha,"requested":math.fsum(y),"served":alpha*math.fsum(y),"binding":binding,"tail_bound":tail})
    realized=state(replace(s,final=tuple(served)))
    for cap,flow in ((bc,realized["g"]),(ic,realized["imports"])):
        require(all(b is None or x<=b+1e-8*max(1,b) for b,x in zip(cap,flow)),"CAPACITY_FEASIBILITY")
    require(all(0<=v<=y+1e-9 for v,y in zip(served,s.final)),"DEMAND_FEASIBILITY")
    missing=tuple(max(0.,y-v) for y,v in zip(s.final,served))
    unused=lambda cap,flow:tuple(None if b is None else max(0.,b-x) for b,x in zip(cap,flow))
    result={"status":"CONDITIONAL_FEASIBLE_ALLOCATION","publication":"BLOCK_PUBLICATION","codes":s.codes,
      "requested_final":s.final,"served_final":tuple(served),"unserved_final":missing,"tiers":rows,
      "required_output":requested["q"],"feasible_output":realized["q"],"feasible_branch_output":realized["g"],
      "required_imports":requested["imports"],"feasible_imports":realized["imports"],
      "branch_limit":bc,"import_limit":ic,"idle_branch_capacity":unused(bc,realized["g"]),"unused_import_capacity":unused(ic,realized["imports"]),
      "totals":{k:math.fsum(realized[k]) for k in ("q","g","imports","wage","other_tax","bridge","surplus","va")},
      "unconstrained_totals":{k:math.fsum(requested[k]) for k in ("q","g","imports","wage","other_tax","bridge","surplus","va")},
      "actual_output":None,"employment":None,"gdp":None,"prices":None,"evidence":limits.evidence,
      "limitations":["fixed coefficients and shares, no substitution or stocks","priority tiers are explicit assumed policy, not welfare optimum","import limits apply only to intermediate imported products","feasible scenario is not observed output; unused capacity is value-equivalent, not jobs"]}
    return {"result":result,"sha256":digest(canonical(result))}
