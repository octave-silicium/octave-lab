"""Inverse native relations only; no occupation equivalence or inferred exposure."""
from collections import defaultdict
from .work_explorer import norm,bounded
class ReverseIndex:
    def __init__(self,work):
        self.work=work
        self.catalog=defaultdict(dict)
        self.links=defaultdict(lambda:defaultdict(list))
        if work.onet:
            g=work.onet
            for (a,b,k),edge in g.edges.items():
                if k!="TASK_DWA":continue
                task,dwa=g.nodes[a],g.nodes[b]
                code=task["native_id"].split(":")[0]
                self.catalog["onet"][b]={"id":b,"label":dwa["label"],"kind":"DWA"}
                self.links["onet"][b].append({"occupation":code,"label":g.occupations[code]["label"],"relation":"TASK_DWA","task":a,"task_label":task["label"],"member":edge["source"],"row":edge["source_row"]})
        if work.rome:
            g=work.rome
            fields={"referentiel_competence":("SKILL","libelle_competence"),"referentiel_savoir":("KNOWLEDGE","libelle_savoir"),"referentiel_contexte_travail":("CONTEXT","libelle_cont_travail")}
            for code,links in g.links.items():
                for n,r,c,status in links:
                    if status!="NATIVE_REFERENCED":continue
                    for table in c:
                        if table not in fields:continue
                        kind,field=fields[table];key=kind+":"+r["code_ogr"]
                        item=g.index[table][r["code_ogr"]][0][1]
                        self.catalog["rome"][key]={"id":key,"label":item[field],"kind":kind}
                        self.links["rome"][key].append({"occupation":code,"label":g.occ[code][0][1]["libelle_rome"],"relation":"NATIVE_"+kind,"member":"liens_rome_referentiels","row":n})
    def concepts(self,source,q="",lang="fr",kind=None,limit=40,offset=0):
        bounded(q,limit,offset)
        if lang not in {"fr","en"}:raise ValueError("LANG")
        with self.work.lock:
            if source=="esco" and self.work.esco:
                rows=[dict(r) for r in self.work.esco.db.execute("SELECT t.uri AS id,t.label,'SKILL_OR_KNOWLEDGE' AS kind,count(DISTINCT r.occupation) AS occupations FROM esco_text t JOIN esco_relation r ON r.skill=t.uri WHERE t.lang=? GROUP BY t.uri,t.label",(lang,))]
            elif source in self.catalog:
                rows=[{**r,"occupations":len({l["occupation"] for l in self.links[source][key]})} for key,r in self.catalog[source].items()]
            else:raise ValueError("SOURCE_UNAVAILABLE")
            terms=norm(q).split()
            rows=sorted((r for r in rows if (kind is None or r["kind"]==kind) and all(t in norm(r["label"]+" "+r["id"]) for t in terms)),key=lambda r:(norm(r["label"]),r["id"]))
            return {"source":source,"total":len(rows),"rows":rows[offset:offset+limit],"next_offset":offset+limit if offset+limit<len(rows) else None,"scope":"LINKED_NATIVE_CONCEPTS_ONLY","publication":"BLOCK_PUBLICATION"}
    def reverse(self,source,id,lang="fr",limit=40,offset=0):
        bounded("",limit,offset)
        if lang not in {"fr","en"} or not isinstance(id,str) or not 1<=len(id)<=300:raise ValueError("QUERY")
        with self.work.lock:
            if source=="esco" and self.work.esco:
                db=self.work.esco.db
                concept=db.execute("SELECT t.label FROM esco_text t JOIN esco_concept c USING(uri) WHERE t.uri=? AND t.lang=? AND c.kind='skill'",(id,lang)).fetchone()
                if not concept:raise ValueError("CONCEPT")
                rows=[dict(r) for r in db.execute("SELECT r.occupation,t.label,r.relation,p.member,p.row_no AS row FROM esco_relation r JOIN esco_text t ON t.uri=r.occupation AND t.lang=? JOIN esco_relation_proof p ON p.occupation=r.occupation AND p.skill=r.skill AND p.relation=r.relation AND p.member=? WHERE r.skill=?",(lang,f"occupationSkillRelations_{lang}.csv",id))]
                title=concept[0];proof={"snapshot_sha256":self.work.esco.sha,"version_status":"USER_SUPPLIED_RELEASE"}
            elif source in self.catalog and id in self.catalog[source]:
                title=self.catalog[source][id]["label"];rows=self.links[source][id]
                proof={"sources":self.work.onet.manifest} if source=="onet" else {"archive_sha256":self.work.rome.manifest["sha256"]}
            else:raise ValueError("CONCEPT")
            groups=defaultdict(list)
            for r in rows:groups[r["occupation"]].append(r)
            result=[{"id":k,"label":v[0]["label"],"relations":v} for k,v in groups.items()]
            result.sort(key=lambda r:(norm(r["label"]),r["id"]))
            return {"source":source,"id":id,"label":title,"total":len(result),"relation_count":len(rows),"rows":result[offset:offset+limit],"next_offset":offset+limit if offset+limit<len(result) else None,"provenance":proof,"evidence":"NATIVE_RELATION_ONLY","publication":"BLOCK_PUBLICATION"}
    def dispatch(self,path,q):
        common={"source","lang","limit","offset"}
        args={k:int(v) if k in {"limit","offset"} else v for k,v in q.items()}
        if path=="/api/work/concepts" and "source" in q and set(q)<=common|{"q","kind"}:return self.concepts(**args)
        if path=="/api/work/reverse" and {"source","id"}<=set(q)<=common|{"id"}:return self.reverse(**args)
        raise ValueError("WORK_ROUTE")
