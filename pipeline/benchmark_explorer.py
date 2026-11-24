"""Internal benchmark on archived data. Publish timings and counts only."""
import json
import platform
import statistics
import time
from pipeline.explorer import Explorer,archive_catalog,LazyExplorer

def measure(fn,n=40):
    fn()
    samples=[]
    for _ in range(n):
        t=time.perf_counter()
        fn()
        samples.append((time.perf_counter()-t)*1000)
    samples.sort()
    return {"iterations":n,"median_ms":round(statistics.median(samples),3),"p95_ms":round(samples[(95*n+99)//100-1],3),"max_ms":round(max(samples),3)}

def main():
    t=time.perf_counter()
    x=Explorer(archive_catalog())
    cold=round((time.perf_counter()-t)*1000,2)
    indeed="indeed_sector_total_daily"
    dares="dares_offers_monthly"
    q=x.discover(indeed,{})
    f=q["choices"]["occupation_family"][0]["value"]
    d=x.discover(dares,{})
    assert d["total"]>0
    sid=d["series"][0]["id"]
    t=time.perf_counter()
    lazy=LazyExplorer()
    lazy.sources()
    lazy_setup=round((time.perf_counter()-t)*1000,3)
    t=time.perf_counter()
    first=lazy.discover("indeed_national_total_daily",{})
    lazy.detail("indeed_national_total_daily",first["series"][0]["id"])
    first_series=round((time.perf_counter()-t)*1000,3)
    assert set(lazy.loaded)=={"indeed_national_total_daily"}
    first_access={}
    for source in ("insee_employment","indeed_sector_total_daily","dares_offers_monthly"):
        t=time.perf_counter()
        lazy.discover(source,{})
        first_access[source]=round((time.perf_counter()-t)*1000,3)
    result={
        "version":"0.3.0","lazy_setup_ms":lazy_setup,"lazy_first_series_ms":first_series,"lazy_other_first_access_ms":first_access,"lazy_sources_loaded":len(lazy.loaded),"environment":{"python":platform.python_version(),"system":platform.system(),"machine":platform.machine()},
        "catalog_build_ms":cold,"source_count":len(x.sources()),
        "archived_cells":sum(len(rows) for rows in x.catalog.by.values()),
        "benchmarks":{
            "indeed_exact_filter":measure(lambda:x.discover(indeed,{"occupation_family":f})),
            "dares_catalog":measure(lambda:x.discover(dares,{})),
            "dares_native_series":measure(lambda:x.detail(dares,sid)),
            "indeed_full_daily":measure(lambda:x.detail("indeed_national_total_daily","0")),
            "indeed_comparison_gate":measure(lambda:x.comparison("indeed_national_total_daily","0","2020-02-01","2020-02-02")),
        },
        "scope":"Python functions on loaded archive catalog; no HTTP or browser, no live collection, no field metrics",
        "values_emitted":False,"public_release_approved":False
    }
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
