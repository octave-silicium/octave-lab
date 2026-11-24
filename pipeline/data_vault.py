"""Internal, local content-addressed vault. Explicit promotion; no public access."""
import argparse, hashlib, json, os, re, sqlite3
from datetime import datetime,timezone
from pathlib import Path
from contextlib import contextmanager
from . import data_observatory as obs

ROOT=Path(__file__).resolve().parents[1]
MAX_BYTES=100_000_000
HEX=re.compile(r"[0-9a-f]{64}")
ID=re.compile(r"[a-z0-9_]{1,100}")
SCHEMA="""
CREATE TABLE IF NOT EXISTS object(sha TEXT PRIMARY KEY, size INTEGER NOT NULL, raw BLOB NOT NULL);
CREATE TABLE IF NOT EXISTS candidate(source TEXT NOT NULL,sha TEXT NOT NULL REFERENCES object(sha),created TEXT NOT NULL,validation TEXT NOT NULL, PRIMARY KEY(source,sha));
CREATE TABLE IF NOT EXISTS active(source TEXT PRIMARY KEY,sha TEXT NOT NULL,FOREIGN KEY(source,sha) REFERENCES candidate(source,sha));
CREATE TABLE IF NOT EXISTS event(id INTEGER PRIMARY KEY,source TEXT NOT NULL,at TEXT NOT NULL,kind TEXT NOT NULL,sha TEXT,previous_sha TEXT,reason TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS event_source ON event(source,id);
"""
def utc():return datetime.now(timezone.utc).isoformat()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def checked_id(s):
    if not isinstance(s,str) or not ID.fullmatch(s):raise ValueError("SOURCE_ID")
    return s
def checked_hash(s):
    if not isinstance(s,str) or not HEX.fullmatch(s):raise ValueError("SHA256")
    return s
class Vault:
    def __init__(self,directory):
        root=Path(directory).expanduser().resolve()
        if root==ROOT or ROOT in root.parents:raise ValueError("VAULT_MUST_BE_OUTSIDE_REPO")
        root.mkdir(mode=0o700,parents=True,exist_ok=True)
        if os.name=="posix" and (root.stat().st_mode & 0o077):raise ValueError("PRIVATE_DIRECTORY_REQUIRED")
        db=root/"vault.sqlite"
        if db.is_symlink():raise ValueError("SYMLINK")
        if not db.exists():
            fd=os.open(db,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
        if os.name=="posix" and db.stat().st_mode & 0o077:raise ValueError("PRIVATE_FILE_REQUIRED")
        self.db=sqlite3.connect(db,timeout=30,isolation_level=None)
        self.db.row_factory=sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=DELETE")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript(SCHEMA)
    def close(self):self.db.close()
    @contextmanager
    def txn(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            if self.db.in_transaction:self.db.execute("ROLLBACK")
            raise
    def event(self,source,kind,digest,previous,reason):
        self.db.execute("INSERT INTO event(source,at,kind,sha,previous_sha,reason) VALUES(?,?,?,?,?,?)",(source,utc(),kind,digest,previous,reason))
    def active_hash(self,source):
        r=self.db.execute("SELECT sha FROM active WHERE source=?",(checked_id(source),)).fetchone()
        return r["sha"] if r else None
    def record_failure(self,source,reason):
        checked_id(source)
        if not isinstance(reason,str) or not re.fullmatch(r"[A-Z0-9_]{1,100}",reason):raise ValueError("REASON_CODE")
        with self.txn():self.event(source,"CHECK_FAILED",None,self.active_hash(source),reason)
    def stage(self,spec,raw):
        source=checked_id(spec["id"])
        # Bind validation to the actual bytes, not a user-supplied PASS report.
        registry={s["id"]:s for s in obs.read_registry()}
        if registry.get(source)!=spec or spec["kind"] in {"manual","onet_pinned"}:raise ValueError("UNQUALIFIED_SOURCE")
        if not isinstance(raw,bytes) or not 0<len(raw)<=MAX_BYTES:raise ValueError("SIZE")
        digest=sha(raw)
        result=obs.check(spec,fetcher=lambda *_:(raw,"",""))
        if result["status"]!="CHECKED" or result.get("sha256")!=digest:
            self.record_failure(source,"VALIDATION_FAILED_OR_REVIEW")
            return {"source":source,"sha":digest,"status":"REJECTED","active":self.active_hash(source)}
        with self.txn():
            self.db.execute("INSERT OR IGNORE INTO object VALUES(?,?,?)",(digest,len(raw),raw))
            old=self.db.execute("SELECT size,raw FROM object WHERE sha=?",(digest,)).fetchone()
            if old["size"]!=len(raw) or sha(old["raw"])!=digest:raise ValueError("CORRUPT_OBJECT")
            cur=self.db.execute("INSERT OR IGNORE INTO candidate VALUES(?,?,?,?)",(source,digest,utc(),json.dumps(result,sort_keys=True)))
            active=self.active_hash(source)
            status="UNCHANGED_ACTIVE" if digest==active else "STAGED" if cur.rowcount else "ALREADY_STAGED"
            self.event(source,status,digest,active,"SOURCE_CHECKED")
        return {"source":source,"sha":digest,"status":status,"active":active,"validation_scope":result["validation_scope"]}
    def promote(self,source,digest,expected,reason):
        checked_id(source);checked_hash(digest)
        if expected is not None:checked_hash(expected)
        if not isinstance(reason,str) or not re.fullmatch(r"[A-Z0-9_]{1,100}",reason):raise ValueError("REASON_CODE")
        with self.txn():
            old=self.active_hash(source)
            if old!=expected:raise ValueError("ACTIVE_CONFLICT")
            r=self.db.execute("SELECT c.validation,o.raw,o.size FROM candidate c JOIN object o USING(sha) WHERE c.source=? AND c.sha=?",(source,digest)).fetchone()
            if not r or sha(r["raw"])!=digest or len(r["raw"])!=r["size"]:raise ValueError("MISSING_OR_CORRUPT_CANDIDATE")
            validation=json.loads(r["validation"])
            if validation.get("status")!="CHECKED" or validation.get("validation_scope")!="SOURCE_NATIVE" or validation.get("sha256")!=digest or validation.get("id")!=source:raise ValueError("INVALID_VALIDATION")
            self.db.execute("INSERT INTO active VALUES(?,?) ON CONFLICT(source) DO UPDATE SET sha=excluded.sha",(source,digest))
            self.event(source,"PROMOTED" if old!=digest else "CONFIRMED",digest,old,reason)
        return {"source":source,"active":digest,"previous":old,"publication":"BLOCK_PUBLICATION"}
    def read(self,source,digest=None):
        checked_id(source)
        d=digest or self.active_hash(source)
        if d is None:raise ValueError("NO_ACTIVE_VERSION")
        checked_hash(d)
        r=self.db.execute("SELECT o.raw,o.size FROM candidate c JOIN object o USING(sha) WHERE c.source=? AND c.sha=?",(source,d)).fetchone()
        if not r or len(r["raw"])!=r["size"] or sha(r["raw"])!=d:raise ValueError("INTEGRITY")
        return r["raw"]
    def revisions(self,source,previous,candidate):
        checked_id(source);checked_hash(previous);checked_hash(candidate)
        a=self.read(source,previous);b=self.read(source,candidate)
        if previous==candidate:return {"source":source,"status":"IDENTICAL_BYTES","added":0,"removed":0,"changed":0}
        spec=next(s for s in obs.read_registry() if s["id"]==source)
        if spec["kind"]=="live_native":
            from .native_revisions import compare
            return compare(source,a,b)
        if spec["kind"] not in {"indeed_national","indeed_sector"}:
            return {"source":source,"status":"REVIEW_REQUIRED","reason":"NATIVE_REVISION_COMPARATOR_NOT_IMPLEMENTED"}
        from decimal import Decimal
        field="indeed_job_postings_index_SA" if spec["kind"]=="indeed_national" else "indeed_job_postings_index"
        def index(raw):
            obs.validate_indeed(raw,spec["kind"])
            return {(r["date"],r.get("display_name","")):Decimal(r[field]) for r in obs.csv_reader(raw,{"date","variable",field}) if r["variable"]=="total postings"}
        old,new=index(a),index(b)
        shared=set(old)&set(new)
        return {"source":source,"status":"NATIVE_REVISION_COUNTS","added":len(set(new)-set(old)),"removed":len(set(old)-set(new)),"changed":sum(old[k]!=new[k] for k in shared),"unchanged":sum(old[k]==new[k] for k in shared),"comparison_scope":"SELECTED_TOTAL_POSTINGS_INDEX_ONLY","publication":"BLOCK_PUBLICATION"}
    def history(self,source):
        checked_id(source)
        return {"source":source,"active":self.active_hash(source),"candidates":[{"sha":r["sha"],"created":r["created"],"validation":json.loads(r["validation"])} for r in self.db.execute("SELECT sha,created,validation FROM candidate WHERE source=? ORDER BY created,sha",(source,))],"events":[dict(r) for r in self.db.execute("SELECT id,at,kind,sha,previous_sha,reason FROM event WHERE source=? ORDER BY id",(source,))]}
    def verify(self):
        integrity=self.db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        fk=not self.db.execute("PRAGMA foreign_key_check").fetchone()
        checked=0
        for r in self.db.execute("SELECT sha,size,raw FROM object"):
            if len(r["raw"])!=r["size"] or sha(r["raw"])!=r["sha"]:raise ValueError("OBJECT_INTEGRITY")
            checked+=1
        if not integrity or not fk:raise ValueError("DATABASE_INTEGRITY")
        return {"integrity":"PASS","objects":checked,"active_sources":self.db.execute("SELECT count(*) FROM active").fetchone()[0],"events":self.db.execute("SELECT count(*) FROM event").fetchone()[0]}
def main():
    p=argparse.ArgumentParser();p.add_argument("--vault",required=True)
    sub=p.add_subparsers(dest="cmd",required=True)
    for cmd in ("history","collect","promote","revisions"):
        s=sub.add_parser(cmd);s.add_argument("source")
        if cmd=="revisions":
            s.add_argument("previous");s.add_argument("candidate")
        if cmd=="promote":
            s.add_argument("sha");s.add_argument("--expected",required=True,help="current hash, or NONE");s.add_argument("--reason",required=True)
    sub.add_parser("verify")
    a=p.parse_args()
    v=Vault(a.vault)
    try:
        if a.cmd=="history":r=v.history(a.source)
        elif a.cmd=="verify":r=v.verify()
        elif a.cmd=="revisions":r=v.revisions(a.source,a.previous,a.candidate)
        elif a.cmd=="promote":r=v.promote(a.source,a.sha,None if a.expected=="NONE" else a.expected,a.reason)
        else:
            s=next(x for x in obs.read_registry() if x["id"]==a.source)
            if s["kind"] in {"manual","onet_pinned"}:raise ValueError("MANUAL_OR_BUNDLE_REQUIRED")
            url=obs.v3.SOURCES[s["id"]] if s["kind"]=="live_native" else s["url"]
            try:
                if s["kind"]=="xlsx":raw,_=obs.ingest_insee.download(url,{"www.insee.fr"})
                else:raw,_,_=obs.fetch(url,MAX_BYTES)
            except Exception:
                v.record_failure(a.source,"FETCH_FAILED");raise
            r=v.stage(s,raw)
        print(json.dumps(r,ensure_ascii=False,indent=2))
        if r.get("status")=="REJECTED":raise SystemExit(2)
    finally:v.close()
if __name__=="__main__":main()
