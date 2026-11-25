"""VERTICAL-001 V0: replay historical pilot without publishing new source values.
Source retrieval is independent; log hashes and aggregate validation status only.
No private data, raw sources or newly derived values uploaded by this workflow.
"""
import json,hashlib,datetime
from pathlib import Path
from .pilot_ict import SOURCES,retrieve,read_csv,quarterly_urssaf,quarterly_dpae,eurostat_ict

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/"research/PILOT-001/pilot_manifest.json"
PARSERS={
 "urssaf_headcount":("private_employment",lambda b:quarterly_urssaf(read_csv(b,{"secteur_na88i","annee","trimestre","effectifs_salaries_cvs"}))),
 "urssaf_dpae":("dpae",lambda b:quarterly_dpae(read_csv(b,{"secteur_na38","annee","trimestre","duree_de_contrat","nature_de_contrat","dpae_cvs"}))),
 "eurostat_ai":("ai_adoption",eurostat_ict)}
def digest(b):return hashlib.sha256(b).hexdigest()
def audit(old,fetcher=retrieve):
    assert old["causal_claims_permitted"] is False
    result={}
    for key,url in SOURCES.items():
        rec={"url":url,"historical_sha256":old["sources"][key]["sha256"],"rights":"PUBLIC_PRODUCT_REVIEW_PENDING","lineage":"URSSAF_ADMIN" if key.startswith("urssaf") else "EUROSTAT_ENTERPRISE_SURVEY"}
        try:
            b=fetcher(url);rec.update(sha256=digest(b),bytes=len(b),same_bytes=digest(b)==rec["historical_sha256"])
            name,parse=PARSERS[key];now=parse(b);previous=old["selected_studies"][name]
            rec.update(status="PARSED",same_selected_result=now==previous)
            if key=="eurostat_ai":
                rec["blocked_comparisons_preserved"]=now["change_2024_vs_2023_pp"] is None and now["change_2025_vs_2024_pp"] is None
            if key=="urssaf_dpae":rec["2025_excluded"]=all(not p.startswith("2025") for p in now["selected_periods"])
        except Exception as e:
            rec.update(status="BLOCKED",error_type=type(e).__name__)
        result[key]=rec
    return {"study":"VERTICAL-001","phase":"V0","collected_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "sources":result,"parsed_sources":sum(r["status"]=="PARSED" for r in result.values()),
            "distinct_lineages":2,"causal_identification":"NOT_IDENTIFIED","publication":"BLOCK_PUBLICATION",
            "historical_reproduction":"SAME_BYTES_AND_RESULTS" if all(r.get("same_bytes") and r.get("same_selected_result") for r in result.values()) else "NOT_ESTABLISHED",
            "note":"No new source values in this audit. Current acquisition is not a historical replay unless digests and selected results agree. Public/commercial rights and independent review remain open."}
def main():
    a=audit(json.loads(OLD.read_text()))
    a["historical_manifest_sha256"]=digest(OLD.read_bytes())
    a["registry_sha256"]={p.name:digest(p.read_bytes()) for p in (ROOT/"governance").glob("*.json") if p.name in {"economic_mechanisms_v2.json","transversal_enrichment_v1.json","shapiro_enrichment_v1.json","investigation_result_v1.json","multi_order_prospective_v1.json","limitations_v1.json"}}
    print("VERTICAL_V0 "+json.dumps(a,ensure_ascii=False))
if __name__=="__main__":main()
