"""G4 v0.5b: discrete-period imported-input inventories and delayed branch capacity.
Fixed-price equivalent units, conditional scenarios, no observed forecasts.
"""
import math
from dataclasses import dataclass,replace,asdict
from .economic_sector_structural import validate,state,require
from .economic_sector_capacity import Limits,allocate
from .economic_core import canonical,digest

@dataclass(frozen=True)
class Period:
    structure:object
    deliveries:tuple # gross exogenous imports of intermediate products arriving at start
    tiers:tuple
    evidence:str

@dataclass(frozen=True)
class CapacityOrder:
    placed:int # 1-based period; known scenario decision
    lag:int # commissioning/withdrawal at start of placed+lag, at least one period
    branch:str
    delta:float # signed flow capacity per period, not monetary capex
    evidence:str

def nonnegative(x,n,why):
    require(isinstance(x,tuple) and len(x)==n and all(type(v) in (int,float) and math.isfinite(v) and v>=0 for v in x),why)
    return tuple(float(v) for v in x)

def trajectory(periods,initial_capacity,initial_stock,orders=(),*,period_unit,evidence):
    require(isinstance(periods,tuple) and 1<=len(periods)<=120,"HORIZON")
    require(period_unit in ("MONTH","QUARTER","YEAR") and isinstance(evidence,str) and evidence.strip(),"TIME_SCOPE")
    codes=periods[0].structure.codes;n=len(codes)
    cap=nonnegative(initial_capacity,n,"CAPACITY");stock=nonnegative(initial_stock,n,"STOCK")
    origin=periods[0].structure.origin
    require(isinstance(orders,tuple),"ORDERS")
    for o in orders:
        require(type(o.placed) is int and 1<=o.placed<=len(periods) and type(o.lag) is int and 1<=o.lag<=120 and o.branch in codes and type(o.delta) in (int,float) and math.isfinite(o.delta) and o.delta!=0 and isinstance(o.evidence,str) and o.evidence.strip(),"ORDER")
    rows=[];pending=[];cum_del=[0.]*n;cum_use=[0.]*n
    for t,p in enumerate(periods,1):
        s=p.structure
        require(s.codes==codes and s.origin==origin and isinstance(p.evidence,str) and p.evidence.strip(),"COMPARABILITY")
        validate(s)
        opening_cap=cap;arrived=[o for o in pending if o.placed+o.lag==t]
        pending=[o for o in pending if o.placed+o.lag!=t]
        cap=tuple(v+math.fsum(o.delta for o in arrived if o.branch==k) for k,v in zip(codes,cap))
        require(all(math.isfinite(v) and v>=0 for v in cap),"NEGATIVE_COMMISSIONED_CAPACITY")
        opening=stock;delivery=nonnegative(p.deliveries,n,"DELIVERIES")
        available=tuple(a+b for a,b in zip(opening,delivery))
        require(all(math.isfinite(v) for v in available),"STOCK_OVERFLOW")
        r=allocate(s,Limits(cap,available,p.tiers,p.evidence))["result"]
        use=r["feasible_imports"]
        require(all(x<=a+1e-9*max(1,a) for a,x in zip(available,use)),"STOCK_FEASIBILITY")
        stock=tuple(max(0.,a-x) for a,x in zip(available,use))
        delta=tuple(b-a for a,b in zip(opening,stock))
        for i in range(n):
            cum_del[i]+=delivery[i];cum_use[i]+=use[i]
            require(abs(initial_stock[i]+cum_del[i]-cum_use[i]-stock[i])<=1e-8*max(1,initial_stock[i]+cum_del[i]),"STOCK_CONSERVATION")
        # use is intermediate imported consumption (G4), not border arrivals.
        # Final served = VA + valuation bridge + border arrivals - stock accumulation.
        lhs=math.fsum(r["served_final"]);rhs=r["totals"]["va"]+r["totals"]["bridge"]+math.fsum(delivery)-math.fsum(delta)
        require(abs(lhs-rhs)<=1e-8*max(1,lhs,abs(rhs)),"FLOW_STOCK_BALANCE")
        placed=[o for o in orders if o.placed==t];pending.extend(placed)
        rows.append({"period":t,"opening_capacity":opening_cap,"capacity":cap,"commissioned":[asdict(o) for o in arrived],"orders_placed":[asdict(o) for o in placed],"opening_stock":opening,"deliveries":delivery,"imported_input_use":use,"closing_stock":stock,"stock_change":delta,"served_final":r["served_final"],"unserved_final":r["unserved_final"],"feasible_branch_output":r["feasible_branch_output"],"idle_capacity":r["idle_branch_capacity"],"tiers":r["tiers"],"totals":r["totals"],"unconstrained_totals":r["unconstrained_totals"],"flow_stock_residual":lhs-rhs})
    result={"status":"CONDITIONAL_DYNAMIC_CAPACITY_STOCK","publication":"BLOCK_PUBLICATION","period_unit":period_unit,"codes":codes,"periods":rows,"pending_orders":[asdict(o) for o in pending],"initial_stock":initial_stock,"closing_stock":stock,"cumulative_deliveries":cum_del,"cumulative_imported_input_use":cum_use,"cumulative_unserved_final":math.fsum(math.fsum(r["unserved_final"]) for r in rows),"actual_output":None,"employment":None,"gdp":None,"prices":None,"evidence":evidence,"limitations":["inventories only for imported intermediate products, pooled with full fungibility within product","arrivals exogenous, beginning-of-period; no domestic inventories, final imports, spoilage, financing or replenishment optimization","capacity orders exogenous, no capex or capital stock inferred; no automatic retirement or investment rule","per-period prices and units assumed comparable, no causal calibration"]}
    return {"result":result,"sha256":digest(canonical(result))}
