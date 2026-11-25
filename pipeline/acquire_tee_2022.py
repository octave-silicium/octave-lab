"""Acquire official 2022 TEE and annual sector accounts. Profile only."""
import json
from pathlib import Path
from pipeline import acquire_tes_income as acq

URLS={"tee.xlsx":"https://www.insee.fr/fr/statistiques/fichier/8988861/TEE_2022_fr.xlsx","sector_eurostat.json":"https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nasa_10_nf_tr?lang=EN&freq=A&unit=CP_MEUR&geo=FR&time=2022","standard.xlsx":acq.URLS["standard.xlsx"]}
def main():
    acq.OUT=Path("tee-2022");acq.OUT.mkdir(exist_ok=True)
    result={"status":"RAW_PROFILE_ONLY","publication":"BLOCK_PUBLICATION","sources":{}}
    for name,url in URLS.items():
        raw,meta=acq.get(name,url);result["sources"][name]=meta
        if name.endswith(".xlsx"):
            p=acq.workbook(raw)
            (acq.OUT/"exact_cells.json").rename(acq.OUT/(name+".cells.json"))
            result[name]=p
        else:result[name]=acq.euro(raw)
    (acq.OUT/"profile.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"sources":result["sources"],"sheets":{k:[{"sheet":s["sheet"],"dimension":s["dimension"],"rows":len(s["rows"])} for s in result[k]["sheets"]] for k in ("tee.xlsx","standard.xlsx")},"eurostat":{k:result["sector_eurostat.json"][k] for k in ("id","size","updated","observed_values")}},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
