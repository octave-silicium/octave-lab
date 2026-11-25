"""G4 v0.7a analytical capital paths; no empirical asset parameters."""
from dataclasses import replace
from .economic_sector_structural import Structure
from .economic_sector_capital import Asset,Vintage,Investment,Period,path

def audit():
    s=Structure(("A","B"),((0,0),(0,0)),((0,0),(0,0)),((1,0),(0,1)),(.5,.5),(0,0),(0,0),(.5,.5),(100,80),"SYNTHETIC")
    p=Period(s,(None,None),(("A","B"),),(1,),"Synthetic")
    a=Asset("machine","A","B",2,10,0,0,10,"Synthetic")
    v=Vintage("machine",10,0,20);i=Investment("expansion","machine",1,5,2,"Synthetic")
    high=replace(p,structure=replace(s,final=(140,80)))
    cases={}
    specs=[
      ("reference",(p,)*5,a,(v,),(),(0,100),[100]*5,[180]*5,[0]*5),
      ("delayed_expansion",(p,p,high,high,high),a,(v,),(i,),(0,100),[100,100,150,150,150],[180,180,220,220,220],[10,0,0,0,0]),
      ("rationed_investment",(p,)*5,a,(v,),(i,),(0,45),[100,100,125,125,125],[90,101.25,101.25,101.25,101.25],[5,0,0,0,0]),
      ("efficiency_decay",(p,)*5,replace(a,efficiency_decay=.1,book_decay=.2),(v,),(),(0,100),[100,90,81,72.9,65.61],[180,162,145.8,131.22,118.098],[0]*5),
      ("retirement",(p,)*5,replace(a,life=2,book_decay=.1),(v,),(),(0,100),[100,100,0,0,0],[180,180,0,0,0],[0]*5),
      ("bootstrap_failure",(p,)*5,replace(a,product="A"),(),(i,),(0,100),[0]*5,[0]*5,[0]*5)]
    for name,ps,asset,vs,orders,nc,expected_cap,expected_other,expected_i in specs:
        receipt=path(ps,(asset,),vs,orders,noncapital_capacity=nc,period_unit="YEAR",evidence="Synthetic")
        result=receipt["result"];rows=result["periods"]
        for row,cap,other,inv in zip(rows,expected_cap,expected_other,expected_i):
            assert abs(row["capacity"][0]-cap)<1e-8,(name,"capacity")
            assert abs(sum(row["other_final_served"])-other)<1e-8,(name,"other",row["other_final_served"],other)
            assert abs(row["investment_acquired"]-inv)<1e-8,(name,"investment")
        if name=="efficiency_decay":
            assert all(abs(r["closing_active_value"]-20*.8**t)<1e-8 for t,r in enumerate(rows,1))
        if name=="retirement":assert abs(rows[1]["retirement_writeoff"]-16.2)<1e-8
        cases[name]={"sha256":receipt["sha256"],"capacity_A":[r["capacity"][0] for r in rows],"other_final_served":[sum(r["other_final_served"]) for r in rows],"investment_acquired":[r["investment_acquired"] for r in rows],"active_value":[r["closing_active_value"] for r in rows],"wip_value":[r["closing_wip_value"] for r in rows],"depreciation":[r["depreciation_proxy"] for r in rows],"writeoff":[r["retirement_writeoff"] for r in rows],"expected_capacity":expected_cap,"expected_other":expected_other,"expected_investment":expected_i}
    return {"status":"SYNTHETIC_CAPITAL_VINTAGE_AUDIT","publication":"BLOCK_PUBLICATION","cases":cases,"verification":"Six paths, independently hand-derived capacity, final-use and acquisition outcomes; historical-cost decay and retirement checked"}
if __name__=="__main__":
    import json
    print(json.dumps(audit(),indent=2))
