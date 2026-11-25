"""Pinned G4 v0.6e valuation and marginal institutional diagnostic."""
import hashlib,io,json,sys
from pathlib import Path
from decimal import Decimal as D
import openpyxl
from pipeline import acquire_tes_income as acq
from pipeline.audit_tee_2022 import HASHES
from pipeline.audit_tes_a38 import SHA,CODES
from pipeline.economic_institutional_bridge import transportation_bounds,proportional_shock

def require(x,msg):
    if not x:raise ValueError(msg)
def main(folder,sym):
    folder=Path(folder);raw={}
    for name in ("tee.xlsx","standard.xlsx"):
        raw[name]=(folder/name).read_bytes()
        require(hashlib.sha256(raw[name]).hexdigest()==HASHES[name],"HASH:"+name)
    sr=Path(sym).read_bytes();require(hashlib.sha256(sr).hexdigest()==SHA,"SYM_HASH")
    acq.OUT=folder
    acq.workbook(raw["tee.xlsx"]);tee=json.loads((folder/"exact_cells.json").read_text())["TEE_COMPLET"]
    acq.workbook(raw["standard.xlsx"]);std=json.loads((folder/"exact_cells.json").read_text())
    w=openpyxl.load_workbook(io.BytesIO(sr),data_only=True);d,m=w.worksheets[1:]
    blanks=[]
    def val(grid,cell,allow_blank=False):
        x=grid.get(cell)
        if x is None:
            require(allow_blank,"MISSING:"+cell);blanks.append(cell);return D(0)
        require(x["type"]=="n" and x["formula"] is None and x["value"] is not None,"NONNUMERIC:"+cell)
        return D(x["value"])
    def sx(sh,r,c):
        v=sh.cell(r,c).value
        require(type(v) in (int,float),"SYM_CELL")
        return D(str(v))
    f=std["TEF"];r=std["TRP"];u=std["TEI"];b=std["CPR_CEB"]
    require(f["C4"]["value"]=="Ménages" and d.cell(9,86).value==m.cell(9,51).value=="Ménages","HOUSEHOLD_SCOPE")
    rows=[];checks=[]
    for i,code in enumerate(CODES):
        a=i+5;j=i+11
        require(all(g["B"+str(a)]["value"]==code for g in (f,r,u)) and d.cell(j,85).value==m.cell(j,50).value==code,"PRODUCT_AXIS")
        basic_d=sx(d,j,86);basic_m=sx(m,j,51)
        purchaser=val(f,"C"+str(a),code=="MB");basic=basic_d+basic_m
        # All-use resource valuation vectors are not household-specific.
        mc,mt,tx,sub=[val(r,k+str(a),True) for k in "IJKM"]
        resources=val(r,"H"+str(a));purchase_resources=val(r,"N"+str(a))
        ci=val(u,"AN"+str(a),code in ("OZ","QB","TZ"));final=val(f,"S"+str(a))
        require(purchase_resources==resources+mc+mt+tx+sub,"RESOURCE_VALUATION:"+code)
        require(purchase_resources==ci+final,"RESOURCE_USE:"+code)
        checks.extend([{"code":code,"check":"resource_valuation","residual":"0"},{"code":code,"check":"resource_use","residual":"0"}])
        rows.append({"code":code,"basic_domestic":str(basic_d),"basic_imported":str(basic_m),"basic_total":str(basic),"purchaser_household":str(purchaser),"net_household_valuation_difference":str(purchaser-basic),"all_use_trade_margin":str(mc),"all_use_transport_margin":str(mt),"all_use_product_tax":str(tx),"all_use_product_subsidy":str(sub),"all_use_basic_resources":str(resources),"all_use_purchaser_resources":str(purchase_resources)})
    totals={k:sum(D(x[k]) for x in rows) for k in rows[0] if k!="code"}
    territorial=val(f,"C42");caf=val(f,"C43",True);observed=val(f,"C44")
    require(abs(totals["purchaser_household"]+territorial+caf-observed)<=D(".1"),"HOUSEHOLD_TOTAL")
    require(abs(totals["basic_total"]-D("1229477.109"))<=D(".000001"),"BASIC_TOTAL")
    require(totals["all_use_trade_margin"]==totals["all_use_transport_margin"]==0,"MARGINS_NET")
    # TEE D1 paid by institutional sector vs TES D1 paid by branch.
    # Exact published totals, no forced balancing of +0.600 M EUR discrepancy.
    from openpyxl.utils import get_column_letter as col
    branches={code:val(b,col(i+3)+"21") for i,code in enumerate(CODES)}
    sectors=["S11","S12","S13","S14","S15","S2"]
    def flows(row):
        require(tee["A"+str(row)]["value"] in ("D1","D4","D42","D5","D61","D62","D7"),"FLOW_CODE")
        left={s:val(tee,c+str(row),True)*1000 for s,c in zip(sectors,"DEFGHJ")}
        right={s:val(tee,c+str(row),True)*1000 for s,c in zip(sectors,"VUTSRP")}
        return left,right
    pay,receive=flows(19)
    resident={s:v for s,v in pay.items() if s!="S2"}
    require(sum(branches.values())==D("1378355.4") and sum(resident.values())==D("1378356"),"D1_SCOPE")
    mapping=transportation_bounds(branches,resident)
    require(D(mapping["original_row_minus_column"])==D("-.6"),"D1_RESIDUAL")
    shock=proportional_shock(mapping,"MA",D("-3000.573"))
    bilateral={name:transportation_bounds(*flows(i)) for name,i in [("D1",19),("D4",34),("D42",36),("D5",44),("D61",45),("D62",51),("D7",52)]}
    # D4 already contains D42: never sum both as separate economic flows.
    out={"status":"EMPIRICAL_VALUATION_AND_MARGINAL_BOUNDS_DIAGNOSTIC","publication":"BLOCK_PUBLICATION","unit":"million EUR current 2022","hashes":{"tee":HASHES["tee.xlsx"],"standard":HASHES["standard.xlsx"],"symmetric":SHA},"rows":rows,"checks":checks,"household":{"totals":{k:str(v) for k,v in totals.items()},"territorial_correction":str(territorial),"caf_fab_correction":str(caf),"purchaser_total":str(observed),"net_difference_after_corrections":str(observed-totals["basic_total"])},"branch_institution_D1_bounds":mapping,"MA_D1_proportional_shock_bounds":shock,"institutional_flow_bounds":bilateral,"blank_cells_zero_for_pinned_layout_only":blanks,"limitations":["net household difference by product is observed, not a tax/margin or origin-specific decomposition","all-use margins and taxes cannot be attributed to households from these tables","cell extrema are sharp separately, not jointly; no structural restrictions beyond nonnegativity; no identified bilateral matrix","unallocated residual is explicit, not an economic actor","D1 branch-to-payer mapping does not identify recipients; proportional shock assumed, not observed","D4 includes D42; no summation of overlapping flow categories; no behavioral calibration or new publication gate"]}
    return out
if __name__=="__main__":print(json.dumps(main(*sys.argv[1:]),ensure_ascii=False,indent=2))
