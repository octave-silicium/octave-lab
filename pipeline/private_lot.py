"""Read-only bridge for the verified private G2 v0.3 SQLite lot. No HTTP or export."""
import hashlib, re, sqlite3
from pathlib import Path

HEX=re.compile(r"[0-9a-f]{64}")
PERIOD=re.compile(r"\d{4}(?:-T[1-4])?")

class PrivateLot:
    def __init__(self,path,expected_sha,*,cross_thread=False):
        self.path=Path(path).expanduser().resolve()
        if not HEX.fullmatch(expected_sha):raise ValueError("SHA256")
        if not self.path.is_file() or any(Path(str(self.path)+s).exists() for s in ("-wal","-journal","-shm")):raise ValueError("NOT_CLOSED_SNAPSHOT")
        with self.path.open("rb") as f:
            if hashlib.file_digest(f,"sha256").hexdigest()!=expected_sha:raise ValueError("SNAPSHOT_INTEGRITY")
        self.sha=expected_sha
        self.db=sqlite3.connect(self.path.as_uri()+"?mode=ro&immutable=1",uri=True,check_same_thread=not cross_thread)
        self.db.row_factory=sqlite3.Row
        self.db.execute("PRAGMA query_only=ON")
        self.db.execute("PRAGMA trusted_schema=OFF")
        required={"source","esco_concept","esco_text","esco_relation","fap_mapping","pcs_probability","mmo_internal"}
        names={r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
        if not required<=names:
            self.close();raise ValueError("SCHEMA")
    def close(self):self.db.close()
    def _rows(self,sql,args=()):return [dict(r) for r in self.db.execute(sql,args)]
    def _result(self,rows):return {"snapshot_sha256":self.sha,"publication":"BLOCK_PUBLICATION","evidence":"REFERENCE_OR_DESCRIPTIVE_ONLY","rows":rows}
    @staticmethod
    def _limit(n):
        if type(n) is not int or not 1<=n<=100:raise ValueError("LIMIT")
        return n
    @staticmethod
    def _text(s):
        if not isinstance(s,str) or not s.strip() or len(s)>300:raise ValueError("QUERY")
        return s
    def search_esco(self,term,lang="fr",limit=30):
        if lang not in {"fr","en"}:raise ValueError("LANG")
        return self._result(self._rows("SELECT t.uri,t.label FROM esco_text t JOIN esco_concept c USING(uri) WHERE c.kind='occupation' AND lang=? AND instr(lower(t.label),lower(?))>0 ORDER BY label,uri LIMIT ?",(lang,self._text(term),self._limit(limit))))
    def esco_skills(self,uri,lang="fr",limit=100):
        if lang not in {"fr","en"}:raise ValueError("LANG")
        return self._result(self._rows("SELECT r.occupation,r.skill,t.label,r.relation FROM esco_relation r JOIN esco_text t ON t.uri=r.skill AND t.lang=? WHERE r.occupation=? ORDER BY r.relation,t.label,r.skill LIMIT ?",(lang,self._text(uri),self._limit(limit))))
    def fap_rome(self,rome,limit=100):
        return self._result(self._rows("SELECT source,member,row_no,rome,qualification,fap,source_fap_label,review FROM fap_mapping WHERE kind='ROME_QUALIF' AND rome=? ORDER BY row_no LIMIT ?",(self._text(rome),self._limit(limit))))
    def mmo_series(self,source,sheet,sector,size,col,start,end,limit=100):
        if (source,sheet) not in {("mmo_Q","MMO_trimestriels"),("mmo_Q","MMO_trimestriels_A17"),("mmo_A","MMO_annuels")}:raise ValueError("SOURCE")
        if not all(isinstance(p,str) and PERIOD.fullmatch(p) and ((len(p)==4)==(source=="mmo_A")) for p in (start,end)) or start>end:raise ValueError("PERIOD")
        rows=self._rows("SELECT source,sheet,row_no,col,period,sector,establishment_size,measure,unit,CASE WHEN quality IN ('REVIEW_REQUIRED') THEN value ELSE NULL END AS value,quality FROM mmo_internal WHERE source=? AND sheet=? AND sector=? AND establishment_size=? AND col=? AND period BETWEEN ? AND ? ORDER BY period LIMIT ?",(source,sheet,self._text(sector),self._text(size),self._text(col),start,end,self._limit(limit)))
        return self._result(rows)
