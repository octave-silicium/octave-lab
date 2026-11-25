"""Pinned 2022 financial stock-flow reconciliation. Missing values stay missing."""
import hashlib,json,sys
from decimal import Decimal as D
from pathlib import Path
from pipeline import acquire_tes_income as acq
HASHES={"bs":"8d2b5c7cba5cdd3e4c26f23e2db345c5177150d82c0165fbeb8216310f9d01b8","tr":"2dcfdb2727416bf91491c7869209fdd681f57bf2253bc220535f0064b370da43","gl":"4eca428e4e73ecef0688e30b10c3cb5b6089bbe8317e2a276c4bb74f12f7b3e0","oc":"d19d570f51976b6ccfbb5369a9e1116f7007c65c22aafda83b795f5d4f294ae0"}
TEE_SHA="9dbee70eb54090d62efdc930f30583761e1f4e81d14fed4cc9a53e93b4eae0b9"
def require(x,msg):
    if not x:raise ValueError(msg)
def main(folder):
    folder=Path(folder);es={}
    for k,h in HASHES.items():
        raw=(folder/(k+".json")).read_bytes();require(hashlib.sha256(raw).hexdigest()==h,"HASH:"+k)
        e=json.loads(raw,parse_float=D);require(e["id"]==["freq","unit","co_nco","sector","finpos","na_item","geo","time"],"AXIS");es[k]=e
    raw=(folder/"tee.xlsx").read_bytes();require(hashlib.sha256(raw).hexdigest()==TEE_SHA,"TEE_HASH")
    acq.OUT=folder;acq.workbook(raw);g=json.loads((folder/"exact_cells.json").read_text())["TEE_COMPLET"]
    require(g["B2"]["value"]=="Année 2022" and g["Y1"]["value"]=="En milliards d'Euros","TEE_SCOPE")
    def v(n,s,p,i,t="2022"):
        e=es[n];ix=0
        for k,x in zip(e["id"],["A","MIO_EUR","NCO",s,p,i,"FR",t]):
            a=e["dimension"][k]["category"]["index"];ix=ix*len(a)+a[x]
        x=e["value"].get(str(ix));return None if x is None else D(x)
    def tee(c,r):
        x=g.get(c+str(r));return None if x is None else D(x["value"])*1000
    identities=[];missing=[];comparisons=[];missing_compare=[];accounts={}
    for s,lc,rc in zip(["S1","S11","S12","S13","S14","S15","S2"],"CDEFGHJ","WVUTSRP"):
        require(g[lc+"2"]["value"]==g[rc+"2"]["value"]==s,"TEE_SECTOR")
        accounts[s]={}
        for p,c in [("ASS",lc),("LIAB",rc)]:
            for i in range(9):
                item="F"+str(i) if i else "F";ti=item if i else "F_TR"
                vals=[v("bs",s,p,item,"2021"),v("tr",s,p,ti),v("gl",s,p,item),v("oc",s,p,item),v("bs",s,p,item)]
                row=dict(zip(("opening","transactions","revaluation","other_changes","closing"),vals),sector=s,position=p,instrument=item)
                if None in vals:missing.append(row)
                else:
                    err=vals[-1]-sum(vals[:-1]);row["residual"]=err;row["status"]="WITHIN_SIMPLE_ROUNDING" if abs(err)<=D("2.5") else "UNRESOLVED_RESIDUAL";identities.append(row)
                for n,r,j in [("bs",178,item),("tr",102,ti),("gl",140,item),("oc",121,item)]:
                    a,b=tee(c,r+i),v(n,s,p,j)
                    rec={"dataset":n,"sector":s,"position":p,"instrument":item,"TEE_MEUR":a,"Eurostat_MEUR":b}
                    if a is None or b is None:missing_compare.append(rec)
                    else:rec["difference"]=a-b;comparisons.append(rec);require(abs(a-b)<=1,"CROSS_SOURCE")
            accounts[s][p]={n:v(n,s,p,"F_TR" if n=="tr" else "F") for n in es}
            accounts[s][p]["opening"]=v("bs",s,p,"F","2021")
        accounts[s]["net"]={k:accounts[s]["ASS"][k]-accounts[s]["LIAB"][k] for k in accounts[s]["ASS"]}
    require(len(identities)==118 and len(missing)==8 and len(comparisons)==419 and len(missing_compare)==85,"COVERAGE")
    require(max(abs(x["residual"]) for x in identities)==4,"PINNED_RESIDUAL")
    return {"status":"EMPIRICAL_FINANCIAL_DIAGNOSTIC_NOT_ADMISSION","publication":"BLOCK_PUBLICATION","unit":"million EUR, NCO","hashes":{**HASHES,"tee":TEE_SHA},"observations":{k:len(e["value"]) for k,e in es.items()},"accounts":accounts,"identities":identities,"missing_identities":missing,"comparisons":comparisons,"missing_comparisons":missing_compare,"household_equity":{"opening":v("bs","S14","ASS","F5","2021"),"closing":v("bs","S14","ASS","F5"),"transactions":v("tr","S14","ASS","F5"),"revaluation":v("gl","S14","ASS","F5"),"other_changes":v("oc","S14","ASS","F5")},"limitations":["nonconsolidated aggregates, not who-to-whom matrices","same national accounts lineage; not independent measurement","missing values not zero; residuals retained, including those beyond 2.5 MEUR rounding bound","no inferred loan rate, household ownership distribution or bank credit supply"]}
if __name__=="__main__":print(json.dumps(main(sys.argv[1]),ensure_ascii=False,indent=2,default=str))
