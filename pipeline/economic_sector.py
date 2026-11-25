"""G4 v0.1: exact domestic input-output accounting and conditional demand requirements.
Bounded dense reference implementation, not a full FIGARO/ICIO solver.
"""
from dataclasses import dataclass,asdict
from fractions import Fraction as F
from pathlib import Path
from .economic_core import require,words,identity,canonical,digest
from .economic_events import integer

@dataclass(frozen=True)
class Table:
    id:str
    revision:int
    geography:str
    year:int
    classification:str
    currency_unit:str
    price_basis:str
    source:str
    evidence_status:str
    products:tuple
    domestic:tuple # supplier row, using product column
    output:tuple
    imports:tuple # imported intermediate inputs by using product
    product_taxes:tuple # net taxes on intermediate inputs, signed
    value_added:tuple
    final_domestic:tuple # final uses of domestic products, total per product
    @property
    def key(self):return identity(self.id,self.revision)

def num(x):
    require(type(x) is int or (isinstance(x,str) and len(x)<=100),"NUMBER")
    try:v=F(x)
    except (ValueError,ZeroDivisionError):raise ValueError("NUMBER") from None
    require(abs(v)<=10**16,"NUMBER_RANGE")
    return v

def vector(x,n):
    require(isinstance(x,tuple) and len(x)==n,"VECTOR")
    return tuple(num(v) for v in x)

def validate(t):
    t.key;n=len(t.products)
    require(1<=n<=64 and len(set(t.products))==n and all(words(x) for x in t.products),"PRODUCTS")
    require(all(words(x) for x in (t.geography,t.classification,t.currency_unit,t.source)) and integer(t.year,1900,2200) and t.price_basis=="BASIC_CURRENT" and t.evidence_status in ("OFFICIAL_FICTIONAL_BENCHMARK","SYNTHETIC"),"TABLE_METADATA")
    require(isinstance(t.domestic,tuple) and len(t.domestic)==n,"MATRIX")
    z=tuple(vector(r,n) for r in t.domestic)
    x,m,tax,v,y=(vector(a,n) for a in (t.output,t.imports,t.product_taxes,t.value_added,t.final_domestic))
    require(all(a>0 for a in x) and all(a>=0 for r in z for a in r) and all(a>=0 for a in (*m,*v,*y)),"TABLE_SIGN")
    for j in range(n):
        require(sum(z[j])+y[j]==x[j],"ROW_BALANCE")
        require(sum(z[i][j] for i in range(n))+m[j]+tax[j]+v[j]==x[j],"COLUMN_BALANCE")
    a=tuple(tuple(z[i][j]/x[j] for j in range(n)) for i in range(n))
    # Conservative sufficient productivity condition, not necessary.
    require(all(sum(a[i][j] for i in range(n))<1 for j in range(n)),"PRODUCTIVITY_BOUND")
    return z,x,m,tax,v,y,a

def solve(a,y):
    n=len(y)
    b=[[F(i==j)-a[i][j] for j in range(n)]+[y[i]] for i in range(n)]
    for k in range(n):
        pivot=next((i for i in range(k,n) if b[i][k]),None)
        require(pivot is not None,"SINGULAR")
        b[k],b[pivot]=b[pivot],b[k];p=b[k][k];b[k]=[v/p for v in b[k]]
        for i in range(n):
            if i==k:continue
            p=b[i][k]
            if p:b[i]=[v-p*w for v,w in zip(b[i],b[k])]
    x=tuple(r[-1] for r in b)
    require(all(x[i]-sum(a[i][j]*x[j] for j in range(n))==y[i] for i in range(n)),"SOLVE_RESIDUAL")
    return x

def run(t,delta_final,capacity=None):
    z,x,m,tax,v,y,a=validate(t);n=len(x);dy=vector(delta_final,n)
    y1=tuple(y[i]+dy[i] for i in range(n));require(all(u>=0 for u in y1),"NEGATIVE_FINAL_USE")
    require(solve(a,y)==x,"BASELINE_REPLAY")
    x1=solve(a,y1);dx=tuple(x1[i]-x[i] for i in range(n))
    require(all(u>=0 for u in x1),"NEGATIVE_OUTPUT")
    dm=tuple(m[i]/x[i]*dx[i] for i in range(n))
    dt=tuple(tax[i]/x[i]*dx[i] for i in range(n))
    dv=tuple(v[i]/x[i]*dx[i] for i in range(n))
    require(sum(dy)==sum(dm)+sum(dt)+sum(dv),"FINAL_USE_DECOMPOSITION")
    cap=vector(capacity,n) if capacity is not None else None
    require(cap is None or all(cap[i]>=x[i] for i in range(n)),"CAPACITY_BASELINE")
    exceeded=[t.products[i] for i in range(n) if cap is not None and x1[i]>cap[i]]
    rows=[{"product":t.products[i],"baseline_output":str(x[i]),"baseline_final_domestic":str(y[i]),"final_demand_change":str(dy[i]),"required_output_change":str(dx[i]),"required_output":str(x1[i]),"indirect_output_change":str(dx[i]-dy[i]),"imported_intermediate_change":str(dm[i]),"intermediate_product_tax_change":str(dt[i]),"gross_value_added_change":str(dv[i]),"capacity":str(cap[i]) if cap is not None else None} for i in range(n)]
    r={"table_ref":t.key,"geography":t.geography,"year":t.year,"classification":t.classification,"currency_unit":t.currency_unit,"price_basis":t.price_basis,"source":t.source,"evidence_status":t.evidence_status,"coefficient_matrix":[[str(u) for u in row] for row in a],"rows":rows,"final_domestic_demand_change":str(sum(dy)),"gross_output_requirement_change":str(sum(dx)),"indirect_output_requirement_change":str(sum(dx)-sum(dy)),"imported_intermediate_requirement_change":str(sum(dm)),"intermediate_product_tax_change":str(sum(dt)),"gross_value_added_requirement_change":str(sum(dv)),"capacity_status":"REQUIREMENTS_EXCEED_CAPACITY" if exceeded else "WITHIN_DECLARED_CAPACITY" if cap is not None else "CAPACITY_UNKNOWN","capacity_exceeded":exceeded,"realized_output_change":None,"employment_change":None,"gdp_change":None,"input_sha256":digest(canonical({"table":asdict(t),"delta":delta_final,"capacity":capacity})),"model_sha256":digest(Path(__file__).read_bytes()),"status":"CONDITIONAL_DEMAND_REQUIREMENTS_NOT_FORECAST","publication":"BLOCK_PUBLICATION"}
    return {"result":r,"sha256":digest(canonical(r))}
