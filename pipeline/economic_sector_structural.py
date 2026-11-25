"""G4 structural requirements at fixed reference prices, NOT an equilibrium forecast."""
import math
from dataclasses import dataclass

def require(ok,why):
    if not ok: raise ValueError(why)
def vec(x,n):
    a=tuple(float(v) for v in x)
    require(len(a)==n and all(math.isfinite(v) for v in a),"AXIS")
    return a
def mat(x,n):
    a=tuple(vec(r,n) for r in x)
    require(len(a)==n,"AXIS")
    return a
def dot(a,b):return math.fsum(x*y for x,y in zip(a,b))
def mv(a,b):return tuple(dot(r,b) for r in a)
def mm(a,b):return tuple(tuple(dot(r,c) for c in zip(*b)) for r in a)
def colsum(a):return tuple(math.fsum(c) for c in zip(*a))
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def norm(a):return math.fsum(abs(x) for x in a)
def close(a,b,tol=1e-7):
    return norm(sub(a,b))<=tol*max(1,norm(a),norm(b))
def matrix_sub(a,b):return tuple(sub(x,y) for x,y in zip(a,b))
@dataclass(frozen=True)
class Structure:
    codes:tuple
    domestic:tuple  # product x branch; basic price inputs per branch output
    imported:tuple  # product x branch
    shares:tuple    # branch x product; fixed allocation within each state
    wage:tuple     # D1 per branch output
    other_tax:tuple # D29-D39 per branch output, signed
    bridge:tuple    # purchaser/basic valuation bridge, signed
    surplus:tuple   # B2g+B3g per output; explicit closure input
    final:tuple     # domestic final demand by product, reference-price M EUR
    origin:str     # SYNTHETIC or PINNED_2022_CONDITIONAL
def validate(s):
    n=len(s.codes)
    require(n>0 and len(set(s.codes))==n and all(isinstance(c,str) and c for c in s.codes),"CODES")
    require(s.origin in ("SYNTHETIC","PINNED_2022_CONDITIONAL"),"ORIGIN")
    B,M,D=(mat(a,n) for a in (s.domestic,s.imported,s.shares))
    w,t,h,k,y=(vec(a,n) for a in (s.wage,s.other_tax,s.bridge,s.surplus,s.final))
    require(all(x>=0 for a in (B,M,D) for r in a for x in r) and all(x>=0 for a in (w,y) for x in a),"NEGATIVE_INPUT")
    require(all(abs(x-1)<=1e-10 for x in colsum(D)),"MARKET_SHARES")
    require(all(abs(a+b+c+d+e+f-1)<=1e-10 for a,b,c,d,e,f in zip(colsum(B),colsum(M),w,t,h,k)),"UNIT_ACCOUNT")
    A=mm(B,D); c=max(colsum(A))
    require(c<1,"PRODUCTIVITY_BOUND")
    return A,c

def solve(A,y,c,*,relative_tol=1e-12):
    # Neumann iteration with L1 certified remainder bound.
    require(type(relative_tol) in (int,float) and 0<relative_tol<=1e-12,"SOLVE_TOLERANCE")
    term=tuple(y);q=term;tol=relative_tol*max(1,norm(y))
    for i in range(10000):
        term=mv(A,term);q=add(q,term)
        bound=norm(term)*c/(1-c)
        if bound<=tol:
            require(close(sub(q,mv(A,q)),y,1e-10),"SOLVE_RESIDUAL")
            return q,bound,i+1
    raise ValueError("SOLVE_CONVERGENCE")

def state(s):
    A,c=validate(s);q,bound,it=solve(A,s.final,c);g=mv(s.shares,q)
    im=mv(s.imported,g);w=tuple(x*y for x,y in zip(s.wage,g))
    t=tuple(x*y for x,y in zip(s.other_tax,g));h=tuple(x*y for x,y in zip(s.bridge,g))
    k=tuple(x*y for x,y in zip(s.surplus,g));va=add(add(w,t),k)
    require(abs(math.fsum(s.final)-math.fsum(im)-math.fsum(h)-math.fsum(va))<=1e-9*max(1,norm(s.final)),"FINAL_BALANCE")
    return {"q":q,"g":g,"imports":im,"wage":w,"other_tax":t,"bridge":h,"surplus":k,"va":va,"A":A,"contraction":c,"tail_bound":bound,"iterations":it}

def compare(base,scenario,capacity=None):
    require(base.codes==scenario.codes and base.origin==scenario.origin,"COMPARABILITY")
    a,b=state(base),state(scenario);A0,A1=a["A"],b["A"];c0,c1=a["contraction"],b["contraction"]
    dy=sub(scenario.final,base.final);dA=matrix_sub(A1,A0);dq=sub(b["q"],a["q"])
    # Exact change identity: dq=R1(dy+dA*q0); signed impulses permitted.
    impulse=mv(dA,a["q"]);total=add(dy,impulse)
    layers=[total,mv(A1,total)];layers.append(mv(A1,layers[-1]))
    remainder=sub(dq,tuple(math.fsum(z) for z in zip(*layers)))
    demand1=solve(A1,dy,c1)[0];demand0=solve(A0,dy,c0)[0]
    struct0=solve(A1,impulse,c1)[0]
    q_demand=add(a["q"],demand0);struct1=solve(A1,mv(dA,q_demand),c1)[0]
    demand=tuple((x+y)/2 for x,y in zip(demand0,demand1));structure=tuple((x+y)/2 for x,y in zip(struct0,struct1))
    require(close(add(demand,structure),dq),"SHAPLEY_BALANCE")
    require(close(add(demand1,struct0),dq),"CHANGE_IDENTITY")
    dg=sub(b["g"],a["g"])
    intensive={};extensive={}
    for k in ("wage","other_tax","bridge","surplus"):
        i0=getattr(base,k);i1=getattr(scenario,k)
        intensive[k]=tuple((y-x)*(u+v)/2 for x,y,u,v in zip(i0,i1,a["g"],b["g"]))
        extensive[k]=tuple((x+y)*(v-u)/2 for x,y,u,v in zip(i0,i1,a["g"],b["g"]))
        require(close(add(intensive[k],extensive[k]),sub(b[k],a[k])),"INCOME_DECOMPOSITION")
    changes={k:sub(b[k],a[k]) for k in ("q","g","imports","wage","other_tax","bridge","surplus","va")}
    cap=None
    if capacity is not None:
        cap=vec(capacity,len(base.codes));require(all(x>=0 for x in cap),"CAPACITY")
        cap={c:max(0,x-y) for c,x,y in zip(base.codes,b["g"],cap)}
    return {"status":"CONDITIONAL_REQUIREMENTS_NOT_FORECAST","publication":"BLOCK_PUBLICATION","codes":base.codes,"changes":changes,
      "demand_shapley":demand,"structure_shapley":structure,"propagation_orders_0_1_2":layers,"propagation_order_3_plus":remainder,
      "income_intensity_effects":intensive,"income_output_effects":extensive,"capacity_excess_requirements":cap,
      "realized_output":None,"employment":None,"gdp":None,"price_effect":None,"net_profit":None,
      "tail_bounds":{"base":a["tail_bound"],"scenario":b["tail_bound"]},
      "totals":{k:math.fsum(v) for k,v in changes.items()}}
