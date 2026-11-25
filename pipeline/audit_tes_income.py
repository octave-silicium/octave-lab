"""Pinned 2022 Insee standard/symmetric TES and Eurostat income reconciliation."""
import hashlib, io, json
from pathlib import Path
import numpy as np
import openpyxl
from openpyxl.utils import get_column_letter
from pipeline.economic_income_bridge import reconcile, effects
from pipeline.audit_tes_a38 import SHA as SYM_SHA, CODES
from pipeline.acquire_tes_income import workbook, OUT

STD_SHA="1a9d587e3a70590a42210f10bca15a63dd85d18dc9946ca654d77e50970a29ed"
EU_SHA="5c822d35fed4fa677d215a958be4730679168700a71d523d8479fb0c24608772"
EU_CODES="A B C10-C12 C13-C15 C16-C18 C19 C20 C21 C22_C23 C24_C25 C26 C27 C28 C29_C30 C31-C33 D E F G H I J58-J60 J61 J62_J63 K L M69-M71 M72 M73-M75 N O P Q86 Q87_Q88 R S T".split()
def require(ok,why):
    if not ok: raise ValueError(why)
def pinned(p,sha):
    b=Path(p).read_bytes(); require(hashlib.sha256(b).hexdigest()==sha,"SOURCE_HASH:"+str(p));return b
def audit(std,sym,eu):
    raw=pinned(std,STD_SHA); workbook(raw)
    cells=json.loads((OUT/"exact_cells.json").read_text())["CPR_CEB"]
    s=openpyxl.load_workbook(io.BytesIO(pinned(sym,SYM_SHA)),data_only=True); d,m=s.worksheets[1:]
    e=json.loads(pinned(eu,EU_SHA))
    require(e["id"]==["freq","unit","nace_r2","na_item","geo","time"] and e["size"]==[1,1,96,8,1,1],"EU_AXES")
    for k,c in [("freq","A"),("unit","CP_MEUR"),("geo","FR"),("time","2022")]:
        require(e["dimension"][k]["category"]["index"]=={c:0},"EU_FILTER")
    require([cells[get_column_letter(j)+"3"]["value"] for j in range(3,40)]==CODES,"STD_CODES")
    require([d.cell(i,3).value for i in range(11,48)]==CODES and [d.cell(9,j).value for j in range(4,41)]==CODES and [d.cell(9,j).value for j in range(45,82)]==CODES and [m.cell(9,j).value for j in range(10,47)]==CODES,"SYM_CODES")
    for r,label in [(4,"P2"),(5,"B1g"),(6,"P1"),(20,"B1g"),(21,"D1"),(22,"B2g & B3g"),(23,"D29"),(24,"D39")]:
        require(cells["A"+str(r)]["value"].strip()==label,"STD_ROW")
    def number(ref):
        c=cells[ref];require(c["type"]=="n" and c["formula"] is None,"STD_CELL"); return float(c["value"])
    # Only missing AM4 is a structural zero reconstructed from two observed cells,
    # additionally checked against the published total and Eurostat P2(T).
    require("AM4" not in cells and number("AM6")==number("AM5"),"STRUCTURAL_ZERO")
    def vec(r):
        return np.array([number(get_column_letter(j)+str(r)) if not (j==39 and r==4) else number("AM6")-number("AM5") for j in range(3,40)])
    v={r:vec(r) for r in (4,5,6,20,21,22,23,24)}
    for r,a in v.items():require(abs(a.sum()-number("AN"+str(r)))<1e-7,"STD_TOTAL")
    require(np.array_equal(v[5],v[20]),"REPEAT_VA")
    require(np.all(v[24]<=0),"SUBSIDY_SIGN")
    def mat(s,rs,cs):
        a=np.array([[float(s.cell(i,j).value) for j in cs] for i in rs]);require(np.all(np.isfinite(a)) and np.all(a>=0),"SYM_CELL");return a
    V=mat(d,range(11,48),range(4,41)); U=mat(d,range(11,48),range(45,82)); M=mat(m,range(11,48),range(10,47));g=V.sum(0);q=V.sum(1);y=mat(d,range(11,48),[95]).ravel()
    require(np.all(g>0) and np.all(q>0),"ZERO_OUTPUT")
    r=reconcile(g,U.sum(0),M.sum(0),v[6],v[4],v[5],v[21],v[23],-v[24],v[22],aggregate_product_tax=float(d["CD51"].value),atol=1e-7)
    ni=e["dimension"]["na_item"]["category"]["index"]; ix=e["dimension"]["nace_r2"]["category"]["index"]
    def obs(c,k):
        i=str(ix[c]*8+ni[k]);require(i in e["value"],"EU_MISSING");return float(e["value"][i]),e.get("status",{}).get(i)
    ev={k:np.array([obs(c,k)[0] for c in EU_CODES]) for k in ni}
    flags={c:{k:obs(c,k)[1] for k in ni if obs(c,k)[1]} for c in EU_CODES}
    flags={c:v for c,v in flags.items() if v}
    checks={}
    for k,a,b in [("P1",ev["P1"],v[6]),("P2",ev["P2"],v[4]),("B1G",ev["B1G"],v[5]),("D1",ev["D1"],v[21]),("D29X39",ev["D29X39"],v[23]+v[24]),("B2A3G",ev["B2A3N"]+ev["P51C"],v[22])]:
        diff=float(np.max(abs(a-b)));require(diff<1e-7,"EU_RECONCILIATION:"+k);checks[k]=diff
    require(np.all(ev["D11"]<=ev["D1"]) and np.all(ev["P51C"]>=0),"EU_COMPONENTS")
    D=V.T/q;A=(U/g)@D
    require(np.max(A.sum(0))<1,"PRODUCTIVITY")
    require(np.max(abs(np.linalg.solve(np.eye(37)-A,y)-q))<1e-7,"BASELINE")
    cases={}
    for c in ("JC","MA","NZ"):
        dy=np.zeros(37);dy[CODES.index(c)]=100;dq=np.linalg.solve(np.eye(37)-A,dy);dg=D@dq
        out=effects(dg,r); im=float(((M/g)@dg).sum())
        require(abs(100-out["gva"]-out["intermediate_bridge"]-im)<1e-7,"FINAL_DEMAND_BALANCE")
        out.update({"gross_output_requirement":float(dq.sum()),"imported_intermediate_requirement":im,"wages_gross":float((ev["D11"]/g)@dg),"employer_social_contributions":float(((ev["D1"]-ev["D11"])/g)@dg),"consumption_fixed_capital":float((ev["P51C"]/g)@dg),"net_operating_surplus_mixed":float((ev["B2A3N"]/g)@dg)})
        require(abs(out["surplus_mixed"]-out["consumption_fixed_capital"]-out["net_operating_surplus_mixed"])<1e-7,"SURPLUS_BRIDGE")
        cases[c]=out
    branches=[{"a38":c,"eurostat":ec,"output":float(g[i]),"intermediate_purchasers":float(v[4][i]),"value_added":float(v[5][i]),"compensation":float(v[21][i]),"other_net_production_taxes":float(v[23][i]+v[24][i]),"gross_surplus_mixed":float(v[22][i]),"valuation_bridge":float(r["intermediate_valuation_bridge"][i]),"wages_gross":float(ev["D11"][i]),"consumption_fixed_capital":float(ev["P51C"][i]),"net_surplus_mixed":float(ev["B2A3N"][i])} for i,(c,ec) in enumerate(zip(CODES,EU_CODES))]
    return {"status":"EMPIRICAL_INCOME_DIAGNOSTIC","publication":"BLOCK_PUBLICATION","source_hashes":{"standard":STD_SHA,"symmetric":SYM_SHA,"eurostat":EU_SHA},"eurostat_updated":e.get("updated"),"flags":flags,"missing_cell_policy":{"CPR_CEB!AM4":"P1-B1G=0, verified against Eurostat T/P2 and total"},"numeric_tolerance_MEUR":1e-7,"eurostat_max_abs_diff_MEUR":checks,"comparison_count":37*6,"source_dependence":"Eurostat harmonization cross-check, not independent measurement","totals":{str(k):float(a.sum()) for k,a in v.items()},"branches":branches,"cases":cases,"valuation_bridge_note":"Purchaser-price intermediate consumption minus domestic+imported basic-price uses, signed; aggregate matches intermediate product taxes, not a branch tax measure","limitations":["fixed coefficients and market shares","net operating surplus includes mixed income","not GDP, employment, disposable income or profit forecast"]}
if __name__=="__main__":
    import sys
    print(json.dumps(audit(*sys.argv[1:]),indent=2,ensure_ascii=False))
