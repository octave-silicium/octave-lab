"""Conditional 2022 structural scenarios. All shock magnitudes are hypothetical."""
import json,sys,io
from dataclasses import replace
from pathlib import Path
import numpy as np
import openpyxl
from pipeline.audit_tes_income import audit,pinned,SYM_SHA,CODES
from pipeline.economic_sector_structural import Structure,compare,state

def main(std,sym,eu):
    income=audit(std,sym,eu)
    s=openpyxl.load_workbook(io.BytesIO(pinned(sym,SYM_SHA)),data_only=True); d,m=s.worksheets[1:]
    def mat(sh,rs,cs):return np.array([[float(sh.cell(i,j).value) for j in cs] for i in rs])
    V=mat(d,range(11,48),range(4,41));U=mat(d,range(11,48),range(45,82));M=mat(m,range(11,48),range(10,47))
    q=V.sum(1);g=V.sum(0);y=mat(d,range(11,48),[95]).ravel()
    B=U/g;I=M/g;D=V.T/q
    bs=income["branches"]
    def v(k):return np.array([x[k] for x in bs])/g
    def tup(x):return tuple(float(a) for a in x)
    def matrix(x):return tuple(tup(r) for r in x)
    base=Structure(tuple(CODES),matrix(B),matrix(I),matrix(D),tup(v("compensation")),tup(v("other_net_production_taxes")),tup(v("valuation_bridge")),tup(v("gross_surplus_mixed")),tup(y),"PINNED_2022_CONDITIONAL")
    ref=state(base)
    assert np.max(abs(np.array(ref["q"])-q))<1e-5 and np.max(abs(np.array(ref["g"])-g))<1e-5,"BASELINE_REPLAY"
    j=CODES.index("JC"); a=CODES.index("MA"); n=CODES.index("NZ")
    # 1 percentage point of output, NOT 1% of employees or wage bill.
    w=np.array(base.wage);w[a]-=.01
    k=np.array(base.surplus);k[a]+=.01
    retention=replace(base,wage=tup(w),surplus=tup(k))
    b=B.copy();im=I.copy();b[j,a]+=.004;im[j,a]+=.003;k[a]-=.007
    purchase=replace(retention,domestic=matrix(b),imported=matrix(im),surplus=tup(k))
    # 10% of an existing input flow, not 10 percentage points of output.
    sub=B.copy();shift=.1*B[n,a];sub[n,a]-=shift;sub[j,a]+=shift
    suppliers=replace(base,domestic=matrix(sub))
    yy=y.copy();yy[a]+=100
    rebound=replace(purchase,final=tup(yy))
    # Explicit demand investment only; no automatic financing or future productive capacity.
    inv=y.copy();inv[j]+=100
    investment=replace(retention,final=tup(inv))
    cases={}
    for name,t in [("pure_distribution",retention),("labor_to_ai_services",purchase),("supplier_switch",suppliers),("combined_demand",rebound),("hypothetical_investment_demand",investment)]:
        r=compare(base,t);A=np.array(t.domestic)@np.array(t.shares)
        alt=np.linalg.solve(np.eye(37)-A,np.array(t.final))
        assert np.max(abs(alt-(q+np.array(r["changes"]["q"]))))<1e-5,"INDEPENDENT_SOLVE"
        dy=sum(t.final)-sum(base.final)
        assert abs(dy-r["totals"]["va"]-r["totals"]["imports"]-r["totals"]["bridge"])<1e-5,"DELTA_BALANCE"
        cases[name]={"totals":r["totals"],"demand_shapley_total":sum(r["demand_shapley"]),"structure_shapley_total":sum(r["structure_shapley"]),"orders":[sum(x) for x in r["propagation_orders_0_1_2"]]+[sum(r["propagation_order_3_plus"])],"wage_intensity_effect":sum(r["income_intensity_effects"]["wage"]),"wage_output_effect":sum(r["income_output_effects"]["wage"]),"top_output_changes":sorted(zip(CODES,r["changes"]["q"]),key=lambda x:-abs(x[1]))[:6],"tail_bounds":r["tail_bounds"],"employment":None,"gdp":None,"price_effect":None,"realized_output":None}
    return {"status":"EMPIRICAL_BASE_HYPOTHETICAL_STRUCTURAL_SCENARIOS","publication":"BLOCK_PUBLICATION","source_hashes":income["source_hashes"],"unit":"M EUR at 2022 reference prices","assumptions":{"pure_distribution":"MA D1 intensity -0.01; gross surplus/mixed +0.01","labor_to_ai_services":"MA D1 intensity -0.01; JC domestic input +0.004; JC imported input +0.003; MA gross surplus/mixed +0.003","supplier_switch":"10% of existing MA purchases of domestic NZ services redirected to domestic JC, at same reference-price value","combined_demand":"labor_to_ai_services plus hypothetical +100 M EUR MA domestic final demand","hypothetical_investment_demand":"pure_distribution plus exogenous +100 M EUR domestic JC final demand, assumed investment; no financing link"},"cases":cases,"limitations":["no causal shock calibration","fixed reference prices, market shares unchanged in pilots","no supply equilibrium, capacity or employment conversion","surplus closure is assumption not profit forecast","AI purchases proxied by broad JC category, no observed AI-specific share"]}
if __name__=="__main__":print(json.dumps(main(*sys.argv[1:]),indent=2))
