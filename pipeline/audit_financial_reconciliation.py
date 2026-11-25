"""G4 v0.7g2 native annual counterpart and quarterly balance sheet comparisons.
No reconciliation by imputation. Archive exact downloads and explicit locators.
"""
import hashlib,json,urllib.request
from decimal import Decimal as D
from pathlib import Path
from datetime import datetime,timezone
BASE="https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
QUERIES={"annual_cp":"nasa_10_f_cp?lang=EN&freq=A&unit=MIO_EUR&geo=FR&time=2022",
         "quarter_bs":"nasq_10_f_bs?lang=EN&freq=Q&unit=MIO_EUR&geo=FR&time=2022-Q4",
         "quarter_cp":"nasq_10_f_cp?lang=EN&freq=Q&unit=MIO_EUR&geo=FR&time=2022-Q4"}
AX=("S11","S12","S13","S14_S15","S2")
def load(out,name,query):
    url=BASE+query
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"OctaveLab economic research"}),timeout=60) as r:
        assert r.geturl().startswith("https://ec.europa.eu/");raw=r.read(4000001);assert 0<len(raw)<=4000000
        meta={"url":url,"resolved_url":r.geturl(),"http":r.status,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"collected_utc":datetime.now(timezone.utc).isoformat()}
    (out/(name+".json")).write_bytes(raw);j=json.loads(raw,parse_float=D)
    assert j["class"]=="dataset"
    meta.update({"updated":j.get("updated"),"axes":{k:j["dimension"][k]["category"]["label"] for k in j["id"]},"size":j["size"],"observed":len(j["value"])})
    return j,meta
def cell(j,selectors):
    choices=[]
    for k in j["id"]:
        idx=j["dimension"][k]["category"]["index"]
        v=selectors.get(k)
        if v is None:return {"value":None,"reason":"UNMAPPED_DIMENSION:"+k,"parts":[]}
        if v in idx:parts=[v]
        elif v=="S14_S15" and all(x in idx for x in ("S14","S15")):parts=["S14","S15"]
        else:return {"value":None,"reason":"AXIS_ABSENT:"+k+":"+v,"parts":[]}
        choices.append(parts)
    from itertools import product
    parts=[]
    for codes in product(*choices):
        ix=0
        for k,n,v in zip(j["id"],j["size"],codes):ix=ix*n+j["dimension"][k]["category"]["index"][v]
        val=j["value"].get(str(ix));parts.append({"locator":str(ix),"codes":dict(zip(j["id"],codes)),"value":str(val) if val is not None else None,"flag":j.get("status",{}).get(str(ix))})
    return {"value":str(sum((D(p["value"]) for p in parts),D(0))) if all(p["value"] is not None for p in parts) else None,"parts":parts,"reason":None if all(p["value"] is not None for p in parts) else "MISSING_VALUE"}
def select(j,side,inst,sector,cp=None):
    freq="Q" if "Q" in j["dimension"]["freq"]["category"]["index"] else "A"
    d={"freq":freq,"unit":"MIO_EUR","geo":"FR","time":"2022-Q4" if freq=="Q" else "2022",
       "co_nco":"NCO","sector":sector,"sector2":cp,"stk_flow":"STK","finpos":side,"na_item":inst}
    return cell(j,d)
def diff(a,b):
    return str(D(a)-D(b)) if a is not None and b is not None else None
def summary(rows,k):
    vals=[D(r[k]) for r in rows if r[k] is not None]
    return {"pairs":len(vals),"exact":sum(x==0 for x in vals),"max_abs":str(max(map(abs,vals))) if vals else None}
def main():
    out=Path("financial-reconcile");out.mkdir(exist_ok=True)
    data={};meta={}
    for name,q in QUERIES.items():
        try:data[name],meta[name]=load(out,name,q)
        except Exception as exc:meta[name]={"status":"ACQUISITION_FAILED","error":str(exc)}
    annual=json.loads(Path("audits/eurostat_financial_network_2022_verified.json").read_text())
    if "quarter_cp" in meta and meta["quarter_cp"].get("sha256")!="9c0193a112cf36b819da700210623ec95520bce86522c460e3f360974ad6104a":
        data.pop("quarter_cp",None);meta["quarter_cp"]["status"]="BLOCKED_VINTAGE_CHANGED"
    missing={"value":None,"reason":"SOURCE_UNAVAILABLE","parts":[]}
    get=lambda name,*a:select(data[name],*a) if name in data else missing
    margins=[];bilateral=[]
    for inst in ("F4","F5"):
        for s in AX:
            for side,key in (("ASS","columns"),("LIAB","rows")):
                av=annual["margins"][inst][key];a=str(D(av["S14"])+D(av["S15"])) if s=="S14_S15" else av[s]
                q=get("quarter_bs",side,inst,s)
                margins.append({"instrument":inst,"sector":s,"side":side,"annual_pinned":a,"quarter":q,"difference":diff(q["value"],a)})
        for issuer in AX:
            for holder in AX:
                row={"instrument":inst,"issuer":issuer,"holder":holder}
                for name in ("annual_cp","quarter_cp"):
                    row[name+"_asset"]=get(name,"ASS",inst,holder,issuer)
                    row[name+"_liability"]=get(name,"LIAB",inst,issuer,holder)
                    row[name+"_mirror"]=diff(row[name+"_asset"]["value"],row[name+"_liability"]["value"])
                row["asset_period_difference"]=diff(row["quarter_cp_asset"]["value"],row["annual_cp_asset"]["value"])
                row["liability_period_difference"]=diff(row["quarter_cp_liability"]["value"],row["annual_cp_liability"]["value"])
                bilateral.append(row)
    totals=[]
    for name,bs in (("annual_cp","annual"),("quarter_cp","quarter")):
        for m in margins:
            s=m["sector"];side=m["side"];suffix="asset" if side=="ASS" else "liability"
            axis="holder" if side=="ASS" else "issuer";vals=[r[name+"_"+suffix]["value"] for r in bilateral if r["instrument"]==m["instrument"] and r[axis]==s]
            total=str(sum(map(D,vals),D(0))) if all(v is not None for v in vals) else None
            ref=m["annual_pinned"] if bs=="annual" else m["quarter"]["value"]
            totals.append({"source":name,"instrument":m["instrument"],"sector":s,"side":side,"observed":sum(v is not None for v in vals),"total":total,"margin":ref,"difference":diff(total,ref)})
    # Native subinstrument coverage; F511 is not all F51.
    native=[]
    for name,j in data.items():
        if "sector2" not in j["id"]:continue
        for inst in j["dimension"]["na_item"]["category"]["index"]:
            for side in ("ASS","LIAB"):
                n=sum(select(j,side,inst,h if side=="ASS" else i,i if side=="ASS" else h)["value"] is not None for i in AX for h in AX)
                native.append({"source":name,"instrument":inst,"side":side,"observed":n})
    brief={"annual_quarter_margins":summary(margins,"difference"),
           "annual_mirrors":summary(bilateral,"annual_cp_mirror"),"quarter_mirrors":summary(bilateral,"quarter_cp_mirror"),
           "annual_quarter_assets":summary(bilateral,"asset_period_difference"),"annual_quarter_liabilities":summary(bilateral,"liability_period_difference"),
           "annual_cp_to_margin":summary([r for r in totals if r["source"]=="annual_cp"],"difference"),
           "quarter_cp_to_margin":summary([r for r in totals if r["source"]=="quarter_cp"],"difference")}
    result={"status":"DIAGNOSTIC_NOT_ADMITTED","sources":meta,"summary":brief,"native_coverage":native,"margins":margins,"bilateral":bilateral,"totals":totals,
            "limitations":["native totals only; no imputation or assumption of consolidation for counterpart series; compare vintages explicitly",
                           "annual vs quarter end stocks, not maturity or default; sector partitions differ; rights and methodological review pending"]}
    (out/"audit.json").write_text(json.dumps(result,indent=2)+"\n")
    print("RECONCILIATION_SUMMARY "+json.dumps({"status":result["status"],"sources":{k:{a:v for a,v in m.items() if a!="axes"} for k,m in meta.items()},"summary":brief,"native_coverage":native,"anchor":next(r for r in bilateral if r["instrument"]=="F4" and r["issuer"]=="S11" and r["holder"]=="S12"),"margins":margins,"totals":totals}))
if __name__=="__main__":main()
