"""Pinned F4/F5 margin bounds, and separate raw quarterly counterpart source acquisition."""
import json,hashlib,sys
from pathlib import Path
from decimal import Decimal as D
from pipeline import acquire_tes_income as acq
from pipeline.economic_institutional_bridge import transportation_bounds
SHA="8d2b5c7cba5cdd3e4c26f23e2db345c5177150d82c0165fbeb8216310f9d01b8"
BASE="https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
def main():
    acq.OUT=Path("financial-network");acq.OUT.mkdir(exist_ok=True)
    raw,meta=acq.get("bs.json",BASE+"nasa_10_f_bs?lang=EN&freq=A&unit=MIO_EUR&geo=FR&time=2021&time=2022")
    if hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError("STOCK_VINTAGE")
    e=json.loads(raw,parse_float=D)
    assert e["id"]==["freq","unit","co_nco","sector","finpos","na_item","geo","time"]
    sectors=("S11","S12","S13","S14","S15","S2")
    def cell(s,p,i):
        idx=0
        for k,n,x in zip(e["id"],e["size"],("A","MIO_EUR","NCO",s,p,i,"FR","2022")):idx=idx*n+e["dimension"][k]["category"]["index"][x]
        return e["value"][str(idx)]
    bounds={}
    for i in ("F4","F5"):
        # Rows are debtors/issuers, columns holders. Diagonal permitted within aggregate sector.
        bounds[i]=transportation_bounds({s:cell(s,"LIAB",i) for s in sectors},{s:cell(s,"ASS",i) for s in sectors})
    out={"status":"EMPIRICAL_MARGINAL_STOCK_BOUNDS_NOT_CLEARING_INPUT","publication":"BLOCK_PUBLICATION","source":meta,"bounds":bounds,"limitations":["stocks not obligations due; F5 includes shares and fund units, not debt","sector diagonals allowed; no maturity, collateral or debtor-level topology","no inference of specific counterpart exposure from marginal stocks"]}
    url=BASE+"nasq_10_f_cp?lang=EN&freq=Q&unit=MIO_EUR&geo=FR&time=2022-Q4"
    try:
        raw,meta=acq.get("counterpart.json",url);p=acq.euro(raw);out["quarterly_counterpart"]={"status":"RAW_PROFILE_ONLY","source":meta,"profile":p}
    except Exception as exc:out["quarterly_counterpart"]={"status":"ACQUISITION_FAILED","url":url,"error":str(exc)}
    (acq.OUT/"audit.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    cp=out["quarterly_counterpart"]
    print(json.dumps({"status":out["status"],"margins":{i:{k:b[k] for k in ("rows","columns","total","original_row_minus_column")} for i,b in bounds.items()},"F4_S11_to_S12":next(x for x in bounds["F4"]["cells"] if x["row"]=="S11" and x["column"]=="S12"),"F5_S11_to_S14":next(x for x in bounds["F5"]["cells"] if x["row"]=="S11" and x["column"]=="S14"),"quarterly_counterpart":{k:v for k,v in cp.items() if k!="profile"},"quarterly_profile":{k:v for k,v in cp.get("profile",{}).items() if k in ("id","size","observed_values","updated")}},indent=2))
if __name__=="__main__":main()
