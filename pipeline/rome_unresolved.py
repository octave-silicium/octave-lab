"""Diagnose unresolved ROME references using only exact native keys; no imputation."""
import json
from collections import Counter,defaultdict
from .rome_graph import load
from .rome_inventory import URL
from .european_work import fetch

def audit(g):
    apps=defaultdict(set)
    for n,r in g.tables["referentiel_appellation"]:
        apps[r["code_ogr"]].add(r["code_rome"])
    extended=defaultdict(set)
    for n,r in g.tables["cr_gd_dp_appellations"]:
        extended[r["ogr_appellation"]].add(r["numero_fiche_rome"])
    result=Counter();rubrics=Counter();blocks=Counter()
    for occupation,links in g.links.items():
        for n,r,candidates,status in links:
            if status!="UNRESOLVED_ITEM":continue
            k=r["code_ogr"]
            rubrics[r["code_rubrique"]]+=1
            blocks[r["code_compo_bloc"]]+=1
            a=apps.get(k,set());b=extended.get(k,set())
            if occupation in a and occupation in b:category="BOTH_EXACT_OCCUPATION"
            elif occupation in a:category="PRIMARY_EXACT_OCCUPATION"
            elif occupation in b:category="EXTENDED_EXACT_OCCUPATION"
            elif a or b:category="CODE_PRESENT_OCCUPATION_NOT_CONFIRMED"
            else:category="NO_MATCH"
            result[category]+=1
    return {"archive_sha256":g.manifest["sha256"],"unresolved":sum(result.values()),"candidate_appellation_matches":dict(result),"rubrics":dict(rubrics),"blocks":dict(blocks),"new_resolved_links":0,"decision":"DIAGNOSTIC_ONLY_REVIEW_REQUIRED"}
if __name__=="__main__":print(json.dumps(audit(load(fetch(URL)[0])),indent=2))
