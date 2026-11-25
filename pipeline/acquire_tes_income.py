"""Acquire standard TES and Eurostat 2022 branch income data; inventory before mapping."""
import hashlib, json, urllib.request, io, zipfile
from pathlib import Path
from datetime import datetime, timezone
import openpyxl

OUT=Path("tes-income"); OUT.mkdir(exist_ok=True)
URLS={
"standard.xlsx":"https://www.insee.fr/fr/statistiques/fichier/8988861/TES_38_2022_fr.xlsx",
"eurostat.json":"https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10_a64?lang=EN&freq=A&unit=CP_MEUR&geo=FR&time=2022"
}
def get(name,url):
    req=urllib.request.Request(url,headers={"User-Agent":"OctaveLab economic research"})
    with urllib.request.urlopen(req,timeout=60) as r:
        if not r.geturl().startswith(("https://www.insee.fr/","https://ec.europa.eu/")): raise ValueError("origin")
        raw=r.read(20_000_001)
        if not 0<len(raw)<=20_000_000: raise ValueError("size")
        meta={"url":url,"resolved_url":r.geturl(),"status":r.status,"content_type":r.headers.get("Content-Type"),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"collected_utc":datetime.now(timezone.utc).isoformat()}
    (OUT/name).write_bytes(raw)
    return raw,meta
def workbook(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if sum(i.file_size for i in z.infolist())>100_000_000 or z.testzip(): raise ValueError("ZIP")
    w=openpyxl.load_workbook(io.BytesIO(raw),data_only=True)
    result=[]
    for s in w:
        rows=[]
        for row in s.iter_rows():
            labels=[[c.coordinate,c.value] for c in row if isinstance(c.value,str) and c.value.strip()]
            vals=[c for c in row if type(c.value) in (int,float)]
            if labels or vals: rows.append({"row":row[0].row,"labels":labels[:12],"numeric_count":len(vals),"first_numeric":[[c.coordinate,c.value] for c in vals[:3]],"last_numeric":[[c.coordinate,c.value] for c in vals[-2:]]})
        result.append({"sheet":s.title,"dimension":s.calculate_dimension(),"rows":rows})
    return result
def euro(raw):
    e=json.loads(raw); assert e["class"]=="dataset"
    return {"id":e["id"],"size":e["size"],"updated":e.get("updated"),"dimensions":{k:{"index":v["category"]["index"],"label":v["category"]["label"]} for k,v in e["dimension"].items()},"observed_values":len(e["value"]),"flags":e.get("status",{})}
def main():
    a,am=get("standard.xlsx",URLS["standard.xlsx"])
    p={"standard":am,"workbook":workbook(a),"status":"PROFILE_ONLY","publication":"BLOCK_PUBLICATION"}
    try:
        b,bm=get("eurostat.json",URLS["eurostat.json"]);p["eurostat"]=bm;p["eurostat_profile"]=euro(b)
    except Exception as exc:
        p["eurostat_error"]=type(exc).__name__+": "+str(exc)
    (OUT/"profile.json").write_text(json.dumps(p,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(p,ensure_ascii=False))
if __name__=="__main__": main()
