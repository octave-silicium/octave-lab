"""W001-v2: synthetic document packets, conservative conventional extraction.
No LLM, OCR, network, payment, or actual business process measurement."""
import argparse,csv,io,json,re,time,statistics
from pathlib import Path
from decimal import Decimal,InvalidOperation
from collections import Counter
from .invoice_benchmark import baseline,digest,evaluate

ROOT=Path(__file__).resolve().parents[1]/"research"/"PILOT-W001"
FIELDS={"invoice":("invoice_id","supplier","order_id","currency","quantity","unit_price","net","tax","total"),"order":("supplier","order_id","currency","quantity","unit_price"),"receipt":("quantity",)}
LABELS={k:k for fields in FIELDS.values() for k in fields}
LABELS.update({"numero facture":"invoice_id","fournisseur":"supplier","commande":"order_id","devise":"currency","quantite":"quantity","prix unitaire":"unit_price","ht":"net","tva":"tax","ttc":"total"})
def key(s):return " ".join(s.strip().casefold().replace("_"," ").split())
LABELS={key(k):v for k,v in LABELS.items()}
def parse_doc(doc):
    if doc["kind"] not in FIELDS:return None,"UNSUPPORTED_DOCUMENT"
    fields=FIELDS[doc["kind"]];text=doc["text"];pairs=[]
    if doc["format"]=="kv":
        for line in text.splitlines():
            if not line.strip():continue
            if ":" not in line:return None,"UNSUPPORTED_LAYOUT"
            a,b=line.split(":",1);pairs.append((a,b.strip()))
    elif doc["format"]=="csv":
        try:
            reader=list(csv.reader(io.StringIO(text),strict=True))
        except csv.Error:return None,"UNSUPPORTED_LAYOUT"
        if len(reader)!=2 or len(reader[0])!=len(reader[1]):return None,"UNSUPPORTED_LAYOUT"
        pairs=list(zip(*reader))
    else:return None,"UNSUPPORTED_LAYOUT"
    result={}
    for raw,value in pairs:
        name=LABELS.get(key(raw))
        if name not in fields:return None,"UNSUPPORTED_FIELD"
        if name in result:return None,"CONTRADICTORY_FIELD"
        if not value:return None,"MISSING_FIELD"
        if name=="quantity":
            if not re.fullmatch(r"\d{1,9}",value):return None,"INVALID_FIELD"
            value=int(value)
        elif name in {"unit_price","net","tax","total"}:
            value=value.replace(",",".")
            if not re.fullmatch(r"\d{1,10}(?:\.\d{1,2})?",value):return None,"INVALID_FIELD"
        result[name]=value
    if set(result)!=set(fields):return None,"MISSING_FIELD"
    return result,None
def classic(case):
    # Scope first: do not silently discard extra documents or instructions.
    docs=case["documents"]
    bykind={}
    for d in docs:
        if d["kind"] not in FIELDS:return {"decision":"ABSTAIN","issues":[]}
        if d["kind"] in bykind:return {"decision":"ABSTAIN","issues":[]}
        bykind[d["kind"]]=d
    if set(bykind)!=set(FIELDS):return {"decision":"REVIEW","issues":["MISSING_DOCUMENT"]}
    data={}
    for kind in FIELDS:
        row,err=parse_doc(bykind[kind])
        if err in {"MISSING_FIELD","CONTRADICTORY_FIELD"}:return {"decision":"REVIEW","issues":[err]}
        if err:return {"decision":"ABSTAIN","issues":[]}
        data[kind]=row
    return baseline({**data,"rules":case["rules"],"previous_invoice_ids":case["previous_invoice_ids"]})
def suite():
    d=json.loads((ROOT/"documents_v2.json").read_text());g=json.loads((ROOT/"documents_gold_v2.json").read_text())
    ids=[c["id"] for c in d["cases"]]
    if len(ids)!=len(set(ids)) or not ids or set(ids)!=set(g["expected"]) or digest(d)!=g["cases_sha256"]:raise ValueError("SUITE_INTEGRITY")
    return d,g
def assess(sub,d,g):
    r=evaluate(sub,d,g)
    expected=g["expected"];byid={o["id"]:o for o in sub["outputs"]}
    strata={}
    for case in d["cases"]:
        s=strata.setdefault(case["stratum"],Counter())
        out=byid[case["id"]];ref=expected[case["id"]]
        s["cases"]+=1;s["exact"]+=int(out["decision"]==ref["decision"] and set(out["issues"])==set(ref["issues"]))
        s["abstain_or_error"]+=int(out["decision"] in {"ABSTAIN","ERROR"})
        s["unsafe_accept"]+=int(out["decision"]=="ACCEPT" and ref["decision"]=="REVIEW")
    r.update({"scope":"SYNTHETIC_HETEROGENEOUS_TEXT_DEVELOPMENT_ONLY","strata":{k:dict(v) for k,v in strata.items()},"blind_test":False,"representative":False})
    if "cost_ledger" in sub:
        from .experiment_cost import cost_ledger
        r["cost_ledger"]=cost_ledger(list(expected),sub["cost_ledger"])
    else:r["cost_ledger"]=None
    # Legacy flat costs are declarations, not validated full costs.
    r["flat_cost_is_not_full_cost"]=True
    return r
def run_classic():
    d,g=suite()
    outputs=[];latencies=[]
    for case in d["cases"]:
        start=time.perf_counter_ns();out=classic(case);latencies.append(time.perf_counter_ns()-start)
        outputs.append({"id":case["id"],**out})
    sub={"run_id":"W001-text-classic-v2","mode":"RULE_BASELINE","suite_sha256":digest(d),"configuration":{"implementation":"document_benchmark.classic v2"},"outputs":outputs}
    r=assess(sub,d,g)
    r["local_compute_only"]={"cases":len(latencies),"median_ns":statistics.median(latencies),"max_ns":max(latencies),"timer":"perf_counter_ns","includes":"one in-memory parser and rules call per case; no I/O, review or integration","not_end_to_end":True}
    return r
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--submission",type=Path);a=p.parse_args()
    if a.submission:
        d,g=suite();result=assess(json.loads(a.submission.read_text()),d,g)
    else:result=run_classic()
    print(json.dumps(result,indent=2))
