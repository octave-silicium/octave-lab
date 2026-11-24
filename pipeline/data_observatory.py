"""Octave Data Observatory v0.1: bounded checks; no publication or automatic promotion."""
import argparse,csv,hashlib,io,json,os,re,sys,tempfile,zipfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date,datetime,timezone
from decimal import Decimal
from pathlib import Path
from . import semantic_v3 as v3,semantic_v4 as v4
from . import work_graph,rome_inventory
from .european_work import fetch

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"governance/refresh_sources.json"
def now():return datetime.now(timezone.utc).isoformat()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def read_registry(path=REGISTRY):
    d=json.loads(Path(path).read_text())
    ids=[s["id"] for s in d["sources"]]
    if len(ids)!=len(set(ids)) or any(not re.fullmatch(r"[a-z0-9_]+",i) for i in ids):raise ValueError("REGISTRY_IDS")
    return d["sources"]
def csv_reader(raw,columns,sep=","):
    r=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")),delimiter=sep)
    if not columns<=set(r.fieldnames or []) or len(set(r.fieldnames or []))!=len(r.fieldnames or []):raise ValueError("SCHEMA")
    for row in r:
        if None in row or any(row[k] is None for k in columns):raise ValueError("ROW_SHAPE")
        yield row
def validate_indeed(raw,kind):
    field="indeed_job_postings_index_SA" if kind=="indeed_national" else "indeed_job_postings_index"
    cols={"date","jobcountry","variable",field}|({"display_name"} if kind=="indeed_sector" else set())
    keys=set();periods=[]
    for r in csv_reader(raw,cols):
        if r["jobcountry"]!="FR":raise ValueError("COUNTRY")
        if r["variable"]!="total postings":continue
        p=date.fromisoformat(r["date"]).isoformat()
        f=r.get("display_name","")
        if kind=="indeed_sector" and not f:raise ValueError("FAMILY")
        val=Decimal(r[field])
        if not val.is_finite() or val<0:raise ValueError("VALUE")
        k=(p,f)
        if k in keys:raise ValueError("DUPLICATE")
        keys.add(k);periods.append(p)
    if not periods:raise ValueError("EMPTY")
    return {"selected_rows":len(keys),"first":min(periods),"last":max(periods)}
def validate_dares(raw):
    keys=set();periods=[]
    cols=set(v3.v2.DARES_FIELDS)
    for r in csv_reader(raw,cols,";"):
        p=r["Date"][:7]
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])",p):raise ValueError("PERIOD")
        k=tuple(r[c] for c in sorted(cols-{"Nombre d'offres d'emploi"}))
        if k in keys:raise ValueError("DUPLICATE")
        keys.add(k);periods.append(p)
        val,flag=v3.v2.parse_value(r["Nombre d'offres d'emploi"])
        if val is not None and (not val.is_finite() or val<0):raise ValueError("VALUE")
    if not keys:raise ValueError("EMPTY")
    return {"rows":len(keys),"first":min(periods),"last":max(periods)}
def validate_xlsx(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if sum(i.file_size for i in z.infolist())>100_000_000 or len(z.namelist())!=len(set(z.namelist())):raise ValueError("ZIP_LIMIT")
        if z.testzip() is not None or not {"xl/workbook.xml","[Content_Types].xml"}<=set(z.namelist()):raise ValueError("XLSX_CONTAINER")
        return {"members":len(z.namelist()),"scope":"CONTAINER_ONLY"}
def validate_live(source,raw,stamp):
    rows,_=(v3.read_urssaf if source in v3.URSSAF else v3.read_euro)(source,raw,stamp)
    if not rows:raise ValueError("EMPTY")
    c=v4.Catalog(v4.wrap_live(r) for r in rows)
    data=c.by[source]
    return {"cells":len(data),"first":min(r.period for r in data),"last":max(r.period for r in data),"quality":dict(Counter(r.quality[0] for r in data))}
def check(s,fetcher=fetch):
    result={"id":s["id"],"checked_at":now(),"mode":s["kind"],"publication":"BLOCK_PUBLICATION","promotion":"NOT_PERFORMED"}
    if s["kind"]=="manual":return {**result,"status":"MANUAL_REVIEW","reason":s["reason"]}
    try:
        kind=s["kind"]
        if kind=="onet_pinned":
            g=work_graph.build()
            a=g.audit()
            return {**result,"status":"PINNED_VERSION_VERIFIED","version":a["version"],"nodes":a["nodes"],"edges":a["edges"],"latest_release_verified":False,"source_hashes":{k:v["sha256"] for k,v in a["sources"].items()}}
        url=v3.SOURCES[s["id"]] if kind=="live_native" else s["url"]
        raw,_,_=fetcher(url,100_000_000)
        sha=digest(raw)
        if kind.startswith("indeed_"):meta=validate_indeed(raw,kind)
        elif kind=="dares":meta=validate_dares(raw)
        elif kind=="xlsx":meta=validate_xlsx(raw)
        elif kind=="rome_inventory":
            inv=rome_inventory.inspect(raw)
            meta={"members":len(inv["members"]),"scope":"NATIVE_INVENTORY_ONLY"}
        elif kind=="live_native":meta=validate_live(s["id"],raw,result["checked_at"])
        else:raise ValueError("UNSUPPORTED_KIND")
        return {**result,"status":"CHECKED","validation_scope":"CONTAINER_OR_INVENTORY" if kind in {"xlsx","rome_inventory"} else "SOURCE_NATIVE","bytes":len(raw),"sha256":sha,"change_vs_reference":"SAME" if sha==s.get("baseline_sha256") else "CHANGED_OR_UNPINNED","coverage":meta}
    except Exception as exc:
        # No raw values, response bodies, credentials or exception details in public logs.
        return {**result,"status":"FAILED","error_type":type(exc).__name__}
def run(sources,scheduled=False,day=None,checker=check):
    day=day or datetime.now(timezone.utc).date()
    due=[s for s in sources if not scheduled or s["frequency"]=="daily" or s["frequency"]=="weekly" and day.weekday()==0 or s["frequency"]=="monthly" and day.day==1]
    with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(checker,due))
    return {"version":"0.1","at":now(),"mode":"METADATA_MONITOR","registered":len(sources),"due":len(due),"not_due":len(sources)-len(due),"statuses":dict(Counter(r["status"] for r in results)),"results":results,"automatic_promotion":False,"vault_provisioned":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--scheduled",action="store_true");a=p.parse_args()
    r=run(read_registry(),a.scheduled)
    print(json.dumps(r,ensure_ascii=False,indent=2))
    if r["statuses"].get("FAILED"):raise SystemExit(2)
if __name__=="__main__":main()
