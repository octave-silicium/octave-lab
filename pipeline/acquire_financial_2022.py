"""Acquire ESA financial accounts; preserve raw sources, no imputation."""
import json
from pathlib import Path
from pipeline import acquire_tes_income as acq
BASE="https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
def main():
    acq.OUT=Path("financial-2022");acq.OUT.mkdir(exist_ok=True)
    profile={"status":"RAW_PROFILE_ONLY","publication":"BLOCK_PUBLICATION","sources":{}}
    for suffix in ("bs","tr","gl","oc"):
        name=suffix+".json";url=BASE+"nasa_10_f_"+suffix+"?lang=EN&freq=A&unit=MIO_EUR&geo=FR&time=2021&time=2022"
        try:
            raw,meta=acq.get(name,url);meta["profile"]=acq.euro(raw);profile["sources"][suffix]=meta
        except Exception as e:profile["sources"][suffix]={"url":url,"error":str(e)}
    (acq.OUT/"profile.json").write_text(json.dumps(profile,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:{**{x:y for x,y in v.items() if x!="profile"},"axes":{d:list(a["index"]) for d,a in v.get("profile",{}).get("dimensions",{}).items()},"observed":v.get("profile",{}).get("observed_values")} for k,v in profile["sources"].items()},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
