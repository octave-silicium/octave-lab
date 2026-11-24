"""ROME export inspection: validate archive and inventory native tables, no public data."""
import csv,io,json,zipfile,hashlib
from pathlib import PurePosixPath
from collections import Counter
from .european_work import fetch
URL="https://api.francetravail.fr/api-nomenclatureemploi/v1/open-data/csv"
def inspect(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos=[i for i in z.infolist() if not i.is_dir()]
        if len(infos)>300 or sum(i.file_size for i in infos)>250_000_000 or len({i.filename for i in infos})!=len(infos):raise ValueError("ZIP_LIMIT")
        if z.testzip() is not None:raise ValueError("ZIP_CRC")
        report={}
        for i in infos:
            p=PurePosixPath(i.filename)
            if p.is_absolute() or ".." in p.parts or "\\" in i.filename:raise ValueError("ZIP_PATH")
            b=z.read(i);item={"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()}
            if p.suffix.lower()==".csv":
                for enc in ("utf-8-sig","cp1252"):
                    try:s=b.decode(enc);break
                    except UnicodeDecodeError:continue
                else:raise ValueError("ENCODING")
                sep=csv.Sniffer().sniff(s[:65536],delimiters=";,|\t").delimiter
                reader=csv.reader(io.StringIO(s,newline=""),delimiter=sep)
                header=next(reader)
                if not header or len(header)!=len(set(header)):raise ValueError("HEADER")
                n=0;shape=Counter()
                for row in reader:
                    if not row:continue
                    n+=1;shape[len(row)]+=1
                item.update({"encoding":enc,"separator":sep,"columns":header,"rows":n,"row_widths":dict(shape)})
            report[i.filename]=item
        return {"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"members":report,"status":"INVENTORY_ONLY"}
if __name__=="__main__":
    raw,_,_=fetch(URL)
    print(json.dumps(inspect(raw),ensure_ascii=False,indent=2))
