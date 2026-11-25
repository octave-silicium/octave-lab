"""G4 v0.7b acquire capital accounts without implicit admission."""
import io,json,zipfile,hashlib,math
from pathlib import Path,PurePosixPath
from pipeline import acquire_tes_income as acq
BASE="https://www.insee.fr/fr/statistiques/fichier/8988825/"
EU="https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
URLS={"fbcf.xlsx":BASE+"T_6301_6303_fr.xlsx","stocks.zip":BASE+"T_6401_6460.zip","ccf.xlsx":BASE+"T_6461_6462_fr.xlsx","eu_stocks.json":EU+"nama_10_nfa_st?lang=EN&freq=A&geo=FR&time=2022","eu_flows.json":EU+"nama_10_nfa_fl?lang=EN&freq=A&geo=FR&time=2022","eu_income.json":EU+"nama_10_a64?lang=EN&freq=A&unit=CP_MEUR&geo=FR&time=2022"}
def main():
    root=Path("capital-2022");root.mkdir(exist_ok=True);acq.OUT=root
    profile={"status":"RAW_PROFILE_ONLY","publication":"BLOCK_PUBLICATION","sources":{},"workbooks":{},"eurostat":{}}
    def wb(name,raw):
        info=acq.workbook(raw);cells=json.loads((root/"exact_cells.json").read_text())
        (root/"exact_cells.json").unlink()
        # Compact inventory of dimensions, labels and 2022 row or column.
        sheets=[]
        for s in info["sheets"]:
            grid=cells[s["sheet"]]
            years=[k for k,v in grid.items() if v["value"] in ("2022","2022.0")]
            sheets.append({"sheet":s["sheet"],"dimension":s["dimension"],"rows":len(s["rows"]),"head":s["rows"][:4],"year_2022_cells":years[:20]})
        profile["workbooks"][name]={"sha256":hashlib.sha256(raw).hexdigest(),"sheets":sheets}
    for name,url in URLS.items():
        raw,meta=acq.get(name,url);profile["sources"][name]=meta
        if name.endswith(".xlsx"):wb(name,raw)
        elif name.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                if sum(i.file_size for i in z.infolist())>100_000_000 or z.testzip():raise ValueError("ZIP")
                seen=set()
                for member in z.infolist():
                    if member.is_dir():continue
                    p=PurePosixPath(member.filename)
                    if p.is_absolute() or ".." in p.parts or not p.name.endswith(".xlsx") or p.name in seen:raise ValueError("ZIP_MEMBER")
                    seen.add(p.name);wb(p.name,z.read(member))
        else:
            e=json.loads(raw);p=acq.euro(raw)
            if math.prod(e["size"])<len(e["value"]):raise ValueError("DIMENSIONS")
            profile["eurostat"][name]=p
    (root/"profile.json").write_text(json.dumps(profile,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"sources":profile["sources"],"workbooks":{k:[{"sheet":s["sheet"],"rows":s["rows"],"year":s["year_2022_cells"],"head":[{"row":r["row"],"labels":r["labels"][:5],"first_numeric":r["first_numeric"]} for r in s["head"]]} for s in v["sheets"]] for k,v in profile["workbooks"].items()},"eurostat":{k:{"id":v["id"],"size":v["size"],"updated":v["updated"],"observed_values":v["observed_values"],"axes":{d:list(x["index"]) for d,x in v["dimensions"].items() if d!="nace_r2"}} for k,v in profile["eurostat"].items()}},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
