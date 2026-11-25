"""V2b2: pinned evidence, exact descriptive signatures, integrated internal dossier.
No causal attribution, calibrated scenario or publication admission.
"""
import argparse,json,os
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
from .economic_core import canonical,digest,require
from .vertical_v2 import make_observations,build as base_build,claim,readreg
from .vertical_v2b import build as econ_build,QUARTERS,coverage as econ_coverage
from .pilot_ict import retrieve

ROOT=Path(__file__).resolve().parents[1]
PIN=ROOT/"audits/vertical_001_v2b_verified.json"
WINDOWS=(("pre_chatgpt","2019-Q2","2022-Q2"),("post_reference","2022-Q2","2026-Q2"),("latest_yoy","2025-Q2","2026-Q2"))
# These are fixed descriptive windows, not treatment dates.
def sign_signature(y,h):
    if y>0 and h<0:return "GVA_UP_HOURS_DOWN"
    if y>0 and 0<=h<y:return "GVA_UP_HOURS_GROW_SLOWER"
    if y>0 and h>y:return "GVA_UP_HOURS_GROW_FASTER"
    if y<0 and h<0:return "BOTH_DOWN"
    if y<0 and h>=0:return "GVA_DOWN_HOURS_NOT_DOWN"
    if y==0 and h<0:return "GVA_FLAT_HOURS_DOWN"
    return "OTHER_OR_EQUAL"

def val(series,k,p):
    x=series.get(k,{}).get("levels",{}).get(p,{}).get("value")
    return F(x) if x is not None else None

def change(series,start,end):
    a,b=(val(series,"gva_real",p) for p in (start,end))
    c,d=(val(series,"total_hours",p) for p in (start,end))
    if any(x is None or x<=0 for x in (a,b,c,d)):
        return {"from":start,"to":end,"status":"BLOCKED_MISSING_OR_NONPOSITIVE","signature":None}
    y=b/a;h=d/c;prod=y/h
    require(y==h*prod,"PRODUCTIVITY_IDENTITY")
    return {"from":start,"to":end,"status":"DESCRIPTIVE_INTERNAL_SAME_PINNED_RELEASE",
        "gva_change_pct":str(100*(y-1)),"hours_change_pct":str(100*(h-1)),
        "productivity_change_pct":str(100*(prod-1)),"signature":sign_signature(y-1,h-1),
        "identity":"GVA growth factor = hours growth factor times productivity growth factor",
        "source_series":["gva_real","total_hours"],"causal_identification":"NOT_IDENTIFIED"}

def signatures(series):
    # Check selectors at the interface rather than relying on labels.
    expected={"gva_real":{"geo":"FR","nace_r2":"J","freq":"Q","s_adj":"SCA","unit":"CLV20_MEUR","na_item":"B1G"},
              "total_hours":{"geo":"FR","nace_r2":"J","freq":"Q","s_adj":"SCA","unit":"THS_HW","na_item":"EMP_DC"}}
    for k,v in expected.items():
        require(series[k]["selectors"]==v,"INCOMPATIBLE_NATIVE_SCOPE")
    yoy=[change(series,f"{int(p[:4])-1}{p[4:]}",p) for p in QUARTERS if p[:4]!="2019"]
    windows=[{"id":i,**change(series,a,b)} for i,a,b in WINDOWS]
    return {"year_on_year":yoy,"windows":windows,
        "classification":"Exact signs; no statistical significance or structural break test. Small revisions can change class.",
        "interpretation":"Real value added and total hours are domestic national accounts; no private headcount or recruitment ratio.",
        "no_ai_attribution":True}

def pin_check(econ,pin):
    sources=econ["result"]["sources"]
    require(set(sources)==set(pin["sources"]),"SOURCE_SET")
    for k,v in sources.items():
        require(v["status"]=="RETRIEVED" and v["sha256"]==pin["sources"][k]["sha256"],"UNREVIEWED_ECONOMIC_VINTAGE:"+k)
    require(econ["sha256"]==digest(canonical(econ["result"])),"ECON_RECEIPT_HASH")

def integrate(base,econ,pin):
    pin_check(econ,pin)
    require(base["sha256"]==digest(canonical(base["result"])),"BASE_RECEIPT_HASH")
    # JSON round trip makes a separate immutable-by-convention receipt.
    p=json.loads(json.dumps(base["result"]))
    es=econ["result"];s=signatures(es["series"])
    p["phase"]="V2b2"
    p["economic_evidence"]={"receipt":econ,"signatures":s,
      "qualification":"INTERNAL_DESCRIPTIVE_PINNED_WITH_CAVEATS",
      "methodology_refs":["https://ec.europa.eu/eurostat/cache/metadata/EN/nama_10_prod_esms.htm","https://ec.europa.eu/eurostat/cache/metadata/EN/nama_10_pe_esms_fr.htm"],
      "national_context":[
        {"id":"N01","source":"https://www.insee.fr/fr/statistiques/9148679","period":"2026-09","status":"PUBLISHED_RELEASE_CONTEXT_ONLY","note":"Insee monthly production release covers September; national detailed series not acquired, no splice with Eurostat."},
        {"id":"N02","source":"https://dares.travail-emploi.gouv.fr/donnees/les-mouvements-de-main-doeuvre","period":"2026Q2","status":"BLOCKED_WORKBOOK_ACCESS","note":"Official page announces workbook; access returned human verification. Published qualitative sector decline only; no realized flow panel or stock reconciliation."}],
      "rights":"BLOCK_PUBLICATION; source-specific review and durable archive pending"}
    c=claim("C06","DESCRIPTIVE_COMPARISON","Real value added and domestic hours growth factors, signatures and productivity identity in matched quarters.","percent, EUR 2020 chain-linked per hour","France NACE J domestic national accounts","2019–2026 through common available quarter",["economic_evidence.receipt","economic_evidence.signatures"],["M032","M049","M054","M059","M063"],"Exact ratios and fixed descriptive windows; no causal treatment date.","Current vintages, possible revisions and aggregate composition; no significance test or AI attribution.","Demand, sector composition, offshoring, capital deepening, labor supply","Revised source or compatible independent measures; compare sectors and pre-trends")
    c["geography"]="France"
    c2=claim("C07","OBSERVATION","Compensation per employee hour, compensation share of nominal GVA, hours per person; NSA same-period ratios only.","nominal EUR/hour, percent, hours/person","France NACE J domestic national accounts","2019–2026 through common available quarter",["economic_evidence.receipt"],["M052","M054","M063"],"D1 includes employer social contributions; matched unadjusted denominators.","Not wages net of tax, not total labor income including self-employed; provisional data.","Composition, hours, wage negotiation","Revision or new comparable data")
    c2["geography"]="France"
    p["claims"].extend((c,c2));p["overview"]["claim_refs"].extend(("C06","C07"));p["overview"]["observation_refs"].append("economic_evidence.signatures")
    texts={"D02":("C06","Real GVA/hours signatures and fixed historical windows added; magnitude and sign in internal evidence."),
        "D03":("C06","Five additional pinned Eurostat datasets; national release context only, no claim of independent corroboration."),
        "D08":("C06","Native STS output, turnover and price series inspectable separately; no price/volume algebra across incompatible populations."),
        "D10":("C06","National accounts GVA/hours accounting identity added; no linkage to private employment flows or AI."),
        "D11":("C07","Unadjusted D1 share and compensation/hour calculated; residual is not pure capital income."),
        "D14":("C06","Descriptive same-vintage signatures, no estimated structural break or causal effect."),
        "D15":("C06","Same-quarter signatures tracked; not an out-of-sample early warning."),
        "D16":("C06","Compare real output and hours before concluding contraction versus decoupling."),
        "D17":("C07","Dares workbook and Insee detailed monthly series unavailable; preserve limitations."),
        "D18":("C06","Five additional source pins and economic receipt hash; full dossier can be generated offline from preserved inputs when available.")}
    for sec in p["sections"]:
        if sec["id"] in texts:
            ref,t=texts[sec["id"]];sec["content"]+=" "+t;sec["claim_refs"].append(ref)
    # No global promotion: evidence informs only particular requirements.
    for e in p["coverage"]:
        if e["id"] in ("M032","M049","M052","M054","M059","M063","SH01"):
            e["reason"]+=" V2b2 adds descriptive national-account ratios/signatures; no full requirement qualification."
            e["claim_refs"]=list(dict.fromkeys(e["claim_refs"]+["C06","C07"]))
            if e["disposition"]=="BLOCKED_MISSING_DATA":e["disposition"]="HYPOTHESIS_ONLY"
    p["code_sha256"].update({x:digest((ROOT/"pipeline"/x).read_bytes()) for x in ("vertical_v2b.py","vertical_v2b2.py")})
    p["economic_source_pins_sha256"]=digest(PIN.read_bytes())
    p["cross_source_numeric_join"]=False # no joining incompatible observation families; qualified national-account ratios separately
    p["within_national_accounts_matched_ratios"]=True
    p["publication"]="BLOCK_PUBLICATION"
    return {"result":p,"sha256":digest(canonical(p))}
def summary(r):
    p=r["result"];e=p["economic_evidence"];s=e["signatures"]
    # No values, directions or computed economic observations in public log.
    return {"study":p["study"],"phase":p["phase"],"publication":p["publication"],"causal_identification":p["causal_identification"],
       "section_count":len(p["sections"]),"claim_count":len(p["claims"]),"coverage_count":len(p["coverage"]),
       "economic_sources":{k:v["sha256"] for k,v in e["receipt"]["result"]["sources"].items()},
       "base_sources":{k:v["sha256"] for k,v in p["observations"]["source_native"].items()},
       "valid_yoy_signatures":sum(x["signature"] is not None for x in s["year_on_year"]),
       "valid_fixed_windows":sum(x["signature"] is not None for x in s["windows"]),
       "economic_receipt_sha256":e["receipt"]["sha256"],"scenario_sha256":p["scenario_receipt"]["sha256"],
       "result_sha256":r["sha256"],"national_context_status":{x["id"]:x["status"] for x in e["national_context"]},
       "registry_sha256":p["registry_sha256"],"code_sha256":p["code_sha256"]}
def main():
    a=argparse.ArgumentParser();a.add_argument("--internal-output",type=Path);args=a.parse_args()
    if args.internal_output:
        target=args.internal_output.resolve();require(not target.is_relative_to(ROOT),"OUTPUT_OUTSIDE_REPO")
    r=integrate(base_build(make_observations()),econ_build(),json.loads(PIN.read_text()))
    if args.internal_output:
        with os.fdopen(os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),"w") as f:json.dump(r,f,ensure_ascii=False,indent=2)
    print("VERTICAL_V2B2 "+json.dumps(summary(r),ensure_ascii=False))
if __name__=="__main__":main()
