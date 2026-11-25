"""G4 v0.7a: domestic investment deliveries, capital vintages and feasible output.
Synthetic fixed-price quantities and historical-cost proxy, not ESA capital stock.
"""
import math
from dataclasses import dataclass,replace,asdict
from .economic_sector_structural import require,validate
from .economic_sector_capacity import Limits,allocate
from .economic_sector_capacity_dynamics import nonnegative
from .economic_core import canonical,digest

@dataclass(frozen=True)
class Asset:
    id:str
    branch:str
    product:str
    acquisition_price:float # M EUR reference value per asset unit
    capacity_per_unit:float # M EUR reference output per period per asset unit at age zero
    efficiency_decay:float # per period; distinct from carrying value
    book_decay:float # per period historical-cost depreciation proxy
    life:int # maximum active periods
    evidence:str

@dataclass(frozen=True)
class Vintage:
    asset:str
    units:float
    age:int
    carrying_value:float # M EUR historical-cost proxy

@dataclass(frozen=True)
class Investment:
    id:str
    asset:str
    period:int
    units:float
    lag:int # delivered at t, operational beginning t+lag
    evidence:str

@dataclass(frozen=True)
class Period:
    structure:object # excludes the modeled investment demand; other final uses fixed
    imported_limits:tuple # intermediate imports only
    tiers:tuple
    efficiency_factor:tuple # explicit asset type efficiency multipliers in asset order
    evidence:str

def finite(x):return type(x) in (int,float) and math.isfinite(x)
def words(x):return isinstance(x,str) and bool(x.strip())
def int_range(x,a,b):return type(x) is int and a<=x<=b
def balance(a,b,reason):require(abs(a-b)<=1e-9*max(1,abs(a),abs(b)),reason)

def path(periods,assets,initial_vintages,investments=(),*,noncapital_capacity,period_unit,evidence):
    require(isinstance(periods,tuple) and 1<=len(periods)<=120 and period_unit in ("MONTH","QUARTER","YEAR") and words(evidence),"HORIZON")
    require(isinstance(assets,tuple) and assets and len({a.id for a in assets})==len(assets),"ASSETS")
    codes=periods[0].structure.codes;n=len(codes);ix={k:i for i,k in enumerate(codes)}
    # No actual stock or product investment-use data admitted in this first tranche.
    require(periods[0].structure.origin=="SYNTHETIC","SYNTHETIC_ONLY")
    noncap=nonnegative(noncapital_capacity,n,"NONCAPITAL_CAPACITY")
    by={a.id:a for a in assets}
    for a in assets:
        require(words(a.id) and a.branch in ix and a.product in ix and words(a.evidence),"ASSET_AXIS")
        require(finite(a.acquisition_price) and a.acquisition_price>0 and finite(a.capacity_per_unit) and a.capacity_per_unit>0 and all(finite(x) and 0<=x<=1 for x in (a.efficiency_decay,a.book_decay)) and int_range(a.life,1,120),"ASSET_PARAMETERS")
    require(isinstance(initial_vintages,tuple) and isinstance(investments,tuple),"LEDGERS")
    for v in initial_vintages:
        require(v.asset in by and finite(v.units) and v.units>0 and int_range(v.age,0,by[v.asset].life-1) and finite(v.carrying_value) and 0<=v.carrying_value<=v.units*by[v.asset].acquisition_price,"VINTAGE")
    require(len({i.id for i in investments})==len(investments),"DUPLICATE_INVESTMENT")
    for i in investments:
        require(words(i.id) and i.asset in by and int_range(i.period,1,len(periods)) and int_range(i.lag,1,120) and finite(i.units) and i.units>0 and words(i.evidence),"INVESTMENT")
    active=list(initial_vintages);pending=[];rows=[]
    def value(vs):return math.fsum(v.carrying_value for v in vs)
    def units(vs):return {a.id:math.fsum(v.units for v in vs if v.asset==a.id) for a in assets}
    for t,p in enumerate(periods,1):
        s=p.structure;require(s.codes==codes and s.origin=="SYNTHETIC" and words(p.evidence),"COMPARABILITY");validate(s)
        factor=nonnegative(p.efficiency_factor,len(assets),"EFFICIENCY_FACTOR");factors=dict(zip(by,factor))
        opening_active=value(active);opening_pending=math.fsum(v.carrying_value for _,_,v in pending)
        opening_units=units(active+[v for _,_,v in pending])
        arriving=[(due,k,v) for due,k,v in pending if due==t];pending=[z for z in pending if z[0]!=t]
        active.extend(v for _,_,v in arriving);commissioned=value([v for _,_,v in arriving])
        capacity=list(noncap)
        for v in active:
            a=by[v.asset];capacity[ix[a.branch]]+=v.units*a.capacity_per_unit*(1-a.efficiency_decay)**v.age*factors[v.asset]
        require(all(math.isfinite(x) for x in capacity),"CAPACITY_OVERFLOW")
        request=[0.]*n;orders=[i for i in investments if i.period==t]
        for i in orders:
            a=by[i.asset];request[ix[a.product]]+=i.units*a.acquisition_price
        total=tuple(y+k for y,k in zip(s.final,request))
        # Same product shares rationing proportionally between other final uses and investment.
        # No investment assumed acquired before the existing feasible allocation serves it.
        out=allocate(replace(s,final=total),Limits(tuple(capacity),p.imported_limits,p.tiers,p.evidence))["result"]
        served=out["served_final"];fractions=tuple(x/y if y else 0. for x,y in zip(served,total))
        other=tuple(y*f for y,f in zip(s.final,fractions));acquired=[];added_units={a.id:0. for a in assets}
        for i in orders:
            a=by[i.asset];u=i.units*fractions[ix[a.product]];cost=u*a.acquisition_price
            if u>0:
                pending.append((t+i.lag,i.id,Vintage(i.asset,u,0,cost)));added_units[i.asset]+=u
            acquired.append({"id":i.id,"asset":i.asset,"product":a.product,"requested_units":i.units,"acquired_units":u,"unfilled_units":max(0.,i.units-u),"acquisition_value":cost,"commission_period":t+i.lag if u else None})
        investment=math.fsum(x["acquisition_value"] for x in acquired)
        balance(math.fsum(served),math.fsum(other)+investment,"FINAL_USE_SPLIT")
        depreciation=[];retired=[];survivors=[]
        for v in active:
            a=by[v.asset];dep=v.carrying_value*a.book_decay
            depreciation.append(dep);remaining=max(0.,v.carrying_value-dep)
            if v.age+1>=a.life:retired.append(Vintage(v.asset,v.units,v.age+1,remaining))
            else:survivors.append(Vintage(v.asset,v.units,v.age+1,remaining))
        dep=math.fsum(depreciation);writeoff=value(retired);active=survivors
        end_active=value(active);end_pending=math.fsum(v.carrying_value for _,_,v in pending)
        balance(end_active,opening_active+commissioned-dep-writeoff,"ACTIVE_BALANCE")
        balance(end_pending,opening_pending+investment-commissioned,"WIP_BALANCE")
        balance(end_active+end_pending,opening_active+opening_pending+investment-dep-writeoff,"TOTAL_CAPITAL_BALANCE")
        ending_units=units(active+[v for _,_,v in pending]);removed=units(retired)
        for k in by:balance(ending_units[k],opening_units[k]+added_units[k]-removed[k],"PHYSICAL_UNITS_BALANCE")
        rows.append({"period":t,"capacity":capacity,"other_final_requested":s.final,"other_final_served":other,"investment_requested":request,"investment_acquired":investment,"investment_orders":acquired,"commissioned":[{"id":k,**asdict(v)} for _,k,v in arriving],"opening_active_value":opening_active,"opening_wip_value":opening_pending,"commissioned_value":commissioned,"depreciation_proxy":dep,"retirement_writeoff":writeoff,"closing_active_value":end_active,"closing_wip_value":end_pending,"closing_units_by_asset_including_wip":ending_units,"retired_units_by_asset":removed,"active_vintages":[asdict(v) for v in active],"allocation":out,"capital_net_surplus":None})
    result={"status":"CONDITIONAL_CAPITAL_VINTAGE_PATH","publication":"BLOCK_PUBLICATION","period_unit":period_unit,"codes":codes,"assets":[asdict(a) for a in assets],"periods":rows,"pending":[{"due":due,"id":k,**asdict(v)} for due,k,v in pending],"evidence":evidence,"gdp":None,"employment":None,"actual_capital_stock":None,"actual_ccf":None,"financing":None,"limitations":["synthetic domestic investment only; other final demand must exclude orders, unfilled orders not automatically carried over","homogeneous divisible assets, additive within branch; noncapital capacity exogenous; no labor or energy complementarity","historical-cost proxy depreciation is not ESA consumption of fixed capital; no price revaluation, salvage or financial balance","investment paid/delivered in one period, no work-in-progress production before delivery; no credit or endogenous decisions","obsolescence via age efficiency decay and exogenous efficiency factors; no automatic technology diffusion","intermediate import limits only, no joint inventory or income loop in this tranche; gross surplus not debited again for depreciation"]}
    return {"result":result,"sha256":digest(canonical(result))}
