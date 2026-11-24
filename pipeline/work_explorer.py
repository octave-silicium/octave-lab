"""Read-only native work explorer. Source types are deliberately not merged."""
import hashlib,json,threading,unicodedata
from pathlib import Path
from . import work_graph,rome_graph
from .private_lot import PrivateLot

def norm(s):return "".join(c for c in unicodedata.normalize("NFKD",s.casefold()) if not unicodedata.combining(c))
def bounded(q,limit,offset):
    if not isinstance(q,str) or len(q)>160 or type(limit)!=int or not 1<=limit<=100 or type(offset)!=int or not 0<=offset<=20000:raise ValueError("QUERY")
def read_pinned(path,sha):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError("SNAPSHOT_HASH")
    return raw

class WorkExplorer:
    def __init__(self,onet=None,rome=None,esco=None,ratings=None):
        self.onet=onet;self.rome=rome;self.esco=esco;self.ratings=ratings;self.lock=threading.RLock()
        from .work_reverse import ReverseIndex
        self.reverse=ReverseIndex(self)
    def close(self):
        if self.esco:self.esco.close()
    def sources(self):
        return [{"id":s,"label":label,"scope":scope,"available":g is not None,"count":count} for s,label,scope,g,count in (
            ("onet","O*NET 31.0","US",self.onet,len(self.onet.occupations) if self.onet else None),
            ("rome","ROME v462","FR",self.rome,len(self.rome.occ) if self.rome else None),
            ("esco","ESCO 1.2.1 (version déclarée)","EU",self.esco,self.esco.db.execute("SELECT count(*) FROM esco_concept WHERE kind='occupation'").fetchone()[0] if self.esco else None))]
    def search(self,source,q="",lang="fr",limit=40,offset=0):
        bounded(q,limit,offset)
        if lang not in {"fr","en"}:raise ValueError("LANG")
        terms=norm(q).split()
        with self.lock:
            if source=="onet" and self.onet:
                rows=[{"id":k,"label":r["label"],"count":len(self.onet.by_occ.get(k,[]))} for k,r in self.onet.occupations.items()]
            elif source=="rome" and self.rome:
                rows=[{"id":k,"label":r[0][1]["libelle_rome"],"count":len(self.rome.links.get(k,[]))} for k,r in self.rome.occ.items()]
            elif source=="esco" and self.esco:
                rows=[dict(r) for r in self.esco.db.execute("SELECT t.uri AS id,t.label,(SELECT count(*) FROM esco_relation r WHERE r.occupation=t.uri) AS count FROM esco_text t JOIN esco_concept c USING(uri) WHERE c.kind='occupation' AND t.lang=?",(lang,))]
            else:raise ValueError("SOURCE_UNAVAILABLE")
            rows=sorted((r for r in rows if all(t in norm(r["id"]+" "+r["label"]) for t in terms)),key=lambda r:(norm(r["label"]),r["id"]))
            return {"source":source,"total":len(rows),"rows":rows[offset:offset+limit],"next_offset":offset+limit if offset+limit<len(rows) else None,"publication":"BLOCK_PUBLICATION"}
    def profile(self,source,id,lang="fr",limit=50,offset=0):
        bounded("",limit,offset)
        if not isinstance(id,str) or not id.strip() or len(id)>300 or lang not in {"fr","en"}:raise ValueError("PROFILE")
        with self.lock:
            if source=="onet" and self.onet:
                p=self.onet.profile(id);o=p["occupation"];rows=[{"kind":"TASK","label":t["task"]["label"],"id":t["task"]["id"],"row":t["task"]["source_row"],"member":t["task"]["source"],"related":[{"label":a["label"],"id":a["id"],"row":a["source_row"],"member":a["source"]} for a in t["activities"]]} for t in p["tasks"]]
                title=o["label"];desc=o["extras"]["description"];provenance={"sources":self.onet.manifest,"attribution":p["attribution"],"license":p["license"]}
            elif source=="rome" and self.rome:
                p=self.rome.profile(id);title=p["occupation"]["libelle_rome"];desc=""
                fields={"referentiel_code_rome":("IDENTITY","libelle_rome"),"referentiel_appellation":("APPELLATION","libelle_appellation_long"),"referentiel_competence":("SKILL","libelle_competence"),"referentiel_savoir":("KNOWLEDGE","libelle_savoir"),"referentiel_contexte_travail":("CONTEXT","libelle_cont_travail"),"item":("ITEM","libelle")}
                rows=[]
                for l in p["links"]:
                    for r in l["references"]:
                        if r["table"]=="item" and len(l["references"])>1:continue
                        kind,field=fields[r["table"]]
                        rows.append({"kind":kind,"label":r["native"][field],"id":l["native"]["code_ogr"],"row":r["row"],"member":r["table"],"link_row":l["row"]})
                    if not l["references"]:rows.append({"kind":"UNRESOLVED","label":l["status"],"id":l["native"]["code_ogr"],"row":l["row"],"member":"liens_rome_referentiels"})
                provenance={"archive_sha256":self.rome.manifest["sha256"],"release":p["release"],"attribution":p["attribution"]}
            elif source=="esco" and self.esco:
                db=self.esco.db
                o=db.execute("SELECT t.label,t.description FROM esco_text t JOIN esco_concept c USING(uri) WHERE c.kind='occupation' AND t.uri=? AND t.lang=?",(id,lang)).fetchone()
                if not o:raise ValueError("UNKNOWN_OCCUPATION")
                title,desc=o
                rows=[dict(r) for r in db.execute("SELECT CASE r.relation WHEN 'essential' THEN 'ESSENTIAL' ELSE 'OPTIONAL' END AS kind,t.label,r.skill AS id,p.member,p.row_no AS row FROM esco_relation r JOIN esco_text t ON t.uri=r.skill AND t.lang=? JOIN esco_relation_proof p ON p.occupation=r.occupation AND p.skill=r.skill AND p.relation=r.relation AND p.member=? WHERE r.occupation=? ORDER BY r.relation,t.label,r.skill",(lang,f"occupationSkillRelations_{lang}.csv",id))]
                names={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if {"esco_extra_edge","esco_extra_node"}<=names:
                    rows.extend(dict(r) for r in db.execute("SELECT 'BROADER' AS kind,coalesce(n.label,t.label) AS label,e.target AS id,e.member,e.row_no AS row FROM esco_extra_edge e LEFT JOIN esco_extra_node n ON n.uri=e.target AND n.lang=e.lang LEFT JOIN esco_text t ON t.uri=e.target AND t.lang=e.lang WHERE e.lang=? AND e.kind='broaderRelationsOccPillar' AND e.origin=? ORDER BY e.target",(lang,id)))
                provenance={"snapshot_sha256":self.esco.sha,"attribution":"European Commission, ESCO; reorganisation Octave Lab.","version_status":"USER_SUPPLIED_RELEASE"}
            else:raise ValueError("SOURCE_UNAVAILABLE")
            return {"source":source,"id":id,"label":title,"description":desc,"total":len(rows),"rows":rows[offset:offset+limit],"next_offset":offset+limit if offset+limit<len(rows) else None,"provenance":provenance,"evidence":"REFERENCE_DESCRIPTION_ONLY","actions":[],"impact_estimates":[],"publication":"BLOCK_PUBLICATION"}
    def dispatch(self,path,q):
        if path=="/api/work/sources" and not q:
            with self.lock:return {"sources":self.sources()}
        if path=="/api/work/ratings" and set(q)=={"id"} and self.ratings:
            return self.ratings.task(q["id"])
        common={"source","lang","limit","offset"}
        if path in {"/api/work/concepts","/api/work/reverse"}:
            return self.reverse.dispatch(path,q)
        args={k:int(q[k]) if k in {"limit","offset"} else q[k] for k in q}
        if path=="/api/work/search" and "source" in q and set(q)<=common|{"q"}:return self.search(**args)
        if path=="/api/work/profile" and {"source","id"}<=set(q)<=common|{"id"}:return self.profile(**args)
        raise ValueError("WORK_ROUTE")
