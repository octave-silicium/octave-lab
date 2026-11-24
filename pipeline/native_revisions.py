"""Technical revision counts for the five live native contracts; not economic comparisons."""
from . import semantic_v3 as v3,semantic_v4 as v4
from datetime import datetime,timezone
def compare(source,a,b):
    if source not in v3.SOURCES:raise ValueError("SOURCE")
    stamp=datetime.now(timezone.utc).isoformat()
    def index(raw):
        rows,_=(v3.read_urssaf if source in v3.URSSAF else v3.read_euro)(source,raw,stamp)
        if not rows:raise ValueError("EMPTY")
        cat=v4.Catalog(v4.wrap_live(r) for r in rows)
        return {(r.period,r.dimensions,r.measure,r.unit):r for r in cat.by[source]}
    old,new=index(a),index(b)
    shared=set(old)&set(new)
    blocked={"RESTRICTED","WITHHELD"}
    safe=[k for k in shared if old[k].quality[0] not in blocked and new[k].quality[0] not in blocked]
    return {"source":source,"status":"NATIVE_REVISION_COUNTS","added":len(set(new)-set(old)),"removed":len(set(old)-set(new)),"shared":len(shared),"visible_value_changed":sum(old[k].value!=new[k].value for k in safe),"visible_value_unchanged":sum(old[k].value==new[k].value for k in safe),"numeric_comparison_withheld":len(shared)-len(safe),"flag_changed":sum(old[k].flag!=new[k].flag for k in shared),"quality_changed":sum(old[k].quality[0]!=new[k].quality[0] for k in shared),"comparison_scope":"NATIVE_KEYS_ACROSS_VINTAGES_TECHNICAL_ONLY","methodological_review":"REQUIRED","publication":"BLOCK_PUBLICATION"}
