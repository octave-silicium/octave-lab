"""LIMITATIONS-001 structural checks and retrospective evidence inventory.
No automated semantic closure. A candidate/source association is not a verified resolution.
"""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REG="governance/limitations_v1.json"
BASE_REG="9c9c5b54845c83595b7af94b5a4fc4e4ef839e8b"
PATTERN=re.compile(r"\blimit(?:e|es|ation|ations|ed|s)\b|\b(?:bloqu\w*|blocked|unqualified|pending|incomplete|non franchi\w*|non qualifi\w*|non valid\w*|non implément\w*|non réalis\w*|à qualifier|à compléter|à construire|à vérifier|à implémenter|reste\w* ouvert\w*|restent à|pas de|absence de|no causal|not a forecast|not estimated|no empirical|hors périmètre|aucun gate|scope limitation|publication.block)\b",re.I)
def require(x,msg):
    if not x:raise ValueError(msg)
def git(*args):
    return subprocess.check_output(["git",*args],cwd=ROOT).decode("utf-8")
def read(p):return json.loads((ROOT/p).read_text())
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def validate(r,arch,shapiro,old=None):
    es=r["entries"];ids={e["id"] for e in es};require(len(ids)==len(es),"DUPLICATE_ID")
    require(r["id"]=="LIMITATIONS-001" and es,"REGISTER")
    mids={m["id"] for m in arch["mechanisms"]};eng={e["id"] for e in arch["engines"]}
    by={e["id"]:e for e in es}
    require(old is None or {e["id"] for e in old["entries"]}<=ids,"SILENT_REMOVAL")
    if old:
        for e in old["entries"]:
            require(by[e["id"]]["origin"]==e["origin"],"ORIGIN_CHANGED:"+e["id"])
    for e in es:
        for key in ("id","type","origin","title","impact","target","remedy","acceptance","status","notes","review_status"):
            require(isinstance(e[key],str) and e[key].strip(),"EMPTY:"+key)
        require(e["status"] in ("OPEN","PARTIAL","BLOCKED","PERMANENT","RESOLVED","RETIRED_JUSTIFIED"),"STATUS")
        require(e["type"] in ("DATA","EMPIRICAL","METHOD","RIGHTS","PRODUCT","IMPLEMENTATION","INTRINSIC"),"TYPE")
        require(e["mechanisms"] and set(e["mechanisms"])<=mids and e["engines"] and set(e["engines"])<=eng,"MAPPING:"+e["id"])
        require(e["sources"] and all((ROOT/p).is_file() for p in e["sources"]),"SOURCE:"+e["id"])
        require(set(e["dependencies"])<=ids-{e["id"]},"DEPENDENCY:"+e["id"])
        require(type(e["publication_blocking"]) is bool and isinstance(e["blocked_claims"],list),"BLOCK_SCOPE")
        require(e["publication_blocking"]==bool(e["blocked_claims"]),"BLOCK_SCOPE")
        require(e["resolution_status"]==e["status"],"STATUS_SYNC")
        if e["type"]=="INTRINSIC":require(e["status"]=="PERMANENT","INTRINSIC_CLOSURE")
        if e["status"] in ("RESOLVED","RETIRED_JUSTIFIED"):
            require(e.get("reviewer") and e.get("review_date") and e.get("closure_reason") and e["closure_evidence"],"UNPROVEN_CLOSURE:"+e["id"])
            require(all(isinstance(x,dict) and x.get("path") and (ROOT/x["path"]).is_file() and x.get("criterion") and x.get("verification_ref") for x in e["closure_evidence"]),"CLOSURE_EVIDENCE")
            if e["status"]=="RESOLVED":require(all(by[d]["status"] in ("RESOLVED","RETIRED_JUSTIFIED","PERMANENT") for d in e["dependencies"]),"OPEN_DEPENDENCY")
    def visit(k,trail):
        require(k not in trail,"DEPENDENCY_CYCLE:"+k)
        for d in by[k]["dependencies"]:visit(d,trail|{k})
    for k in ids:visit(k,set())
    # A requirement is still tracked when no family association was made.
    obligation=lambda k,label,status,links:{"id":k,"label":label,"original_status":status,"linked_limitations":sorted(links),"qualification":"TO_VERIFY_FROM_ORIGINAL_CONTRACT"}
    obligations=[obligation(m["id"],m["name"],m["status"],[e["id"] for e in es if m["id"] in e["mechanisms"]]) for m in arch["mechanisms"]]
    obligations += [obligation(x["id"],x["concept"],x["status"],[e["id"] for e in es if set(x["mechanisms"])&set(e["mechanisms"])]) for x in shapiro["entries"]]
    obligations += [obligation(x["id"],x["name"],x["status"],[e["id"] for e in es if x["id"] in e["engines"]]) for x in arch["engines"]]
    obligations += [obligation(x["id"],x["name"],"ARCHITECTURE_TARGET",[e["id"] for e in es if any(m["layer"]==x["id"] and m["id"] in e["mechanisms"] for m in arch["mechanisms"])]) for x in arch["layers"]]
    obligations += [obligation("IF-%02d"%(i+1),x["from"]+" → "+x["to"]+": "+x["flow"],x["status"],[]) for i,x in enumerate(arch["interfaces"])]
    obligations += [obligation("G-M"+str(i),"Historical scientific gate","NOT_PROMOTED_BY_REGISTER",[]) for i in range(6)]
    obligations += [obligation("E-G"+str(i),"Economic scientific gate","NOT_PROMOTED_BY_REGISTER",[]) for i in range(7)]
    obligations += [obligation("UX-G"+str(i),"UX gate","NOT_PROMOTED_BY_REGISTER",[]) for i in range(5)]
    return obligations

def inventory(rev,entries):
    paths=git("ls-tree","-r","--name-only",rev).splitlines()
    paths=[p for p in paths if (p.startswith(("docs/","research/","governance/")) and p.endswith((".md",".json"))) or (p.startswith("pipeline/") and p.endswith(".py")) or p=="README.md"]
    paths=[p for p in paths if p not in (REG,"docs/LIMITATIONS-001.md") and not p.startswith("pipeline/limitations_")]
    files=[];candidates=[]
    for path in paths:
        raw=git("show",rev+":"+path)
        heading="";matches=0
        related=sorted(e["id"] for e in entries if path in e["sources"])
        for i,line in enumerate(raw.splitlines(),1):
            if line.startswith("#"):heading=line.strip()
            if not PATTERN.search(line):continue
            matches+=1
            candidates.append({"id":digest(path+"\0"+str(i)+"\0"+line)[:24],"path":path,"line":i,"heading":heading,"verbatim":line,"suggested_families":related,"status":"SEMANTIC_TRIAGE_PENDING"})
        files.append({"path":path,"sha256":digest(raw),"lines":len(raw.splitlines()),"candidate_count":matches,"related_families":related})
    return {"revision":rev,"files":files,"candidates":candidates}
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",default="limitations-audit.json");p.add_argument("--release-gate",action="store_true");args=p.parse_args()
    r=read(REG);arch=read("governance/economic_mechanisms_v2.json");sh=read("governance/shapiro_enrichment_v1.json")
    old=json.loads(git("show",BASE_REG+":"+REG))
    obligations=validate(r,arch,sh,old)
    baseline=inventory(r["baseline_commit"],r["entries"])
    head=git("rev-parse","HEAD").strip()
    current=inventory(head,r["entries"])
    initial={f["path"]:f["sha256"] for f in baseline["files"]};now={f["path"]:f["sha256"] for f in current["files"]}
    drift=[{"path":k,"status":"SOURCE_REVIEW_REQUIRED"} for k in sorted(set(initial)|set(now)) if initial.get(k)!=now.get(k)]
    blockers=[e["id"] for e in r["entries"] if e["publication_blocking"] and e["status"] not in ("RESOLVED","RETIRED_JUSTIFIED")]
    report={"register":r["id"],"status":"STRUCTURAL_CHECK_PASSED_SEMANTIC_TRIAGE_PENDING","baseline":baseline,"current":current,"source_drift":drift,"obligations":obligations,"open_publication_blockers":blockers,"release_status":"BLOCK_UNQUALIFIED_PUBLICATION","semantic_coverage":"NOT_CERTIFIED; lexical scan includes false positives and may miss implicit limitations"}
    Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    summary={"register":r["id"],"baseline_commit":r["baseline_commit"],"checked_commit":head,"families":len(r["entries"]),"by_status":{s:sum(e["status"]==s for e in r["entries"]) for s in sorted({e["status"] for e in r["entries"]})},"baseline_files":len(baseline["files"]),"baseline_lines":sum(x["lines"] for x in baseline["files"]),"baseline_candidates":len(baseline["candidates"]),"current_files":len(current["files"]),"current_candidates":len(current["candidates"]),"obligation_count":len(obligations),"unlinked_mechanisms":[x["id"] for x in obligations if re.fullmatch(r"M\d{3}",x["id"]) and not x["linked_limitations"]],"source_drift":drift,"publication_blockers":len(blockers),"release_status":report["release_status"],"semantic_triage":"PENDING"}
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if args.release_gate:raise SystemExit("BLOCK_UNQUALIFIED_PUBLICATION: scope-specific independent review required; initial register cannot authorize release")
if __name__=="__main__":main()
