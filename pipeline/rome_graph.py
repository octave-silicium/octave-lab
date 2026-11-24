"""ROME v462 source-native graph; preserve unresolved or ambiguous references."""
import csv,io,json,re,zipfile
from collections import Counter,defaultdict
from .rome_inventory import inspect,URL
from .european_work import fetch
VERSION="v462"
KEYS={"referentiel_code_rome":"code_rome","referentiel_appellation":"code_ogr","referentiel_competence":"code_ogr","referentiel_savoir":"code_ogr_savoir","referentiel_contexte_travail":"code_ogr","item":"code_ogr"}
TYPES=("referentiel_competence","referentiel_savoir","referentiel_contexte_travail")
class Graph:
    def __init__(self,tables,manifest,release):
        self.tables=tables;self.manifest=manifest;self.release=release
        self.index={}
        for t,k in KEYS.items():
            ix=defaultdict(list)
            for n,r in tables[t]:
                if r[k].strip():ix[r[k]].append((n,r))
            self.index[t]=dict(ix)
        self.occ=self.index["referentiel_code_rome"]
        if len(self.occ)!=len(tables["referentiel_code_rome"]) or any(len(v)!=1 or not re.fullmatch(r"[A-Z]\d{4}",k) for k,v in self.occ.items()):raise ValueError("OCCUPATION_KEY")
        self.links=defaultdict(list);self.counts=Counter();self.types=Counter()
        for n,r in tables["liens_rome_referentiels"]:
            o,k=r["code_rome"],r["code_ogr"]
            candidates=[t for t in (*TYPES,"item") if k in self.index[t]]
            types=[t for t in candidates if t!="item"]
            if o not in self.occ:status="ORPHAN_OCCUPATION"
            elif not candidates:status="UNRESOLVED_ITEM"
            elif len(types)>1 or any(len(self.index[t][k])>1 for t in candidates):status="AMBIGUOUS_REFERENCE"
            else:status="NATIVE_REFERENCED"
            self.links[o].append((n,r,candidates,status));self.counts[status]+=1
            self.types[types[0] if len(types)==1 else "item_only" if not types and candidates else "unresolved_or_multiple"]+=1
    def profile(self,code):
        if code not in self.occ:raise ValueError("UNKNOWN_OCCUPATION")
        n,r=self.occ[code][0]
        return {"occupation":r,"row":n,"release":self.release,"links":[{"row":i,"native":v,"status":s,"references":[{"table":t,"row":j,"native":w} for t in c for j,w in self.index[t][v["code_ogr"]]] if s=="NATIVE_REFERENCED" else []} for i,v,c,s in self.links.get(code,[])],"tasks":[],"actions":[],"publication":"BLOCK_PUBLICATION","attribution":"France Travail, ROME, données ouvertes ; réorganisation Octave Lab."}
    def audit(self):
        return {"status":"NATIVE_GRAPH_LOADED","version_token":VERSION,"release":self.release,"archive_sha256":self.manifest["sha256"],"tables":{k:len(v) for k,v in self.tables.items()},"occupations":len(self.occ),"occupations_with_links":sum(k in self.links for k in self.occ),"link_status":dict(self.counts),"link_type_candidates":dict(self.types),"duplicate_native_ids":{t:sum(len(v)-1 for v in ix.values()) for t,ix in self.index.items()},"crosswalks_validated":0,"actions":0,"publication":"BLOCK_PUBLICATION"}
def load(raw):
    m=inspect(raw);tables={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        release=z.read("version.txt").decode("utf-8-sig").strip()
        if not release or len(release)>1000:raise ValueError("VERSION")
        for name,meta in m["members"].items():
            if not name.endswith(".csv"):continue
            x=re.fullmatch(r"unix_(.+)_"+VERSION+r"_utf8\.csv",name)
            if not x or meta["separator"]!="," or any(int(k)!=len(meta["columns"]) for k in meta["row_widths"]):raise ValueError("SCHEMA")
            table=x[1]
            rows=list(enumerate(csv.DictReader(io.StringIO(z.read(name).decode(meta["encoding"]),newline="")),2))
            if len(rows)!=meta["rows"] or table in tables:raise ValueError("ROWS")
            if table in KEYS and KEYS[table] not in meta["columns"]:raise ValueError("KEY")
            if table=="liens_rome_referentiels" and not {"code_rome","code_ogr","code_rubrique","code_compo_bloc"}<=set(meta["columns"]):raise ValueError("LINK_SCHEMA")
            tables[table]=rows
    if not set(KEYS)|{"liens_rome_referentiels"}<=set(tables):raise ValueError("MISSING_TABLE")
    return Graph(tables,m,release)
if __name__=="__main__":
    raw,_,_=fetch(URL)
    print(json.dumps(load(raw).audit(),ensure_ascii=False,indent=2))
