"""G4 income bridge: standard-library accounting, no observed admission without qualified accounts."""
import math

def require(ok, reason):
    if not ok: raise ValueError(reason)

def vector(x):
    try:
        vals=tuple(float(v) for v in x)
    except (TypeError,ValueError,OverflowError):
        raise ValueError("AXIS") from None
    require(len(vals)>0 and all(math.isfinite(v) for v in vals),"AXIS")
    return vals

def reconcile(g, domestic, imported, standard_output, standard_ci, va, compensation, other_tax, subsidy, surplus, *, aggregate_product_tax, atol):
    """Same vintage and branch axis; surplus includes mixed income, D39 positive."""
    require(type(atol) in (int,float) and math.isfinite(atol) and 0<=atol<=1,"TOLERANCE")
    v=[vector(x) for x in (g,domestic,imported,standard_output,standard_ci,va,compensation,other_tax,subsidy,surplus)]
    require(all(len(x)==len(v[0]) for x in v),"AXIS")
    g,u,m,p,ci,b,w,t,s,eb=v
    require(all(x>0 for x in g) and all(x>=0 for a in (u,m,ci,w,t,s) for x in a),"SIGN")
    def check(a,b,name):
        require(max(abs(x-y) for x,y in zip(a,b))<=atol,name)
    check(g,p,"OUTPUT")
    check(tuple(x-y for x,y in zip(p,ci)),b,"PRODUCTION_ACCOUNT")
    check(tuple(a+c-d+z for a,c,d,z in zip(w,t,s,eb)),b,"OPERATING_ACCOUNT")
    bridge=tuple(a-c-d for a,c,d in zip(ci,u,m))
    require(abs(math.fsum(bridge)-float(aggregate_product_tax))<=atol,"INTERMEDIATE_VALUATION_BRIDGE")
    net=tuple(a-b for a,b in zip(t,s))
    ratio=lambda a: tuple(x/y for x,y in zip(a,g))
    return {"value_added":b,"compensation":w,"other_net_production_tax":net,"surplus_mixed":eb,"intermediate_valuation_bridge":bridge,"gva_intensity":ratio(b),"compensation_intensity":ratio(w),"tax_intensity":ratio(net),"surplus_mixed_intensity":ratio(eb),"intermediate_bridge_intensity":ratio(bridge)}

def effects(dg,r):
    dg=vector(dg)
    require(len(dg)==len(r["gva_intensity"]),"SHOCK_AXIS")
    out={k:math.fsum(x*y for x,y in zip(dg,r[k+"_intensity"])) for k in ("gva","compensation","tax","surplus_mixed","intermediate_bridge")}
    require(abs(out["gva"]-out["compensation"]-out["tax"]-out["surplus_mixed"])<=1e-7*max(1,abs(out["gva"])),"SHOCK_INCOME_BALANCE")
    return {**out,"employment":None,"net_profit":None,"household_disposable_income":None,"status":"CONDITIONAL_FIXED_INTENSITY_NOT_FORECAST"}
