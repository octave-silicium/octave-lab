"""G4 v0.6e: exact marginal bounds, not reconstructed bilateral flows."""
from decimal import Decimal as D
from .economic_sector_structural import require

def transportation_bounds(rows,cols):
    """Unrestricted nonnegative transportation polytope with known margins.
    Exact sharp bounds for each cell individually; extrema not jointly achievable.
    Preserve any reconciliation discrepancy as explicit unallocated margin.
    """
    require(isinstance(rows,dict) and isinstance(cols,dict) and rows and cols,"AXIS")
    require("UNALLOCATED_RESIDUAL" not in rows and "UNALLOCATED_RESIDUAL" not in cols,"RESERVED_AXIS")
    r={k:D(str(v)) for k,v in rows.items()};c={k:D(str(v)) for k,v in cols.items()}
    require(all(v.is_finite() and v>=0 for v in (*r.values(),*c.values())),"NONNEGATIVE")
    sr=sum(r.values());sc=sum(c.values());total=max(sr,sc)
    require(total>0,"EMPTY")
    if sr<sc:r["UNALLOCATED_RESIDUAL"]=sc-sr
    if sc<sr:c["UNALLOCATED_RESIDUAL"]=sr-sc
    cells=[]
    for i,a in r.items():
        for j,b in c.items():
            lo=max(D(0),a+b-total);hi=min(a,b)
            cells.append({"row":i,"column":j,"lower":str(lo),"upper":str(hi)})
    return {"rows":{k:str(v) for k,v in r.items()},"columns":{k:str(v) for k,v in c.items()},"total":str(total),"original_row_minus_column":str(sr-sc),"cells":cells,"status":"MARGINAL_BOUNDS_NOT_IDENTIFIED_MATRIX"}

def proportional_shock(bounds,row,delta):
    """A signed shock proportional across the selected row's unknown allocation."""
    a=D(bounds["rows"][row]);d=D(str(delta))
    require(a>0 and d.is_finite() and d>=-a,"SHOCK")
    result=[]
    for cell in bounds["cells"]:
        if cell["row"]!=row:continue
        x=d*D(cell["lower"])/a;y=d*D(cell["upper"])/a
        result.append({"column":cell["column"],"lower":str(min(x,y)),"upper":str(max(x,y))})
    return result
