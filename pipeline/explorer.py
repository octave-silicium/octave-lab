"""G1 v0.3: loopback-only research explorer, no public publication."""
import argparse
from collections import defaultdict, Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
from pathlib import Path
from itertools import chain
import json
import re
import time
import unicodedata
import hashlib
import threading
from datetime import datetime, timezone
from . import semantic_v4 as v4

ROOT=Path(__file__).resolve().parents[1]
STATIC=ROOT/"explorer"
VERSION="0.3.0"
LABELS={
 "indeed_sector_total_daily":("Indeed · Familles professionnelles","Indice d'annonces par intitulé professionnel, pas des embauches."),
 "indeed_national_total_daily":("Indeed · France","Indice national d'annonces sur Indeed, CVS."),
 "dares_offers_monthly":("Dares · Offres France Travail","Offres collectées ou satisfaites, arrondies à la centaine. Géographie historique à qualifier."),
 "insee_employment":("Insee · Emploi salarié","Stock en fin de trimestre, CVS, en milliers. France hors Mayotte."),
 "urssaf_na88":("Urssaf · Effectifs sectoriels","Emploi privé par activité des employeurs, pas par métier."),
 "urssaf_dpae_na38":("Urssaf · Déclarations sectorielles","DPAE par activité et contrat, pas embauches effectives."),
 "urssaf_dpae_monthly":("Urssaf · Déclarations mensuelles","DPAE nationales, pas embauches effectives."),
 "eurostat_nace":("Eurostat · IA par activité","Enquête entreprises. Panier IA modifié en 2025."),
 "eurostat_size":("Eurostat · IA par taille","Enquête entreprises, classes natives. Chevauchement possible avec le jeu sectoriel.")
}
DIM_LABELS={"country":"Champ géographique","industry":"Activité économique","category_kind":"Type de catégorie","occupation_family":"Famille professionnelle","region_code":"Code région","region_label":"Région (source)","department_code":"Code département","department_label":"Département (source)","offer_type":"Type d'offre","employment_type":"Type d'emploi","qualification":"Qualification","data_type":"Type de données","geo":"Zone","nace_r2":"Activité NACE","size_emp":"Taille d'entreprise","indic_is":"Indicateur","freq":"Fréquence","unit":"Unité","secteur_na88i":"Activité NA88","secteur_na38i":"Activité NA38","secteur_na38":"Activité NA38","grand_secteur_d_activite":"Grand secteur","grand_secteur_d_activite_agrege":"Grand secteur agrégé","duree_de_contrat":"Durée du contrat","nature_de_contrat":"Nature du contrat"}
UNITS={"index_points":"Points d'indice","thousand_employees":"Milliers de salariés","offers_rounded_to_hundred":"Offres (arrondies à la centaine)","employees":"Salariés","declarations":"Déclarations","PC_ENT":"% des entreprises"}

def normalized(text):
    return "".join(c for c in unicodedata.normalize("NFKD",text.casefold()) if not unicodedata.combining(c))

WINDOWS={"D":(30,90,365),"M":(12,36,60),"Q":(4,12,20),"A":(3,5,10)}

def series_key(source,dimensions,measure,unit):
    # Native identity, independent of row ordering and observation values.
    # This is not a crosswalk and does not prove comparability across vintages.
    payload=json.dumps(["native-series-v1",source,sorted(dimensions),measure,unit,v4.FREQ[source]],ensure_ascii=False,separators=(",",":"))
    return hashlib.sha256(payload.encode()).hexdigest()

class Explorer:
    def __init__(self,catalog):
        self.catalog=catalog
        self.series={}
        self.by_key={}
        for source,rows in catalog.by.items():
            groups=defaultdict(list)
            for r in rows:
                groups[(r.dimensions,r.measure,r.unit)].append(r)
            self.series[source]=[]
            self.by_key[source]={}
            for i,(key,recs) in enumerate(sorted(groups.items())):
                dims,measure,unit=key
                recs.sort(key=lambda r:r.period)
                sid=series_key(source,dims,measure,unit)
                g={"id":sid,"dims":dict(dims),"measure":measure,"unit":unit,"rows":recs}
                if sid in self.by_key[source]:
                    raise ValueError("SERIES_KEY_COLLISION")
                self.series[source].append(g)
                self.by_key[source][sid]=g
    def group(self,source,sid):
        if source not in self.series or not isinstance(sid,str):
            raise ValueError("SERIES")
        if sid in self.by_key[source]:
            return self.by_key[source][sid]
        # Compatibility for old local callers only. Never save a numeric alias.
        if re.fullmatch(r"0|[1-9]\d{0,6}",sid) and int(sid)<len(self.series[source]):
            return self.series[source][int(sid)]
        raise ValueError("SERIES")
    def sources(self):
        return [{"id":s,"label":LABELS[s][0],"description":LABELS[s][1],"series":len(self.series[s]),"frequency":v4.FREQ[s],"persistence":"ARCHIVE" if s in v4.ARCHIVE_SOURCES else "LIVE","vintage":self.catalog.vintages[s][0],"license":v4.LICENSE[s]} for s in LABELS if s in self.series]
    def discover(self,source,filters,query=""):
        if source not in self.series or not isinstance(filters,dict) or not set(filters)<=v4.NATIVE_DIMS[source]|{"_measure","_unit"}:
            raise ValueError("FILTER")
        if any(not isinstance(v,str) or len(v)>500 for v in filters.values()):
            raise ValueError("FILTER_VALUE")
        def fields(g):
            return {**g["dims"],"_measure":g["measure"],"_unit":g["unit"]}
        if not isinstance(query,str) or len(query)>160:
            raise ValueError("SEARCH_QUERY")
        terms=normalized(query).split()
        eligible=[g for g in self.series[source] if all(t in normalized(" ".join(fields(g).values())) for t in terms)]
        groups=[g for g in eligible if all(fields(g).get(k)==v for k,v in filters.items())]
        choices={}
        for key in sorted(v4.NATIVE_DIMS[source]|{"_measure","_unit"}):
            counts=Counter(fields(g)[key] for g in eligible if all(k==key or fields(g).get(k)==v for k,v in filters.items()))
            choices[key]=[{"value":v,"count":n} for v,n in sorted(counts.items())]
        return {"total":len(groups),"query":query,"choices":choices,"series":[{"id":g["id"],"dimensions":g["dims"],"measure":g["measure"],"unit":g["unit"],"count":len(g["rows"]),"start":g["rows"][0].period,"end":g["rows"][-1].period} for g in groups[:100]],"truncated":len(groups)>100}
    def detail(self,source,sid,start=None,end=None,offset=0,limit=50):
        g=self.group(source,sid)
        if any(p is not None and not v4.valid_period(source,p) for p in (start,end)) or start and end and start>end:
            raise ValueError("PERIOD")
        if type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=100:
            raise ValueError("PAGE")
        rows=[r for r in g["rows"] if (start is None or r.period>=start) and (end is None or r.period<=end)]
        if len(rows)>4000:
            raise ValueError("NARROW_PERIOD")
        points=[]
        for r in rows:
            level,_=r.quality
            points.append({"period":r.period,"value":str(r.value) if r.value is not None and level not in {"WITHHELD","RESTRICTED"} else None,"quality":level,"flag":r.flag})
        records=[]
        for r in rows[offset:offset+limit]:
            d=r.internal_result()
            if d["quality"] in {"WITHHELD","RESTRICTED"}:
                d["value"]=None
            records.append(d)
        windows=[{"count":n,"start":g["rows"][-n].period,"end":g["rows"][-1].period} for n in WINDOWS[v4.FREQ[source]] if len(g["rows"])>=n]
        return {"windows":windows,"source":source,"id":g["id"],"snapshot_sha256":self.catalog.vintages[source][1],"vintage":self.catalog.vintages[source][0],"persistence":"ARCHIVE" if source in v4.ARCHIVE_SOURCES else "LIVE","dimensions":g["dims"],"measure":g["measure"],"unit":g["unit"],"unit_label":UNITS.get(g["unit"],g["unit"]),"total":len(rows),"offset":offset,"next_offset":offset+limit if offset+limit<len(rows) else None,"points":points,"records":records,"quality":dict(Counter(r.quality[0] for r in rows)),"full_start":g["rows"][0].period,"full_end":g["rows"][-1].period,"comparison":"REVIEW_REQUIRED","publication":"BLOCK_PUBLICATION"}
    def comparison(self,source,sid,start,end):
        # Exact observations, same native series and vintage. No change calculated.
        if not start or not end or not v4.valid_period(source,start) or not v4.valid_period(source,end) or start>=end:
            raise ValueError("COMPARISON_PERIOD")
        self.detail(source,sid,start,end,limit=1)  # validate identifiers and bounds
        rows=[r for r in self.group(source,sid)["rows"] if start<=r.period<=end]
        if not rows or rows[0].period!=start or rows[-1].period!=end:
            return {"decision":"BLOCK","reason":"MISSING_ENDPOINT","periods":[start,end],"change":None}
        blockers=Counter(reason for r in rows if r.quality[0] in {"RESTRICTED","WITHHELD"} for reason in r.quality[1])
        if blockers:
            return {"decision":"BLOCK","reason":"QUALITY_RESTRICTION_IN_INTERVAL","quality_reasons":sorted(blockers),"periods":[start,end],"change":None}
        if any(r.flag for r in rows):
            return {"decision":"REVIEW_REQUIRED","reason":"SOURCE_FLAG_IN_INTERVAL","periods":[start,end],"change":None}
        decision=v4.compare(rows[0],rows[-1])
        return {"decision":"BLOCK" if decision.startswith("BLOCK") else "REVIEW_REQUIRED","reason":decision,"periods":[start,end],"change":None}

    def point(self,source,sid,period):
        result=self.detail(source,sid,period,period,limit=1)
        if result["total"]!=1:
            raise ValueError("POINT")
        return result["records"][0]

def archive_catalog():
    records=chain((v4.v2.wrap(o) for o in v4.v2.v1.read_insee()),v4.v2.iter_indeed(),v4.v2.iter_dares())
    return v4.Catalog(v4.wrap_archive(c) for c in records)

def load_source(source):
    if source=="insee_employment":
        cells=(v4.v2.wrap(o) for o in v4.v2.v1.read_insee())
    elif source.startswith("indeed_") and source in v4.ARCHIVE_SOURCES:
        cells=v4.v2.iter_indeed(only_series=source)
    elif source=="dares_offers_monthly":
        cells=v4.v2.iter_dares()
    elif source in v4.LIVE_SOURCES:
        raw=v4.v3.retrieve(v4.v3.SOURCES[source])
        stamp=datetime.now(timezone.utc).isoformat()
        rows,_=(v4.v3.read_urssaf if source in v4.v3.URSSAF else v4.v3.read_euro)(source,raw,stamp)
        return v4.Catalog(v4.wrap_live(r) for r in rows)
    else:
        raise ValueError("SOURCE")
    return v4.Catalog(v4.wrap_archive(c) for c in cells)


class LazyExplorer:
    """Single verified load per source and process. Failures do not poison other sources."""
    def __init__(self,live=False,loader=load_source):
        self.allowed=set(v4.ARCHIVE_SOURCES)|(set(v4.LIVE_SOURCES) if live else set())
        self.loader=loader
        self.loaded={}
        self.locks={s:threading.Lock() for s in self.allowed}
    def sources(self):
        result=[]
        for s in LABELS:
            if s not in self.allowed:
                continue
            loaded=self.loaded.get(s)
            if loaded:
                result.extend(loaded.sources())
            else:
                result.append({"id":s,"label":LABELS[s][0],"description":LABELS[s][1],
                    "series":None,"frequency":v4.FREQ[s],"persistence":"ARCHIVE" if s in v4.ARCHIVE_SOURCES else "LIVE",
                    "vintage":None,"license":v4.LICENSE[s]})
        return result
    def get(self,source):
        if source not in self.allowed:
            raise ValueError("SOURCE")
        with self.locks[source]:
            if source not in self.loaded:
                cat=self.loader(source)
                if set(cat.by)!={source}:
                    raise ValueError("SOURCE_SCOPE")
                self.loaded[source]=Explorer(cat)
            return self.loaded[source]
    def discover(self,source,filters,query=""):
        x=self.get(source)
        d=x.discover(source,filters,query)
        d["source_meta"]=x.sources()[0]
        return d
    def detail(self,source,*args,**kwargs):
        return self.get(source).detail(source,*args,**kwargs)
    def point(self,source,*args,**kwargs):
        return self.get(source).point(source,*args,**kwargs)
    def comparison(self,source,*args,**kwargs):
        return self.get(source).comparison(source,*args,**kwargs)
    def restore(self,source,sid,sha,start=None,end=None):
        if source not in v4.ARCHIVE_SOURCES or not re.fullmatch(r"[0-9a-f]{64}",sid) or not re.fullmatch(r"[0-9a-f]{64}",sha):
            raise ValueError("SAVED_RESEARCH_SCOPE")
        x=self.get(source)
        if x.catalog.vintages[source][1]!=sha:
            return {"decision":"VINTAGE_MISMATCH","publication":"BLOCK_PUBLICATION"}
        return {"decision":"MATCH","series":x.detail(source,sid,start,end)}


def make_handler(explorer):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass
        def send(self,status,data,typ):
            self.send_response(status)
            for k,v in {"Content-Type":typ,"Content-Length":str(len(data)),"Cache-Control":"no-store","X-Content-Type-Options":"nosniff","Referrer-Policy":"no-referrer","X-Frame-Options":"DENY","Content-Security-Policy":"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"}.items():
                self.send_header(k,v)
            self.end_headers()
            self.wfile.write(data)
        def j(self,status,d):
            self.send(status,json.dumps(d,ensure_ascii=False,separators=(",",":")).encode(),"application/json; charset=utf-8")
        def do_GET(self):
            if self.headers.get("Host","")!=f"127.0.0.1:{self.server.server_port}" or self.headers.get("Sec-Fetch-Site") not in (None,"none","same-origin"):
                return self.j(403,{"error":"Accès local uniquement."})
            if len(self.path)>8192:
                return self.j(400,{"error":"Requête trop longue."})
            try:
                u=urlsplit(self.path)
                if u.path in {"/","/app.js","/style.css"}:
                    name={"/":"index.html","/app.js":"app.js","/style.css":"style.css"}[u.path]
                    typ={"index.html":"text/html; charset=utf-8","app.js":"text/javascript; charset=utf-8","style.css":"text/css; charset=utf-8"}[name]
                    return self.send(200,(STATIC/name).read_bytes(),typ)
                q=parse_qs(u.query,keep_blank_values=True,max_num_fields=12)
                if any(len(v)!=1 for v in q.values()):
                    raise ValueError("DUPLICATE_PARAMETER")
                q={k:v[0] for k,v in q.items()}
                if u.path=="/api/sources" and not q:
                    return self.j(200,{"version":VERSION,"sources":explorer.sources(),"mode":"LOCAL_INTERNAL","labels":DIM_LABELS})
                if u.path=="/api/discover" and set(q)<={"source","filters","q"}:
                    return self.j(200,explorer.discover(q["source"],json.loads(q.get("filters","{}")),q.get("q","")))
                if u.path=="/api/compare" and set(q)=={"source","id","start","end"}:
                    return self.j(200,explorer.comparison(q["source"],q["id"],q["start"],q["end"]))
                if u.path=="/api/series" and set(q)<={"source","id","start","end","offset"}:
                    return self.j(200,explorer.detail(q["source"],q["id"],q.get("start") or None,q.get("end") or None,int(q.get("offset","0"))))
                if u.path=="/api/restore" and set(q)=={"source","id","sha","start","end"} and isinstance(explorer,LazyExplorer):
                    return self.j(200,explorer.restore(q["source"],q["id"],q["sha"],q["start"] or None,q["end"] or None))
                if u.path=="/api/point" and set(q)=={"source","id","period"}:
                    return self.j(200,explorer.point(q["source"],q["id"],q["period"]))
                return self.j(404,{"error":"Ressource inconnue ou non autorisée."})
            except (ValueError,KeyError,TypeError):
                return self.j(400,{"error":"Sélection incompatible. Vérifier les filtres et la période."})
            except (BrokenPipeError,ConnectionResetError):
                return
            except Exception:
                return self.j(500,{"error":"Lecture indisponible. Aucune donnée de remplacement."})
    return Handler

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--live",action="store_true")
    ap.add_argument("--port",type=int,default=8765)
    args=ap.parse_args()
    t=time.perf_counter()
    server=ThreadingHTTPServer(("127.0.0.1",args.port),make_handler(LazyExplorer(live=args.live)))
    print(f"Octave Lab local : http://127.0.0.1:{server.server_port} | prêt en {time.perf_counter()-t:.2f}s",flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()

if __name__=="__main__":
    main()
