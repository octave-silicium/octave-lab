"""Compare declared model submissions and classical controls on the same frozen suite.
No inference call, no claim of blinded or independent evidence."""
import argparse,json
from pathlib import Path
from collections import Counter
from .document_benchmark import suite,assess,classic,digest
ROOT=Path(__file__).resolve().parents[1]/"research"/"PILOT-W001"
def classical_submission(d):
    return {"run_id":"W001-classic-v2.1","mode":"RULE_BASELINE","suite_sha256":digest(d),"configuration":{"implementation":"document_benchmark.classic v2.1"},"outputs":[{"id":c["id"],**classic(c,exception_aware=True)} for c in d["cases"]]}
def compare(d,g,subs):
    if not subs or len({s["run_id"] for s in subs})!=len(subs):raise ValueError("RUN_IDS")
    expected=g["expected"]
    reports=[assess(s,d,g) for s in subs]
    output_maps=[{o["id"]:o for o in s["outputs"]} for s in subs]
    def exact(out,ref):return out["decision"]==ref["decision"] and set(out["issues"])==set(ref["issues"])
    pairs=[]
    for i in range(len(subs)):
        for j in range(i+1,len(subs)):
            counts=Counter()
            for k,ref in expected.items():
                a,b=exact(output_maps[i][k],ref),exact(output_maps[j][k],ref)
                counts["both_correct" if a and b else "a_only" if a else "b_only" if b else "neither_correct"]+=1
            pairs.append({"a":subs[i]["run_id"],"b":subs[j]["run_id"],"counts":{k:counts[k] for k in ("both_correct","a_only","b_only","neither_correct")},"exact_difference_cases":counts["b_only"]-counts["a_only"]})
    return {"suite_sha256":digest(d),"cases":len(expected),"runs":reports,"paired":pairs,"scope":"DESCRIPTIVE_DEVELOPMENT_COMPARISON","independent_validation":False,"significance_or_generalization":None,"publication":"BLOCK_PUBLICATION"}
def main():
    p=argparse.ArgumentParser();p.add_argument("--cases",type=Path);p.add_argument("--gold",type=Path);p.add_argument("--submission",type=Path,action="append");a=p.parse_args()
    d,g=suite(a.cases,a.gold)
    paths=a.submission if a.submission else [ROOT/"gpt62_conversation_dev.json"] if a.cases is None else []
    subs=[classical_submission(d)]+[json.loads(path.read_text()) for path in paths]
    print(json.dumps(compare(d,g,subs),indent=2))
if __name__=="__main__":main()
