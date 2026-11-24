"""G1 v0.1: loopback-only research explorer, no public publication."""
import argparse
from collections import defaultdict, Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
from pathlib import Path
from itertools import chain
import json
import re
import time
from . import semantic_v4 as v4

ROOT=Path(__file__).resolve().parents[1]
STATIC=ROOT/"explorer"
VERSION="0.1.0"
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

class Explorer:
    def __init__(self,catalog):
        self.catalog=catalog
        self.series={}
        for source,rows in catalog.by.items():
            groups=defaultdict(list)
            for r in rows:
                groups[(r.dimensions,r.measure,r.unit)].append(r)
            self.series[source]=[]
            for i,(key,recs) in enumerate(sorted(groups.items())):
                dims,measure,unit=key
                recs.sort(key=lambda r:r.period)
                self.series[source].append({"id":str(i),"dims":dict(dims),"measure":measure,"unit":unit,"rows":recs})
    def sources(self):
        return [{"id":s,"label":LABELS[s][0],"description":LABELS[s][1],"series":len(self.series[s]),"frequency":v4.FREQ[s],"persistence":"ARCHIVE" if s in v4.ARCHIVE_SOURCES else "LIVE","vintage":self.catalog.vintages[s][0],"license":v4.LICENSE[s]} for s in LABELS if s in self.series]
    def discover(self,source,filters):
        if source not in self.series or not isinstance(filters,dict) or not set(filters)<=v4.NATIVE_DIMS[source]|{"_measure","_unit"}:
            raise ValueError("FILTER")
        if any(not isinstance(v,str) or len(v)>500 for v in filters.values()):
            raise ValueError("FILTER_VALUE")
        def fields(g):
            return {**g["dims"],"_measure":g["measure"],"_unit":g["unit"]}
        groups=[g for g in self.series[source] if all(fields(g).get(k)==v for k,v in filters.items())]
        choices={}
        for key in sorted(v4.NATIVE_DIMS[source]|{"_measure","_unit"}):
            counts=Counter(fields(g)[key] for g in groups)
            choices[key]=[{"value":v,"count":n} for v,n in sorted(counts.items())]
        return {"total":len(groups),"choices":choices,"series":[{"id":g["id"],"dimensions":g["dims"],"measure":g["measure"],"unit":g["unit"],"count":len(g["rows"]),"start":g["rows"][0].period,"end":g["rows"][-1].period} for g in groups[:100]],"truncated":len(groups)>100}
    def detail(self,source,sid,start=None,end=None,offset=0,limit=50):
        if source not in self.series or not re.fullmatch(r"0|[1-9]\d{0,6}",sid) or int(sid)>=len(self.series[source]):
            raise ValueError("SERIES")
        if any(p is not None and not v4.valid_period(source,p) for p in (start,end)) or start and end and start>end:
            raise ValueError("PERIOD")
        if type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=100:
            raise ValueError("PAGE")
        g=self.series[source][int(sid)]
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
        return {"source":source,"id":sid,"dimensions":g["dims"],"measure":g["measure"],"unit":g["unit"],"unit_label":UNITS.get(g["unit"],g["unit"]),"total":len(rows),"offset":offset,"next_offset":offset+limit if offset+limit<len(rows) else None,"points":points,"records":records,"quality":dict(Counter(r.quality[0] for r in rows)),"full_start":g["rows"][0].period,"full_end":g["rows"][-1].period,"comparison":"REVIEW_REQUIRED","publication":"BLOCK_PUBLICATION"}
    def point(self,source,sid,period):
        result=self.detail(source,sid,period,period,limit=1)
        if result["total"]!=1:
            raise ValueError("POINT")
        return result["records"][0]

def archive_catalog():
    records=chain((v4.v2.wrap(o) for o in v4.v2.v1.read_insee()),v4.v2.iter_indeed(),v4.v2.iter_dares())
    return v4.Catalog(v4.wrap_archive(c) for c in records)

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
                if u.path=="/api/discover" and set(q)<={"source","filters"}:
                    return self.j(200,explorer.discover(q["source"],json.loads(q.get("filters","{}"))))
                if u.path=="/api/series" and set(q)<={"source","id","start","end","offset"}:
                    return self.j(200,explorer.detail(q["source"],q["id"],q.get("start") or None,q.get("end") or None,int(q.get("offset","0"))))
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
    catalog=v4.build_catalog()[0] if args.live else archive_catalog()
    server=ThreadingHTTPServer(("127.0.0.1",args.port),make_handler(Explorer(catalog)))
    print(f"Octave Lab local : http://127.0.0.1:{server.server_port} | prêt en {time.perf_counter()-t:.2f}s",flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()

if __name__=="__main__":
    main()
