"""S1 v0.3: live source-native tables and internal query engine.
No joined data, no values in audit output; source bytes stay in memory.
"""
from dataclasses import dataclass
from datetime import datetime, timezone, date
from decimal import Decimal
from collections import Counter, defaultdict
from itertools import product
import hashlib
import csv
import io
import json
import math
import re
from .pilot_ict import retrieve
from . import semantic_v2 as v2
from .data_governance import comparison_gate

VERSION="0.3.0"
SOURCES={
 "urssaf_na88": "https://open.urssaf.fr/api/explore/v2.1/catalog/datasets/effectifs-salaries-et-masse-salariale-du-secteur-prive-france-entiere-x-na88/exports/csv?use_labels=false",
 "urssaf_dpae_na38": "https://open.urssaf.fr/api/explore/v2.1/catalog/datasets/dpae-france-entiere-x-na38/exports/csv?use_labels=false",
 "urssaf_dpae_monthly": "https://open.urssaf.fr/api/explore/v2.1/catalog/datasets/dpae-mensuelles-france-entiere/exports/csv?use_labels=false",
 "eurostat_size": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/isoc_eb_ai?geo=FR&geo=EU27_2020&lang=EN&sinceTimePeriod=2022",
 "eurostat_nace": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/isoc_eb_ain2?geo=FR&lang=EN&sinceTimePeriod=2022",
}
URSSAF={
 "urssaf_na88": dict(dims=("grand_secteur_d_activite","secteur_na38i","secteur_na88i"), measures=("effectifs_salaries_brut","effectifs_salaries_cvs"), time="dernier_jour_du_trimestre", freq="Q", concept="private employee stock", unit="employees"),
 "urssaf_dpae_na38": dict(dims=("grand_secteur_d_activite_agrege","grand_secteur_d_activite","secteur_na38","duree_de_contrat","nature_de_contrat"), measures=("dpae_brut","dpae_cvs"),time="dernier_jour_du_trimestre",freq="Q", concept="declarations, not realized hires",unit="declarations"),
 "urssaf_dpae_monthly": dict(dims=("duree_de_contrat","nature_de_contrat"), measures=("dpae_brut","dpae_cvs"),time="dernier_jour_du_mois",freq="M",concept="declarations, not realized hires",unit="declarations"),
}
EURO_DIMS={"freq","geo","indic_is","nace_r2","size_emp","time","unit"}
MAX_GRID=1_000_000

@dataclass(frozen=True)
class Cell:
    source: str
    period: str
    dimensions: tuple
    measure: str
    unit: str
    value: Decimal | None
    flag: str
    sha256: str
    vintage: str
    locator: str

    @property
    def key(self):
        return self.source,self.period,self.dimensions,self.measure,self.unit,self.vintage

    def __post_init__(self):
        if self.source not in SOURCES or not self.locator or not self.measure or not self.unit:
            raise ValueError("CELL_METADATA")
        if tuple(sorted(self.dimensions))!=self.dimensions or len(dict(self.dimensions))!=len(self.dimensions):
            raise ValueError("CELL_DIMENSIONS")
        if not re.fullmatch(r"[0-9a-f]{64}",self.sha256) or datetime.fromisoformat(self.vintage).tzinfo is None:
            raise ValueError("CELL_PROVENANCE")
        if self.value is None:
            if not self.flag:
                raise ValueError("MISSING_WITHOUT_FLAG")
        elif not isinstance(self.value,Decimal) or not self.value.is_finite() or self.value<0:
            raise ValueError("INVALID_NUMBER")
        elif self.unit=="PC_ENT" and self.value>100:
            raise ValueError("INVALID_PERCENT")


def ordered_dims(d):
    return tuple(sorted((k, v if v else "[source blank]") for k,v in d.items()))


def sparse(obj, length):
    if isinstance(obj,list):
        if len(obj)>length:
            raise ValueError("SPARSE_LENGTH")
        return {i:v for i,v in enumerate(obj) if v is not None}
    if not isinstance(obj,dict):
        raise ValueError("SPARSE_TYPE")
    out={}
    for k,v in obj.items():
        if not isinstance(k,str) or not k.isdigit() or str(int(k))!=k or int(k)>=length:
            raise ValueError("SPARSE_INDEX")
        if v is not None:
            out[int(k)]=v
    return out


def category_order(cat,size):
    idx=cat["index"]
    if isinstance(idx,list):
        codes=idx
    elif isinstance(idx,dict):
        if any(type(i) is not int for i in idx.values()) or set(idx.values())!=set(range(size)):
            raise ValueError("CATEGORY_INDEX")
        codes=sorted(idx,key=idx.get)
    else:
        raise ValueError("CATEGORY_TYPE")
    if len(codes)!=size or len(set(codes))!=size or not all(isinstance(c,str) and c for c in codes):
        raise ValueError("CATEGORY_COVERAGE")
    return codes


def read_euro(source,raw,vintage):
    j=json.loads(raw,parse_float=Decimal)
    ids=j["id"]; sizes=j["size"]
    if len(ids)!=7 or set(ids)!=EURO_DIMS or len(sizes)!=7 or any(type(n) is not int or n<=0 for n in sizes):
        raise ValueError("EUROSTAT_DIMENSION_SCHEMA")
    n=math.prod(sizes)
    if n>MAX_GRID:
        raise ValueError("EUROSTAT_GRID_LIMIT")
    codes=[category_order(j["dimension"][dim]["category"],size) for dim,size in zip(ids,sizes)]
    values=sparse(j.get("value",{}),n)
    flags=sparse(j.get("status",{}),n)
    sha=hashlib.sha256(raw).hexdigest()
    # Include flagged missing cells; count completely absent cells separately.
    records=[]
    for offset in sorted(set(values)|set(flags)):
        pos=offset; selectors={}
        for dim,size,labels in reversed(list(zip(ids,sizes,codes))):
            pos,i=divmod(pos,size)
            selectors[dim]=labels[i]
        if selectors["freq"]!="A" or not re.fullmatch(r"\d{4}",selectors["time"]):
            raise ValueError("EUROSTAT_PERIOD")
        flag=flags.get(offset,"")
        if not isinstance(flag,str):
            raise ValueError("EUROSTAT_FLAG_TYPE")
        value=values.get(offset)
        if value is not None and (isinstance(value,bool) or not isinstance(value,(int,Decimal))):
            raise ValueError("EUROSTAT_VALUE_TYPE")
        if value is None:
            flag=flag or "MISSING"
        records.append(Cell(source,selectors.pop("time"),ordered_dims(selectors),
            selectors["indic_is"],selectors["unit"],None if value is None else Decimal(value),
            flag,sha,vintage,"jsonstat:"+str(offset)))
    return records,{"grid_cells":n,"absent_unflagged":n-len(records),"value_cells":len(values),"flagged_cells":sum(bool(x) for x in flags.values()),"dimension_sizes":dict(zip(ids,sizes))}


def read_urssaf(source,raw,vintage):
    config=URSSAF[source]
    rdr=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")),delimiter=";")
    required=set(config["dims"]+config["measures"]+(config["time"],"annee","trimestre"))
    if not required.issubset(rdr.fieldnames or []):
        raise ValueError("URSSAF_SCHEMA")
    sha=hashlib.sha256(raw).hexdigest()
    rows=[]; count=0
    for i,r in enumerate(rdr,2):
        count+=1
        d=date.fromisoformat(r[config["time"]][:10])
        q=(d.month-1)//3+1
        if int(r["annee"])!=d.year or int(r["trimestre"])!=q:
            raise ValueError("URSSAF_PERIOD_MISMATCH")
        p=f"{d.year}Q{q}" if config["freq"]=="Q" else d.strftime("%Y-%m")
        native=ordered_dims({k:r[k] for k in config["dims"]})
        for m in config["measures"]:
            val,flag=v2.parse_value(r[m])
            rows.append(Cell(source,p,native,m,config["unit"],val,flag,sha,vintage,f"csv:{i}:{m}"))
    if not count:
        raise ValueError("URSSAF_EMPTY")
    return rows,{"source_rows":count,"measures":list(config["measures"]),"concept":config["concept"],"native_codes_not_crosswalk":True}


class Index:
    """Exact source-native lookup only; no automatic sums or cross-source joins."""
    def __init__(self,cells):
        self.by_source=defaultdict(list); self.keys=set()
        for c in cells:
            if c.key in self.keys:
                raise ValueError("DUPLICATE_CELL")
            self.keys.add(c.key); self.by_source[c.source].append(c)

    def query(self,source,filters=None,*,measure=None,unit=None,start=None,end=None,limit=1000):
        if source not in self.by_source or not isinstance(limit,int) or not 1<=limit<=10000:
            raise ValueError("QUERY_SCOPE")
        filters=filters or {}
        available={k for c in self.by_source[source] for k,v in c.dimensions}
        if not set(filters)<=available or not all(isinstance(v,str) and v for v in filters.values()):
            raise ValueError("UNKNOWN_FILTER")
        if start and end and start>end:
            raise ValueError("QUERY_PERIOD_ORDER")
        out=[]
        for c in self.by_source[source]:
            d=dict(c.dimensions)
            if any(d.get(k)!=v for k,v in filters.items()) or (measure is not None and c.measure!=measure) or (unit is not None and c.unit!=unit) or (start and c.period<start) or (end and c.period>end):
                continue
            out.append(c)
        # No silent truncation: caller receives exact coverage and a bounded page.
        return {"total":len(out),"truncated":len(out)>limit,"records":sorted(out,key=lambda c:(c.period,c.dimensions,c.measure,c.unit))[:limit]}

    def coverage(self,source):
        cells=self.by_source[source]
        dims=defaultdict(set)
        for c in cells:
            for k,v in c.dimensions:
                dims[k].add(v)
        return {"dimension_cardinality":{k:len(v) for k,v in sorted(dims.items())},
            "observed_dimension_measure_unit_combinations":len({(c.dimensions,c.measure,c.unit) for c in cells if c.value is not None}),
            "period_min":min(c.period for c in cells),"period_max":max(c.period for c in cells),
            "observed":sum(c.value is not None for c in cells),"missing_flagged":sum(c.value is None for c in cells),
            "flag_counts":dict(Counter(c.flag for c in cells if c.flag))}


def compare(a,b):
    if (a.source,a.dimensions,a.measure,a.unit,a.sha256,a.vintage)!=(b.source,b.dimensions,b.measure,b.unit,b.sha256,b.vintage) or a.period>=b.period:
        return "BLOCK_SEMANTIC_OR_VINTAGE"
    if a.value is None or b.value is None or a.flag or b.flag:
        return "BLOCK_MISSING_OR_FLAG_REVIEW"
    if a.source.startswith("eurostat_"):
        if a.period<"2025"<=b.period:
            return "BLOCK_2025_DEFINITION_REVIEW"
        return "REVIEW_REQUIRED"
    if a.source=="urssaf_na88":
        if a.period<"2027Q1"<=b.period:
            return "BLOCK_CLASSIFICATION"
        return comparison_gate("urssaf_na88_"+a.measure,a.period,b.period)["decision"]
    if a.source=="urssaf_dpae_na38":
        if a.period<"2027Q1"<=b.period:
            return "BLOCK_CLASSIFICATION"
        return comparison_gate("urssaf_dpae_na38_quarterly",a.period,b.period)["decision"]
    if a.source=="urssaf_dpae_monthly":
        return comparison_gate("urssaf_dpae_monthly_over_1_month",a.period,b.period)["decision"]
    return "BLOCK"


def publication_gate(cell,purpose):
    # No live dataset values are approved for release by this increment.
    return "INTERNAL_REVIEW_ONLY" if purpose=="internal_research" else "BLOCK_PUBLICATION"


def run(fetcher=retrieve):
    cells=[]; metadata={}
    for source,url in SOURCES.items():
        raw=fetcher(url)
        stamp=datetime.now(timezone.utc).isoformat()
        rows,profile=(read_urssaf if source in URSSAF else read_euro)(source,raw,stamp)
        if not rows:
            raise ValueError("EMPTY_SOURCE")
        cells.extend(rows)
        metadata[source]={"source_url":url,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"retrieved_at":stamp,**profile}
    idx=Index(cells)
    for s in SOURCES:
        metadata[s].update(idx.coverage(s))
        metadata[s]["publication_gate"]="BLOCK_PUBLICATION"
    # Query exact France ICT, same codes as prior pilot; do not emit values.
    q=idx.query("eurostat_nace",{"geo":"FR","nace_r2":"J","size_emp":"GE10","indic_is":"E_AI_TANY","freq":"A"},measure="E_AI_TANY",unit="PC_ENT")
    if not q["total"]:
        raise ValueError("PILOT_QUERY_NO_COVERAGE")
    return {"version":VERSION,"sources":metadata,"total_cells":len(cells),
        "observed_cells":sum(c.value is not None for c in cells),"missing_flagged_cells":sum(c.value is None for c in cells),
        "pilot_exact_query_count":q["total"],"pilot_exact_query_flag_count":sum(bool(c.flag) for c in q["records"]),
        "raw_or_derived_values_published":False,"cross_source_join_permitted":False,"causal_claims_permitted":False,"full_source_qualification":False}


if __name__=="__main__":
    try:
        print(json.dumps(run(),ensure_ascii=False,indent=2))
    except Exception as exc:
        # Do not echo source rows, sensitive data or URLs in public workflow logs.
        print(json.dumps({"status":"BLOCKED","error_type":type(exc).__name__}))
        raise SystemExit(2)
