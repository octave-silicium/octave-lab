"""Acquire and inventory Insee 9.400 A38; never admits an observed table to G4."""
import argparse, hashlib, json, re, zipfile, urllib.request
from pathlib import Path
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

URL = "https://www.insee.fr/fr/statistiques/fichier/8988861/TES_symetrique_A38_2022DEF_fr.xlsx"
PAGE = "https://www.insee.fr/fr/statistiques/8988861"
LICENSE = "https://www.insee.fr/fr/information/2008466?page=copyright.htm"
NS = {"s":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
MAX_BYTES = 10_000_000

def profile(path):
    raw = path.read_bytes()
    if not (0 < len(raw) <= MAX_BYTES): raise ValueError("SIZE")
    with zipfile.ZipFile(path) as z:
        if sum(i.file_size for i in z.infolist()) > 50_000_000: raise ValueError("ZIP_SIZE")
        if z.testzip(): raise ValueError("ZIP_CRC")
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rel = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        targets = {x.attrib["Id"]:x.attrib["Target"] for x in rel}
        sheets=[]
        for s in wb.findall("s:sheets/s:sheet", NS):
            rid=s.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            target=targets[rid]
            member=target.lstrip("/") if target.startswith("/") else "xl/"+target
            if not re.fullmatch(r"xl/worksheets/sheet[0-9]+\.xml",member): raise ValueError("SHEET_PATH")
            root=ET.fromstring(z.read(member))
            cells=root.findall(".//s:sheetData/s:row/s:c",NS)
            counts={"numeric":0,"text":0,"formula":0,"error":0,"empty":0,"other":0}
            for c in cells:
                v=c.find("s:v",NS); f=c.find("s:f",NS)
                typ=c.attrib.get("t","n")
                key=("formula" if f is not None else "text" if typ in ("s","inlineStr","str") else "error" if typ=="e" else "empty" if v is None or v.text is None else "numeric" if typ=="n" else "other")
                counts[key]+=1
            dim=root.find("s:dimension",NS)
            sheets.append({"name":s.attrib["name"],"state":s.attrib.get("state","visible"),"xml_path":member,"dimension":dim.attrib.get("ref") if dim is not None else None,"cells":counts})
        if not sheets: raise ValueError("NO_SHEETS")
    return {"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"sheets":sheets}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--output",type=Path,required=True); p.add_argument("--local",type=Path)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    path=a.output/"TES_symetrique_A38_2022DEF_fr.xlsx"
    if a.local:
        raw=a.local.read_bytes(); meta={"acquisition":"local_unverified_origin"}
    else:
        req=urllib.request.Request(URL,headers={"User-Agent":"OctaveLab research data acquisition"})
        with urllib.request.urlopen(req,timeout=60) as r:
            if not r.geturl().startswith("https://www.insee.fr/"): raise ValueError("REDIRECT_ORIGIN")
            raw=r.read(MAX_BYTES+1)
            meta={"acquisition":"official_https","resolved_url":r.geturl(),"http_status":r.status,"etag":r.headers.get("ETag"),"last_modified":r.headers.get("Last-Modified"),"content_type":r.headers.get("Content-Type")}
    if not 0<len(raw)<=MAX_BYTES: raise ValueError("SIZE")
    path.write_bytes(raw)
    result={"source":"Insee","source_url":URL,"publication_url":PAGE,"publication_date":"2026-08-05","license_reference":LICENSE,"license_candidate":"Etalab Open Licence 2.0; verify workbook exceptions before admission","year":2022,"classification_candidate":"A38","accounting_base":2020,"collected_utc":datetime.now(timezone.utc).isoformat(),**meta,**profile(path),"status":"RAW_PROFILE_ONLY","observed_matrix_admitted":False,"publication":"BLOCK_PUBLICATION"}
    (a.output/"manifest.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
