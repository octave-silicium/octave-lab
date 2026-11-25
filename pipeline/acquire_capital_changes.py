"""Acquire national wealth change accounts and Eurostat 2020–22 stock bridge."""
import json
from pathlib import Path
from pipeline import acquire_tes_income as acq
BASE="https://www.insee.fr/fr/statistiques/fichier/8988859/"
URLS={**{f"wealth_{i}.xlsx":BASE+f"T_{i}_fr.xlsx" for i in (8211,8212,8213,8214,8220)},"wealth_investment.xlsx":BASE+"T_8221_8222_fr.xlsx","eu_stock_bridge.json":"https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10_nfa_st?lang=EN&freq=A&geo=FR&time=2020&time=2021&time=2022"}
def main():
    out=Path("capital-change");out.mkdir(exist_ok=True);acq.OUT=out
    profile={"status":"RAW_PROFILE_ONLY","publication":"BLOCK_PUBLICATION","sources":{}}
    for name,url in URLS.items():
        try:
            raw,meta=acq.get(name,url)
            profile["sources"][name]=meta
            if name.endswith(".xlsx"):
                p=acq.workbook(raw)
                (out/"exact_cells.json").rename(out/(name+".cells.json"))
                meta["sheets"]=[{"sheet":s["sheet"],"rows":len(s["rows"]),"head":s["rows"][:5]} for s in p["sheets"]]
            else:meta["profile"]={k:v for k,v in acq.euro(raw).items() if k not in ("dimensions","flags")}
        except Exception as exc:profile["sources"][name]={"status":"FAILED","url":url,"error":str(exc)}
    (out/"profile.json").write_text(json.dumps(profile,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(profile,ensure_ascii=False))
    if any(x.get("status")!="200" and x.get("status")!=200 for x in profile["sources"].values()):raise ValueError("SOURCE_FAILURE")
if __name__=="__main__":main()
