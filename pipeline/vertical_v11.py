"""V1 coverage extension: same-vintage internal diagnostics, no automatic release.
Review official corrected DPAE vintage before admitting affected comparisons.
"""
import json
from .vertical_v1 import employment,dpae,OLD,SOURCES,retrieve,digest,require,REGISTRIES,ROOT
from .pilot_ict import get_index,eurostat_offset,eurostat_flag,eurostat_value,eurostat_ict
from .economic_core import canonical,digest as canonical_digest

PERIODS=tuple(f"{y}Q{q}" for y in range(2019,2027) for q in range(1,5) if y<2026 or q<=3)
def diagnostic(a,kind):
    # Keep complete observations distinct from comparisons permitted by the existing registry.
    # Pre-2023 headcounts are separate segments; 2025+ DPAE are candidate observations only.
    for r in a["periods"]:
        p=r["period"]
        r["segment"]="PRE_DSN_REVIEW" if kind=="employment" and p<"2021Q1" else "PRE_APPRENTICE_REVIEW" if kind=="employment" and p<"2023Q1" else "POST_APPRENTICE" if kind=="employment" else "CORRECTION_VINTAGE_REVIEW" if p>="2025Q1" else "PRE_CORRECTION"
        if kind=="dpae" and p>="2025Q1" and r["status"]=="OBSERVED_INTERNAL":r["status"]="CANDIDATE_REVISED_VINTAGE_REVIEW"
    for c in a["same_quarter_year_on_year"]:
        if kind=="dpae" and c["to"]>="2025Q1":
            c.pop("relative_change_pct",None);c.pop("components",None);c.pop("groups",None)
            c.update(status="BLOCKED_REVISED_VINTAGE_REVIEW",change=None)
    return a
def summarize(a):
    complete=[r["period"] for r in a["periods"] if r["total"] is not None]
    return {"first_complete":min(complete) if complete else None,"last_complete":max(complete) if complete else None,"complete_periods":len(complete),
            "candidate_periods":[r["period"] for r in a["periods"] if r["status"]=="CANDIDATE_REVISED_VINTAGE_REVIEW"],
            "missing_periods":[r["period"] for r in a["periods"] if r["total"] is None],
            "descriptive_comparisons":sum(c["status"]=="DESCRIPTIVE_INTERNAL" for c in a["same_quarter_year_on_year"]),
            "blocked_comparisons":sum(c["status"].startswith("BLOCKED") for c in a["same_quarter_year_on_year"])}
def adoption_coverage(b):
    j=json.loads(b);s=eurostat_ict(b);required=s["selected_codes"];out=[]
    for y in sorted(get_index(j["dimension"]["time"]["category"])):
        try:
            sel={**required,"time":y};v=eurostat_value(j,sel)
            if v is not None:out.append({"year":y,"flag":eurostat_flag(j,sel)})
        except ValueError:continue
    return {"available_years":out,"comparison_status":"BLOCKED_PENDING_DEFINITION_REVIEW"}
def audit(old,fetcher=retrieve):
    require(old["causal_claims_permitted"] is False,"CAUSAL_GATE")
    out={}
    for k,u in SOURCES.items():
        rec={"url":u,"publication":"BLOCK_PUBLICATION"}
        try:
            b=fetcher(u);rec.update(sha256=digest(b),same_vintage_bytes=digest(b)==old["sources"][k]["sha256"])
            require(rec["same_vintage_bytes"],"NEW_VINTAGE_REVIEW_REQUIRED")
            if k=="eurostat_ai":rec["coverage"]=adoption_coverage(b)
            else:
                a=diagnostic(employment(b,PERIODS) if k=="urssaf_headcount" else dpae(b,PERIODS),"employment" if k=="urssaf_headcount" else "dpae")
                rec["coverage"]=summarize(a);rec["internal_result_sha256"]=canonical_digest(canonical(a))
            rec["status"]="PARSED_INTERNAL"
        except Exception as e:rec.update(status="BLOCKED",error_type=type(e).__name__)
        out[k]=rec
    return {"study":"VERTICAL-001","phase":"V1.1_COVERAGE","target":"2019Q1–2026Q3, only available observations","sources":out,
            "publication":"BLOCK_PUBLICATION","causal_identification":"NOT_IDENTIFIED",
            "registry_sha256":{p:digest((ROOT/"governance"/p).read_bytes()) for p in REGISTRIES}}
if __name__=="__main__":print("VERTICAL_V11 "+json.dumps(audit(json.loads(OLD.read_text())),ensure_ascii=False))
