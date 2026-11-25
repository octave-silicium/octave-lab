"""Synthetic analytical and pinned-2022 conditional income feedback audits."""
import io,json,sys
from dataclasses import replace
import numpy as np
import openpyxl
from pipeline.audit_tes_income import audit,pinned,SYM_SHA,CODES
from pipeline.economic_sector_structural import Structure
from pipeline.economic_sector_prices import PricePolicy,price
from pipeline.economic_sector_budget import HouseholdBasket,BudgetPolicy
from pipeline.economic_sector_income_feedback import IncomeRule,Period,distribute,feedback

def main(std,sym,eu):
    income=audit(std,sym,eu)
    wb=openpyxl.load_workbook(io.BytesIO(pinned(sym,SYM_SHA)),data_only=True);d,m=wb.worksheets[1:]
    def mat(sh,rs,cs):return np.array([[float(sh.cell(i,j).value) for j in cs] for i in rs])
    V=mat(d,range(11,48),range(4,41));U=mat(d,range(11,48),range(45,82));M=mat(m,range(11,48),range(10,47))
    q=V.sum(1);g=V.sum(0);y=mat(d,range(11,48),[95]).ravel()
    B=U/g;I=M/g;D=V.T/q;bs=income["branches"]
    def v(k):return np.array([x[k] for x in bs])/g
    def tup(x):return tuple(float(a) for a in x)
    def matrix(x):return tuple(tup(r) for r in x)
    base=Structure(tuple(CODES),matrix(B),matrix(I),matrix(D),tup(v("compensation")),tup(v("other_net_production_taxes")),tup(v("valuation_bridge")),tup(v("gross_surplus_mixed")),tup(y),"PINNED_2022_CONDITIONAL")
    assert d.cell(9,86).value==m.cell(9,51).value=="Ménages"
    hd=mat(d,range(11,48),[86]).ravel();hi=mat(m,range(11,48),[51]).ravel()
    h=HouseholdBasket(tup(hd),tup(hi),"Pinned 2022 household basic-price uses")
    R=float(hd.sum()+hi.sum());n=len(CODES);ones=(1.,)*n;zeros=(0.,)*n;a=CODES.index("MA")
    p=PricePolicy(ones,ones,ones,ones,ones,"Hypothetical full transmission")
    retain=replace(p,pass_through=zeros)
    bp=BudgetPolicy(R,0,1,(10.,)*n,(10.,)*n,ones,"Hypothetical fixed expenditure shares; no reserve")
    rule=IncomeRule(.25,0,.5,.6,0,.1,100000.,1,"Illustrative income shares and transfer; not estimated")
    baseline=price(base,base,p)["result"]["nominal"]
    rule=replace(rule,envelope_share=R/distribute(baseline,rule)["household_resources_proxy"])
    assert rule.envelope_share<=1
    # Independent benchmark: solve nominal flows directly, then replay lagged budget and allocation.
    w=np.array(base.wage);w[a]-=.01;k=np.array(base.surplus);k[a]+=.01
    shock=replace(base,wage=tup(w),surplus=tup(k))
    more=replace(rule,domestic_distribution_share=.8)
    transfer=replace(rule,public_transfer=rule.public_transfer+3000.573)
    specs=[("reference",base,p,rule),("retention",shock,retain,rule),("transmission",shock,p,rule),
      ("retention_more_distribution",shock,retain,more),("transmission_transfer",shock,p,transfer)]
    cases={}
    for name,st,ppol,ir in specs:
        periods=(Period(st,ppol,bp,ir,"Hypothetical annual repeated conditions"),)*6
        receipt=feedback(base,h,periods,R,period_unit="YEAR",evidence="Conditional repeated 2022 structure; not a forecast")
        r=receipt["result"];BB=np.array(st.domestic);MM=np.array(st.imported);DD=np.array(st.shares);rho=np.array(ppol.pass_through)
        external=MM.T@np.array(ppol.import_price)+np.array(st.wage)*ppol.wage_price+np.array(st.other_tax)*ppol.tax_price+np.array(st.bridge)*ppol.bridge_price
        pb=np.linalg.solve(np.eye(n)-np.diag(rho)@BB.T@DD.T,1+rho*(external-(1-np.array(base.surplus))))
        pp=DD.T@pb;sur=pb-BB.T@pp-external;res=R;summary=[]
        for row in r["periods"]:
            spend=hd*res/R;imports=hi*res/R;hh=spend/pp
            assert np.all(hh<=10*hd+1e-9) and np.all(imports<=10*hi+1e-9),"CAPS_INACTIVE"
            qq=np.linalg.solve(np.eye(n)-BB@DD,y-hd+hh);gg=DD@qq
            W=np.dot(st.wage,gg);K=np.dot(sur,gg);T=np.dot(st.other_tax,gg)
            reserve=max(0,K)*ir.capital_consumption_share;capital=max(0,K-reserve)*ir.domestic_distribution_share
            resident=W*(1-ir.social_share)*(1-ir.foreign_wage_share)
            H=(resident+capital)*(1-ir.direct_tax_rate)+ir.public_transfer
            next_res=H*ir.envelope_share
            assert abs(row["input_envelope"]-res)<1e-5 and abs(row["income"]["next_basic_price_envelope"]-next_res)<1e-5,"INDEPENDENT_FEEDBACK"
            assert abs(row["nominal"]["gross_surplus_mixed"]-K)<1e-5,"INDEPENDENT_SURPLUS"
            assert abs(row["nominal"]["compensation"]-W)<1e-5,"INDEPENDENT_COMPENSATION"
            assert abs(row["income"]["public_allocation_pool"]-(W*ir.social_share+T+(resident+capital)*ir.direct_tax_rate))<1e-5,"INDEPENDENT_PUBLIC"
            summary.append({"period":row["period"],"input_envelope":row["input_envelope"],"next_envelope":row["income"]["next_basic_price_envelope"],"household_volume_change":row["household_volume_change"],"compensation":W,"gross_surplus_mixed":K,"household_capital_mixed_allocation":capital,"public_allocation_residual":row["income"]["public_allocation_residual"],"gross_output_volume":row["reference_price_volume"]["gross_output"]})
            res=next_res
        cases[name]={"sha256":receipt["sha256"],"periods":summary,"income_rule":r["periods"][0]["income_rule"]}
    return {"status":"EMPIRICAL_STRUCTURE_HYPOTHETICAL_INCOME_FEEDBACK","publication":"BLOCK_PUBLICATION","source_hashes":income["source_hashes"],"reference_envelope":R,"reference_income_rule":cases["reference"]["income_rule"],"cases":cases,"verification":"Independent dense NumPy solve, fixed expenditure shares with inactive caps, independently replayed annual income and consumption recursion","limits":["Only production accounts and basket observed; distribution rules illustrative, scalar envelope_share anchored to reference basket only","not actual institutional accounts, measured disposable income, savings, fiscal balance, employment or prediction"]}
if __name__=="__main__":print(json.dumps(main(*sys.argv[1:]),indent=2))
