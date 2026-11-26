"""Generate a non-authoritative traceability projection from pinned public contracts.
Preserve source records and statuses. No inferred evidence or qualification."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from pipeline.limitations_audit import git

SPECS = {
 "architecture": ("economic_mechanisms_v2.json", ("layers","engines","mechanisms","interfaces","cross_cutting","references","limits")),
 "transversal": ("transversal_enrichment_v1.json", ("entries","pre_milestone_controls","architecture_invariants","coverage_policy")),
 "shapiro": ("shapiro_enrichment_v1.json", ("entries","architecture_invariants","thesis")),
 "result": ("investigation_result_v1.json", ("depth_levels","sections","claim_required","claim_types","acceptance","coverage")),
 "prospective": ("multi_order_prospective_v1.json", ("mandatory_dimensions","scenario_families","node_path_required","scenario_required","stop_rules","acceptance","distinctions","scope")),
 "engineering": ("engineering_assurance_v1.json", ("requirements",)),
 "limitations": ("limitations_v1.json", ("entries","dependency_semantics")),
 "rights": ("source_rights.json", ("sources",)),
 "refresh": ("refresh_sources.json", ("sources",)),
 "terminology": ("terminology_fr_v1.json", ("entries",)),
}
GATES = {
 "G-M": ("docs/METH-003.md", r"^\|\s*(G-M[0-5])\s*\|"),
 "UX-G": ("docs/UX-001.md", r"^(UX-G[0-4])\s*:"),
 "V": ("docs/PRODUCT-FIRST-001.md", r"^\|\s*(V[0-5])\s*\|"),
}
def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",",":")).encode()).hexdigest()

def project_document(namespace, path, obj, fields, revision):
    rows=[]
    for field in fields:
        val=obj[field]
        if isinstance(val,list):
            items=[(str(i),v) for i,v in enumerate(val)]
        elif isinstance(val,dict):
            items=list(val.items())
        else:
            items=[("value",val)]
        for key,value in items:
            if isinstance(value,dict) and "id" in value:
                local=str(value["id"])
            elif not isinstance(val,list):
                local=key
            else:
                # No position-based identity for unnamed arrays. Edits require reconciliation.
                local=digest(value)
            pointer="/"+field+("/"+key.replace("~","~0").replace("/","~1") if isinstance(val,(list,dict)) else "")
            rows.append({"id":namespace+":"+field+":"+local,
                         "namespace":namespace,"category":field,
                         "source":{"path":path,"pointer":pointer,"commit":revision,
                                   "version":obj.get("version"),"sha256":digest(value)},
                         "record":value,
                         "original_status":value.get("status") if isinstance(value,dict) else None,
                         "contract_status":obj.get("status"),
                         "traceability_status":"SOURCE_BOUND_EVIDENCE_NOT_ADJUDICATED",
                         "qualification_promoted":False})
    return rows

def validate(rows):
    ids=[r["id"] for r in rows]
    if len(ids)!=len(set(ids)): raise ValueError("Duplicate canonical row")
    for r in rows:
        if r["qualification_promoted"] is not False: raise ValueError("Promotion forbidden")
        if r["source"]["sha256"]!=digest(r["record"]): raise ValueError("Source drift")
    return rows

def build(ref):
    revision=git("rev-parse","--verify",ref+"^{commit}").strip()
    rows=[]; docs=[]
    for ns,(name,fields) in SPECS.items():
        path="governance/"+name
        raw=git("show",revision+":"+path)
        obj=json.loads(raw)
        part=project_document(ns,path,obj,fields,revision)
        rows.extend(part)
        docs.append({"path":path,"version":obj.get("version"),"sha256":hashlib.sha256(raw.encode()).hexdigest(),
                     "rows":len(part),"metadata_and_unprojected_fields":sorted(set(obj)-set(fields))})
    for prefix,(path,pat) in GATES.items():
        raw=git("show",revision+":"+path)
        found=[]
        for i,line in enumerate(raw.splitlines(),1):
            m=re.match(pat,line)
            if m:
                gid=m.group(1); found.append(gid)
                rows.append({"id":"gate:"+gid,"namespace":"gate","category":prefix,
                             "source":{"path":path,"line":i,"commit":revision,"sha256":digest(line)},
                             "record":line,"original_status":None,"contract_status":None,
                             "traceability_status":"SOURCE_BOUND_EVIDENCE_NOT_ADJUDICATED","qualification_promoted":False})
        expected=[prefix+str(i) for i in range(5 if prefix=="UX-G" else 6)]
        if sorted(found)!=sorted(expected): raise ValueError("Gate coverage "+prefix+repr(found))
    # Economic gates share one normative paragraph: retain it exactly, no fabricated split.
    path="docs/ARCH-002.md"; raw=git("show",revision+":"+path)
    matches=[(i,line) for i,line in enumerate(raw.splitlines(),1) if all("E-G"+str(k)+" :" in line for k in range(7))]
    if len(matches)!=1: raise ValueError("Economic gate paragraph drift")
    i,line=matches[0]
    for k in range(7):
        rows.append({"id":"gate:E-G"+str(k),"namespace":"gate","category":"E-G",
                     "source":{"path":path,"line":i,"commit":revision,"sha256":digest(line)},
                     "record":line,"original_status":None,"contract_status":None,
                     "traceability_status":"SOURCE_BOUND_EVIDENCE_NOT_ADJUDICATED","qualification_promoted":False})
    validate(rows)
    # Typed, declared relationships only, no equivalence or coverage inferred from a file reference.
    lookup={}
    for r in rows:
        v=r["record"]
        if isinstance(v,dict) and "id" in v:
            lookup.setdefault(v["id"],[]).append(r["id"])
    edges=[]; unresolved=[]
    for r in rows:
        v=r["record"]
        if not isinstance(v,dict): continue
        for key in ("mechanisms","engines","limitations","dependencies","layer","from","to"):
            values=v.get(key,[])
            if isinstance(values,str): values=[values]
            if not isinstance(values,list): continue
            for target in values:
                if not isinstance(target,str): continue
                matches=lookup.get(target,[])
                edge={"source":r["id"],"field":key,"declared_target":target}
                if len(matches)==1: edges.append({**edge,"target":matches[0]})
                else: unresolved.append({**edge,"matches":matches})
    # Cross-registry coverage comparisons are obligations to inspect, not gate results.
    result=json.loads(git("show",revision+":governance/investigation_result_v1.json"))
    arch=json.loads(git("show",revision+":governance/economic_mechanisms_v2.json"))
    coverage=result["coverage"]
    comparisons={}
    for key,kind in (("mechanism_ids","mechanisms"),("layers","layers"),("engines","engines")):
        expected={v["id"] for v in arch[kind]}
        actual=set(coverage[key])
        comparisons[kind]={"missing":sorted(expected-actual),"unexpected":sorted(actual-expected)}
    summary={"revision":revision,"rows":len(rows),"by_namespace":dict(sorted(Counter(r["namespace"] for r in rows).items())),
             "sources":len(docs),"declared_edges":len(edges),"unresolved_declared_edges":len(unresolved),
             "result_base_coverage":comparisons,"qualification_promoted":0,"publication_authorized":False}
    return {"summary":summary,"sources":docs,"rows":rows,"declared_edges":edges,"unresolved_edges":unresolved,
            "limits":["Projection of selected canonical public JSON fields and gate definitions; other document paragraphs and private requirements remain outside.",
                      "Rows overlap and include vocabulary, data sources and criteria; not a mechanism count.",
                      "References and source status are not proof of implementation. Unnamed array identity changes when its content changes.",
                      "Review source revisions, evidence, runtime applicability and rights separately."]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ref",required=True)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    out=build(a.ref)
    a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("AUDIT_C_SUMMARY="+json.dumps(out["summary"],sort_keys=True))
if __name__=="__main__": main()
