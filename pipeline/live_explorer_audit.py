"""Internal live HTTP integration audit. No values or screenshots in the report."""
import json
import threading
import time
from http.server import ThreadingHTTPServer
from http.client import HTTPConnection
from urllib.parse import urlencode
from .explorer import LazyExplorer,make_handler
from . import semantic_v4 as v4

def run():
    x=LazyExplorer(live=True)
    server=ThreadingHTTPServer(("127.0.0.1",0),make_handler(x))
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    def get(path,params=None,host=None):
        conn=HTTPConnection("127.0.0.1",server.server_port,timeout=120)
        try:
            conn.request("GET",path+("?" + urlencode(params) if params else ""),headers={"Host":host or f"127.0.0.1:{server.server_port}"})
            r=conn.getresponse()
            if r.getheader("Cache-Control")!="no-store":
                raise ValueError("CACHE_POLICY")
            return r.status,json.loads(r.read())
        finally:
            conn.close()
    try:
        status,meta=get("/api/sources")
        if status!=200 or len(meta["sources"])!=9 or x.loaded:
            raise ValueError("INITIAL_CATALOG")
        result={}
        for source in sorted(v4.LIVE_SOURCES):
            t=time.perf_counter()
            status,d=get("/api/discover",{"source":source,"filters":"{}"})
            if status!=200 or not d["series"]:
                raise ValueError("DISCOVERY")
            elapsed=round((time.perf_counter()-t)*1000,2)
            series=d["series"][0]
            status,detail=get("/api/series",{"source":source,"id":series["id"]})
            if status!=200 or detail["publication"]!="BLOCK_PUBLICATION" or detail["persistence"]!="LIVE":
                raise ValueError("DETAIL")
            if any(p["quality"] in {"WITHHELD","RESTRICTED"} and p["value"] is not None for p in detail["points"]+detail["records"]):
                raise ValueError("VALUE_LEAK")
            status,point=get("/api/point",{"source":source,"id":series["id"],"period":detail["points"][0]["period"]})
            if status!=200 or point["publication"]!="BLOCK_PUBLICATION":
                raise ValueError("POINT")
            if point["quality"] in {"WITHHELD","RESTRICTED"} and point["value"] is not None:
                raise ValueError("POINT_LEAK")
            status,_=get("/api/restore",{"source":source,"id":series["id"],"sha":detail["snapshot_sha256"],"start":"","end":""})
            if status!=400:
                raise ValueError("LIVE_RESTORE_NOT_BLOCKED")
            cat=x.loaded[source].catalog
            if set(cat.by)!={source}:
                raise ValueError("SOURCE_ISOLATION")
            # Verify every series through the same serializer, without publishing values.
            counts={"series":0,"cells":0,"masked":0}
            for g in x.loaded[source].series[source]:
                response=x.loaded[source].detail(source,g["id"])
                counts["series"]+=1
                counts["cells"]+=response["total"]
                for p in response["points"]:
                    if p["quality"] in {"WITHHELD","RESTRICTED"}:
                        counts["masked"]+=1
                        if p["value"] is not None:
                            raise ValueError("FULL_SOURCE_LEAK")
            result[source]={**counts,"first_access_ms":elapsed,"http_discover_detail_point":"PASS","live_restore":"BLOCKED","sha256":detail["snapshot_sha256"]}
        status,_=get("/api/sources",host="example.org")
        if status!=403 or set(x.loaded)!=v4.LIVE_SOURCES:
            raise ValueError("SECURITY_OR_SCOPE")
        return {"version":"0.3.0","sources":result,"loaded_live_sources":len(result),"values_emitted":False,"browser_live_tested":False,"production_vault_provisioned":False}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

if __name__=="__main__":
    try:
        print(json.dumps(run(),indent=2))
    except Exception as exc:
        print(json.dumps({"status":"BLOCKED","error_type":type(exc).__name__}))
        raise SystemExit(2)
