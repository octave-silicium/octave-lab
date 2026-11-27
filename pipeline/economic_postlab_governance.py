"""POSTLAB-FOLLOWUP-001: structural coverage and milestone receipt checks.
Not an empirical validator; no publication or gate promotion.
"""
import argparse
import json
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
MAIN="governance/postlab_contradictory_v1.json"
DETAIL="governance/postlab_contradictory_detail_v1.json"
LEDGER="governance/postlab_followup_v1.json"

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def present(value):
    return isinstance(value,str) and bool(value.strip())

def expected(main, detail):
    out={}
    def add(i,k,l):
        require(i not in out,"DUPLICATE_SOURCE:"+i)
        out[i]=(k,l)
    for a in detail["axes"]:
        for field,kind,code in (("phenomena","phenomenon","PH"),("models","model","MO"),("data_sources","data","DA"),("outputs","output","OU")):
            for n,label in enumerate(a[field],1):
                add(f'{a["id"]}-{code}{n:02d}',kind,label)
    for b in detail["bibliography"]:
        add(b["id"],"bibliography",b["author"]+" — "+b["title"])
    for n,s in enumerate(detail["examples"],1):
        add(f"EX{n:02d}","example",s)
    for field,kind,key in (("axes","axis","concept"),("entries","objection","concept"),("scenarios","scenario","name")):
        for x in main[field]:
            add(x["id"],kind,x[key])
    return out

def evidence_ok(e):
    return isinstance(e,dict) and all(present(e.get(k)) for k in ("ref","criterion","date","reviewer"))

def validate(main,detail,ledger):
    exp=expected(main,detail)
    entries=ledger["entries"]
    by={e["id"]:e for e in entries}
    require(len(by)==len(entries),"DUPLICATE_LEDGER")
    require(set(by)==set(exp),"MISSING_OR_UNKNOWN:"+str(sorted(set(by)^set(exp))))
    require(ledger["id"]=="POSTLAB-FOLLOWUP-001","REGISTER")
    for i,e in by.items():
        require((e["kind"],e["label"])==exp[i],"LABEL_OR_KIND_CHANGED:"+i)
        require(e["priority"] in ("P0","P1","P2") and e["target_stages"] and present(e["review_trigger"]),"SCHEDULING:"+i)
        require(present(e["next_action"]),"NEXT_ACTION:"+i)
        require(e["status"] in ("OPEN","IN_PROGRESS","BLOCKED","DEFERRED","COMPLETE"),"STATUS:"+i)
        require(set(e["steps"])==set(ledger["steps_by_kind"][e["kind"]]),"STEPS:"+i)
        for k,s in e["steps"].items():
            require(s["status"] in ("PENDING","IN_PROGRESS","BLOCKED","DONE","NOT_APPLICABLE_JUSTIFIED"),"STEP_STATUS:"+i+":"+k)
            if s["status"]=="DONE":
                require(s["evidence"] and all(evidence_ok(x) for x in s["evidence"]),"UNPROVEN_DONE:"+i+":"+k)
            if s["status"]=="NOT_APPLICABLE_JUSTIFIED":
                require(present(s.get("reason")) and s["evidence"] and all(evidence_ok(x) for x in s["evidence"]),"UNPROVEN_NA:"+i+":"+k)
            if s["status"]=="BLOCKED":
                require(present(s.get("reason")) and present(s.get("next_action")),"UNEXPLAINED_BLOCK:"+i+":"+k)
        if e["status"] in ("BLOCKED","DEFERRED"):
            require(present(e.get("reason")) and present(e.get("dependency")),"UNEXPLAINED_DEFERRAL:"+i)
        if e["status"]=="COMPLETE":
            require(all(s["status"] in ("DONE","NOT_APPLICABLE_JUSTIFIED") for s in e["steps"].values()) and evidence_ok(e.get("closure_review")),"UNPROVEN_CLOSURE:"+i)
    return {"items":len(entries),"by_kind":dict(Counter(e["kind"] for e in entries)),"by_status":dict(Counter(e["status"] for e in entries)),"scientific_validation":False}

def template(ledger,milestone):
    return {"id":milestone,"status":"UNREVIEWED","date":"","reviewer":"","scope":"","baseline_commit":"","next_milestone":"","dispositions":[{"id":e["id"],"status":"UNREVIEWED","reason":"","next_action":"","evidence":[]} for e in ledger["entries"]]}

def validate_receipt(ledger,receipt):
    for k in ("id","date","reviewer","scope","baseline_commit","next_milestone"):
        require(present(receipt.get(k)),"RECEIPT_FIELD:"+k)
    require(receipt.get("status")=="REVIEWED","UNREVIEWED_RECEIPT")
    rows=receipt["dispositions"]
    ids=[x["id"] for x in rows]
    require(len(ids)==len(set(ids)) and set(ids)=={e["id"] for e in ledger["entries"]},"RECEIPT_COVERAGE")
    for r in rows:
        require(r["status"] in ("PROGRESSED","REVIEWED_OPEN","BLOCKED","DEFERRED","OUT_OF_SCOPE"),"RECEIPT_STATUS:"+r["id"])
        require(present(r.get("reason")) and present(r.get("next_action")),"RECEIPT_REASON_NEXT:"+r["id"])
        if r["status"]=="PROGRESSED":
            require(r["evidence"] and all(evidence_ok(x) for x in r["evidence"]),"RECEIPT_PROOF:"+r["id"])
    return {"milestone":receipt["id"],"dispositions":len(rows),"by_status":dict(Counter(r["status"] for r in rows)),"scientific_validation":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--template")
    p.add_argument("--receipt")
    p.add_argument("--output")
    a=p.parse_args()
    ledger=read(ROOT/LEDGER)
    result=validate(read(ROOT/MAIN),read(ROOT/DETAIL),ledger)
    if a.template:
        result=template(ledger,a.template)
    if a.receipt:
        result=validate_receipt(ledger,read(a.receipt))
    raw=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if a.output: Path(a.output).write_text(raw,encoding="utf-8")
    else: print(raw,end="")

if __name__=="__main__":
    main()
