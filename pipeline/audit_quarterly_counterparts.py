"""Quarterly bilateral stock diagnostic; no imputation or conversion to due debt."""
import json, hashlib, urllib.request
from decimal import Decimal as D
from pathlib import Path
BASE="https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
URL=BASE+"nasq_10_f_cp?lang=EN&freq=Q&unit=MIO_EUR&geo=FR&time=2022-Q4"
PIN="9c0193a112cf36b819da700210623ec95520bce86522c460e3f360974ad6104a"
AX=("S11","S12","S13","S14_S15","S2")
def qualify(raw,annual):
    sha=hashlib.sha256(raw).hexdigest()
    if sha!=PIN:return {"status":"BLOCKED_VINTAGE_CHANGED","sha256":sha,"expected":PIN}
    j=json.loads(raw,parse_float=D);assert j["id"]==["freq","unit","sector2","sector","stk_flow","finpos","na_item","geo","time"]
    dims={k:j["dimension"][k]["category"] for k in j["id"]}
    stock=[k for k,v in dims["stk_flow"]["label"].items() if v.lower()=="stock"];assert len(stock)==1
    def components(axis,code):
        idx=dims[axis]["index"]
        if code in idx:return (code,)
        if code=="S14_S15" and all(x in idx for x in ("S14","S15")):return ("S14","S15")
        return ()
    mapping={k:{a:components(k,a) for a in AX} for k in ("sector","sector2")}
    def instruments(inst):
        idx=dims["na_item"]["index"]
        if inst in idx:return (inst,)
        parts={"F4":("F41","F42"),"F5":("F51","F52")}.get(inst,())
        return parts if parts and all(x in idx for x in parts) else ()
    print("NATIVE_AXES",json.dumps({k:dims[k]["label"] for k in ("sector","sector2","na_item","stk_flow")}))
    def cell(holder,issuer,side,inst):
        sector,cp=(holder,issuer) if side=="ASS" else (issuer,holder)
        parts=[]
        for sc in mapping["sector"][sector]:
            for cc in mapping["sector2"][cp]:
                for ni in instruments(inst):
                    ix=0
                    for k,n,v in zip(j["id"],j["size"],("Q","MIO_EUR",cc,sc,stock[0],side,ni,"FR","2022-Q4")):
                        ix=ix*n+dims[k]["index"][v]
                    v=j["value"].get(str(ix))
                    parts.append({"sector":sc,"counterpart":cc,"instrument":ni,"value":str(v) if v is not None else None,"flag":j.get("status",{}).get(str(ix)),"locator":str(ix)})
        total=sum((D(x["value"]) for x in parts),D(0)) if parts and all(x["value"] is not None for x in parts) else None
        return {"value":str(total) if total is not None else None,"components":parts,"axis_available":bool(parts)}
    result={}
    for inst in ("F4","F5"):
        m=[];a=annual["margins"][inst]
        def margin(s,side):
            v=a[side]
            return D(v["S14"])+D(v["S15"]) if s=="S14_S15" else D(v[s])
        for issuer in AX:
            for holder in AX:
                x=cell(holder,issuer,"ASS",inst);y=cell(holder,issuer,"LIAB",inst)
                va=D(x["value"]) if x["value"] is not None else None;vl=D(y["value"]) if y["value"] is not None else None
                # Retain both observations; no preferred value where sources disagree.
                m.append({"issuer":issuer,"holder":holder,"asset":x,"liability":y,
                    "mirror_difference":str(va-vl) if va is not None and vl is not None else None,
                    "annual_bound_lower":str(max(D(0),margin(issuer,"rows")+margin(holder,"columns")-D(a["total"]))),
                    "annual_bound_upper":str(min(margin(issuer,"rows"),margin(holder,"columns")))})
        sums=[]
        for sector in AX:
            for side,axis,key in (("asset","holder","columns"),("liability","issuer","rows")):
                vals=[r[side]["value"] for r in m if r[axis]==sector]
                total=sum(map(D,vals),D(0)) if all(v is not None for v in vals) else None
                sums.append({"sector":sector,"side":side,"quarterly_sum":str(total) if total is not None else None,"annual_margin":str(margin(sector,key)),
                             "difference":str(total-margin(sector,key)) if total is not None else None,"observed_cells":sum(v is not None for v in vals)})
        pairs=[D(r["mirror_difference"]) for r in m if r["mirror_difference"] is not None]
        result[inst]={"cells":m,"margins":sums,"asset_observed":sum(r["asset"]["value"] is not None for r in m),
                      "liability_observed":sum(r["liability"]["value"] is not None for r in m),"mirror_pairs":len(pairs),
                      "mirror_exact":sum(x==0 for x in pairs),"max_abs_mirror_difference":str(max(map(abs,pairs))) if pairs else None,
                      "margin_pairs":sum(x["difference"] is not None for x in sums),
                      "max_abs_margin_difference":str(max(abs(D(x["difference"])) for x in sums if x["difference"] is not None)) if any(x["difference"] is not None for x in sums) else None}
    return {"status":"BILATERAL_STOCK_DIAGNOSTIC_NOT_ADMITTED","sha256":sha,"updated":j.get("updated"),"stock_code":stock[0],"axis":AX,"native_sector_codes":{k:list(dims[k]["index"]) for k in ("sector","sector2")},"axis_mapping":mapping,"instrument_mapping":{i:instruments(i) for i in ("F4","F5")},"instruments":result,
            "limitations":["missing cells not zero; retain mirrors, flags, annual vs quarterly differences, no automatic reconciliation","F4/F5 stocks, not due debt; aggregate absent requires all disjoint subinstruments (F41/F42 or F51/F52); otherwise unknown; no firm-level topology","S14/S15 grouped to match quarterly; no overlap with total or subsectors; vintage and coverage discrepancies retained"]}
def main():
    out=Path("counterpart-qualification");out.mkdir(exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(URL,headers={"User-Agent":"OctaveLab economic research"}),timeout=60) as r:
        assert r.geturl().startswith("https://ec.europa.eu/");raw=r.read(2000001);assert 0<len(raw)<=2000000
    (out/"counterpart.json").write_bytes(raw)
    annual=json.loads(Path("audits/eurostat_financial_network_2022_verified.json").read_text())
    result=qualify(raw,annual);(out/"audit.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="instruments"}|{"instruments":{i:{k:v for k,v in d.items() if k!="cells" and k!="margins"}|{"margins":d["margins"],"anchor":next(x for x in d["cells"] if x["issuer"]=="S11" and x["holder"]=="S12")} for i,d in result.get("instruments",{}).items()}},indent=2))
if __name__=="__main__":main()
