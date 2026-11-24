"""Vault v0.3: verified backup/restore and durable local collection scheduling.
No automatic promotion, no public data, no remote deployment.
"""
import argparse, hashlib, json, os, shutil, sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from .data_vault import Vault,ROOT,MAX_BYTES,checked_hash
from . import data_observatory as obs

def file_hash(p):
    with p.open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()

def new_private_directory(path):
    p=Path(path).expanduser().resolve()
    if p==ROOT or ROOT in p.parents:raise ValueError("OUTSIDE_REPOSITORY_REQUIRED")
    p.mkdir(mode=0o700,parents=False,exist_ok=False)
    return p

def backup(vault,destination):
    """SQLite's consistent snapshot API; do not copy an open database file."""
    p=new_private_directory(destination)
    try:
        target=p/"vault.sqlite"
        fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
        dest=sqlite3.connect(target)
        try:vault.db.backup(dest)
        finally:dest.close()
        copy=Vault(p)
        try:
            verified=copy.verify()
            active=dict(copy.db.execute("SELECT source,sha FROM active"))
        finally:copy.close()
        manifest={"version":1,"created":obs.now(),"database_sha256":file_hash(target),"bytes":target.stat().st_size,"verification":verified,"active":active,"scope":"PRIVATE_LOCAL_BACKUP","publication":"BLOCK_PUBLICATION"}
        fd=os.open(p/"manifest.json",os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(manifest,f,indent=2);f.flush();os.fsync(f.fileno())
        return manifest
    except BaseException:
        shutil.rmtree(p)
        raise

def restore(backup_directory,destination,expected_sha256):
    """Restore to a new directory only; caller supplies independently retained hash."""
    checked_hash(expected_sha256)
    src=Path(backup_directory).expanduser().resolve()
    raw=src/"vault.sqlite";meta=src/"manifest.json"
    if not raw.is_file() or not meta.is_file() or raw.is_symlink() or meta.is_symlink():raise ValueError("BACKUP_FILES")
    manifest=json.loads(meta.read_text())
    if manifest.get("version")!=1 or manifest.get("database_sha256")!=expected_sha256 or file_hash(raw)!=expected_sha256 or raw.stat().st_size!=manifest.get("bytes"):raise ValueError("BACKUP_INTEGRITY")
    p=new_private_directory(destination)
    try:
        target=p/"vault.sqlite"
        fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,"wb") as out,raw.open("rb") as inp:
            shutil.copyfileobj(inp,out);out.flush();os.fsync(out.fileno())
        if file_hash(target)!=expected_sha256:raise ValueError("COPY_INTEGRITY")
        copy=Vault(p)
        try:
            verified=copy.verify()
            active=dict(copy.db.execute("SELECT source,sha FROM active"))
            if verified!=manifest["verification"] or active!=manifest["active"]:raise ValueError("RESTORE_STATE")
        finally:copy.close()
        return {"status":"RESTORED","backup_sha256":expected_sha256,"verification":verified,"active":active,"publication":"BLOCK_PUBLICATION"}
    except BaseException:
        shutil.rmtree(p)
        raise

CHECK_EVENTS=("STAGED","ALREADY_STAGED","UNCHANGED_ACTIVE","CHECK_FAILED")
SUCCESS_EVENTS=CHECK_EVENTS[:-1]
def freshness(vault,spec,now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise ValueError("TIMEZONE")
    source=spec["id"]
    def last(kinds):
        marks=",".join("?" for _ in kinds)
        r=vault.db.execute("SELECT at,kind FROM event WHERE source=? AND kind IN ("+marks+") ORDER BY id DESC LIMIT 1",(source,*kinds)).fetchone()
        return (datetime.fromisoformat(r["at"]),r["kind"]) if r else (None,None)
    attempt,kind=last(CHECK_EVENTS);success,_=last(SUCCESS_EVENTS)
    active=vault.active_hash(source)
    supported=spec["kind"] not in {"manual","onet_pinned"}
    interval={"daily":1,"weekly":7,"monthly":30}[spec["frequency"]]
    due=supported and (attempt is None or now-attempt>=timedelta(hours=6) if kind=="CHECK_FAILED" else success is None or now-success>=timedelta(days=interval))
    # Keep the failure alert even when a retry is not yet due.
    pending=vault.db.execute("SELECT count(*) FROM candidate WHERE source=? AND sha<>coalesce(?, '')",(source,active)).fetchone()[0]
    return {"source":source,"mode":"COLLECTOR" if supported else "MANUAL_OR_BUNDLE","due":bool(due) if supported else False,"last_attempt":attempt.isoformat() if attempt else None,"last_success":success.isoformat() if success else None,"last_status":kind,"active_sha256":active,"nonactive_candidates":pending,"check_overdue":bool(success is None or now-success>=timedelta(days=interval)) if supported else None,"alert":"CHECK_FAILED" if kind=="CHECK_FAILED" else "NO_ACTIVE_VERSION" if supported and active is None else "MANUAL_OR_BUNDLE" if not supported else None,"data_freshness":"NOT_ESTIMATED_FROM_CHECK_TIME"}

def retrieve(spec):
    url=obs.v3.SOURCES[spec["id"]] if spec["kind"]=="live_native" else spec["url"]
    if spec["kind"]=="xlsx":return obs.ingest_insee.download(url,{"www.insee.fr"})[0]
    return obs.fetch(url,MAX_BYTES)[0]

def collect_due(vault,force=False,fetcher=retrieve,sources=None):
    sources=obs.read_registry() if sources is None else sources
    results=[]
    for spec in sources:
        state=freshness(vault,spec)
        if state["mode"]!="COLLECTOR":
            results.append({"source":spec["id"],"status":"MANUAL_OR_BUNDLE"});continue
        if not force and not state["due"]:
            results.append({"source":spec["id"],"status":"NOT_DUE"});continue
        try:raw=fetcher(spec)
        except Exception as exc:
            vault.record_failure(spec["id"],"FETCH_FAILED")
            results.append({"source":spec["id"],"status":"FETCH_FAILED","error_type":type(exc).__name__});continue
        try:r=vault.stage(spec,raw)
        except Exception as exc:
            vault.record_failure(spec["id"],"STAGE_FAILED")
            results.append({"source":spec["id"],"status":"STAGE_FAILED","error_type":type(exc).__name__});continue
        if r["status"] in {"STAGED","ALREADY_STAGED"} and r.get("active"):
            try:r["revisions"]=vault.revisions(spec["id"],r["active"],r["sha"])
            except Exception:r["revisions"]={"status":"REVIEW_REQUIRED","reason":"COMPARISON_FAILED"}
        results.append(r)
    return {"mode":"PRIVATE_LOCAL_COLLECTION","results":results,"health":[freshness(vault,s) for s in sources],"automatic_promotion":False,"publication":"BLOCK_PUBLICATION"}

def main():
    p=argparse.ArgumentParser();p.add_argument("--vault",required=True)
    sub=p.add_subparsers(dest="cmd",required=True)
    s=sub.add_parser("backup");s.add_argument("destination")
    s=sub.add_parser("restore");s.add_argument("backup_directory");s.add_argument("--sha256",required=True)
    s=sub.add_parser("collect-due");s.add_argument("--force",action="store_true")
    sub.add_parser("health")
    a=p.parse_args()
    if a.cmd=="restore":r=restore(a.backup_directory,a.vault,a.sha256)
    else:
        v=Vault(a.vault)
        try:
            if a.cmd=="backup":r=backup(v,a.destination)
            elif a.cmd=="health":r={"sources":[freshness(v,s) for s in obs.read_registry()]}
            else:r=collect_due(v,a.force)
        finally:v.close()
    print(json.dumps(r,indent=2))
    if a.cmd=="collect-due" and any(x["status"] in {"FETCH_FAILED","STAGE_FAILED","REJECTED"} for x in r["results"]):raise SystemExit(2)
if __name__=="__main__":main()
