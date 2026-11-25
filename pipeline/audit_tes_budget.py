"""G4 budget audit on pinned 2022 domestic/imported household uses."""
import io,json,sys
from dataclasses import replace
import numpy as np
import openpyxl
from pipeline.audit_tes_income import audit,pinned,SYM_SHA,CODES
from pipeline.economic_sector_structural import Structure
from pipeline.economic_sector_prices import PricePolicy
from pipeline.economic_sector_budget import HouseholdBasket,BudgetPolicy,budgeted

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
    assert d.cell(9,86).value==m.cell(9,51).value=="Ménages"
    assert "prix de base" in d["B59"].value and "prix de base" in m["B53"].value
    assert [d.cell(i,85).value for i in range(11,48)]==[m.cell(i,50).value for i in range(11,48)]==list(CODES)
    hd=mat(d,range(11,48),[86]).ravel();hi=mat(m,range(11,48),[51]).ravel()
    assert np.all(hd>=0) and np.all(hi>=0) and np.all(hd<=y) and np.all(hi<=mat(m,range(11,48),[60]).ravel())
    assert abs(hd.sum()-d.cell(48,86).value)<1e-6 and abs(hi.sum()-m.cell(48,51).value)<1e-6
    h=HouseholdBasket(tup(hd),tup(hi),"Pinned Insee 2022 symmetric TES, domestic CH11:CH47, imports AY11:AY47, household basic-price uses, not purchaser spending")
    n=len(CODES);a=CODES.index("MA");j=CODES.index("JC");ci=CODES.index("CI")
    w=np.array(base.wage);w[a]-=.01;k=np.array(base.surplus);k[a]+=.01
    s=replace(base,wage=tup(w),surplus=tup(k))
    b=B.copy();im=I.copy();b[j,a]+=.004;im[j,a]+=.003;k[a]-=.007
    purchase=replace(s,domestic=matrix(b),imported=matrix(im),surplus=tup(k))
    ones=(1.,)*n;p=PricePolicy(ones,ones,ones,ones,ones,"Hypothetical price transmission")
    budget=BudgetPolicy(float(hd.sum()+hi.sum()),0,1,(10.,)*n,(10.,)*n,ones,"Hypothetical fixed nominal use envelope, CES elasticity 1, no reserve")
    fp=np.ones(n);fp[ci]=1.2
    cases={}
    for name,st,pol,bp in [
        ("identity",base,p,budget),
        ("retained_gain",s,replace(p,pass_through=(0.,)*n),budget),
        ("fixed_proportions",s,p,replace(budget,elasticity=0)),
        ("constant_expenditure_shares",s,p,budget),
        ("substitution",s,p,replace(budget,elasticity=2)),
        ("tech_purchase_substitution",purchase,p,replace(budget,elasticity=2)),
        ("reserve_5pct",s,p,replace(budget,elasticity=2,reserve_share=.05)),
        ("saturated_basket",s,p,replace(budget,domestic_cap=ones,imported_cap=ones)),
        ("final_import_price_shock",base,p,replace(budget,elasticity=2,final_import_price=tup(fp)))]:
        receipt=budgeted(base,st,pol,h,bp);r=receipt["result"]
        # Independent price calculation and scalar monotone root for capped allocation.
        BB=np.array(st.domestic);MM=np.array(st.imported);DD=np.array(st.shares);rho=np.array(pol.pass_through)
        external=MM.T@np.array(pol.import_price)+np.array(st.wage)*pol.wage_price+np.array(st.other_tax)*pol.tax_price+np.array(st.bridge)*pol.bridge_price
        pb=np.linalg.solve(np.eye(n)-np.diag(rho)@BB.T@DD.T,1+rho*(external-(1-np.array(base.surplus))))
        pp=DD.T@pb;pr=np.r_[pp,bp.final_import_price];weights=np.r_[hd,hi]
        scores=weights*pr**(1-bp.elasticity);caps=weights*pr*np.r_[bp.domestic_cap,bp.imported_cap]
        target=min(bp.resources*(1-bp.reserve_share),float(caps.sum()))
        lo=0.;high=max(caps[scores>0]/scores[scores>0])
        for _ in range(100):
            mid=(lo+high)/2
            if np.minimum(caps,mid*scores).sum()<target:lo=mid
            else:high=mid
        ex=np.minimum(caps,high*scores);vol=ex/pr
        assert np.max(abs(vol-np.r_[r["domestic_household_volume"],r["imported_household_volume"]]))<1e-5,"INDEPENDENT_BUDGET"
        yy=y-hd+vol[:n];qq=np.linalg.solve(np.eye(n)-BB@DD,yy)
        assert abs(qq.sum()-r["sector"]["reference_price_volume"]["gross_output"])<1e-5,"INDEPENDENT_OUTPUT"
        assert abs(ex.sum()+r["budget"]["unspent"]-bp.resources)<1e-5,"INDEPENDENT_RESERVE"
        cases[name]={"sha256":receipt["sha256"],"budget":r["budget"],"fixed_basket_price_effect":r["fixed_basket_price_effect"],"household_volume_change":r["household_volume_change"],"domestic_household_volume_change":float(sum(r["domestic_household_volume_change"])),"imported_household_volume_change":float(sum(r["imported_household_volume_change"])),"top_domestic_changes":sorted(zip(CODES,r["domestic_household_volume_change"]),key=lambda z:-abs(z[1]))[:6],"nominal":r["sector"]["nominal"],"reference_price_volume":r["sector"]["reference_price_volume"],"extended_nominal_scope":r["extended_nominal_scope"]}
    return {"status":"EMPIRICAL_BASKET_HYPOTHETICAL_BUDGET_SCENARIOS","publication":"BLOCK_PUBLICATION","source_hashes":income["source_hashes"],"basket":{"domestic":float(hd.sum()),"direct_import":float(hi.sum()),"total":budget.resources,"domestic_cells":"CH11:CH47","import_cells":"AY11:AY47","valuation":"basic prices; margins reallocated to trade and transport products; net product taxes excluded"},"cases":cases,"verification":"independent dense price/output solve and scalar bisection of capped expenditures","limitations":["not household disposable income or observed saving","all policy parameters hypothetical; fixed aggregate basket, no new products, no purchaser price or full final imports"]}
if __name__=="__main__":print(json.dumps(main(*sys.argv[1:]),indent=2))
