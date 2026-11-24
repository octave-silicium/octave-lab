"""G2 v0.1: native O*NET 31.0 occupation/task/activity graph, no inferred edges."""
import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request,urlopen

VERSION="31.0"
SCHEME="ONET-SOC-2019"
BASE="https://www.onetcenter.org/dl_files/database/db_31_0_csv/"
ATTRIBUTION="Includes information from the O*NET 31.0 Database by the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA), under CC BY 4.0. O*NET® is a trademark of USDOL/ETA. Octave Lab has reorganized the data; USDOL/ETA has not approved, endorsed or tested these modifications."
LICENSE="https://creativecommons.org/licenses/by/4.0/"
FILES={
 "occupation_data":(1016,{"O*NET-SOC Code","Title","Description"}),
 "task_statements":(18838,{"O*NET-SOC Code","Task ID","Task","Task Type"}),
 "gwas_to_iwas_to_dwas":(2087,{"GWA Element ID","GWA Element Name","IWA Element ID","IWA Element Name","DWA Element ID","DWA Element Name"}),
 "tasks_to_dwas":(24087,{"O*NET-SOC Code","Task ID","DWA Element ID"}),
}
def fetch(name):
    with urlopen(Request(BASE+name+".csv",headers={"User-Agent":"OctaveLab/0.1 research"}),timeout=45) as response:
        raw=response.read(20_000_001)
    if len(raw)>20_000_000:raise ValueError("SIZE")
    return raw

def parse(name,raw,strict=True):
    reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    required=FILES[name][1]
    if not required<=set(reader.fieldnames or []) or len(set(reader.fieldnames or []))!=len(reader.fieldnames or []):
        raise ValueError("SCHEMA_"+name)
    rows=list(reader)
    if strict and len(rows)!=FILES[name][0]:raise ValueError("ROW_COUNT_"+name)
    if any(None in r or any(r[k] is None for k in required) for r in rows):raise ValueError("ROW_SHAPE_"+name)
    return rows

class Graph:
    def __init__(self,tables,manifest):
        self.manifest=manifest
        self.nodes={}
        self.edges={}
        self.by_occ=defaultdict(list)
        self.by_task=defaultdict(list)
        def node(kind,key,label,table,row,extra=None):
            if not key or not label.strip():raise ValueError("EMPTY_NODE")
            uid=f"onet:{VERSION}:{kind}:{key}"
            data={"id":uid,"kind":kind,"native_id":key,"label":label,"source":table,
                  "source_row":row,"status":"SOURCE_DOCUMENTED","extras":extra or {}}
            if uid in self.nodes:
                previous=self.nodes[uid]
                if any(previous[k]!=data[k] for k in ("kind","native_id","label","extras")):raise ValueError("CONFLICTING_NODE")
            else:self.nodes[uid]=data
            return uid
        def edge(a,b,kind,table,row):
            if a not in self.nodes or b not in self.nodes:raise ValueError("DANGLING_EDGE_"+kind)
            key=(a,b,kind)
            if key in self.edges:
                # Hierarchy rows can repeat parent links legitimately.
                if kind not in {"GWA_IWA"}:raise ValueError("DUPLICATE_EDGE_"+kind)
                return
            self.edges[key]={"from":a,"to":b,"kind":kind,"source":table,"source_row":row,"status":"SOURCE_DOCUMENTED"}
        def uid(kind,k):return f"onet:{VERSION}:{kind}:{k}"
        for i,r in enumerate(tables["occupation_data"],2):
            code=r["O*NET-SOC Code"]
            if not re.fullmatch(r"\d{2}-\d{4}\.\d{2}",code):raise ValueError("OCCUPATION_CODE")
            if uid("occupation",code) in self.nodes:raise ValueError("DUPLICATE_OCCUPATION")
            node("occupation",code,r["Title"],"occupation_data",i,{"description":r["Description"],"geography":"US","scheme":SCHEME})
        for i,r in enumerate(tables["task_statements"],2):
            code,tid=r["O*NET-SOC Code"],r["Task ID"]
            if not tid.isdigit():raise ValueError("TASK_ID")
            task=node("task",code+":"+tid,r["Task"],"task_statements",i,{k:r[k] for k in ("Task Type","Date","Domain Source","Incumbents Responding") if k in r})
            edge(uid("occupation",code),task,"OCCUPATION_TASK","task_statements",i)
            self.by_occ[code].append(task)
        for i,r in enumerate(tables["gwas_to_iwas_to_dwas"],2):
            ids=[]
            for kind,prefix in (("gwa","GWA"),("iwa","IWA"),("dwa","DWA")):
                ids.append(node(kind,r[prefix+" Element ID"],r[prefix+" Element Name"],"gwas_to_iwas_to_dwas",i))
            edge(ids[0],ids[1],"GWA_IWA","gwas_to_iwas_to_dwas",i)
            edge(ids[1],ids[2],"IWA_DWA","gwas_to_iwas_to_dwas",i)
        for i,r in enumerate(tables["tasks_to_dwas"],2):
            a=uid("task",r["O*NET-SOC Code"]+":"+r["Task ID"])
            b=uid("dwa",r["DWA Element ID"])
            edge(a,b,"TASK_DWA","tasks_to_dwas",i)
            self.by_task[a].append(b)
        self.occupations={n["native_id"]:n for n in self.nodes.values() if n["kind"]=="occupation"}
    def search(self,q="",limit=30):
        if not isinstance(q,str) or len(q)>160 or type(limit)!=int or not 1<=limit<=100:raise ValueError("QUERY")
        tokens=q.casefold().split()
        rows=[{"code":k,"title":n["label"],"tasks":len(self.by_occ.get(k,[]))}
              for k,n in sorted(self.occupations.items()) if all(t in (k+" "+n["label"]).casefold() for t in tokens)]
        return {"total":len(rows),"results":rows[:limit],"version":VERSION,"geography":"US"}
    def profile(self,code):
        if code not in self.occupations:raise ValueError("UNKNOWN_OCCUPATION")
        tasks=[]
        for tid in self.by_occ.get(code,[]):
            tasks.append({"task":self.nodes[tid],"activities":[self.nodes[d] for d in self.by_task.get(tid,[])]})
        return {"occupation":self.occupations[code],"tasks":tasks,
                "coverage":{"tasks":len(tasks),"mapped_tasks":sum(bool(t["activities"]) for t in tasks)},
                "atomic_actions":[],"processes":[],"impact_estimates":[],"evidence":"REFERENCE_DESCRIPTION_ONLY",
                "geography":"US","version":VERSION,"attribution":ATTRIBUTION,"license":LICENSE}
    def audit(self):
        kinds=Counter(n["kind"] for n in self.nodes.values())
        edge_counts=Counter(e["kind"] for e in self.edges.values())
        mapped=sum(bool(self.by_task.get(t)) for tasks in self.by_occ.values() for t in tasks)
        return {"version":VERSION,"geography":"US","nodes":dict(kinds),"edges":dict(edge_counts),
                "occupations_with_tasks":len(self.by_occ),"occupations_without_tasks":kinds["occupation"]-len(self.by_occ),
                "mapped_tasks":mapped,"unmapped_tasks":kinds["task"]-mapped,
                "tasks_with_multiple_dwas":sum(len(v)>1 for v in self.by_task.values()),
                "dwas_used":len({d for v in self.by_task.values() for d in v}),
                "atomic_actions":0,"processes":0,"impact_estimates":0,"crosswalks":0,"sources":self.manifest,
                "attribution":ATTRIBUTION,"license":LICENSE,"gate":"G-M0_PARTIAL","values_emitted":False}

def build(fetcher=fetch,strict=True):
    manifest={};tables={}
    for name in FILES:
        raw=fetcher(name)
        tables[name]=parse(name,raw,strict)
        manifest[name]={"url":BASE+name+".csv","sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),
                        "rows":len(tables[name]),"retrieved_at":datetime.now(timezone.utc).isoformat()}
    return Graph(tables,manifest)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--search")
    p.add_argument("--occupation")
    args=p.parse_args()
    try:
        g=build()
        print(json.dumps(g.profile(args.occupation) if args.occupation else g.search(args.search) if args.search is not None else g.audit(),ensure_ascii=False,indent=2))
    except Exception as exc:
        print(json.dumps({"status":"BLOCKED","error_type":type(exc).__name__,"reason":str(exc) if isinstance(exc,ValueError) else "COLLECTION_FAILED"}))
        raise SystemExit(2)
if __name__=="__main__":main()
