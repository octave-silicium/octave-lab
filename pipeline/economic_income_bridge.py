"""G4 income bridge: no observed admission without qualified same-vintage accounts."""
import numpy as np

def require(ok, reason):
    if not ok: raise ValueError(reason)

def reconcile(g, domestic, imported, standard_output, standard_ci, va, compensation, other_tax, subsidy, surplus, *, aggregate_product_tax, atol):
    """Inputs in same currency, vintage, branch axis; surplus includes mixed income.
    other_tax and subsidy are D29 and D39 gross positive amounts.
    atol must be justified externally from source precision; no balancing adjustment.
    """
    require(type(atol) in (int,float) and np.isfinite(atol) and 0<=atol<=1,"TOLERANCE")
    v=[np.asarray(x,dtype=float) for x in (g,domestic,imported,standard_output,standard_ci,va,compensation,other_tax,subsidy,surplus)]
    require(all(x.ndim==1 and x.shape==v[0].shape and np.all(np.isfinite(x)) for x in v),"AXIS")
    g,u,m,p,ci,b,w,t,s,eb=v
    require(np.all(g>0) and all(np.all(x>=0) for x in (u,m,ci,w,t,s)),"SIGN")
    def check(a,b,name):
        require(np.max(np.abs(a-b))<=atol,name)
    check(g,p,"OUTPUT")
    check(p-ci,b,"PRODUCTION_ACCOUNT")
    check(w+t-s+eb,b,"OPERATING_ACCOUNT")
    bridge=ci-u-m
    check(float(bridge.sum()),float(aggregate_product_tax),"INTERMEDIATE_VALUATION_BRIDGE")
    return {"value_added":b,"compensation":w,"other_net_production_tax":t-s,"surplus_mixed":eb,"intermediate_valuation_bridge":bridge,"gva_intensity":b/g,"compensation_intensity":w/g,"tax_intensity":(t-s)/g,"surplus_mixed_intensity":eb/g,"intermediate_bridge_intensity":bridge/g}

def effects(dg,r):
    dg=np.asarray(dg,dtype=float)
    require(dg.shape==r["gva_intensity"].shape and np.all(np.isfinite(dg)),"SHOCK_AXIS")
    out={k:float(np.dot(dg,r[k+"_intensity"])) for k in ("gva","compensation","tax","surplus_mixed","intermediate_bridge")}
    require(abs(out["gva"]-out["compensation"]-out["tax"]-out["surplus_mixed"])<=1e-7*max(1,abs(out["gva"])),"SHOCK_INCOME_BALANCE")
    return {**out,"employment":None,"net_profit":None,"household_disposable_income":None,"status":"CONDITIONAL_FIXED_INTENSITY_NOT_FORECAST"}
