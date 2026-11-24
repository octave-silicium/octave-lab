"""W001 evaluation v0.1. Synthetic structured documents, not observed invoices.
A deterministic rules baseline is evaluated alongside future human/AI submissions.
No real participant or model result is fabricated.
"""
import argparse,hashlib,json,re,statistics
from decimal import Decimal,InvalidOperation
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]/"research"/"PILOT-W001"
D=Decimal
def load(name):return json.loads((ROOT/name).read_text())
def digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def amount(x):
    if not isinstance(x,str) or not re.fullmatch(r"\d{1,10}(?:\.\d{1,2})?",x):raise ValueError("AMOUNT")
    return D(x)
def count(x):
    if type(x)!=int or x<0:raise ValueError("QUANTITY")
    return x
def baseline(case):
    """Exact deterministic check of a narrow, defined synthetic rule set."""
    i,p,r=case["invoice"],case["order"],case["receipt"]
    issues=set()
    for k in ("invoice_id","supplier","order_id","currency","quantity","unit_price","net","tax","total"):
        if k not in i or i[k] is None or i[k]=="":issues.add("MISSING_FIELD")
    if not issues:
        if i["supplier"]!=p["supplier"]:issues.add("SUPPLIER_MISMATCH")
        if i["order_id"]!=p["order_id"]:issues.add("ORDER_MISMATCH")
        if i["currency"]!=p["currency"]:issues.add("CURRENCY_MISMATCH")
        if count(i["quantity"])!=count(p["quantity"]) or count(i["quantity"])!=count(r["quantity"]):issues.add("QUANTITY_MISMATCH")
        if amount(i["unit_price"])!=amount(p["unit_price"]):issues.add("PRICE_MISMATCH")
        if amount(i["net"])!=count(i["quantity"])*amount(i["unit_price"]):issues.add("NET_MISMATCH")
        if amount(i["tax"])!=(amount(i["net"])*D(case["rules"]["tax_rate"])).quantize(D("0.01")):issues.add("TAX_MISMATCH")
        if amount(i["total"])!=amount(i["net"])+amount(i["tax"]):issues.add("TOTAL_MISMATCH")
        if i["invoice_id"] in case["previous_invoice_ids"]:issues.add("DUPLICATE")
    return {"decision":"REVIEW" if issues else "ACCEPT","issues":sorted(issues)}
def validated_suite():
    data=load("cases.json");gold=load("gold.json")
    cases=data["cases"];keys=[x["id"] for x in cases]
    if len(keys)!=len(set(keys)) or set(keys)!=set(gold["expected"]) or gold["cases_sha256"]!=digest(data):raise ValueError("SUITE_INTEGRITY")
    return data,gold
def evaluate(submission,data,gold):
    if submission.get("suite_sha256")!=digest(data):raise ValueError("SUITE_HASH")
    mode=submission.get("mode")
    if mode not in {"RULE_BASELINE","HUMAN","AI","HYBRID"}:raise ValueError("MODE")
    if not isinstance(submission.get("run_id"),str) or not submission["run_id"].strip() or not isinstance(submission.get("configuration"),dict) or not submission["configuration"]:raise ValueError("RUN_METADATA")
    config=submission["configuration"]
    if mode in {"AI","HYBRID"} and not all(isinstance(config.get(k),str) and config[k].strip() for k in ("model_version","prompt_sha256","tool_policy","execution_date")):raise ValueError("AI_METADATA")
    if mode in {"HUMAN","HYBRID"} and not isinstance(config.get("participant_code"),str):raise ValueError("PARTICIPANT")
    expected=gold["expected"];seen=set();c=Counter();scores=[];times=[];costs=[]
    for out in submission["outputs"]:
        k=out["id"]
        if k not in expected or k in seen:raise ValueError("CASE_ID")
        seen.add(k);ref=expected[k]
        decision=out.get("decision");issues=out.get("issues")
        if decision not in {"ACCEPT","REVIEW","ERROR","ABSTAIN"} or not isinstance(issues,list) or any(not isinstance(x,str) for x in issues) or len(issues)!=len(set(issues)):raise ValueError("OUTPUT")
        c["cases"]+=1
        if decision==ref["decision"]:c["decision_correct"]+=1
        if decision==ref["decision"] and set(issues)==set(ref["issues"]):c["exact_case_correct"]+=1
        if ref["decision"]=="REVIEW" and decision=="ACCEPT":c["false_accept"]+=1
        if ref["decision"]=="ACCEPT" and decision=="REVIEW":c["false_review"]+=1
        if decision in {"ABSTAIN","ERROR"}:c["abstain_or_error"]+=1
        c["issue_tp"]+=len(set(issues)&set(ref["issues"]))
        c["issue_fp"]+=len(set(issues)-set(ref["issues"]))
        c["issue_fn"]+=len(set(ref["issues"])-set(issues))
        # Optional measured metrics require a trace reference; no imputation, no estimate.
        for field,target in (("wall_seconds",times),("total_cost_eur",costs)):
            if out.get(field) is not None:
                try:v=D(str(out[field]))
                except InvalidOperation:raise ValueError("MEASUREMENT")
                if not v.is_finite() or v<0 or not isinstance(out.get("measurement_ref"),str) or not out["measurement_ref"].strip():raise ValueError("MEASUREMENT")
                target.append(v)
    if seen!=set(expected):raise ValueError("INCOMPLETE_SUITE")
    n=len(seen);positive=sum(x["decision"]=="REVIEW" for x in expected.values())
    def ratio(x,y):return x/y if y else None
    return {"run_id":submission["run_id"],"mode":mode,"suite_sha256":digest(data),"cases":n,"counts":{k:c[k] for k in ("decision_correct","exact_case_correct","false_accept","false_review","abstain_or_error","issue_tp","issue_fp","issue_fn")},"decision_accuracy":ratio(c["decision_correct"],n),"exact_case_accuracy":ratio(c["exact_case_correct"],n),"false_accept_rate_on_anomalies":ratio(c["false_accept"],positive),"issue_precision":ratio(c["issue_tp"],c["issue_tp"]+c["issue_fp"]),"issue_recall":ratio(c["issue_tp"],c["issue_tp"]+c["issue_fn"]),"measured_wall_cases":len(times),"median_wall_seconds":str(statistics.median(times)) if len(times)==n else None,"measured_cost_cases":len(costs),"total_cost_eur":str(sum(costs)) if len(costs)==n else None,"scope":"SYNTHETIC_STRUCTURED_CONTROL_ONLY","measurement_authentication":"NOT_INDEPENDENTLY_VERIFIED","production_readiness":False,"employment_impact":None,"publication":"BLOCK_PUBLICATION"}
def run_baseline():
    data,gold=validated_suite()
    sub={"run_id":"W001-rules-v1","mode":"RULE_BASELINE","configuration":{"implementation":"invoice_benchmark.baseline v1"},"suite_sha256":digest(data),"outputs":[{"id":case["id"],**baseline(case)} for case in data["cases"]]}
    return evaluate(sub,data,gold)
def main():
    p=argparse.ArgumentParser();p.add_argument("--submission",type=Path);a=p.parse_args()
    if a.submission:
        data,gold=validated_suite();r=evaluate(json.loads(a.submission.read_text()),data,gold)
    else:r=run_baseline()
    print(json.dumps(r,indent=2))
if __name__=="__main__":main()
