"""S1 v0.4: unified internal query facade, quality and source vintage policy."""
from dataclasses import dataclass
from datetime import datetime, timezone, date
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
import hashlib
import json
import re
import os
from itertools import chain

from . import semantic_v2 as v2, semantic_v3 as v3

VERSION="0.4.0"
ARCHIVE_SOURCES={"indeed_sector_total_daily","indeed_national_total_daily","dares_offers_monthly","insee_employment"}
LIVE_SOURCES=set(v3.SOURCES)
SOURCES=ARCHIVE_SOURCES|LIVE_SOURCES
FREQ={s:v2.CONTRACTS[s]["frequency"] for s in ARCHIVE_SOURCES}
FREQ.update({s:v3.URSSAF[s]["freq"] if s in v3.URSSAF else "A" for s in LIVE_SOURCES})
# Source-native dimensions: no renaming to a universal industry/occupation code.
NATIVE_DIMS={
 "indeed_sector_total_daily":{"country","occupation_family"},
 "indeed_national_total_daily":{"country"},
 "dares_offers_monthly":{"region_code","region_label","department_code","department_label","offer_type","employment_type","qualification","data_type"},
 "insee_employment":{"industry","category_kind","country"},
 **{s:set(c["dims"]) for s,c in v3.URSSAF.items()},
 **{s:v3.EURO_DIMS-{"time"} for s in ("eurostat_nace","eurostat_size")},
}
LICENSE={s:v2.CONTRACTS[s]["license"] for s in ARCHIVE_SOURCES}
LICENSE.update({s:"ODbL-1.0" if s in v3.URSSAF else "EUROSTAT_REUSE_REVIEW" for s in LIVE_SOURCES})
LINEAGE={s:v2.CONTRACTS[s]["lineage"] for s in ARCHIVE_SOURCES}
LINEAGE.update({s:"FR_admin_mixed" if s in v3.URSSAF else "Eurostat_ICT_survey" for s in LIVE_SOURCES})
FLAG_URL="https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Tutorial:Symbols_and_abbreviations"
CONF_URL="https://ec.europa.eu/eurostat/data/database"
COG_URL="https://www.insee.fr/fr/information/2560452"


def flag_reasons(flag):
    # Retain raw token. Explicitly recognize only the observed codes.
    return {"":(), "b":("SERIES_BREAK",), "u":("LOW_RELIABILITY",),
        "bu":("SERIES_BREAK","LOW_RELIABILITY"), "|C":("CONFIDENTIAL_STATUS_REVIEW",),
        "MISSING":("MISSING",)}.get(flag,("UNKNOWN_FLAG_REVIEW",))


def valid_period(source,p):
    if not isinstance(p,str):
        return False
    f=FREQ[source]
    if f=="D":
        try:
            return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}",p)) and date.fromisoformat(p).isoformat()==p
        except ValueError:
            return False
    return bool(re.fullmatch({"M":r"\d{4}-(0[1-9]|1[0-2])","Q":r"\d{4}Q[1-4]","A":r"\d{4}"}[f],p))


@dataclass(frozen=True)
class Record:
    source: str
    period: str
    dimensions: tuple
    measure: str
    unit: str
    value: Decimal | None
    flag: str
    vintage: str
    sha256: str
    locator: str
    source_url: str
    method: str
    persistence: str
    native: object

    def __post_init__(self):
        if self.source not in SOURCES or not valid_period(self.source,self.period):
            raise ValueError("INVALID_SOURCE_PERIOD")
        if tuple(sorted(self.dimensions))!=self.dimensions or len(dict(self.dimensions))!=len(self.dimensions) or set(dict(self.dimensions))!=NATIVE_DIMS[self.source]:
            raise ValueError("INVALID_SOURCE_DIMENSIONS")
        if not all(isinstance(v,str) and v for k,v in self.dimensions):
            raise ValueError("INVALID_DIMENSION_VALUE")
        if self.source in ARCHIVE_SOURCES:
            if not isinstance(self.native,v2.Cell) or self.native.series!=self.source or self.persistence!="PINNED_ARTIFACT":
                raise ValueError("ARCHIVE_NATIVE_REQUIRED")
            c=v2.CONTRACTS[self.source]
            expected=(self.native.period,tuple(sorted((d.kind,d.value) for d in self.native.dimensions)),c["measure"],c["unit"],self.native.value,self.native.raw_flag,self.native.vintage,self.native.sha256,self.native.locator,self.native.source_url,self.native.method)
        else:
            if not isinstance(self.native,v3.Cell) or self.native.source!=self.source or self.persistence!="LIVE_TRANSIENT":
                raise ValueError("LIVE_NATIVE_REQUIRED")
            expected=(self.native.period,self.native.dimensions,self.native.measure,self.native.unit,self.native.value,self.native.flag,self.native.vintage,self.native.sha256,self.native.locator,v3.SOURCES[self.source],"source_native_live")
        actual=(self.period,self.dimensions,self.measure,self.unit,self.value,self.flag,self.vintage,self.sha256,self.locator,self.source_url,self.method)
        if actual!=expected:
            raise ValueError("NATIVE_RECORD_MISMATCH")

    @property
    def key(self):
        return self.source,self.period,self.dimensions,self.measure,self.unit,self.vintage

    @property
    def quality(self):
        reasons=[]
        if self.source.startswith("eurostat_"):
            reasons.extend(flag_reasons(self.flag))
        elif self.flag:
            reasons.append("SOURCE_FLAG_REVIEW")
        if self.value is None:
            reasons.append("MISSING_VALUE")
        if self.source=="urssaf_dpae_na38" and "2025Q2"<=self.period<="2025Q3" or self.source=="urssaf_dpae_monthly" and "2025-04"<=self.period<="2025-09":
            reasons.append("DPAE_2025_DECLARATION_ERROR_REVIEW")
        if self.source in {"urssaf_na88","urssaf_dpae_na38"} and self.period>="2027Q1":
            reasons.append("NAF_2027_CLASSIFICATION_REVIEW")
        if self.source=="dares_offers_monthly":
            reasons.append("HISTORICAL_GEOCODE_UNQUALIFIED")
            if "[source blank]" in dict(self.dimensions).values():
                reasons.append("NATIVE_DIMENSION_BLANK")
        if self.source=="insee_employment":
            reasons.append("INSEE_REVISION_REVIEW")
        if "CONFIDENTIAL_STATUS_REVIEW" in reasons or self.value is None:
            level="WITHHELD"
        elif any(r in reasons for r in ("LOW_RELIABILITY","DPAE_2025_DECLARATION_ERROR_REVIEW","NAF_2027_CLASSIFICATION_REVIEW","UNKNOWN_FLAG_REVIEW")):
            level="RESTRICTED"
        elif reasons:
            level="REVIEW_REQUIRED"
        else:
            level="DESCRIPTIVE_ONLY"
        return level,tuple(reasons)

    def internal_result(self):
        level,reasons=self.quality
        # Do not expose a confidential or unavailable cell even on the internal facade.
        value=None if level=="WITHHELD" else self.value
        return {"source":self.source,"period":self.period,"dimensions":dict(self.dimensions),
            "measure":self.measure,"unit":self.unit,"value":None if value is None else str(value),
            "quality":level,"reasons":list(reasons),"raw_flag":self.flag,"vintage":self.vintage,
            "sha256":self.sha256,"locator":self.locator,"source_url":self.source_url,
            "license":LICENSE[self.source],"lineage":LINEAGE[self.source],"persistence":self.persistence,
            "evidence":"DESCRIPTIVE_ONLY","publication":"BLOCK_PUBLICATION"}


def wrap_archive(c):
    if c.series not in ARCHIVE_SOURCES:
        raise ValueError("PILOT_EXTRACT_EXCLUDED")
    cfg=v2.CONTRACTS[c.series]
    return Record(c.series,c.period,tuple(sorted((d.kind,d.value) for d in c.dimensions)),
        cfg["measure"],cfg["unit"],c.value,c.raw_flag,c.vintage,c.sha256,c.locator,c.source_url,c.method,"PINNED_ARTIFACT",c)


def wrap_live(c):
    return Record(c.source,c.period,c.dimensions,c.measure,c.unit,c.value,c.flag,c.vintage,c.sha256,c.locator,v3.SOURCES[c.source],"source_native_live","LIVE_TRANSIENT",c)


class Catalog:
    def __init__(self,records):
        self.by=defaultdict(list)
        self.fields=defaultdict(lambda:defaultdict(set))
        keys=set(); vintages=defaultdict(set)
        for r in records:
            if r.key in keys:
                raise ValueError("DUPLICATE_NATIVE_KEY")
            keys.add(r.key); vintages[r.source].add((r.vintage,r.sha256))
            self.by[r.source].append(r)
            for k,v in r.dimensions:
                self.fields[r.source][k].add(v)
        if any(len(x)!=1 for x in vintages.values()):
            raise ValueError("MULTIPLE_VINTAGES_REQUIRE_EXPLICIT_SELECTION")
        self.vintages={s:next(iter(v)) for s,v in vintages.items()}

    def query(self,source,filters=None,*,measure=None,unit=None,start=None,end=None,offset=0,limit=200,purpose="internal_research"):
        if purpose!="internal_research":
            raise PermissionError("PUBLICATION_BLOCKED")
        if source not in self.by or type(limit) is not int or not 1<=limit<=1000 or type(offset) is not int or offset<0:
            raise ValueError("QUERY_SCOPE")
        filters=filters or {}
        if not isinstance(filters,dict) or not set(filters)<=NATIVE_DIMS[source] or not all(isinstance(v,str) and v for v in filters.values()):
            raise ValueError("UNKNOWN_FILTER")
        if any(p is not None and not valid_period(source,p) for p in (start,end)) or start and end and start>end:
            raise ValueError("QUERY_PERIOD")
        if measure is not None and measure not in {r.measure for r in self.by[source]} or unit is not None and unit not in {r.unit for r in self.by[source]}:
            raise ValueError("UNKNOWN_MEASURE_OR_UNIT")
        rows=[r for r in self.by[source] if all(dict(r.dimensions).get(k)==v for k,v in filters.items()) and (measure is None or measure==r.measure) and (unit is None or unit==r.unit) and (start is None or r.period>=start) and (end is None or r.period<=end)]
        rows.sort(key=lambda r:(r.period,r.dimensions,r.measure,r.unit))
        return {"source":source,"total":len(rows),"offset":offset,"limit":limit,
            "next_offset":offset+limit if offset+limit<len(rows) else None,
            "quality_counts":dict(Counter(r.quality[0] for r in rows)),
            "records":[r.internal_result() for r in rows[offset:offset+limit]],
            "zero_results_means_no_coverage":not rows,"publication":"BLOCK_PUBLICATION"}

    def coverage(self,source,filters=None):
        if source not in self.by:
            raise ValueError("UNKNOWN_SOURCE")
        filters=filters or {}
        if not set(filters)<=NATIVE_DIMS[source]:
            raise ValueError("UNKNOWN_FILTER")
        rows=[r for r in self.by[source] if all(dict(r.dimensions).get(k)==v for k,v in filters.items())]
        choices=defaultdict(set)
        for r in rows:
            for k,v in r.dimensions:
                choices[k].add(v)
        return {"rows":len(rows),"choices":{k:sorted(v) for k,v in sorted(choices.items())},
                "combinations":len({(r.dimensions,r.measure,r.unit) for r in rows if r.value is not None}),
                "quality_counts":dict(Counter(r.quality[0] for r in rows))}


def compare(a,b):
    if a.source!=b.source or a.dimensions!=b.dimensions or (a.measure,a.unit)!=(b.measure,b.unit):
        return "BLOCK_SEMANTIC_MISMATCH"
    if a.quality[0] in {"RESTRICTED","WITHHELD"} or b.quality[0] in {"RESTRICTED","WITHHELD"}:
        return "BLOCK_QUALITY"
    # Underlying comparisons remain conservative; no numeric change in this API.
    decision=v2.compare(a.native,b.native)["decision"] if a.source in ARCHIVE_SOURCES else v3.compare(a.native,b.native)
    return decision if decision.startswith("BLOCK") else "REVIEW_REQUIRED"


def local_vintage_store(root,source,raw,*,retrieved_at,approved=False):
    """Opt-in local-only vault mechanism. No production vault is provisioned."""
    if approved is not True or source not in LIVE_SOURCES:
        raise PermissionError("ARCHIVE_APPROVAL_REQUIRED")
    root=Path(root).expanduser().resolve()
    repo=v2.ROOT.resolve()
    if root==repo or repo in root.parents:
        raise ValueError("VAULT_MUST_BE_OUTSIDE_REPOSITORY")
    if datetime.fromisoformat(retrieved_at).tzinfo is None:
        raise ValueError("VINTAGE_TIMEZONE")
    sha=hashlib.sha256(raw).hexdigest()
    folder=root/source/sha
    folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    path=folder/"original.bin"
    # No overwrite; verify existing content instead of silently replacing it.
    try:
        with path.open("xb") as f:
            f.write(raw)
        os.chmod(path,0o600)
    except FileExistsError:
        if hashlib.sha256(path.read_bytes()).hexdigest()!=sha:
            raise ValueError("VAULT_HASH_MISMATCH")
    manifest={"source":source,"url":v3.SOURCES[source],"sha256":sha,"bytes":len(raw),"retrieved_at":retrieved_at,"publication":"BLOCK_PUBLICATION"}
    key=hashlib.sha256(retrieved_at.encode()).hexdigest()
    m=folder/(key+".json")
    try:
        with m.open("x",encoding="utf-8") as f:
            json.dump(manifest,f,indent=2)
        os.chmod(m,0o600)
    except FileExistsError:
        if json.loads(m.read_text())!=manifest:
            raise ValueError("VAULT_MANIFEST_MISMATCH")
    return manifest


def build_catalog(fetcher=v3.retrieve,root=v2.ROOT):
    archived=chain((v2.wrap(o) for o in v2.v1.read_insee(root)),v2.iter_indeed(root),v2.iter_dares(root))
    live=[]; metas={}
    for source,url in v3.SOURCES.items():
        raw=fetcher(url); stamp=datetime.now(timezone.utc).isoformat()
        rows,profile=(v3.read_urssaf if source in v3.URSSAF else v3.read_euro)(source,raw,stamp)
        if not rows:
            raise ValueError("EMPTY_LIVE_SOURCE")
        live.extend(wrap_live(c) for c in rows)
        metas[source]={"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"retrieved_at":stamp}
    cat=Catalog(chain((wrap_archive(c) for c in archived),live))
    if set(cat.by)!=SOURCES:
        raise ValueError("INCOMPLETE_CATALOG")
    return cat,metas


def run():
    cat,metas=build_catalog()
    counts={s:len(cat.by[s]) for s in sorted(cat.by)}
    coverage={s:{"combinations":cat.coverage(s)["combinations"],"quality_counts":cat.coverage(s)["quality_counts"]} for s in sorted(cat.by)}
    pilot=cat.query("eurostat_nace",{"geo":"FR","nace_r2":"J","size_emp":"GE10","indic_is":"E_AI_TANY","freq":"A"},measure="E_AI_TANY",unit="PC_ENT")
    if pilot["total"]!=3:
        raise ValueError("PILOT_QUERY_COVERAGE")
    # Only metadata, never values, in publicly visible logs.
    pilot_flags=[{k:r[k] for k in ("period","raw_flag","quality","reasons")} for r in pilot["records"]]
    return {"version":VERSION,"counts":counts,"coverage":coverage,
        "archived_cells":sum(counts[s] for s in ARCHIVE_SOURCES),
        "live_transient_cells":sum(counts[s] for s in LIVE_SOURCES),
        "excluded_pilot_excerpt_cells":9,"pilot_flag_metadata":pilot_flags,
        "live_source_manifest":metas,"production_vault_provisioned":False,
        "public_values_emitted":False,"cross_source_join_permitted":False,"causal_claims_permitted":False}


if __name__=="__main__":
    try:
        print(json.dumps(run(),ensure_ascii=False,indent=2))
    except Exception as exc:
        print(json.dumps({"status":"BLOCKED","error_type":type(exc).__name__}))
        raise SystemExit(2)
