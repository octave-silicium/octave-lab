"""Explicit approved-vintage reader. A server session pins one set of active hashes."""
import csv,hashlib,io,json,sqlite3
from pathlib import Path
from decimal import Decimal
from . import data_observatory as obs, semantic_v4 as v4
from .data_vault import ROOT,checked_hash
from .explorer import LazyExplorer,Explorer,LABELS

class ActiveCatalog:
    def __init__(self,directory):
        root=Path(directory).expanduser().resolve()
        if root==ROOT or ROOT in root.parents:raise ValueError("PRIVATE_VAULT_REQUIRED")
        p=root/"vault.sqlite"
        if not p.is_file() or p.is_symlink():raise ValueError("VAULT_NOT_FOUND")
        import os
        if os.name=="posix" and ((root.stat().st_mode|p.stat().st_mode)&0o077):raise ValueError("PRIVATE_PERMISSIONS")
        self.path=p
        self.specs={s["id"]:s for s in obs.read_registry()}
        with self.connection() as db:
            rows=db.execute("SELECT a.source,a.sha,c.created,c.validation FROM active a JOIN candidate c ON c.source=a.source AND c.sha=a.sha").fetchall()
        self.pins={}
        for source,digest,created,validation in rows:
            if source not in v4.SOURCES:continue
            m=json.loads(validation)
            if m.get("id")!=source or m.get("sha256")!=digest or m.get("status")!="CHECKED" or m.get("validation_scope")!="SOURCE_NATIVE":raise ValueError("ACTIVE_VALIDATION")
            self.pins[source]=(checked_hash(digest),created)
        if not self.pins:raise ValueError("NO_APPROVED_ANALYTICAL_SOURCE")
    def connection(self):
        from contextlib import contextmanager
        @contextmanager
        def opened():
            db=sqlite3.connect(self.path.as_uri()+"?mode=ro",uri=True)
            try:
                db.execute("PRAGMA query_only=ON")
                db.execute("PRAGMA trusted_schema=OFF")
                yield db
            finally:db.close()
        return opened()
    def raw(self,source):
        if source not in self.pins:raise ValueError("NO_PINNED_ACTIVE")
        digest,stamp=self.pins[source]
        with self.connection() as db:
            r=db.execute("SELECT o.raw,o.size FROM candidate c JOIN object o USING(sha) WHERE c.source=? AND c.sha=?",(source,digest)).fetchone()
        if not r or len(r[0])!=r[1] or hashlib.sha256(r[0]).hexdigest()!=digest:raise ValueError("PINNED_OBJECT_INTEGRITY")
        return r[0],digest,stamp
    def load(self,source):
        raw,h,stamp=self.raw(source)
        spec=self.specs[source]
        validation=obs.check(spec,fetcher=lambda *_:(raw,"",""))
        if validation.get("status")!="CHECKED" or validation.get("validation_scope")!="SOURCE_NATIVE" or validation.get("sha256")!=h:raise ValueError("CURRENT_CONTRACT_REJECTED")
        v2=v4.v2
        if source in v4.LIVE_SOURCES:
            rows,_=(v4.v3.read_urssaf if source in v4.v3.URSSAF else v4.v3.read_euro)(source,raw,stamp)
            return v4.Catalog(v4.wrap_live(r) for r in rows)
        url=spec["url"]
        if source=="insee_employment":
            rows,a=obs.ingest_insee.extract(raw)
            cells=(v2.wrap(v2.v1.Observation(source,r["sector_label"],r["category_kind"],r["quarter"].replace("-T","Q"),Decimal(str(r["employees_thousands"])),stamp,h,url,f"vault:{h}:normalized-row-{i}",a["method_vintage"])) for i,r in enumerate(rows,2))
        elif source.startswith("indeed_"):
            sector=source=="indeed_sector_total_daily"
            field="indeed_job_postings_index" if sector else "indeed_job_postings_index_SA"
            def indeed():
                for n,r in enumerate(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))),2):
                    if r["variable"]!="total postings":continue
                    dims={"country":"FR"}
                    if sector:dims["occupation_family"]=r["display_name"]
                    val,flag=v2.parse_value(r[field])
                    yield v2.Cell(source,r["date"],v2.dims("Indeed_native","vault-source-native",**dims),val,"OBSERVED" if val is not None else "MISSING",stamp,h,url,f"vault:{h}:csv-line-{n}","source native total postings SA; vault intake",flag)
            cells=indeed()
        elif source=="dares_offers_monthly":
            def dares():
                for n,r in enumerate(csv.DictReader(io.StringIO(raw.decode("utf-8-sig")),delimiter=";"),2):
                    p=r["Date"]
                    if len(p)==10 and p.endswith("-01"):p=p[:7]
                    native=dict(region_code=r["Code région"],region_label=r["Région"],department_code=r["Code département"],department_label=r["Département"],data_type=r["Type de données"],offer_type=r["Type d'offre d'emploi"],employment_type=r["Type d'emploi"],qualification=r["Qualification"])
                    val,flag=v2.parse_value(r["Nombre d'offres d'emploi"])
                    yield v2.Cell(source,p,v2.dims("Dares_native","vault-source-native",**native),val,"OBSERVED" if val is not None else "MISSING",stamp,h,url,f"vault:{h}:csv-line-{n}","source native; rounded counts; 2013 review",flag)
            cells=dares()
        else:raise ValueError("UNSUPPORTED_SOURCE")
        return v4.Catalog(v4.wrap_archive(c) for c in cells)

class VaultExplorer(LazyExplorer):
    def __init__(self,directory):
        self.active=ActiveCatalog(directory)
        super().__init__(live=True,loader=self.active.load)
        self.allowed=set(self.active.pins)
    def sources(self):
        return [{**r,"persistence":"ARCHIVE","vintage":self.active.pins[r["id"]][1],"snapshot_sha256":self.active.pins[r["id"]][0],"storage":"VAULT_SESSION_PIN","vintage_kind":"INTAKE_TIMESTAMP"} for r in super().sources()]
    def discover(self,source,filters,query=""):
        d=super().discover(source,filters,query)
        d["source_meta"]=next(r for r in self.sources() if r["id"]==source)
        return d
    def detail(self,source,*args,**kwargs):
        d=super().detail(source,*args,**kwargs)
        d["persistence"]="ARCHIVE";d["storage"]="VAULT_SESSION_PIN";d["vintage_kind"]="INTAKE_TIMESTAMP"
        for r in d["records"]:
            r["persistence"]="VAULT_SESSION_PIN";r["vintage_kind"]="INTAKE_TIMESTAMP"
        return d
    def point(self,source,*args,**kwargs):
        d=super().point(source,*args,**kwargs);d["persistence"]="VAULT_SESSION_PIN";d["vintage_kind"]="INTAKE_TIMESTAMP";return d
    def restore(self,source,sid,sha,start=None,end=None):
        if source not in self.allowed:raise ValueError("SOURCE")
        checked_hash(sid);checked_hash(sha)
        if self.active.pins[source][0]!=sha:return {"decision":"VINTAGE_MISMATCH","publication":"BLOCK_PUBLICATION"}
        return {"decision":"MATCH","series":self.detail(source,sid,start,end)}
