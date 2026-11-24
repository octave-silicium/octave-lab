"""S1 v0.2: source-native dimensions and archived observations.

No occupational/industry crosswalk, implicit aggregation, causal inference or
publication authorization. Existing v0.1 contracts remain unchanged.
"""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from collections import Counter
import csv
import gzip
import hashlib
import io
import json
import re
from urllib.parse import urlsplit

from . import semantic as v1

VERSION = "0.2.0"
ROOT = Path(__file__).resolve().parents[1]
DARES_FIELDS = ("Date", "Code région", "Région", "Code département",
                "Département", "Type de données", "Type d'offre d'emploi",
                "Type d'emploi", "Qualification", "Nombre d'offres d'emploi")
# Native dimension labels are not asserted to be cross-source codes.
DIMENSION_TYPES = {
    "industry", "occupation_family", "region_code", "region_label",
    "department_code", "department_label", "offer_type", "employment_type",
    "qualification", "data_type", "enterprise_size", "country", "category_kind",
    "work_node"
}
CONTRACTS = {
    "indeed_sector_total_daily": dict(measure="posting_index", unit="index_points",
        population="Indeed postings classified by title", geography="FR",
        frequency="D", adjustment="SA_7day_moving_average", taxonomy="Indeed_display_name",
        license="CC-BY-4.0", lineage="Indeed_Hiring_Lab", definition="total postings"),
    "indeed_national_total_daily": dict(measure="posting_index", unit="index_points",
        population="Indeed postings", geography="FR", frequency="D",
        adjustment="SA_7day_moving_average", taxonomy="Indeed_national",
        license="CC-BY-4.0", lineage="Indeed_Hiring_Lab", definition="total postings"),
    "dares_offers_monthly": dict(measure="offer_count_by_native_type", unit="offers_rounded_to_hundred",
        population="offers entrusted to France Travail or satisfied according to native type",
        geography="FR_excl_Mayotte_source_geographies", frequency="M", adjustment="raw",
        taxonomy="Dares_source_labels_and_geocodes", license="LO-2.0",
        lineage="FT_DARES_STMT", definition="native offer, employment and qualification categories"),
}
for name in v1.CONTRACTS:
    c = dict(zip(v1.FIELDS, v1.CONTRACTS[name]))
    CONTRACTS[name] = dict(c, license={"INSEE_EMPLOI_SECTORIEL_TRIMESTRIEL":"LO-2.0",
        "DS-015_urssaf_private_sector_na88":"ODbL-1.0",
        "URSSAF_DPAE_NA38_QUARTERLY":"ODbL-1.0"}.get(c["rights_id"], "UNQUALIFIED"),
        lineage=c["dependency_family"])


@dataclass(frozen=True, order=True)
class Dimension:
    kind: str
    scheme: str
    version: str
    value: str

    def __post_init__(self):
        if self.kind not in DIMENSION_TYPES or not all(isinstance(x, str) and x.strip() for x in (self.scheme, self.version, self.value)):
            raise ValueError("INVALID_DIMENSION")


@dataclass(frozen=True)
class WorkNodeRef:
    """Reserved reference only. No ontology, mapping or validation claimed."""
    kind: str
    namespace: str
    identifier: str
    version: str
    status: str = "PROPOSED"

    def __post_init__(self):
        if self.kind not in {"profession","task","action","process"} or self.status != "PROPOSED":
            raise ValueError("UNQUALIFIED_WORK_NODE")
        if not all(isinstance(x,str) and x.strip() for x in (self.namespace,self.identifier,self.version)):
            raise ValueError("INVALID_WORK_NODE")


@dataclass(frozen=True)
class Cell:
    series: str
    period: str
    dimensions: tuple
    value: Decimal | None
    status: str
    vintage: str
    sha256: str
    source_url: str
    locator: str
    method: str
    raw_flag: str = ""
    legacy: v1.Observation | None = None

    def __post_init__(self):
        if self.series not in CONTRACTS or self.status not in {"OBSERVED","MISSING"}:
            raise ValueError("UNKNOWN_CONTRACT_OR_STATUS")
        if self.series in v1.CONTRACTS and not isinstance(self.legacy,v1.Observation):
            raise ValueError("LEGACY_OBSERVATION_REQUIRED")
        if self.series not in v1.CONTRACTS and self.legacy is not None:
            raise ValueError("UNEXPECTED_LEGACY_OBSERVATION")
        freq = CONTRACTS[self.series]["frequency"]
        if freq == "D":
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", self.period):
                raise ValueError("INVALID_DAY")
            date.fromisoformat(self.period)
        elif not re.fullmatch({"M":r"\d{4}-(0[1-9]|1[0-2])","Q":r"\d{4}Q[1-4]","A":r"\d{4}"}[freq],self.period):
            raise ValueError("INVALID_PERIOD")
        if not self.dimensions or not all(isinstance(d, Dimension) for d in self.dimensions) or len({d.kind for d in self.dimensions}) != len(self.dimensions):
            raise ValueError("INVALID_DIMENSIONS")
        if self.dimensions != tuple(sorted(self.dimensions)):
            raise ValueError("DIMENSIONS_MUST_BE_CANONICAL")
        if self.status == "MISSING":
            if self.value is not None or not self.raw_flag:
                raise ValueError("MISSING_VALUE_REQUIRES_FLAG")
        elif not isinstance(self.value,Decimal) or not self.value.is_finite() or self.value < 0:
            raise ValueError("INVALID_NUMBER")
        if self.value is not None and self.series.startswith("indeed_") and not (0 < self.value < 10000):
            raise ValueError("INVALID_INDEX")
        if self.value is not None and self.series == "dares_offers_monthly" and self.value != self.value.to_integral_value():
            raise ValueError("NON_INTEGER_OFFER_COUNT")
        if not re.fullmatch(r"[0-9a-f]{64}",self.sha256):
            raise ValueError("INVALID_SHA256")
        if datetime.fromisoformat(self.vintage.replace("Z","+00:00")).tzinfo is None:
            raise ValueError("INVALID_VINTAGE")
        u=urlsplit(self.source_url)
        if u.scheme != "https" or not u.hostname or u.username or u.password or not self.locator.strip() or not self.method.strip():
            raise ValueError("INVALID_PROVENANCE")
        if self.legacy is not None:
            o=self.legacy
            if (self.series,self.period,self.value,self.vintage,self.sha256,self.source_url,self.locator,self.method,self.dimensions,self.status)!=(o.series,o.period,o.value,o.vintage,o.sha256,o.source_url,o.locator,o.method_vintage,legacy_dims(o),"OBSERVED"):
                raise ValueError("LEGACY_MISMATCH")

    @property
    def key(self):
        return self.series,self.period,self.dimensions,self.vintage


def dims(scheme, version, **values):
    # Empty native codes/labels are explicit unknown/not supplied, never France or zero.
    return tuple(sorted(Dimension(k,scheme,version,v if v.strip() else "[source blank]") for k,v in values.items()))


def legacy_dims(o):
    extra={"enterprise_size":"GE10"} if o.series == "eurostat_ai_tany" else {}
    return dims(o.contract["taxonomy"], o.method_vintage, industry=o.sector,
        category_kind=o.category_kind, country=o.contract["geography"], **extra)


def wrap(o):
    return Cell(o.series,o.period,legacy_dims(o),o.value,"OBSERVED",o.vintage,o.sha256,
                o.source_url,o.locator,o.method_vintage,legacy=o)


def parse_value(s):
    s=s.strip()
    if s in {"","NA","N/A",":","..","ND","n.d."}:
        return None,"MISSING:"+(s or "blank")
    try:
        return Decimal(s.replace("\u202f","").replace("\xa0","").replace(" ","").replace(",",".")),""
    except InvalidOperation as e:
        raise ValueError("UNRECOGNIZED_NUMERIC_TOKEN:"+s[:30]) from e


def raw_verified(path,sha,size,compressed=False):
    raw=path.read_bytes()
    if compressed:
        # Bound decompression before allocating untrusted oversized data.
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f:
            raw=f.read(size+1)
    if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=sha:
        raise ValueError("RAW_ARCHIVE_HASH_OR_SIZE_MISMATCH:"+path.name)
    return raw


def iter_indeed(root=ROOT, only_series=None):
    folder=root/"snapshots/indeed-fr/2026-11"
    m=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
    if not m["publish_gate"].startswith("PASS_DESCRIPTIVE_ONLY") or m["no_causal_inference"] is not True:
        raise ValueError("INDEED_MANIFEST_GATE")
    for source, series, field in (("indeed_fr_sector","indeed_sector_total_daily","indeed_job_postings_index"),
        ("indeed_fr_national","indeed_national_total_daily","indeed_job_postings_index_SA")):
        if only_series is not None and series!=only_series:
            continue
        s=m["status"][source]
        if s["result"]!="OK" or s["license"]!="CC BY 4.0":
            raise ValueError("INDEED_SOURCE_GATE")
        name=Path(s["filename"]).name
        raw=raw_verified(folder/name,s["sha256"],s["bytes"])
        rows=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        if set(rows.fieldnames or [])!=set(s["columns"]):
            raise ValueError("INDEED_SCHEMA_MISMATCH")
        count=selected=0
        for n,r in enumerate(rows,2):
            count+=1
            if r["jobcountry"]!="FR":
                raise ValueError("INDEED_GEOGRAPHY_MISMATCH")
            if r["variable"]!="total postings":
                continue
            selected+=1
            kw={"country":"FR"}
            if source=="indeed_fr_sector":
                if not r["display_name"].strip():
                    raise ValueError("INDEED_MISSING_OCCUPATION")
                kw["occupation_family"]=r["display_name"]
            val,flag=parse_value(r[field])
            yield Cell(series,r["date"],dims("Indeed_native","2026-11 snapshot",**kw),
                val,"OBSERVED" if val is not None else "MISSING",s["downloaded_at"],s["sha256"],
                s["url"],f"{folder.relative_to(root)}/{name}:{n}","2026-11 source snapshot; total postings SA",flag)
        if count!=s["rows"] or not selected:
            raise ValueError("INDEED_ROW_COUNT_MISMATCH")
        if source=="indeed_fr_sector" and selected!=s["analysis"]["valid_sector_rows"]:
            raise ValueError("INDEED_SELECTED_COUNT_MISMATCH")


def iter_dares(root=ROOT):
    folder=root/"snapshots/dares-ft-monthly/2026-11"
    m=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
    if m["source_id"]!="DS-004_dares_offers_monthly" or m["license"]!="Licence Ouverte / Open Licence 2.0":
        raise ValueError("DARES_MANIFEST_GATE")
    sha=m["sha256_uncompressed_original"]
    name=Path(m["compressed_file"]).name
    raw=raw_verified(folder/name,sha,m["original_n_bytes"],compressed=True)
    rows=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")),delimiter=";")
    if set(rows.fieldnames or [])!=set(DARES_FIELDS):
        raise ValueError("DARES_SCHEMA_MISMATCH")
    count=0
    for n,r in enumerate(rows,2):
        count+=1
        period=r["Date"]
        if re.fullmatch(r"\d{4}-\d{2}-01",period):
            period=period[:7]
        native=dict(region_code=r["Code région"],region_label=r["Région"],
            department_code=r["Code département"],department_label=r["Département"],
            data_type=r["Type de données"],offer_type=r["Type d'offre d'emploi"],
            employment_type=r["Type d'emploi"],qualification=r["Qualification"])
        val,flag=parse_value(r["Nombre d'offres d'emploi"])
        yield Cell("dares_offers_monthly",period,dims("Dares_native","2026-11 snapshot",**native),
            val,"OBSERVED" if val is not None else "MISSING",m["retrieved_at_utc"],sha,m["original_url"],
            f"{folder.relative_to(root)}/{name}:uncompressed-line-{n}","source native; rounded counts; 2013 review",flag)
    if count!=96252:
        raise ValueError("DARES_REFERENCE_ROW_COUNT_MISMATCH")


def compare(a,b):
    if (a.series,a.dimensions)!=(b.series,b.dimensions):
        return {"decision":"BLOCK","reason":"SEMANTIC_MISMATCH"}
    if (a.vintage,a.sha256)!=(b.vintage,b.sha256):
        return {"decision":"BLOCK","reason":"VINTAGE_MISMATCH"}
    if a.period>=b.period or a.status!="OBSERVED" or b.status!="OBSERVED":
        return {"decision":"BLOCK","reason":"ORDER_OR_MISSING"}
    if a.method!=b.method:
        return {"decision":"BLOCK","reason":"METHOD_BREAK"}
    if a.legacy is not None and b.legacy is not None:
        return v1.compare(a.legacy,b.legacy)
    if a.series=="dares_offers_monthly" and a.period<"2013-07"<=b.period:
        # Conservative for all native offer types until code-level review.
        return {"decision":"BLOCK","reason":"DARES_JULY_2013_REVIEW"}
    return {"decision":"REVIEW_REQUIRED","reason":"Source-specific breaks, coverage and flags not fully qualified"}


def release(cell,purpose,*,attributed=False,adapted_database=None):
    if cell.status!="OBSERVED":
        return {"decision":"BLOCK","reason":"MISSING"}
    if cell.legacy is not None:
        return v1.release(cell.legacy,purpose,attributed=attributed,adapted_database=adapted_database)
    if purpose=="internal_research":
        return {"decision":"ALLOW_INTERNAL","reason":"Known archive license; no external publication"}
    if purpose not in {"public_chart","paid_report","public_dataset_export"} or not attributed or adapted_database is not False:
        return {"decision":"BLOCK","reason":"PUBLIC_USE_PRECONDITIONS"}
    # Known open licenses; actual output review not yet complete.
    return {"decision":"REVIEW_REQUIRED","reason":"Attribution, source-specific scope and faithful meaning required"}


def audit(root=ROOT):
    seen=set()
    counts=Counter()
    missing=Counter()
    dimensions={}
    periods={}
    for c in (x for stream in ((wrap(o) for o in v1.read_insee(root)+v1.read_pilot(root)),iter_indeed(root),iter_dares(root)) for x in stream):
        if c.key in seen:
            raise ValueError("DUPLICATE_CELL:"+c.series)
        seen.add(c.key)
        counts[c.series]+=1
        if c.status=="MISSING":
            missing[c.series]+=1
        dd=dimensions.setdefault(c.series,{})
        for d in c.dimensions:
            dd.setdefault(d.kind,set()).add(d.value)
        low,high=periods.get(c.series,(c.period,c.period))
        periods[c.series]=(min(low,c.period),max(high,c.period))
    if set(counts)!=set(CONTRACTS):
        raise ValueError("INCOMPLETE_CONTRACT_COVERAGE")
    return {"version":VERSION,"counts":dict(counts),"missing":dict(missing),"total":sum(counts.values()),
        "coverage":{s:{k:len(v) for k,v in d.items()} for s,d in dimensions.items()},
        "periods":periods,"verified_original_archive_bytes":["indeed_fr_sector","indeed_fr_national","DS-004_dares_offers_monthly"],
        "status":"SOURCE_NATIVE_DESCRIPTIVE_ONLY","causal_claims_permitted":False,
        "cross_source_join_permitted":False,"full_source_qualification":False}


if __name__=="__main__":
    print(json.dumps(audit(),ensure_ascii=False,indent=2))
