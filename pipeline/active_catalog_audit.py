"""Verify all nine analytical sources through the approved vault and local HTTP."""
import gzip,json,tempfile,threading
from pathlib import Path
from http.server import ThreadingHTTPServer
from http.client import HTTPConnection
from urllib.parse import urlencode
from collections import Counter
from .data_vault import Vault,sha,ROOT
from .vault_ops import retrieve,backup,restore
from .data_observatory import read_registry
from .active_catalog import VaultExplorer
from .explorer import make_handler
def run():
    specs=[s for s in read_registry() if s["kind"] in {"indeed_national","indeed_sector","dares","xlsx","live_native"}]
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);v=Vault(root/"vault")
        for s in specs:
            h=s["baseline_sha256"];kind=s["kind"]
            if kind.startswith("indeed_"):
                suffix="national" if kind=="indeed_national" else "sector"
                raw=(ROOT/"snapshots/indeed-fr/2026-11"/f"indeed_fr_{suffix}_{h[:12]}.csv").read_bytes()
            elif kind=="dares":raw=gzip.decompress((ROOT/"snapshots/dares-ft-monthly/2026-11"/f"dares_ft_monthly_{h[:12]}.csv.gz").read_bytes())
            elif kind=="xlsx":raw=(ROOT/"snapshots/insee-sector/2026-11"/f"insee_sector_{h[:12]}.xlsx").read_bytes()
            else:raw=retrieve(s)
            if kind!="live_native" and sha(raw)!=h:raise ValueError("ARCHIVE_HASH")
            d=v.stage(s,raw)
            if d["status"]!="STAGED":raise ValueError("STAGE")
            v.promote(s["id"],d["sha"],None,"CI_ACCEPTANCE_ONLY")
        m=backup(v,root/"backup");v.close()
        restore(root/"backup",root/"restored",m["database_sha256"])
        x=VaultExplorer(root/"restored")
        server=ThreadingHTTPServer(("127.0.0.1",0),make_handler(x))
        t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        def get(path,params=None):
            conn=HTTPConnection("127.0.0.1",server.server_port,timeout=120)
            try:
                conn.request("GET",path+("?" + urlencode(params) if params else ""))
                r=conn.getresponse()
                return r.status,json.loads(r.read())
            finally:conn.close()
        try:
            status,meta=get("/api/sources")
            assert status==200 and len(meta["sources"])==9 and not x.loaded
            results={}
            for s in specs:
                sid=s["id"]
                status,d=get("/api/discover",{"source":sid})
                assert status==200 and d["series"]
                g=d["series"][0]
                status,series=get("/api/series",{"source":sid,"id":g["id"]})
                assert status==200 and series["storage"]=="VAULT_SESSION_PIN" and series["snapshot_sha256"]==x.active.pins[sid][0]
                status,again=get("/api/restore",{"source":sid,"id":g["id"],"sha":series["snapshot_sha256"],"start":"","end":""})
                assert status==200 and again["decision"]=="MATCH"
                counts=Counter()
                rows=0
                e=x.loaded[sid]
                for group in e.series[sid]:
                    # The same serializer as HTTP, without transmitting or logging all values.
                    d=x.detail(sid,group["id"])
                    rows+=d["total"]
                    for p in d["points"]:
                        counts[p["quality"]]+=1
                        if p["quality"] in {"RESTRICTED","WITHHELD"} and p["value"] is not None:raise ValueError("MASK")
                results[sid]={"cells":rows,"series":len(e.series[sid]),"quality":dict(counts),"sha256":series["snapshot_sha256"],"http":"PASS"}
            return {"scope":"TEMPORARY_CI_RESTORED_APPROVED_VAULT","sources":results,"cells":sum(r["cells"] for r in results.values()),"all_sources":len(results),"backup_bytes":m["bytes"],"publication":"BLOCK_PUBLICATION","raw_data_uploaded":False,"production_deployed":False}
        finally:server.shutdown();server.server_close();t.join()
if __name__=="__main__":
    try:print(json.dumps(run(),indent=2))
    except Exception as e:
        print(json.dumps({"status":"FAILED","error_type":type(e).__name__,"reason":str(e) if isinstance(e,ValueError) and str(e).isupper() else "ACCEPTANCE_FAILED"}));raise SystemExit(2)
