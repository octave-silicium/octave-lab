"""Attach local Dares evidence to the V2b2 internal dossier; no network required."""
import argparse,json,os
from pathlib import Path
from .economic_core import canonical,digest,require
from .vertical_v2 import claim
from .vertical_mmo import build as mmo_build,digest as mmo_digest,PINS
ROOT=Path(__file__).resolve().parents[1]
def integrate(base,mmo):
    require(base["sha256"]==digest(canonical(base["result"])),"BASE_HASH")
    require(base["result"]["phase"]=="V2b2" and base["result"]["publication"]=="BLOCK_PUBLICATION","BASE_SCOPE")
    require(mmo["sha256"]==mmo_digest(mmo["result"]),"MMO_HASH")
    require(mmo["result"]["phase"]=="V2b3-MMO" and mmo["result"]["publication"]=="BLOCK_PUBLICATION","MMO_SCOPE")
    require({k:s["sha256"] for k,s in mmo["result"]["sources"].items()}==PINS,"MMO_PINS")
    p=json.loads(json.dumps(base["result"]));p["phase"]="V2b3";p["dares_mmo_evidence"]=mmo
    p["economic_evidence"]["national_context"]=[x for x in p["economic_evidence"]["national_context"] if x["id"]!="N02"]+[{"id":"N02","status":"LOCAL_ORIGINAL_REPLAYED","source":"https://dares.travail-emploi.gouv.fr/donnees/les-mouvements-de-main-doeuvre","period":"2026Q2","receipt_ref":"dares_mmo_evidence"}]
    c=claim("C08","DESCRIPTIVE_COMPARISON","Realized contract entries and endings by type and reason; comparisons inside each pinned workbook only.","contracts and percent","JZ all establishments, private metropolitan France excluding agriculture, temp agency contracts and private households","2019–2026Q2 quarterly; through 2025 annual",["dares_mmo_evidence"],["M049","M050","M061","M063"],"Exact native rows, quarter-over-same-quarter, annual separately, contract balance not employment stock change.","No quarterly detailed layoffs, no distinct worker counts, revisions and shared DSN lineage; no reconciliation to DPAE or employment.","Hiring normalization, composition, demand, mobility, substitution","New vintage, independent worker transitions or sector-level exposure panel")
    c["geography"]="France métropolitaine";p["claims"].append(c);p["overview"]["claim_refs"].append("C08");p["overview"]["observation_refs"].append("dares_mmo_evidence")
    for s in p["sections"]:
        if s["id"] in ("D02","D03","D05","D10","D14","D15","D17","D18"):
            s["content"]+=" Dares MMO local originals integrated: native quarterly and annual contracts, no stock reconciliation or causal attribution."
            s["claim_refs"].append("C08")
    for e in p["coverage"]:
        if e["id"] in ("M049","M050","M061","M063","AC08"):
            e["reason"]+=" Dares contract-flow evidence added; unique-person mobility and full mechanism qualification remain open."
            e["claim_refs"]=list(dict.fromkeys(e["claim_refs"]+["C08"]))
    p["code_sha256"].update({x:digest((ROOT/"pipeline"/x).read_bytes()) for x in ("vertical_mmo.py","vertical_v2b3.py")})
    return {"result":p,"sha256":digest(canonical(p))}
def main():
    a=argparse.ArgumentParser();a.add_argument("base",type=Path);a.add_argument("quarterly",type=Path);a.add_argument("annual",type=Path);a.add_argument("output",type=Path);x=a.parse_args()
    target=x.output.resolve();require(not target.is_relative_to(ROOT),"OUTPUT_OUTSIDE_REPO")
    r=integrate(json.loads(x.base.read_text()),mmo_build(x.quarterly,x.annual))
    with os.fdopen(os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),"w") as f:json.dump(r,f,ensure_ascii=False,indent=2)
    print(json.dumps({"phase":"V2b3","sha256":r["sha256"],"publication":"BLOCK_PUBLICATION"}))
if __name__=="__main__":main()
