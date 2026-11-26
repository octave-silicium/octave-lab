"""Prepare a monthly Indeed snapshot in a local checkout, never push or publish.
The operator supplies a separately reviewed manifest digest. Hash integrity does not authenticate source.
First successful monthly snapshot is immutable. A different candidate for that month is a conflict.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
from tools.indeed_public_bundle import SOURCES, require, utc_time, preflight
from pipeline.run import validate_csv, analyze_sector

ATTRIBUTION = ("Source: Indeed Hiring Lab | CC BY 4.0\n"
    "https://github.com/hiring-lab/job_postings_tracker\nhttps://creativecommons.org/licenses/by/4.0/\n"
    "Original indices; occupation categories are not employer NACE sectors or employment counts.\n")
MAX_BYTES=25*1024*1024

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def strict_json(raw):
    def pairs(items):
        d={}
        for k,v in items:
            require(k not in d,"Duplicate JSON key")
            d[k]=v
        return d
    return json.loads(raw,object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Invalid JSON constant")))

def regular(path,limit):
    require(path.is_file() and not path.is_symlink() and path.resolve()==path.absolute(),"Unsafe file path")
    require(path.stat().st_size<=limit,"File exceeds size limit")
    raw=path.read_bytes()
    require(len(raw)<=limit,"File exceeds size limit")
    return raw

def inspect_candidate(folder,approved_sha):
    require(isinstance(approved_sha,str) and re.fullmatch(r"[0-9a-f]{64}",approved_sha),"Review digest required")
    raw=regular(folder/"manifest.json",65536)
    require(sha(raw)==approved_sha,"Reviewed manifest mismatch")
    m=strict_json(raw)
    require(set(m)=={"scope","run_at","files","derived_outputs_included","product_release_authorized"}
            and m["scope"]=="INDEED_ORIGINALS_ONLY" and m["derived_outputs_included"] is False
            and m["product_release_authorized"] is False,"Candidate scope denied")
    run_at=utc_time(m["run_at"])
    require(isinstance(m["files"],list) and len(m["files"])==2,"Wrong source count")
    selected={}
    for x in m["files"]:
        require(set(x)=={"source_id","filename","sha256","bytes","url","license","downloaded_at"},"Unexpected file metadata")
        sid=x["source_id"]
        require(sid in SOURCES and sid not in selected and x["url"]==SOURCES[sid] and x["license"]=="CC BY 4.0","Source denied")
        h=x["sha256"]
        require(isinstance(h,str) and re.fullmatch(r"[0-9a-f]{64}",h),"Invalid SHA")
        name=sid+"_"+h[:12]+".csv"
        require(x["filename"]==name,"Invalid filename")
        data=regular(folder/name,MAX_BYTES)
        require(type(x["bytes"]) is int and x["bytes"]==len(data) and sha(data)==h,"Candidate bytes mismatch")
        delta=(utc_time(x["downloaded_at"])-run_at).total_seconds()
        require(0<=delta<=7200,"Invalid download time")
        selected[sid]=(x,data)
    require(set(selected)==set(SOURCES),"Missing source")
    require(set(p.name for p in folder.iterdir())=={"manifest.json","ATTRIBUTION.txt",*(x["filename"] for x,_ in selected.values())},"Unexpected bundle entries")
    require(regular(folder/"ATTRIBUTION.txt",4096).decode()==ATTRIBUTION,"Attribution mismatch")
    return m,selected

def legacy_manifest(root,m,selected,scratch,approved_sha):
    reg=strict_json(regular(root/"pipeline/sources.json",65536))
    preflight(reg)
    out={"run_at":m["run_at"],"status":{},"source_registry_version":"pipeline/sources.json",
         "no_causal_inference":True,"license_gate":True,
         "publish_gate":"PASS_DESCRIPTIVE_ONLY: reviewed original candidate revalidated locally",
         "reviewed_candidate_manifest_sha256":approved_sha,"product_release_authorized":False}
    for row in reg["sources"]:
        sid=row["id"]
        if sid not in selected:
            out["status"][sid]={"result":"SKIPPED_LICENSE_REVIEW","reason":"Outside approved Indeed scope"}
            continue
        x,data=selected[sid]
        meta=validate_csv(data,sid)
        status={**meta,"result":"OK","format":"csv","sha256":x["sha256"],"bytes":x["bytes"],
                "filename":x["filename"],"url":x["url"],"license":"CC BY 4.0","public_redistribution":True,
                "downloaded_at":x["downloaded_at"]}
        if sid=="indeed_fr_sector":
            status["analysis"]=analyze_sector(data,scratch)
        out["status"][sid]=status
    return out

def same_existing(target,selected):
    m=strict_json(regular(target/"manifest.json",65536))
    require(m.get("publish_gate","").startswith("PASS_DESCRIPTIVE_ONLY") and m.get("no_causal_inference") is True,"Existing snapshot unqualified")
    for sid,(x,_) in selected.items():
        old=m["status"][sid]
        require(old.get("sha256")==x["sha256"] and old.get("bytes")==x["bytes"] and Path(old["filename"]).name==x["filename"],
                "Monthly snapshot conflict: no overwrite")
        require(sha(regular(target/x["filename"],MAX_BYTES))==x["sha256"],"Existing snapshot corrupted")
    require(set(p.name for p in target.iterdir())=={"manifest.json","ATTRIBUTION.txt",*(x["filename"] for x,_ in selected.values())},"Unexpected existing snapshot entries")
    regular(target/"ATTRIBUTION.txt",4096)

def promote(root,folder,approved_sha):
    root=root.absolute(); folder=folder.absolute()
    m,selected=inspect_candidate(folder,approved_sha)
    month=utc_time(m["run_at"]).strftime("%Y-%m")
    base=root/"snapshots/indeed-fr"; target=base/month
    require(base.resolve()==base.absolute(),"Unsafe archive path")
    base.mkdir(parents=True,exist_ok=True)
    # Exclusive cooperative lock; stale locks require explicit operator review, not automatic deletion.
    lock=base/("."+month+".lock")
    lock.mkdir()
    try:
        require(not target.is_symlink(),"Unsafe target")
        if target.exists():
            same_existing(target,selected)
            return {"decision":"ALREADY_ARCHIVED","month":month,"product_release_authorized":False}
        with tempfile.TemporaryDirectory(prefix=".review-",dir=base) as tmp:
            scratch=Path(tmp); stage=scratch/"snapshot"; stage.mkdir()
            legacy=legacy_manifest(root,m,selected,scratch,approved_sha)
            for x,data in selected.values():
                (stage/x["filename"]).write_bytes(data)
            (stage/"manifest.json").write_text(json.dumps(legacy,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            (stage/"ATTRIBUTION.txt").write_text(ATTRIBUTION,encoding="utf-8")
            require(not target.exists() and not target.is_symlink(),"Concurrent target creation")
            stage.rename(target)
        return {"decision":"LOCAL_SNAPSHOT_PREPARED","month":month,"product_release_authorized":False}
    finally:
        lock.rmdir()

def main():
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path.cwd())
    p.add_argument("--candidate",required=True,type=Path);p.add_argument("--reviewed-manifest-sha256",required=True)
    a=p.parse_args();print(json.dumps(promote(a.root,a.candidate,a.reviewed_manifest_sha256),sort_keys=True))
if __name__=="__main__":main()
