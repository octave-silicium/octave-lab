"""Narrow public Indeed artifact builder. No network or Git writes.
Preflight verifies the only-open collection scope; bundle emits exact attributed originals.
Not a general release authorization or legal review."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile

SOURCES={
 "indeed_fr_sector":"https://raw.githubusercontent.com/hiring-lab/job_postings_tracker/master/FR/job_postings_by_sector_FR.csv",
 "indeed_fr_national":"https://raw.githubusercontent.com/hiring-lab/job_postings_tracker/master/FR/aggregate_job_postings_FR.csv",
}
def require(ok,message):
    if not ok:raise ValueError(message)
def preflight(registry):
    rows=registry["sources"]
    ids=[x["id"] for x in rows]
    require(len(ids)==len(set(ids)),"Duplicate source id")
    require(all(type(x.get("public_redistribution")) is bool for x in rows),"Non-boolean redistribution flag")
    allowed={x["id"]:x for x in rows if x.get("public_redistribution") is True}
    require(set(allowed)==set(SOURCES),"Unexpected open source scope")
    for sid,url in SOURCES.items():
        x=allowed[sid]
        require(x.get("url")==url and x.get("license")=="CC BY 4.0"
                and x.get("format")=="csv" and x.get("required") is True,"Source contract drift")
    return allowed
def utc_time(value):
    require(isinstance(value,str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)",value),"Invalid UTC collection timestamp")
    return dt.datetime.fromisoformat(value.replace("Z","+00:00"))
def checked_path(root,filename,sid,digest):
    require(isinstance(filename,str) and re.fullmatch(
        r"archive/raw/[0-9]{8}T[0-9]{6}Z/"+re.escape(sid)+r"_"+digest[:12]+r"\.csv",filename),"Unexpected input path")
    p=root/filename
    require(p.is_file() and p.resolve()==p.absolute(),"Missing file or symlink")
    return p
def bundle(root,output):
    root=root.resolve()
    require(not output.exists() and not output.is_symlink(),"Output must be fresh")
    registry=json.loads((root/"pipeline/sources.json").read_text())
    preflight(registry)
    manifest=json.loads((root/"outputs/live/manifest.json").read_text())
    require(manifest.get("publish_gate","").startswith("PASS_DESCRIPTIVE_ONLY:"),"Collection gate denied")
    require(manifest.get("license_gate") is True and manifest.get("no_causal_inference") is True,"Gate flags missing")
    run_at=utc_time(manifest.get('run_at'))
    statuses=manifest["status"]
    require(set(statuses)=={x["id"] for x in registry["sources"]},"Manifest source scope mismatch")
    require(all(x.get("result")=="SKIPPED_LICENSE_REVIEW" for k,x in statuses.items() if k not in SOURCES),"Non-approved source present")
    selected=[]
    for sid,url in SOURCES.items():
        x=statuses[sid]; digest=x.get("sha256","")
        require(x.get("result")=="OK" and x.get("url")==url and x.get("license")=="CC BY 4.0"
                and x.get("public_redistribution") is True and x.get("format")=="csv","Source result denied")
        require(isinstance(digest,str) and re.fullmatch(r"[0-9a-f]{64}",digest),"Invalid digest")
        p=checked_path(root,x.get("filename"),sid,digest)
        raw=p.read_bytes()
        require(hashlib.sha256(raw).hexdigest()==digest and len(raw)==x.get("bytes"),"Content integrity mismatch")
        downloaded=utc_time(x.get('downloaded_at'))
        require(dt.timedelta(0)<=downloaded-run_at<=dt.timedelta(hours=2), 'Collection time inconsistent')
        require(p.parent.name==run_at.strftime('%Y%m%dT%H%M%SZ'),'Collection folder timestamp mismatch')
        selected.append((sid,url,p,raw,digest,x['downloaded_at']))
    output.parent.mkdir(parents=True,exist_ok=True)
    # Publish only after all inputs are validated. Stage fresh directory and rename.
    stage=Path(tempfile.mkdtemp(prefix=".indeed-stage-",dir=output.parent))
    try:
        files=[]
        for sid,url,p,raw,digest,downloaded in selected:
            (stage/p.name).write_bytes(raw)
            files.append({"source_id":sid,"filename":p.name,"sha256":digest,"bytes":len(raw),"url":url,
                          "license":"CC BY 4.0","downloaded_at":downloaded})
        (stage/"ATTRIBUTION.txt").write_text("Source: Indeed Hiring Lab | CC BY 4.0\n"
            "https://github.com/hiring-lab/job_postings_tracker\nhttps://creativecommons.org/licenses/by/4.0/\n"
            "Original indices; occupation categories are not employer NACE sectors or employment counts.\n")
        (stage/"manifest.json").write_text(json.dumps({"scope":"INDEED_ORIGINALS_ONLY",
            "run_at":manifest["run_at"],"files":files,"derived_outputs_included":False,"product_release_authorized":False},indent=2)+"\n")
        stage.rename(output)
    finally:
        if stage.exists():shutil.rmtree(stage)
    return {"files":len(files),"derived_outputs_included":False,"product_release_authorized":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path.cwd())
    p.add_argument("--preflight",action="store_true");p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.preflight:
        preflight(json.loads((a.root/"pipeline/sources.json").read_text()))
        print("INDEED_SCOPE_PREFLIGHT_OK")
    else:
        require(a.output is not None,"Output required")
        print(json.dumps(bundle(a.root,a.output)))
if __name__=="__main__":main()
