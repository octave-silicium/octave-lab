"""G4 v0.7f: exact synthetic pari-passu clearing and conditional credit headroom.
Eisenberg-Noe regular special case: each debtor has a positive external obligation.
Not a calibrated bank, insolvency or prudential model."""
from fractions import Fraction as F
from .economic_sector_structural import require
from .economic_core import canonical,digest

def q(x):
    require(type(x) in (int,float,str,F),"NUMBER")
    try:v=F(str(x))
    except (ValueError,ZeroDivisionError,OverflowError):raise ValueError("NUMBER")
    require(v>=0,"NONNEGATIVE")
    return v
def solve(a,b):
    n=len(b);m=[list(r)+[v] for r,v in zip(a,b)]
    for i in range(n):
        j=next((j for j in range(i,n) if m[j][i]),None);require(j is not None,"SINGULAR")
        m[i],m[j]=m[j],m[i];v=m[i][i];m[i]=[x/v for x in m[i]]
        for j in range(n):
            if i!=j:
                v=m[j][i];m[j]=[x-v*y for x,y in zip(m[j],m[i])]
    return [r[-1] for r in m]
def clear(codes,liabilities,external_due,liquidity,*,evidence):
    require(isinstance(codes,tuple) and 1<=len(codes)<=30 and len(set(codes))==len(codes) and all(isinstance(k,str) and k.strip() for k in codes),"AXIS")
    require(isinstance(evidence,str) and evidence.strip(),"EVIDENCE")
    n=len(codes);require(len(liabilities)==len(external_due)==len(liquidity)==n and all(len(r)==n for r in liabilities),"SHAPE")
    L=[[q(x) for x in r] for r in liabilities];o=list(map(q,external_due));e=list(map(q,liquidity))
    require(all(L[i][i]==0 for i in range(n)),"SELF_CLAIM")
    b=[sum(r)+v for r,v in zip(L,o)]
    require(all(not x or y>0 for x,y in zip(b,o)),"EXTERNAL_LEAK_REQUIRED")
    P=[[x/b[i] if b[i] else F(0) for x in r] for i,r in enumerate(L)]
    incoming=lambda p,i:sum((P[j][i]*p[j] for j in range(n)),F(0))
    p=b[:];defaults=set();rounds=[]
    # Fictitious default algorithm: monotonically expand the set of short payers.
    for _ in range(n+1):
        new={i for i in range(n) if e[i]+incoming(p,i)<b[i]}|defaults
        if new==defaults:break
        rounds.append([codes[i] for i in sorted(new-defaults)]);defaults=new
        d=sorted(defaults);ok=set(range(n))-defaults
        a=[[F(int(i==j))-P[j][i] for j in d] for i in d]
        x=[e[i]+sum((P[j][i]*b[j] for j in ok),F(0)) for i in d]
        vals=solve(a,x);p=b[:]
        for i,v in zip(d,vals):p[i]=v
    else:raise ValueError("NO_CONVERGENCE")
    require(all(0<=p[i]<=b[i] and p[i]==min(b[i],e[i]+incoming(p,i)) for i in range(n)),"CLEARING_RESIDUAL")
    paid=[[P[i][j]*p[i] for j in range(n)] for i in range(n)]
    outside=[o[i]*p[i]/b[i] if b[i] else F(0) for i in range(n)]
    remaining=[e[i]+incoming(p,i)-p[i] for i in range(n)]
    short=[b[i]-p[i] for i in range(n)]
    lost=[sum((L[j][i]-paid[j][i] for j in range(n)),F(0)) for i in range(n)]
    require(sum(e)==sum(remaining)+sum(outside) and all(x>=0 for x in remaining),"LIQUIDITY_CONSERVATION")
    require(sum(short)==sum(lost)+sum(o)-sum(outside),"SHORTFALL_CONSERVATION")
    out={"status":"SYNTHETIC_CLEARING_NOT_FORECAST","publication":"BLOCK_PUBLICATION","codes":codes,"evidence":evidence,
      "liabilities":[list(map(str,r)) for r in L],"external_due":list(map(str,o)),"initial_liquidity":list(map(str,e)),
      "payments":list(map(str,p)),"paid_matrix":[list(map(str,r)) for r in paid],"external_paid":list(map(str,outside)),
      "unpaid_matrix":[[str(L[i][j]-paid[i][j]) for j in range(n)] for i in range(n)],"unpaid_total_by_debtor":list(map(str,short)),
      "unpaid_claims_by_creditor":list(map(str,lost)),"remaining_liquidity":list(map(str,remaining)),"default_rounds":rounds,
      "actual_default":None,"actual_loss":None,"limitations":["all modeled obligations due simultaneously, equal priority, divisible payments, no bankruptcy cost or fire sales","positive outside obligations for every debtor, ensuring strict contraction and unique solution","unpaid claim is not automatically a permanent credit loss; no legal insolvency conclusion","external settlement liquidity exogenous, no intraday timeline, bank runs or collateral"]}
    return {"result":out,"sha256":digest(canonical(out))}

def credit_headroom(receipt,bank,*,capital,existing_rwa,minimum_ratio,new_risk_weight,credit_limit,loss_recognition,requests,evidence):
    """Conditional write-down and pro-rata credit allocation; not actual origination."""
    r=receipt["result"];require(r["status"]=="SYNTHETIC_CLEARING_NOT_FORECAST" and receipt["sha256"]==digest(canonical(r)),"RECEIPT")
    require(bank in r["codes"] and isinstance(evidence,str) and evidence.strip(),"BANK")
    K,R,k,w,lim,loss=map(q,(capital,existing_rwa,minimum_ratio,new_risk_weight,credit_limit,loss_recognition))
    require(0<k<=1 and w>0 and loss<=1,"POLICY")
    require(isinstance(requests,dict) and requests and bank not in requests and set(requests)<=set(r["codes"]),"REQUESTS")
    want={a:q(v) for a,v in requests.items()};total=sum(want.values())
    unpaid=q(r["unpaid_claims_by_creditor"][r["codes"].index(bank)])
    impairment=unpaid*loss;after=K-impairment
    # Hold existing RWA constant deliberately, no mechanical release through defaults.
    head=max(F(0),(after/k-R)/w);approved=min(head,lim,total)
    allocations={a:v*approved/total if total else F(0) for a,v in want.items()}
    require(sum(allocations.values())==approved,"CREDIT_ALLOCATION")
    out={"status":"CONDITIONAL_CREDIT_HEADROOM","publication":"BLOCK_PUBLICATION","source_receipt":receipt["sha256"],"bank":bank,
      "capital_before":str(K),"unpaid_claims":str(unpaid),"loss_recognition":str(loss),"assumed_impairment":str(impairment),
      "capital_after":str(after),"existing_rwa_held_constant":str(R),"minimum_ratio":str(k),"new_risk_weight":str(w),
      "capital_shortfall":str(max(F(0),k*R-after)),"capital_based_headroom":str(head),"exogenous_credit_limit":str(lim),
      "requested":{a:str(v) for a,v in want.items()},"approved":{a:str(v) for a,v in allocations.items()},"approved_total":str(approved),
      "actual_regulatory_capital":None,"actual_credit_granted":None,"evidence":evidence,
      "limitations":["explicit assumed impairment fraction, not measured loss given default or write-off","existing RWA fixed, no capital buffers, liquidity, leverage, deposit insurance, collateral or central bank","pro-rata rationing, no optimization or new loan booking; usable as scenario ceiling in v0.7d only after explicit mapping"]}
    return {"result":out,"sha256":digest(canonical(out))}
