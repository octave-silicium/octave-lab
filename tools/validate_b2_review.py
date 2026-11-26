"""Bind first-pass review dispositions to the exact pinned B1 groups.
Does not update the limitations register or close any group."""
import hashlib
import json
import argparse
from pathlib import Path
from collections import Counter
from tools.limitation_triage import build

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "governance" / "audit_master_b2_review_v1.json"

def validate(reg, queue, known):
    p0 = [g for g in queue["groups"] if g["priority"] == "P0_REVIEW"]
    ids = "\n".join(g["group_id"] for g in p0)
    if hashlib.sha256(ids.encode()).hexdigest() != reg["p0_order_sha256"]:
        raise ValueError("P0 order drift")
    if queue["summary"]["revision"] != reg["queue_revision"]:
        raise ValueError("Wrong queue revision")
    if reg["publication_authorized"] is not False or queue["summary"]["publication_authorized"] is not False:
        raise ValueError("Publication authorization forbidden")
    rows = reg["rows"]
    if [r["ordinal"] for r in rows] != list(range(1, len(p0)+1)):
        raise ValueError("Incomplete or duplicated review ordinal")
    allowed = {"HISTORICAL_OR_SCOPED_EVIDENCE","BINDING_CONTRACT","ACTIVE_GAP",
               "CODE_GUARD_OR_SCOPE_DECLARATION","SCOPED_EXCEPTION","LEXICAL_FALSE_POSITIVE_FOR_SECURITY"}
    out = []
    for r, g in zip(rows, p0):
        if (r["disposition"] not in allowed or not r["rationale"].strip()
                or not r["candidate_families"] or not set(r["candidate_families"]) <= known
                or r["closure_authorized"] is not False
                or r["verification_status"] != "CONTEXT_AND_EVIDENCE_PENDING"):
            raise ValueError("Invalid disposition")
        out.append({**r, "group_id": g["group_id"],
                    "members": [{k:m[k] for k in ("id","path","line")} for m in g["members"]]})
    return {"rows":out,"summary":{
        "first_pass_reviewed":len(out),"p0_occurrences":sum(len(r["members"]) for r in out),
        "other_groups_pending":len(queue["groups"])-len(out),
        "context_and_evidence_pending":len(out),"closure_authorized":0,
        "dispositions":dict(sorted(Counter(r["disposition"] for r in out).items())),
        "publication_authorized":False}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    a=p.parse_args()
    reg=json.loads(REGISTER.read_text(encoding="utf-8"))
    queue=build(reg["queue_revision"])
    known={e["id"] for e in json.loads((ROOT/"governance"/"limitations_v1.json").read_text())["entries"]}
    out=validate(reg,queue,known)
    a.output.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print("AUDIT_B2_SUMMARY="+json.dumps(out["summary"],sort_keys=True))

if __name__=="__main__":
    main()
