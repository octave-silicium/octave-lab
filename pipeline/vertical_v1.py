"""VERTICAL-001 V1: internal source-native descriptive investigation.
No causal claims, no cross-source joins, no automatic public data release.
"""
import argparse,datetime,hashlib,json,os,re
from decimal import Decimal,InvalidOperation
from pathlib import Path
from .pilot_ict import SOURCES,retrieve,read_csv,eurostat_ict
from .vertical_v0 import OLD,digest
from .data_governance import comparison_gate,public_use_gate
from .economic_core import canonical,digest as canonical_digest

ROOT=Path(__file__).resolve().parents[1]
DIVISIONS=("58","59","60","61","62","63")
GROUPS={"JA":("58","59","60"),"JB":("61",),"JC":("62","63")}
CONTRACTS=("CDI","CDD de plus d'un mois")
HEAD_PERIODS=tuple(f"{y}Q{q}" for y in range(2023,2027) for q in range(1,5) if y<2026 or q<=2)
DPAE_PERIODS=tuple(f"{y}Q{q}" for y in range(2022,2025) for q in range(1,5))
REGISTRIES=("economic_mechanisms_v2.json","transversal_enrichment_v1.json","shapiro_enrichment_v1.json","investigation_result_v1.json","multi_order_prospective_v1.json","limitations_v1.json","source_rights.json","series_events.json")
def require(ok,reason):
    if not ok:raise ValueError(reason)
def number(x):
    try:v=Decimal(x.strip().replace(" ","").replace("\u202f","").replace(",","."))
    except (InvalidOperation,AttributeError):raise ValueError("INVALID_VALUE") from None
    require(v.is_finite() and v>=0,"INVALID_VALUE");return v
def pkey(r):
    y,q=int(r["annee"]),int(r["trimestre"]);require(1<=q<=4,"INVALID_QUARTER");return f"{y}Q{q}"
def textval(x):return format(x,"f")
def pct(d,b):return textval((100*d/b).quantize(Decimal("0.0001"))) if b else None
def component_series(raw,periods,expected,series_id,groups=None):
    """A missing component blocks that period; never silently sum a partial sector."""
    by={p:{} for p in periods}
    for p,k,v,loc in raw:
        if p not in by:continue
        require(k in expected,"UNEXPECTED_COMPONENT")
        require(k not in by[p],"DUPLICATE_COMPONENT")
        by[p][k]=(v,loc)
    records=[];complete={}
    for p,cells in by.items():
        missing=sorted(set(expected)-set(cells))
        if missing:
            records.append({"period":p,"status":"BLOCKED_MISSING_COMPONENT","missing":missing,"total":None});continue
        vals={k:v for k,(v,_) in cells.items()}
        total=sum(vals.values(),Decimal(0));complete[p]=vals
        row={"period":p,"status":"OBSERVED_INTERNAL","total":textval(total),"components":{k:textval(vals[k]) for k in sorted(vals)},
             "source_csv_record_numbers":{k:cells[k][1] for k in sorted(cells)}}
        if groups:
            row["groups"]={g:textval(sum((vals[k] for k in ks),Decimal(0))) for g,ks in groups.items()}
            require(sum(Decimal(v) for v in row["groups"].values())==total,"GROUP_IDENTITY")
        records.append(row)
    comparisons=[]
    for p in periods:
        prev=f"{int(p[:4])-1}{p[4:]}"
        if prev not in by:continue
        gate=comparison_gate(series_id,prev,p)
        if gate["decision"]!="ALLOW_WITH_CAVEATS" or prev not in complete or p not in complete:
            comparisons.append({"from":prev,"to":p,"status":"BLOCKED","gate":gate,"change":None});continue
        a,b=complete[prev],complete[p];base=sum(a.values());delta=sum(b.values())-base
        detail={k:{"change":textval(b[k]-a[k]),"relative_change_pct":pct(b[k]-a[k],a[k]),"contribution_to_total_growth_pp":pct(b[k]-a[k],base)} for k in sorted(a)}
        require(sum(Decimal(x["change"]) for x in detail.values())==delta,"CONTRIBUTION_IDENTITY")
        c={"from":prev,"to":p,"status":"DESCRIPTIVE_INTERNAL","gate":gate,"change":textval(delta),"relative_change_pct":pct(delta,base),"components":detail}
        if groups:
            c["groups"]={}
            for g,ks in groups.items():
                x=sum(a[k] for k in ks);y=sum(b[k] for k in ks)
                c["groups"][g]={"change":textval(y-x),"relative_change_pct":pct(y-x,x),"contribution_to_total_growth_pp":pct(y-x,base)}
        comparisons.append(c)
    return {"periods":records,"same_quarter_year_on_year":comparisons,"series_id":series_id,"method":"exact decimal sum, full native components only; contribution = component change / opening aggregate; no causal attribution"}
def employment(data):
    rows=read_csv(data,{"secteur_na88i","annee","trimestre","effectifs_salaries_cvs"})
    raw=[]
    for n,r in enumerate(rows,1):
        m=re.match(r"^(5[89]|6[0-3])(?:\s|$)",r["secteur_na88i"].strip())
        if not m:continue
        p=pkey(r)
        if p in HEAD_PERIODS:raw.append((p,m[1],number(r["effectifs_salaries_cvs"]),n))
    return component_series(raw,HEAD_PERIODS,DIVISIONS,"urssaf_na88_effectifs_salaries_cvs",GROUPS)
def dpae(data):
    rows=read_csv(data,{"secteur_na38","annee","trimestre","duree_de_contrat","nature_de_contrat","dpae_cvs"})
    raw=[]
    for n,r in enumerate(rows,1):
        sec=r["secteur_na38"].strip().split(" ")[0];contract=r["nature_de_contrat"].strip()
        if sec not in GROUPS or contract not in CONTRACTS or r["duree_de_contrat"].strip()!="Contrat de plus d'un mois":continue
        p=pkey(r)
        if p in DPAE_PERIODS:raw.append((p,sec+"|"+contract,number(r["dpae_cvs"]),n))
    groups={g:tuple(g+"|"+c for c in CONTRACTS) for g in GROUPS}
    expected=tuple(k for ks in groups.values() for k in ks)
    return component_series(raw,DPAE_PERIODS,expected,"urssaf_dpae_na38_quarterly",groups)
def adoption(data):
    s=eurostat_ict(data)
    return {"unit":s["unit"],"population":s["population"],"native_selectors":s["selected_codes"],
            "levels":[{"year":y,"value":v,"flag":s["source_flags"][y],"status":"LEVEL_ONLY"} for y,v in s["selected_years"].items()],
            "comparisons":[{"from":"2023","to":"2024","change":None,"status":"BLOCKED_SOURCE_BREAK"},
                           {"from":"2024","to":"2025","change":None,"status":"BLOCKED_BASKET_CHANGE"}]}
def build(old,fetcher=retrieve):
    require(old["causal_claims_permitted"] is False,"CAUSAL_GATE")
    rights={"urssaf_headcount":"DS-015_urssaf_private_sector_na88","urssaf_dpae":"URSSAF_DPAE_NA38_QUARTERLY"}
    parsers={"urssaf_headcount":employment,"urssaf_dpae":dpae,"eurostat_ai":adoption}
    recs={}
    for k,u in SOURCES.items():
        r={"url":u,"source_family":"URSSAF_ADMIN" if k.startswith("urssaf") else "EUROSTAT_ENTERPRISE_SURVEY",
           "publication":"BLOCK_PUBLICATION","source_rights":public_use_gate(rights[k],"internal_research") if k in rights else {"decision":"INTERNAL_RESEARCH_ONLY_PENDING_REGISTRY_REVIEW","reason":"Eurostat general reuse notice, source-specific review pending"}}
        try:
            b=fetcher(u);r.update(sha256=digest(b),same_vintage_bytes=digest(b)==old["sources"][k]["sha256"])
            require(r["same_vintage_bytes"],"SOURCE_VINTAGE_CHANGED_REVIEW_REQUIRED")
            r["analysis"]=parsers[k](b);r["status"]="PARSED_INTERNAL"
        except Exception as e:
            r.update(status="BLOCKED",error_type=type(e).__name__)
            if isinstance(e,ValueError) and str(e)=="SOURCE_VINTAGE_CHANGED_REVIEW_REQUIRED":r["reason"]="SOURCE_VINTAGE_CHANGED_REVIEW_REQUIRED"
        recs[k]=r
    payload={"study":"VERTICAL-001","phase":"V1","scope":"France, NACE Rev.2 J, employer activities not digital occupations",
             "sources":recs,"registry_sha256":{p:digest((ROOT/"governance"/p).read_bytes()) for p in REGISTRIES},
             "publication":"BLOCK_PUBLICATION","causal_identification":"NOT_IDENTIFIED","cross_source_numeric_join":False,
             "excluded_periods":{"employment":"Before 2023Q1: apprentice definition break; through 2026Q2 fixed horizon","dpae":"2025 onward: conservative contract declaration quality hold","adoption":"all changes withheld; only reported annual levels"},
             "competing_explanations":[{"id":"H_AI","hypothesis":"AI substitution / complementarity","discriminating_evidence":"predefined task exposure, matched occupations and employers, adoption timing and output/quality"},
              {"id":"H_CYCLE","hypothesis":"Demand / post-pandemic hiring normalization","discriminating_evidence":"orders, turnover, volumes and comparable pretrends"},
              {"id":"H_OFFSHORE","hypothesis":"Offshoring, outsourcing or sector reclassification","discriminating_evidence":"cross-border services, employer transitions and work location"},
              {"id":"H_FINANCE","hypothesis":"Financing constraints","discriminating_evidence":"investment, cash flow, loan terms and firm-level timing"},
              {"id":"H_SUPPLY","hypothesis":"Labor supply, attrition and occupational mismatch","discriminating_evidence":"separations, wages, hours, vacancies and cohort flows"}],
             "oem_comparator":{"status":"BLOCKED_MISSING_DATA","reason":"No admitted joint occupation-sector-time vacancy/exposure panel. External AI-LERT not reproduced."}}
    return {"result":payload,"sha256":canonical_digest(canonical(payload))}
def safe_summary(receipt):
    """Allowlist only; never pass source observations, comparisons, claims or locators through."""
    r=receipt["result"];out={}
    for k,v in r["sources"].items():
        a=v.get("analysis",{})
        out[k]={"status":v["status"],"sha256":v.get("sha256"),"same_vintage_bytes":v.get("same_vintage_bytes"),
                "complete_periods":sum(x["status"]=="OBSERVED_INTERNAL" for x in a.get("periods",[])),
                "descriptive_comparisons":sum(x["status"]=="DESCRIPTIVE_INTERNAL" for x in a.get("same_quarter_year_on_year",[])),
                "blocked_periods":sum(x["status"]=="BLOCKED_MISSING_COMPONENT" for x in a.get("periods",[])),
                "level_only_count":len(a.get("levels",[])),"blocked_change_count":sum(x["status"].startswith("BLOCKED") for x in a.get("comparisons",[]))}
    return {"study":r["study"],"phase":r["phase"],"publication":r["publication"],"causal_identification":r["causal_identification"],
            "sources":out,"result_sha256":receipt["sha256"],"registry_sha256":r["registry_sha256"],"oem_comparator_status":r["oem_comparator"]["status"]}
def main():
    p=argparse.ArgumentParser();p.add_argument("--internal-output",type=Path);args=p.parse_args()
    if args.internal_output:
        target=args.internal_output.resolve();require(not target.is_relative_to(ROOT),"OUTPUT_MUST_BE_OUTSIDE_REPOSITORY")
    r=build(json.loads(OLD.read_text()))
    if args.internal_output:
        # No overwrite or world-readable output.
        with os.fdopen(os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),"w") as f:json.dump(r,f,ensure_ascii=False,indent=2)
    print("VERTICAL_V1 "+json.dumps(safe_summary(r),ensure_ascii=False))
if __name__=="__main__":main()
