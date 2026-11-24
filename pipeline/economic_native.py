"""Native G1 bridge. No crosswalk, conversion, aggregation or public values."""
from datetime import date,datetime
from calendar import monthrange
from .economic_core import Scope,Evidence,Quantity,Claim,Graph,Requirements,digest,canonical,require
from . import semantic_v4 as v4
def bounds(p,f):
    y=int(p[:4])
    if f=="D":return p,p
    if f=="A":return f"{y:04d}-01-01",f"{y:04d}-12-31"
    m=int(p[5:7]) if f=="M" else (int(p[-1])-1)*3+1
    end=m if f=="M" else m+2
    return date(y,m,1).isoformat(),date(y,end,monthrange(y,end)[1]).isoformat()
def from_record(r):
    require(isinstance(r,v4.Record),"NATIVE_RECORD_REQUIRED")
    require(r.quality[0]=="DESCRIPTIVE_ONLY" and r.value is not None,"NATIVE_QUALITY_BLOCKED")
    stamp=datetime.fromisoformat(r.vintage)
    require(stamp.tzinfo is not None,"VINTAGE_TIMEZONE")
    ident=digest(canonical([r.source,r.period,r.dimensions,r.measure,r.unit,r.vintage,r.sha256,r.locator]))
    native=r.internal_result()
    dims=dict(r.dimensions);start,end=bounds(r.period,v4.FREQ[r.source])
    scope=Scope("Source-native: "+canonical(dims).decode(),dims.get("geo",dims.get("country","SOURCE_NATIVE_GEOGRAPHY_UNQUALIFIED")),r.source+" native version unqualified",start,end,"NOT_CONVERTED")
    ev=Evidence("native:evidence:"+ident,1,"NATIVE_SOURCE",r.source_url,r.locator,r.sha256,r.vintage,stamp.date().isoformat(),None,"INTERNAL_ONLY","DESCRIPTIVE_ONLY")
    c=Claim("native:claim:"+ident,1,"OBSERVATION",r.source+" / "+r.measure+" / "+r.period,"Descriptive input only",scope,Quantity(r.value,"NATIVE",r.unit),(ev.key,),(),"Native record; no conversion or crosswalk; storage "+r.persistence+"; lineage "+native["lineage"]+"; license "+native["license"],"Source native definition; publication and comparative rights not qualified","No causal attribution","Re-evaluate on revised source vintage",())
    return ev,c
def from_live_record(r):
    require(isinstance(r,v4.Record) and r.persistence=="LIVE_TRANSIENT","LIVE_NATIVE_REQUIRED")
    return from_record(r)

def from_active_catalog(active, source):
    # ActiveCatalog revalidates the bytes and pins before parsing; no fallback.
    from .active_catalog import ActiveCatalog
    require(isinstance(active,ActiveCatalog),"ACTIVE_CATALOG_REQUIRED")
    catalog=active.load(source)
    h,stamp=active.pins[source]
    admitted=[];blocked=0
    for r in catalog.by[source]:
        require((r.sha256,r.vintage)==(h,stamp),"ACTIVE_PIN_MISMATCH")
        if r.quality[0]!="DESCRIPTIVE_ONLY" or r.value is None:
            blocked+=1
            continue
        admitted.append(from_record(r))
    return admitted,{"source":source,"sha256":h,"vintage":stamp,"admitted":len(admitted),"blocked":blocked,"storage":"APPROVED_SESSION_PIN","publication":"BLOCK_PUBLICATION"}

def audit():
    from datetime import timezone
    from . import semantic_v3 as v3
    source="eurostat_nace"
    raw=v3.retrieve(v3.SOURCES[source]);stamp=datetime.now(timezone.utc).isoformat()
    rows,_=v3.read_euro(source,raw,stamp);records=[v4.wrap_live(x) for x in rows]
    admitted=[r for r in records if r.quality[0]=="DESCRIPTIVE_ONLY" and r.value is not None]
    blocked=[r for r in records if r.quality[0]!="DESCRIPTIVE_ONLY" or r.value is None]
    # Exercise every cell; never print values or snapshot content.
    es=[];cs=[]
    for r in admitted:
        e,c=from_live_record(r);assert c.quantity.value==r.value and c.quantity.native_unit==r.unit
        es.append(e);cs.append(c)
    for r in blocked:
        try:from_live_record(r)
        except ValueError as e:assert str(e)=="NATIVE_QUALITY_BLOCKED"
        else:raise AssertionError("blocked record admitted")
    graph=Graph(Requirements(),evidence=es,claims=cs)
    assert len(graph.claims)==len(admitted)>0
    return {"source":source,"source_sha256":digest(raw),"collected_at":stamp,"native_rows":len(records),"admitted":len(admitted),"blocked":len(blocked),"exact_value_unit_preserved":True,"graph_sha256":graph.fingerprint,"raw_values_emitted":False,"production_or_publication_approved":False}
if __name__=="__main__":
    import json
    print(json.dumps(audit(),indent=2))
