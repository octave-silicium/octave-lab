"""Acquire standard TES and Eurostat 2022 branch income data; inventory before mapping."""
import hashlib, json, urllib.request, io, zipfile
from pathlib import Path
from datetime import datetime, timezone
import openpyxl, re
from xml.etree import ElementTree as ET

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
    ns={"s":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rid="{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    import posixpath
    result=[]; exact={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if sum(i.file_size for i in z.infolist())>100_000_000 or z.testzip(): raise ValueError("ZIP")
        wb=ET.fromstring(z.read("xl/workbook.xml"))
        rel=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        targets={x.attrib["Id"]:x.attrib["Target"] for x in rel}
        strings=[]
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("s:si",ns):
                strings.append("".join(x.text or "" for x in si.findall(".//s:t",ns)))
        for s in wb.findall("s:sheets/s:sheet",ns):
            target=targets[s.attrib[rid]]
            member=target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/"+target)
            if not re.fullmatch(r"xl/worksheets/sheet[0-9]+\.xml",member): raise ValueError("SHEET_PATH")
            root=ET.fromstring(z.read(member)); rows=[]; cells={}
            for row in root.findall(".//s:sheetData/s:row",ns):
                labels=[]; vals=[]
                for c in row.findall("s:c",ns):
                    ref=c.attrib["r"]; typ=c.get("t","n"); v=c.find("s:v",ns); f=c.find("s:f",ns)
                    value=v.text if v is not None else None
                    if typ=="s" and value is not None: value=strings[int(value)]
                    if typ=="inlineStr": value="".join(x.text or "" for x in c.findall(".//s:t",ns))
                    if value is None and f is None: continue
                    cells[ref]={"type":typ,"value":value,"formula":f.text if f is not None else None}
                    if typ in ("s","inlineStr","str") and value: labels.append([ref,value])
                    if typ=="n" and value is not None and f is None: vals.append([ref,value])
                if labels or vals: rows.append({"row":int(row.attrib["r"]),"labels":labels[:45],"numeric_count":len(vals),"first_numeric":vals[:3],"last_numeric":vals[-2:]})
            dim=root.find("s:dimension",ns)
            result.append({"sheet":s.attrib["name"],"dimension":dim.get("ref") if dim is not None else None,"rows":rows})
            exact[s.attrib["name"]]=cells
    (OUT/"exact_cells.json").write_text(json.dumps(exact,ensure_ascii=False,indent=2))
    return {"sheets":result,"reader":"OOXML cell XML only; styles/drawings not interpreted"}
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
