"""Opt-in private G2 read-only API, integrated behind the existing local HTTP guard."""
import threading
from .private_lot import PrivateLot
class PrivateRoutes:
    def __init__(self,path,sha):
        self.lot=PrivateLot(path,sha,cross_thread=True)
        self.lock=threading.Lock()
    def close(self):
        with self.lock:self.lot.close()
    def dispatch(self,path,q):
        with self.lock:
            if path=="/api/private/status" and not q:
                return {"snapshot_sha256":self.lot.sha,"mode":"LOCAL_INTERNAL_READ_ONLY","publication":"BLOCK_PUBLICATION"}
            if path=="/api/private/esco/search" and "q" in q and set(q)<={"q","lang","limit"}:
                return self.lot.search_esco(q["q"],q.get("lang","fr"),int(q.get("limit","30")))
            if path=="/api/private/esco/skills" and "uri" in q and set(q)<={"uri","lang","limit"}:
                return self.lot.esco_skills(q["uri"],q.get("lang","fr"),int(q.get("limit","100")))
            if path=="/api/private/fap/rome" and "rome" in q and set(q)<={"rome","limit"}:
                return self.lot.fap_rome(q["rome"],int(q.get("limit","100")))
            required={"source","sheet","sector","size","col","start","end"}
            if path=="/api/private/mmo/series" and required<=set(q)<=required|{"limit"}:
                return self.lot.mmo_series(**{k:q[k] for k in required},limit=int(q.get("limit","100")))
            raise ValueError("PRIVATE_ROUTE_OR_PARAMETERS")
