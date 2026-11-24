"""O*NET task ratings: native scales only, no duration or exposure inference."""
import csv,hashlib,io,json
from collections import Counter,defaultdict
from decimal import Decimal,InvalidOperation
from urllib.request import Request,urlopen
from urllib.parse import urlsplit
from . import work_graph as wg
MISSING={"","n/a","na","null"}
FIELDS={"O*NET-SOC Code","Task ID","Scale ID","Scale Name","Category","Data Value","N","Standard Error","Lower CI Bound","Upper CI Bound","Recommend Suppress","Date","Domain Source"}
def missing(x):return x.strip().casefold() in MISSING
def numeric(x):
    if missing(x):return None
    v=Decimal(x)
    if not v.is_finite():raise ValueError("NONFINITE")
    return v
def fetch(name):
    url=wg.BASE+name+".csv"
    with urlopen(Request(url,headers={"User-Agent":"OctaveLab/0.6 research"}),timeout=90) as r:
        if urlsplit(r.geturl()).hostname!="www.onetcenter.org":raise ValueError("UNEXPECTED_HOST")
        raw=r.read(100_000_001)
    if not raw or len(raw)>100_000_000:raise ValueError("SIZE")
    return raw
def rows(raw,required):
    r=csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
    if not required<=set(r.fieldnames or []) or len(set(r.fieldnames or []))!=len(r.fieldnames or []):raise ValueError("SCHEMA")
    for n,x in enumerate(r,2):
        if None in x or any(v is None for v in x.values()):raise ValueError("ROW_SHAPE")
        yield n,x
class Ratings:
    def __init__(self,graph,raw,categories):
        self.graph=graph;self.by_task=defaultdict(list);self.counts=Counter();self.issues=Counter();self.orphans=[];self.keys=set()
        self.category={r["Category"]:r["Category Description"] for _,r in rows(categories,{"Scale ID","Category","Category Description"}) if r["Scale ID"]=="FT"}
        if set(self.category)!={str(i) for i in range(1,8)}:raise ValueError("FREQUENCY_CATEGORIES")
        self.manifest={name:{"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b),"url":wg.BASE+name+".csv"} for name,b in (("task_ratings",raw),("task_categories",categories))}
        for n,r in rows(raw,FIELDS):
            uid=f'onet:{wg.VERSION}:task:{r["O*NET-SOC Code"]}:{r["Task ID"]}'
            scale=r["Scale ID"];cat="" if missing(r["Category"]) else r["Category"]
            if scale not in {"IM","RT","FT"} or (scale=="FT" and cat not in self.category) or (scale!="FT" and cat):raise ValueError("SCALE_CATEGORY")
            # Reject duplicate native scale/category cells, not average them.
            key=(uid,scale,cat)
            if key in self.keys:raise ValueError("DUPLICATE_RATING")
            self.keys.add(key)
            val=numeric(r["Data Value"]);N=numeric(r["N"])
            se=numeric(r["Standard Error"]);lo=numeric(r["Lower CI Bound"]);hi=numeric(r["Upper CI Bound"])
            flag=r["Recommend Suppress"].strip().upper()
            if val is not None and not (Decimal(1 if scale=="IM" else 0)<=val<=Decimal(5 if scale=="IM" else 100)):raise ValueError("SCALE_RANGE")
            if N is not None and (N<0 or N!=N.to_integral_value()) or se is not None and se<0 or lo is not None and hi is not None and lo>hi:raise ValueError("UNCERTAINTY")
            self.counts[scale]+=1
            status="WITHHELD" if flag=="Y" or val is None else "REVIEW_REQUIRED" if flag!="N" else "DESCRIPTIVE_ONLY"
            if uid not in graph.nodes:
                self.orphans.append((n,r));self.issues["ORPHAN_TASK"]+=1;continue
            if r.get("Task") and r["Task"]!=graph.nodes[uid]["label"]:
                self.issues["LABEL_MISMATCH"]+=1;status="WITHHELD"
            self.issues[status]+=1
            visible=status=="DESCRIPTIVE_ONLY"
            self.by_task[uid].append({"scale":scale,"scale_name":r["Scale Name"],"category":cat or None,"category_label":self.category.get(cat),"value":str(val) if visible else None,"n":str(N) if N is not None else None,"standard_error":str(se) if visible and se is not None else None,"lower_ci":str(lo) if visible and lo is not None else None,"upper_ci":str(hi) if visible and hi is not None else None,"flag":flag,"date":r["Date"],"domain_source":r["Domain Source"],"status":status,"row":n,"member":"task_ratings","source_sha256":self.manifest["task_ratings"]["sha256"]})
    def task(self,uid):
        if uid not in self.graph.nodes or self.graph.nodes[uid]["kind"]!="task":raise ValueError("TASK")
        return {"task":uid,"ratings":self.by_task.get(uid,[]),"sources":self.manifest,"scope":"US_TASK_SURVEY_NOT_TIME_SHARE","duration_seconds":None,"publication":"BLOCK_PUBLICATION"}
    def audit(self):
        groups=Counter();complete=0;review=0
        for records in self.by_task.values():
            present={r["scale"] for r in records}
            for k in present:groups[k]+=1
            ft=[r for r in records if r["scale"]=="FT"]
            if len(ft)==7 and all(r["value"] is not None for r in ft):
                complete+=1
                if abs(sum(Decimal(r["value"]) for r in ft)-100)>Decimal("0.1"):review+=1
        return {"rows":sum(self.counts.values()),"rows_by_scale":dict(self.counts),"tasks_with_ratings":len(self.by_task),"tasks_without_ratings":sum(n["kind"]=="task" for n in self.graph.nodes.values())-len(self.by_task),"tasks_by_scale":dict(groups),"quality_and_issues":dict(self.issues),"complete_visible_ft_distributions":complete,"ft_sum_review":review,"source_manifest":self.manifest,"scope":"US_NATIVE_SCALES_ONLY","duration_weights":None,"publication":"BLOCK_PUBLICATION"}
if __name__=="__main__":
    g=wg.build();r=Ratings(g,fetch("task_ratings"),fetch("task_categories"))
    print(json.dumps({"ratings":r.audit(),"pilot":r.task("onet:31.0:task:43-3031.00:2486")},indent=2))
