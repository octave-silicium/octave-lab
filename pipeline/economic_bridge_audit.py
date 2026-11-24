"""CI acceptance: official O*NET + approved temporary Indeed vault, no raw values emitted."""
import json,tempfile
from pathlib import Path
from . import work_graph,invoice_pilot
from .economic_work import from_onet_profile
from .economic_native import from_active_catalog
from .data_vault import Vault,ROOT
from .data_observatory import read_registry
from .active_catalog import ActiveCatalog
def run():
    g=from_onet_profile(work_graph.build(),invoice_pilot.CODE,include_candidate=True)
    counts={kind:sum(e.kind==kind for e in g.entities.values()) for kind in ("OCCUPATION","TASK","PROCESS","ACTION")}
    assert counts["OCCUPATION"]==1 and counts["PROCESS"]==1 and counts["ACTION"]==6
    assert all(c.quantity is None for c in g.claims.values())
    spec=next(s for s in read_registry() if s["kind"]=="indeed_national")
    h=spec["baseline_sha256"]
    raw=(ROOT/"snapshots/indeed-fr/2026-11"/f"indeed_fr_national_{h[:12]}.csv").read_bytes()
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)/"vault";v=Vault(root)
        d=v.stage(spec,raw);assert d["status"]=="STAGED" and d["sha"]==h
        v.promote(spec["id"],h,None,"CI_ACCEPTANCE_ONLY");v.close()
        active=ActiveCatalog(root);rows,meta=from_active_catalog(active,spec["id"])
        assert len(rows)>0 and all(e.sha256==h for e,c in rows)
    return {"onet_entities":counts,"onet_assertions":len(g.assertions),"onet_graph_sha256":g.fingerprint,"approved_vault":meta,"publication":"BLOCK_PUBLICATION","production_deployed":False,"scientific_gate_promoted":False}
if __name__=="__main__":print(json.dumps(run(),indent=2))
