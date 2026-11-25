"""G4 v0.6a audit: conditional prices on pinned annual French accounts."""
import io,json,sys
from dataclasses import replace
import numpy as np
import openpyxl
from pipeline.audit_tes_income import audit,pinned,SYM_SHA,CODES
from pipeline.economic_sector_structural import Structure
from pipeline.economic_sector_prices import PricePolicy,DemandPolicy,price

def main(std,sym,eu):
    income=audit(std,sym,eu)
    wb=openpyxl.load_workbook(io.BytesIO(pinned(sym,SYM_SHA)),data_only=True);d,m=wb.worksheets[1:]
    def mat(sh,rs,cs):return np.array([[float(sh.cell(i,j).value) for j in cs] for i in rs])
    V=mat(d,range(11,48),range(4,41));U=mat(d,range(11,48),range(45,82));M=mat(m,range(11,48),range(10,47))
    q=V.sum(1);g=V.sum(0);y=mat(d,range(11,48),[95]).ravel()
    B=U/g;I=M/g;D=V.T/q
    bs=income["branches"]
    def v(k):return np.array([x[k] for x in bs])/g
    def tup(x):return tuple(float(a) for a in x)
    def matrix(x):return tuple(tup(r) for r in x)
    base=Structure(tuple(CODES),matrix(B),matrix(I),matrix(D),tup(v("compensation")),tup(v("other_net_production_taxes")),tup(v("valuation_bridge")),tup(v("gross_surplus_mixed")),tup(y),"PINNED_2022_CONDITIONAL")
    n=len(CODES);a=CODES.index("MA");j=CODES.index("JC");ci=CODES.index("CI")
    w=np.array(base.wage);w[a]-=.01
    k=np.array(base.surplus);k[a]+=.01
    retention=replace(base,wage=tup(w),surplus=tup(k))
    b=B.copy();im=I.copy();b[j,a]+=.004;im[j,a]+=.003;k[a]-=.007
    purchase=replace(retention,domestic=matrix(b),imported=matrix(im),surplus=tup(k))
    ones=(1.,)*n;zeros=(0.,)*n
    p=PricePolicy(ones,ones,ones,ones,ones,"Hypothetical pass-through and factor price relatives")
    mp=np.ones(n);mp[ci]=1.2
    eps=np.zeros(n);eps[a]=2
    share=np.zeros(n);share[a]=.5
    demand=DemandPolicy(tup(eps),tup(share),(1.1,)*n,"Hypothetical responsive half of MA domestic final demand, elasticity 2, cap 1.1; not estimated")
    cases={}
    for name,s,pol,dp in [
        ("identity",base,p,None),
        ("retained_gain",retention,replace(p,pass_through=zeros),None),
        ("full_pass_through",retention,p,None),
        ("half_pass_through",retention,replace(p,pass_through=(.5,)*n),None),
        ("ai_purchase_full",purchase,p,None),
        ("import_price_shock",base,replace(p,import_price=tup(mp)),None),
        ("ai_purchase_rebound",purchase,p,demand)]:
        receipt=price(base,s,pol,dp);r=receipt["result"]
        BB=np.array(s.domestic);MM=np.array(s.imported);DD=np.array(s.shares)
        rho=np.array(pol.pass_through)
        external=MM.T@np.array(pol.import_price)+np.array(s.wage)*pol.wage_price+np.array(s.other_tax)*pol.tax_price+np.array(s.bridge)*pol.bridge_price
        pb=np.linalg.solve(np.eye(n)-np.diag(rho)@BB.T@DD.T,1+rho*(external-(1-np.array(base.surplus))))
        pp=DD.T@pb
        assert np.max(abs(pb-r["branch_price"]))<1e-10 and np.max(abs(pp-r["product_price"]))<1e-10,"PRICE_REFERENCE"
        yy=np.array(s.final)
        if dp:yy=yy*((1-np.array(dp.responsive_share))+np.array(dp.responsive_share)*np.minimum(dp.max_multiple,pp**(-np.array(dp.elasticity))))
        qq=np.linalg.solve(np.eye(n)-BB@DD,yy);gg=DD@qq
        surplus=pb-(BB.T@pp+external)
        assert abs(pb@gg-r["nominal"]["gross_output"])<1e-5,"NOMINAL_REFERENCE"
        assert abs(surplus@gg-r["nominal"]["gross_surplus_mixed"])<1e-5,"SURPLUS_REFERENCE"
        assert np.max(abs(yy-r["final_volume_equivalent"]))<1e-5,"DEMAND_REFERENCE"
        cases[name]={"sha256":receipt["sha256"],"branch_price_MA":r["branch_price"][a],"product_price_MA":r["product_price"][a],"unit_surplus_MA":r["unit_gross_surplus"][a],"top_product_price_changes":sorted(zip(CODES,[x-1 for x in r["product_price"]]),key=lambda x:-abs(x[1]))[:6],"nominal":r["nominal"],"reference_price_volume":r["reference_price_volume"],"base_reference":r["base_reference"],"final_value_decomposition":r["final_value_decomposition"],"price_induced_MA":r["price_induced_final_change"][a],"tail_bound":r["price_tail_bound"]}
    return {"status":"EMPIRICAL_BASE_HYPOTHETICAL_PRICE_SCENARIOS","publication":"BLOCK_PUBLICATION","source_hashes":income["source_hashes"],"unit":"M EUR reference 2022 or conditional nominal EUR as explicitly labeled","assumptions":{"retention":"MA D1 intensity -0.01, gross surplus +0.01 at reference prices","purchase":"MA D1 intensity -0.01, domestic JC input +0.004, imported JC input +0.003","import":"CI intermediate import price +20%","rebound":"half of MA domestic final demand responsive, elasticity 2, saturation 1.1"},"cases":cases,"verification":"independent dense NumPy solve, nominal accounts and demand checks"}
if __name__=="__main__":print(json.dumps(main(*sys.argv[1:]),indent=2))
