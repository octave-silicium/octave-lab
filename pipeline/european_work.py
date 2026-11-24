"""G2 v0.2 European reference acquisition and native ESCO CSV import."""
import argparse,csv,hashlib,io,json,re,zipfile
from pathlib import Path,PurePosixPath
from collections import Counter,defaultdict
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from urllib.parse import urlencode,urlsplit

ESCO_VERSION="1.2.1"
ESCO_NOTICE="This service uses the ESCO classification of the European Commission. Data reorganized by Octave Lab."
ESCO_TERMS="https://esco.ec.europa.eu/en/use-esco/download/privacy-statement"
ROME_META="https://www.data.gouv.fr/api/1/datasets/repertoire-operationnel-des-metiers-et-des-emplois-rome/"
ROME_TERMS="https://www.francetravail.org/files/live/sites/peorg/files/documents/Statistiques-et-analyses/Open-data/ROME/rome_licence_ouverte.pdf"
ESCO_API="https://ec.europa.eu/esco/api/resource/occupation"
EXAMPLE_URI="http://data.europa.eu/esco/occupation/528f90ed-e250-48bd-aacc-ffb7b1de5654"
MAX_BYTES=100_000_000

def digest(raw):return hashlib.sha256(raw).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def fetch(url,limit=MAX_BYTES):
    with urlopen(Request(url,headers={"User-Agent":"OctaveLab research/0.2","Accept":"application/json, application/octet-stream, */*"}),timeout=30) as response:
        raw=response.read(limit+1)
        if len(raw)>limit:raise ValueError("SIZE_LIMIT")
        return raw,response.headers.get("Content-Type",""),response.geturl()

def rows(raw,required):
    r=csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
    if not required<=set(r.fieldnames or []) or len(set(r.fieldnames or []))!=len(r.fieldnames or []):raise ValueError("SCHEMA")
    for n,row in enumerate(r,2):
        if None in row or any(row[k] is None for k in required):raise ValueError("ROW_SHAPE")
        yield n,row

def concept(uri,kind):
    if not re.fullmatch(r"https?://data\.europa\.eu/esco/"+kind+r"/[0-9a-fA-F-]{36}",uri):raise ValueError("URI_TYPE")
    return uri.replace("https://","http://",1)

class EscoGraph:
    def __init__(self,files,manifest):
        self.manifest=manifest
        self.occupations={};self.skills={};self.edges={};self.by_occ=defaultdict(list)
        for key,kind,target in (("occupations_fr","occupation",self.occupations),("skills_fr","skill",self.skills)):
            for n,r in rows(files[key],{"conceptUri","preferredLabel"}):
                uri=concept(r["conceptUri"],kind)
                if uri in target or not r["preferredLabel"].strip():raise ValueError("CONCEPT_DUPLICATE_OR_EMPTY")
                target[uri]={"id":f"esco:{ESCO_VERSION}:{uri}","uri":uri,"kind":kind,"label":r["preferredLabel"],"description":r.get("description",""),"native_type":r.get("skillType",""),"source":key,"row":n,"status":"SOURCE_DOCUMENTED","language":"fr"}
        for n,r in rows(files["occupationSkillRelations"],{"occupationUri","skillUri","relationType"}):
            a,b=concept(r["occupationUri"],"occupation"),concept(r["skillUri"],"skill")
            typ=r["relationType"]
            if a not in self.occupations or b not in self.skills:raise ValueError("DANGLING_EDGE")
            if typ not in {"essential","optional"}:raise ValueError("RELATION_TYPE")
            key=(a,b)
            if key in self.edges:raise ValueError("DUPLICATE_OR_CONFLICTING_EDGE")
            self.edges[key]={"from":self.occupations[a]["id"],"to":self.skills[b]["id"],"kind":typ,"source":"occupationSkillRelations","row":n,"status":"SOURCE_DOCUMENTED"}
            self.by_occ[a].append((b,typ))
        if not self.occupations or not self.skills or not self.edges:raise ValueError("EMPTY_GRAPH")
    def profile(self,uri):
        uri=concept(uri,"occupation")
        if uri not in self.occupations:raise ValueError("UNKNOWN_OCCUPATION")
        return {"occupation":self.occupations[uri],"skills":[{"skill":self.skills[b],"relation":t} for b,t in self.by_occ[uri]],"tasks":[],"atomic_actions":[],"crosswalks":[],"scope":"EU_CLASSIFICATION_NOT_OBSERVED_WORK","attribution":ESCO_NOTICE}
    def audit(self):
        return {"occupations":len(self.occupations),"skills":len(self.skills),"edges":len(self.edges),"relation_types":dict(Counter(e["kind"] for e in self.edges.values())),"occupations_with_skills":len(self.by_occ),"occupations_without_skills":len(self.occupations)-len(self.by_occ),"manifest":self.manifest,"version_claim":ESCO_VERSION,"version_status":"USER_SUPPLIED_RELEASE_NOT_INDEPENDENTLY_VERIFIED","attribution":ESCO_NOTICE,"crosswalks":0,"atomic_actions":0,"public_release":"BLOCKED_PENDING_RELEASE_VERIFICATION"}

def import_esco(path,expected_sha256):
    raw=Path(path).read_bytes()
    if len(raw)>MAX_BYTES or not re.fullmatch(r"[0-9a-f]{64}",expected_sha256) or digest(raw)!=expected_sha256:raise ValueError("ARCHIVE_INTEGRITY")
    files={};manifest={"archive_sha256":expected_sha256,"terms":ESCO_TERMS,"members":{}}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if sum(i.file_size for i in z.infolist())>250_000_000:raise ValueError("UNCOMPRESSED_LIMIT")
        for info in z.infolist():
            name=PurePosixPath(info.filename).name
            if name not in {"occupations_fr.csv","skills_fr.csv","occupationSkillRelations.csv","occupationSkillRelations_fr.csv"}:continue
            key=name.removesuffix(".csv")
            if key=="occupationSkillRelations_fr":key="occupationSkillRelations"
            if key in files:raise ValueError("AMBIGUOUS_MEMBER")
            files[key]=z.read(info)
            manifest["members"][key]={"name":info.filename,"sha256":digest(files[key]),"bytes":len(files[key])}
    if set(files)!={"occupations_fr","skills_fr","occupationSkillRelations"}:raise ValueError("MISSING_MEMBERS")
    return EscoGraph(files,manifest)

def access_audit(fetcher=fetch):
    report={"retrieved_at":now(),"esco":{"target_version":ESCO_VERSION,"full_zip":"OFFICIAL_FORM_HUMAN_DOWNLOAD_REQUIRED","terms":ESCO_TERMS},"rome":{"terms":ROME_TERMS},"crosswalks":0}
    try:
        raw,typ,final=fetcher(ROME_META,5_000_000)
        d=json.loads(raw)
        if d.get("slug")!="repertoire-operationnel-des-metiers-et-des-emplois-rome":raise ValueError("ROME_DATASET_ID")
        res=[]
        for r in d["resources"]:
            extra=r.get("extras") or {}
            res.append({"id":r["id"],"title":r.get("title"),"format":r.get("format"),"url":r.get("url"),"last_modified":r.get("last_modified"),"provider_check_available":extra.get("check:available"),"provider_check_status":extra.get("check:status")})
        report["rome"].update({"status":"METADATA_VERIFIED","license":d.get("license"),"last_modified":d.get("last_modified"),"metadata_sha256":digest(raw),"resources":res,"resource_count":len(res),"provider_unavailable_count":sum(r["provider_check_available"] is False for r in res)})
        # Probe only explicitly published resource URLs for official métier files.
        candidates=[r for r in res if r["format"] in {"xlsx","csv","zip","json"} and any(t in (r["title"] or "").casefold() for t in ("toutes les données du rome","fiches métiers","référentiel des métiers","arborescence principale"))]
        candidates.sort(key=lambda r: (0 if r["format"]=="csv" else 1 if r["format"]=="json" else 2,r["title"]))
        probes=[]
        for r in candidates[:2]:
            u=r["url"];host=urlsplit(u).hostname or ""
            if urlsplit(u).scheme!="https" or not (host=="api.francetravail.fr" or host=="francetravail.org" or host.endswith(".francetravail.org") or host=="data.gouv.fr" or host.endswith(".data.gouv.fr")):continue
            try:
                b,ct,end=fetcher(u,MAX_BYTES)
                actual="ZIP_CONTAINER" if b.startswith(b"PK\x03\x04") else "HTML_OR_OTHER"
                probes.append({"id":r["id"],"status":"BYTES_RECEIVED","content_type":ct,"format_check":actual,"bytes":len(b),"sha256":digest(b)})
            except HTTPError as e:probes.append({"id":r["id"],"status":"HTTP_BLOCKED","http_status":e.code})
            except Exception as e:probes.append({"id":r["id"],"status":"UNAVAILABLE","error_type":type(e).__name__})
        report["rome"]["probes"]=probes
        report["rome"]["ingestion"]="NOT_VALIDATED"
    except Exception as e:report["rome"].update({"status":"BLOCKED","error_type":type(e).__name__})
    # The public API documents v1.2.0. Probe only that explicit version, no fallback.
    url=ESCO_API+"?"+urlencode({"uri":EXAMPLE_URI,"language":"fr","selectedVersion":"v1.2.0"})
    try:
        raw,typ,final=fetcher(url,2_000_000)
        d=json.loads(raw)
        if d.get("uri")!=EXAMPLE_URI:raise ValueError("ESCO_URI")
        links=d.get("_links") or {}
        report["esco"]["api_probe"]={"status":"PROFILE_RESPONSE_VERIFIED","requested_version":"v1.2.0","response_version_verified":False,"uri":EXAMPLE_URI,"sha256":digest(raw),"link_keys":sorted(links),"bytes":len(raw),"note":"Not a full 1.2.1 dataset; no graph ingestion."}
    except HTTPError as e:report["esco"]["api_probe"]={"status":"HTTP_BLOCKED","http_status":e.code}
    except Exception as e:report["esco"]["api_probe"]={"status":"UNAVAILABLE","error_type":type(e).__name__}
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument("--esco-zip");p.add_argument("--sha256");a=p.parse_args()
    if a.esco_zip:
        if not a.sha256:p.error("--sha256 required")
        report=import_esco(a.esco_zip,a.sha256).audit()
    else:report=access_audit()
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
