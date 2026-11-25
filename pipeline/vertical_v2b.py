"""VERTICAL-001 V2b: source-native STS and harmonized national accounts ratios.
Candidate internal evidence. No numeric joining to DPAE or AI adoption.
"""
import json,urllib.parse,datetime,re,argparse,os
from pathlib import Path
from fractions import Fraction as F
from .pilot_ict import retrieve,get_index,eurostat_offset,eurostat_flag
from .economic_core import canonical,digest,require

ROOT=Path(__file__).resolve().parents[1]
API="https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
SPECS={
 "national_accounts_output":("namq_10_a10",{"geo":"FR","nace_r2":"J","freq":"Q","sinceTimePeriod":"2019"}),
 "national_accounts_work":("namq_10_a10_e",{"geo":"FR","nace_r2":"J","freq":"Q","sinceTimePeriod":"2019"}),
 "sts_production":("sts_sepr_m",{"geo":"FR","nace_r2":"J","freq":"M","sinceTimePeriod":"2019"}),
 "sts_turnover":("sts_setu_m",{"geo":"FR","nace_r2":"J","freq":"M","sinceTimePeriod":"2019"}),
 "sts_prices":("sts_sepp_q",{"geo":"FR","nace_r2":"J","freq":"Q","sinceTimePeriod":"2019"})}
QUARTERS=tuple(f"{y}-Q{q}" for y in range(2019,2027) for q in range(1,5) if y<2026 or q<=3)
MONTHS=tuple(f"{y}-{m:02}" for y in range(2019,2027) for m in range(1,13) if y<2026 or m<=10)
# Only exact native codes; do not silently select nearest or change base.
SERIES={
 "gva_real":("national_accounts_output",{"unit":"CLV20_MEUR","s_adj":"SCA","na_item":"B1G"}),
 "gva_nominal":("national_accounts_output",{"unit":"CP_MEUR","s_adj":"SCA","na_item":"B1G"}),
 "compensation":("national_accounts_output",{"unit":"CP_MEUR","s_adj":"SCA","na_item":"D1"}),
 "total_hours":("national_accounts_work",{"unit":"THS_HW","s_adj":"SCA","na_item":"EMP_DC"}),
 "employee_hours":("national_accounts_work",{"unit":"THS_HW","s_adj":"SCA","na_item":"SAL_DC"}),
 "total_persons":("national_accounts_work",{"unit":"THS_PER","s_adj":"SCA","na_item":"EMP_DC"}),
 "employee_persons":("national_accounts_work",{"unit":"THS_PER","s_adj":"SCA","na_item":"SAL_DC"}),
 "production_index":("sts_production",{"unit":"I21","s_adj":"SCA","indic_bt":"PRD"}),
 "turnover_index":("sts_turnover",{"unit":"I21","s_adj":"SCA","indic_bt":"TOVT"}),
 "producer_price_index":("sts_prices",{"unit":"I21","s_adj":"NSA","indic_bt":"PRC"})}
def fetch_sources(fetcher=retrieve):
    out={}
    for k,(dataset,params) in SPECS.items():
        url=API+dataset+"?"+urllib.parse.urlencode({"lang":"EN",**params})
        r={"url":url,"dataset":dataset,"publication":"BLOCK_PUBLICATION"}
        try:
            b=fetcher(url);j=json.loads(b,parse_float=str)
            require(j.get("class")=="dataset","JSONSTAT_CLASS")
            r.update(status="RETRIEVED",sha256=digest(b),updated=j.get("updated"),bytes=len(b),
                     dimensions={d:list(get_index(j["dimension"][d]["category"])) for d in j["id"] if d!="time"},data=j)
        except Exception as e:r.update(status="BLOCKED",error_type=type(e).__name__)
        out[k]=r
    return out
def select(j,params,periods):
    required={"geo":"FR","nace_r2":"J","freq":"M" if periods==MONTHS else "Q",**params}
    require(set(j["id"])==set(required)|{"time"},"UNEXPECTED_DIMENSIONS")
    for k,v in required.items():require(v in get_index(j["dimension"][k]["category"]),"MISSING_NATIVE_SELECTOR:"+k+":"+v)
    series={}
    for p in periods:
        if p not in get_index(j["dimension"]["time"]["category"]):series[p]={"value":None,"flag":None,"status":"MISSING_PERIOD"};continue
        sel={**required,"time":p};i=eurostat_offset(j,sel);values=j.get("value",{})
        v=values.get(str(i)) if isinstance(values,dict) else values[i]
        flag=eurostat_flag(j,sel)
        if v is None:series[p]={"value":None,"flag":flag,"status":"MISSING_VALUE","offset":i};continue
        # Only unflagged, provisional or estimated observations used in diagnostic.
        ok=flag in ("","p","e","pe","ep","p e","e p")
        series[p]={"value":str(F(str(v))) if ok else None,"flag":flag,"status":"OBSERVED_CANDIDATE" if ok else "BLOCKED_FLAG","offset":i}
    return {"selectors":required,"levels":series}
def ratios(series):
    # ESA2010 national accounts only: domestic employment and GVA same country,
    # section and quarterly SCA; employee compensation / employee hours (not take-home pay).
    defs={"real_gva_per_total_hour":("gva_real","total_hours",1000,"EUR at 2020 chain-linked volume per hour"),
          "compensation_per_employee_hour":("compensation","employee_hours",1000,"nominal EUR per employee hour"),
          "employee_compensation_share":("compensation","gva_nominal",100,"percent nominal GVA; excludes self-employed mixed income"),
          "hours_per_person":("total_hours","total_persons",1,"hours per employed person per quarter")}
    out={}
    for k,(n,d,scale,unit) in defs.items():
        levels={}
        for p in QUARTERS:
            a=series.get(n,{}).get("levels",{}).get(p,{}).get("value");b=series.get(d,{}).get("levels",{}).get(p,{}).get("value")
            levels[p]=str(F(a)*scale/F(b)) if a is not None and b is not None and F(b)>0 else None
        changes={}
        for p,v in levels.items():
            prev=str(int(p[:4])-1)+p[4:];a=levels.get(prev)
            changes[p]=str(100*(F(v)/F(a)-1)) if a is not None and F(a)>0 and v is not None else None
        out[k]={"numerator":n,"denominator":d,"unit":unit,"levels":levels,"yoy_pct":changes,"status":"CONDITIONAL_DESCRIPTIVE_COMPATIBILITY_REVIEW"}
    return out
def build(fetcher=retrieve):
    sources=fetch_sources(fetcher);series={}
    for k,(src,params) in SERIES.items():
        s=sources[src];r={"source":src,"status":"BLOCKED","selectors":params}
        if s["status"]=="RETRIEVED":
            try:
                r.update(select(s["data"],params,MONTHS if SPECS[src][1]["freq"]=="M" else QUARTERS));r["status"]="CANDIDATE_INTERNAL"
            except ValueError as e:r["reason"]=str(e)
        series[k]=r
    source_records={k:{x:v for x,v in r.items() if x!="data"} for k,r in sources.items()}
    result={"study":"VERTICAL-001","phase":"V2b","sources":source_records,"series":series,"ratios":ratios(series),
            "publication":"BLOCK_PUBLICATION","causal_identification":"NOT_IDENTIFIED",
            "rights":"Eurostat source-specific review pending; internal diagnostics only",
            "dares":{"status":"CANDIDATE_NOT_ACQUIRED","source":"https://dares.travail-emploi.gouv.fr/donnees/les-mouvements-de-main-doeuvre","scope":"Metropolitan private sector excluding agriculture, temporary agency work and private households; realized contracts and separations, not DPAE","reason":"Workbook and exact sector dimensions not yet acquired; do not assume detailed quarterly series from headline publication."},
            "limits":["No STS-to-national-accounts numeric bridge or private-sector Urssaf denominator used.",
                      "Same native national-account scope and frequency only, compatibility review pending; chain-linked values not additive across branches.",
                      "No inferred adoption effect, no sector calibration, no claim of independent source families from Eurostat dissemination.",
                      "Snapshot of current vintage, not point-in-time backtest; source-specific publication and revision review pending."]}
    return {"result":result,"sha256":digest(canonical(result))}
def coverage(r):
    p=r["result"];out={}
    for k,s in p["series"].items():
        obs=[t for t,v in s.get("levels",{}).items() if v["value"] is not None]
        out[k]={"status":s["status"],"reason":s.get("reason"),"count":len(obs),"first":min(obs) if obs else None,"last":max(obs) if obs else None,
                "flags":sorted(set(v["flag"] for v in s.get("levels",{}).values() if v["flag"] is not None))}
    def ratio_cov(a):
        obs=[t for t,v in a["levels"].items() if v is not None];return {"count":len(obs),"last":max(obs) if obs else None}
    return {"study":p["study"],"phase":p["phase"],"publication":p["publication"],"causal_identification":p["causal_identification"],
            "sources":p["sources"],"series":out,"ratios":{k:ratio_cov(a) for k,a in p["ratios"].items()},"dares":p["dares"],"result_sha256":r["sha256"]}
def main():
    p=argparse.ArgumentParser();p.add_argument("--internal-output",type=Path);args=p.parse_args();r=build()
    if args.internal_output:
        target=args.internal_output.resolve();require(not target.is_relative_to(ROOT),"OUTPUT_OUTSIDE_REPO")
        with os.fdopen(os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),"w") as f:json.dump(r,f,ensure_ascii=False,indent=2)
    print("VERTICAL_V2B "+json.dumps(coverage(r),ensure_ascii=False))
if __name__=="__main__":main()
