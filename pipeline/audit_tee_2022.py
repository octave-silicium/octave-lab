"""Pinned 2022 institutional account audit; decimal rounding and explicit scopes."""
import hashlib,json,sys
from decimal import Decimal as D
from pathlib import Path
from pipeline import acquire_tes_income as acq

HASHES={"tee.xlsx":"9dbee70eb54090d62efdc930f30583761e1f4e81d14fed4cc9a53e93b4eae0b9","standard.xlsx":"1a9d587e3a70590a42210f10bca15a63dd85d18dc9946ca654d77e50970a29ed","sector_eurostat.json":"1ba61468e382c07becabfefb441ada9801180268768bae8de4c0718322b65a49"}
SECTORS={"S1":("C","W"),"S11":("D","V"),"S12":("E","U"),"S13":("F","T"),"S14":("G","S"),"S15":("H","R")}
# A blank in the selected flow grid may denote no recorded flow, never silently
# substitute for a missing balancing item or an unobserved Eurostat value.
def require(ok,msg):
    if not ok:raise ValueError(msg)
def main(folder):
    folder=Path(folder);raw={}
    for name,sha in HASHES.items():
        raw[name]=(folder/name).read_bytes()
        require(hashlib.sha256(raw[name]).hexdigest()==sha,"HASH:"+name)
    # Re-extract from raw pinned workbooks, not unchecked sidecar.
    acq.OUT=folder
    acq.workbook(raw["tee.xlsx"]);tee=json.loads((folder/"exact_cells.json").read_text())["TEE_COMPLET"]
    acq.workbook(raw["standard.xlsx"]);std=json.loads((folder/"exact_cells.json").read_text())
    def val(grid,cell,allow_blank=False):
        x=grid.get(cell)
        if x is None:
            require(allow_blank,"MISSING:"+cell)
            return D(0)
        require(x["type"]=="n" and x["formula"] is None and x["value"] is not None,"NONNUMERIC:"+cell)
        return D(x["value"])
    def label(c):return tee[c]["value"]
    require(label("B2")=="Année 2022" and label("Y1")=="En milliards d'Euros","VINTAGE_UNIT")
    for s,(l,r) in SECTORS.items():require(label(l+"2")==label(r+"2")==s,"SECTOR_AXIS")
    for row,code in {7:"P1",11:"P2",14:"B1g/PIB",15:"P51c",19:"D1",29:"B2g",30:"B3g",34:"D4",41:"B5g/RNB",60:"B6g",63:"P3",75:"D8",77:"B8g",98:"B9NF"}.items():require(label("A"+str(row))==code,"ROW_CODE")
    checks=[];blanks=[];accounts={}
    def chk(name,reported,terms,step=D(".001")):
        calc=sum(terms,D(0));error=reported-calc;bound=step*(len(terms)+1)/2
        require(abs(error)<=bound,name+":"+str(error))
        checks.append({"name":name,"reported":str(reported),"calculated":str(calc),"residual":str(error),"rounding_bound":str(bound)})
    for s,(l,r) in SECTORS.items():
        def read(col,row,flow=False):
            cell=col+str(row)
            if flow and cell not in tee:blanks.append({"sector":s,"cell":cell,"interpretation":"unrecorded flow in selected TEE layout; zero for identity only"})
            return val(tee,cell,flow)
        L=lambda row,flow=False:read(l,row,flow)
        R=lambda row,flow=False:read(r,row,flow)
        p1=R(7);p2=L(11);taxprod=R(12) if s=="S1" else D(0);va=L(14)-taxprod
        chk(s+":production",L(14),[p1,-p2,taxprod])
        chk(s+":generation_income",L(14),[L(19),L(22,True),L(25,True),L(29),L(30,True)])
        chk(s+":primary_income",L(41),[L(29),L(30,True),R(19,True),R(22,True),R(25,True),R(34,True),-L(34,True)])
        chk(s+":disposable_income",L(60),[L(41)]+[R(i,True)-L(i,True) for i in (44,45,51,52)],step=D(".002"))
        chk(s+":gross_saving",L(77),[L(60),-L(63,True),R(75,True),-L(75,True)])
        chk(s+":net_saving",L(78),[L(77),-L(15)])
        chk(s+":net_lending",L(98),[L(77),R(89,True),R(90,True),-L(92),-L(94,True),-L(95,True),-L(96,True)])
        chk(s+":financial_flow",R(101),[L(102),-R(102)])
        chk(s+":net_worth",R(187),[L(155),L(178),-R(178)])
        accounts[s]={k:str(v) for k,v in {"output":p1,"intermediate":p2,"gva":va,"gdp_if_S1":L(14) if s=="S1" else D(0),"compensation_paid":L(19),"compensation_received":R(19,True),"gross_operating_surplus":L(29),"gross_mixed_income":L(30,True),"fixed_capital_consumption":L(15),"property_income_received":R(34,True),"property_income_paid":L(34,True),"primary_income":L(41),"direct_tax_paid":L(44,True),"social_contributions_paid":L(45,True),"cash_benefits_received":R(51,True),"disposable_income":L(60),"consumption":L(63,True),"pension_adjustment_net":R(75,True)-L(75,True),"gross_saving":L(77),"net_saving":L(78),"gross_fixed_investment":L(92),"net_lending":L(98),"financial_net_lending":R(101),"statistical_adjustment":L(99),"net_worth":R(187)}.items()}
    chk("national_net_lending_vs_rest_of_world",val(tee,"C98"),[-val(tee,"J98")])
    chk("national_wage_cross_border",val(tee,"W19"),[val(tee,"C19"),val(tee,"J19"),-val(tee,"P19")])
    for k in ("gva","compensation_paid","gross_operating_surplus","gross_mixed_income","fixed_capital_consumption","disposable_income","consumption","gross_saving","net_lending"):
        # GVA S1 is derived from independently rounded GDP and taxes.
        chk("resident_aggregation:"+k,D(accounts["S1"][k]),[D(accounts[s][k]) for s in list(SECTORS)[1:]],step=D(".002"))
    # TES standard: branch account totals and household final consumption.
    a=std["CPR_CEB"];f=std["TEF"]
    require(f["C4"]["value"]=="Ménages" and f["A44"]["value"]=="TOTAL","TEF_LAYOUT")
    bridge=[]
    def match(k,tee_value,tes_cell,grid):
        t=val(grid,tes_cell);err=D(tee_value)*1000-t
        require(abs(err)<=D(".55"),"TES_BRIDGE:"+k)
        bridge.append({"item":k,"TEE_MEUR":str(D(tee_value)*1000),"TES_MEUR":str(t),"TES_cell":tes_cell,"residual_MEUR":str(err)})
    n=accounts["S1"]
    for k,cell in [("output","AN6"),("intermediate","AN4"),("gva","AN5"),("compensation_paid","AN21")]:match(k,n[k],cell,a)
    match("household_consumption",accounts["S14"]["consumption"],"C44",f)
    e=json.loads(raw["sector_eurostat.json"]);require(e["id"]==["freq","unit","direct","na_item","sector","geo","time"] and e["size"]==[1,1,2,132,14,1,1],"EUROSTAT_AXES")
    idx={k:x["category"]["index"] for k,x in e["dimension"].items()}
    require(idx["freq"]=={"A":0} and idx["unit"]=={"CP_MEUR":0} and idx["geo"]=={"FR":0} and idx["time"]=={"2022":0},"EUROSTAT_SCOPE")
    comparisons=[];missing=[]
    for s in SECTORS:
        for k,item,direction in [("disposable_income","B6G","RECV"),("gross_saving","B8G","RECV"),("net_lending","B9","RECV"),("compensation_paid","D1","PAID"),("consumption","P3","PAID"),("fixed_capital_consumption","P51C","PAID"),("primary_income","B5GQ" if s=="S1" else "B5G","RECV")]:
            loc=str((idx["direct"][direction]*132+idx["na_item"][item])*14+idx["sector"][s])
            if loc not in e["value"]:
                missing.append({"sector":s,"item":item,"direction":direction});continue
            x=D(str(e["value"][loc]));t=D(accounts[s][k])*1000;diff=t-x
            require(abs(diff)<=1,"EUROSTAT_COMPARE:"+s+":"+item)
            comparisons.append({"sector":s,"item":item,"direction":direction,"TEE_MEUR":str(t),"Eurostat_MEUR":str(x),"difference_MEUR":str(diff),"flag":e.get("status",{}).get(loc)})
    household=accounts["S14"];cons=val(f,"C44");territory=val(f,"C42")
    basic=D("1229477.109") # audited v0.6b pinned symmetric household basket
    out={"status":"EMPIRICAL_INSTITUTIONAL_DIAGNOSTIC_NOT_ENGINE_ADMISSION","publication":"BLOCK_PUBLICATION","source_hashes":HASHES,"units":"TEE billion EUR; TES and Eurostat million EUR","accounts":accounts,"checks":checks,"blank_flow_assumptions":blanks,"TES_bridge":bridge,"Eurostat_comparisons":comparisons,"Eurostat_missing":missing,"Eurostat_updated":e.get("updated"),"household_valuation":{"basic_price_basket_MEUR":str(basic),"purchaser_price_consumption_MEUR":str(cons),"aggregate_difference_MEUR":str(cons-basic),"territorial_correction_MEUR":str(territory),"difference_before_territorial_correction_MEUR":str(cons-territory-basic),"warning":"aggregate bridge only; no tax/margin allocation by product and origin"},"household_gross_saving_rate":str(D(household["gross_saving"])/(D(household["disposable_income"])+D(household["pension_adjustment_net"]))),"national_financial_vs_nonfinancial_gap_MdEUR":str(D(n["financial_net_lending"])-D(n["net_lending"])),"limitations":["blank flow interpretation conditional on pinned layout; not imputation of missing Eurostat data","rounded publication, preserve residuals; same underlying national accounts not independent measurement","no branch-to-institution allocation, bilateral flow matrix, price bridge by product or behavioral calibration"]}
    return out
if __name__=="__main__":print(json.dumps(main(sys.argv[1]),ensure_ascii=False,indent=2))
