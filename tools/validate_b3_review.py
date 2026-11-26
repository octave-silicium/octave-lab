"""Additional routing of non-P0 queue; explicit IDs are hints, never semantic proof."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from tools.limitation_triage import build

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "governance/audit_master_b3_review_v1.json"
PATTERN = re.compile(r"(?<![\w-])(?:M\d{3}|AC\d{2}|SH\d{2}|E\d{2}|L\d{2}|LIM-[A-Z]\d{2}|G-M\d|E-G\d|UX-G\d|D\d{2})(?!\w)")
CONTRACT_DOCS = {"ARCH-002.md","RESULT-001.md","PROSPECT-001.md","METH-003.md",
                 "UX-001.md","TRANSFORM-001.md","ENGINEERING-ASSURANCE-001.md",
                 "PRODUCT-FIRST-001.md","BENCH-001.md","AUDIT-TRANSVERSAL-001.md",
                 "DD-SHAPIRO-001-INTEGRATION.md","COMMON-STATE-001.md"}

def refs(text, known):
    return sorted(set(PATTERN.findall(text)) & known)

def source_kind(path):
    if path.startswith("pipeline/"):
        return "CODE_DECLARATION_REVIEW"
    if path.startswith("governance/"):
        return "CANONICAL_REGISTER_REVIEW"
    if Path(path).name in CONTRACT_DOCS:
        return "CONTRACT_OR_MILESTONE_REVIEW"
    if path.startswith("docs/") or path == "README.md":
        return "HISTORICAL_OR_METHOD_DOC_REVIEW"
    return "RESEARCH_REVIEW"

def validate(reg, queue, known_families, known_ids):
    groups = queue["groups"]
    non = [g for g in groups if g["priority"] != "P0_REVIEW"]
    digest = hashlib.sha256("\n".join(g["group_id"] for g in non).encode()).hexdigest()
    if digest != reg["non_p0_order_sha256"] or queue["summary"]["revision"] != reg["queue_revision"]:
        raise ValueError("Queue drift")
    if reg["publication_authorized"] is not False or queue["summary"]["publication_authorized"] is not False:
        raise ValueError("Publication authorization forbidden")
    by = {r["ordinal"]:r for r in reg["rows"]}
    if len(by) != len(reg["rows"]):
        raise ValueError("Duplicate review ordinal")
    valid_ordinals = {i for i,g in enumerate(groups,1) if g["priority"]!="P0_REVIEW"}
    if not set(by) <= valid_ordinals:
        raise ValueError("Unexpected review ordinal")
    dispositions = {"CONTRACT","ACTIVE_GAP","EVIDENCE_SCOPE","HISTORICAL","GUARD_REVIEW"}
    out = []
    for i,g in enumerate(groups,1):
        if i not in valid_ordinals:
            continue
        kinds = sorted({source_kind(m["path"]) for m in g["members"]})
        hints = sorted({r for m in g["members"] for r in refs(m["verbatim"],known_ids)})
        row = {"ordinal":i,"group_id":g["group_id"],"priority":g["priority"],
               "source_kinds":kinds,"literal_known_ids":hints,
               "file_suggestions":g["file_suggestions"],
               "members":[{k:m[k] for k in ("id","path","line")} for m in g["members"]],
               "review_status":"ROUTING_ONLY_PENDING_SEMANTIC","closure_authorized":False}
        if i in by:
            r=by[i]
            if (r["disposition"] not in dispositions or not r["rationale"].strip()
                    or not r["candidate_families"] or not set(r["candidate_families"]) <= known_families
                    or r["verification_status"]!="CONTEXT_AND_EVIDENCE_PENDING"
                    or r["closure_authorized"] is not False):
                raise ValueError("Invalid targeted review")
            row.update(r,review_status="FIRST_PASS_CONTEXT_AND_EVIDENCE_PENDING")
        out.append(row)
    review = [r for r in out if r["review_status"].startswith("FIRST_PASS")]
    return {"rows":out,"summary":{"non_p0_groups":len(out),
             "occurrences":sum(len(r["members"]) for r in out),
             "literal_id_hint_groups":sum(bool(r["literal_known_ids"]) for r in out),
             "source_kinds":dict(sorted(Counter(t for r in out for t in r["source_kinds"]).items())),
             "first_pass_reviewed":len(review),"routing_only_pending":len(out)-len(review),
             "dispositions":dict(sorted(Counter(r["disposition"] for r in review).items())),
             "closure_authorized":0,"publication_authorized":False},
            "limits":["Literal known IDs may appear in examples or ranges; no semantic attribution.",
                      "Source kinds are routing hints, not proof of validity.",
                      "Targeted first pass is not independent evidence verification."]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    reg=json.loads(REG.read_text())
    q=build(reg["queue_revision"])
    def read(path): return json.loads((ROOT/path).read_text())
    families={e["id"] for e in read("governance/limitations_v1.json")["entries"]}
    ids=set(families)
    for path,key in [
        ("governance/economic_mechanisms_v2.json","mechanisms"),
        ("governance/economic_mechanisms_v2.json","layers"),
        ("governance/economic_mechanisms_v2.json","engines"),
        ("governance/transversal_enrichment_v1.json","entries"),
        ("governance/shapiro_enrichment_v1.json","entries"),
        ("governance/investigation_result_v1.json","sections")]:
        ids.update(e["id"] for e in read(path)[key])
    ids.update("G-M"+str(i) for i in range(6))
    ids.update("E-G"+str(i) for i in range(7))
    ids.update("UX-G"+str(i) for i in range(5))
    result=validate(reg,q,families,ids)
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print("AUDIT_B3_SUMMARY="+json.dumps(result["summary"],sort_keys=True))
if __name__=="__main__":
    main()
