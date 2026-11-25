"""V1.2: qualify only the pinned corrected NA38 release for internal descriptive use.
Legacy source gate remains blocked. No public release and no causal claim.
"""
import json,re,html,datetime
from decimal import Decimal
from .vertical_v1 import OLD,SOURCES,retrieve,digest,require,number,pkey,read_csv,GROUPS,CONTRACTS,pct
from .vertical_v11 import PERIODS
from .economic_core import canonical,digest as canonical_digest
META="https://open.urssaf.fr/api/explore/v2.1/catalog/datasets/dpae-france-entiere-x-na38"
PIN="42cd99124b1ef5f0a39afc481c42e70d5adc0fbfb535a7cb53f2653dfd41f549"
ANCHOR={"CDI":Decimal(1036794),"CDD de plus d'un mois":Decimal(973672)}
NOTICE="https://www.data.gouv.fr/datasets/declarations-prealables-a-lembauche-france-entiere-x-secteur-na38"
DASHBOARD="https://open.urssaf.fr/explore/dataset/dpae-france-entiere-x-na38/dataviz/"
def metadata(b):
    j=json.loads(b);require(j.get("dataset_id")=="dpae-france-entiere-x-na38","DATASET_ID")
    m=j["metas"]["default"];desc=html.unescape(re.sub("<[^>]*>"," ",m.get("description","")))
    desc=" ".join(desc.lower().split())
    require(all(t in desc for t in ("30 octobre 2026","correctifs","secteur privé","non-fonctionnaires")),"CORRECTION_NOTICE_NOT_MATCHED")
    modified=m.get("modified") or m.get("data_processed")
    require(isinstance(modified,str) and modified[:10]>="2026-10-30","MODIFIED_VINTAGE")
    return {"dataset_id":j["dataset_id"],"modified":modified,"publisher":m.get("publisher"),"notice_sha256":digest(b),"corrected_private_scope_notice":True}
def parse(b):
    require(digest(b)==PIN,"UNREVIEWED_VINTAGE")
    rows=read_csv(b,{"secteur_na38","annee","trimestre","duree_de_contrat","nature_de_contrat","dpae_cvs"})
    selected={};national={};native=set()
    for n,r in enumerate(rows,1):
        p=pkey(r)
        if p not in PERIODS or r["nature_de_contrat"].strip() not in CONTRACTS or r["duree_de_contrat"].strip()!="Contrat de plus d'un mois":continue
        c=r["nature_de_contrat"].strip();sec=r["secteur_na38"].strip().split(" ")[0]
        key=(p,sec,c);require(key not in native,"DUPLICATE_NATIVE");native.add(key)
        v=number(r["dpae_cvs"])
        if p=="2026Q3":national[c]=national.get(c,Decimal(0))+v
        if sec in GROUPS:selected[key]=(v,n)
    require(set(national)==set(ANCHOR),"ANCHOR_MISSING")
    # Source's published rounded total vs sum of displayed native rounded cells.
    # Allow <= number of components/2 plus 0.5 rounding; record actual residuals.
    residual={c:national[c]-ANCHOR[c] for c in ANCHOR}
    counts={c:sum(p=="2026Q3" and x==c for p,_,x in native) for c in ANCHOR}
    require(all(abs(residual[c])<=Decimal(counts[c]+1)/2 for c in ANCHOR),"NATIONAL_ANCHOR_MISMATCH")
    require(len(selected)==len(PERIODS)*len(GROUPS)*len(CONTRACTS),"INCOMPLETE_J_PANEL")
    levels={}
    for p in PERIODS:
        vals={g:sum(selected[p,g,c][0] for c in CONTRACTS) for g in GROUPS}
        levels[p]={"total":str(sum(vals.values())),"groups":{g:str(v) for g,v in vals.items()},
                   "components":{g+"|"+c:{"value":str(selected[p,g,c][0]),"source_record":selected[p,g,c][1]} for g in GROUPS for c in CONTRACTS}}
    comparisons=[]
    for p in PERIODS:
        prev=f"{int(p[:4])-1}{p[4:]}"
        if prev not in levels:continue
        a,z=levels[prev],levels[p];base=Decimal(a["total"]);delta=Decimal(z["total"])-base
        groups={g:{"change":str(Decimal(z["groups"][g])-Decimal(a["groups"][g])),"relative_change_pct":pct(Decimal(z["groups"][g])-Decimal(a["groups"][g]),Decimal(a["groups"][g]))} for g in GROUPS}
        require(sum(Decimal(g["change"]) for g in groups.values())==delta,"CONTRIBUTION_IDENTITY")
        comparisons.append({"from":prev,"to":p,"status":"DESCRIPTIVE_SAME_CORRECTED_VINTAGE_WITH_CAVEATS","change":str(delta),"relative_change_pct":pct(delta,base),"groups":groups})
    return {"levels":levels,"comparisons":comparisons,"anchor_residual":{k:str(v) for k,v in residual.items()},"anchor_component_counts":counts}
def audit(fetcher=retrieve):
    m=metadata(fetcher(META));b=fetcher(SOURCES["urssaf_dpae"]);a=parse(b)
    result={"study":"VERTICAL-001","phase":"V1.2","metadata":m,"csv_sha256":digest(b),"scope":"private general scheme excluding temporary agency work, CVS-CJO; declarations not realized hires",
           "source_notice":NOTICE,"source_dashboard":DASHBOARD,"series_id":"urssaf_dpae_na38_private_corrected_20261030_pinned",
           "admission":"INTERNAL_DESCRIPTIVE_SAME_VINTAGE_WITH_CAVEATS","legacy_gate":"UNCHANGED_BLOCK",
           "publication":"BLOCK_PUBLICATION","causal_identification":"NOT_IDENTIFIED","periods":len(a["levels"]),
           "comparisons":len(a["comparisons"]),"previously_held_comparisons":sum(c["to"]>="2025Q1" for c in a["comparisons"]),
           "anchor_residual":a["anchor_residual"],"anchor_component_counts":a["anchor_component_counts"],
           "internal_result_sha256":canonical_digest(canonical(a)),
           "limitations":["Publisher confirms statistical corrections and private scope for dataset; no independent microdata correction audit or old/new scope bridge.",
                          "National published dashboard itself compares one and three years. Same release only; no splicing with old data or unrestricted comparability claim.",
                          "Provisional values and revisions, residual biases and sector-specific correction uncertainty remain."] }
    return result
if __name__=="__main__":
    print("VERTICAL_V12 "+json.dumps(audit(),ensure_ascii=False))
