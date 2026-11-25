"""Pinned Insee 2022 A38 empirical audit; diagnostic only, no publication gate."""
import hashlib, io, json, sys, zipfile
from pathlib import Path
import numpy as np
import openpyxl

SHA="db4189aa708c10122dadf09c17f8bb49e1dd45561f93bf5527abe8473a29aa73"
SOURCE="https://www.insee.fr/fr/statistiques/8988861"
CODES="AZ BZ CA CB CC CD CE CF CG CH CI CJ CK CL CM DZ EZ FZ GZ HZ IZ JA JB JC KZ LZ MA MB MC NZ OZ PZ QA QB RZ SZ TZ".split()

def require(ok, reason):
    if not ok: raise ValueError(reason)

def audit(path):
    raw=Path(path).read_bytes()
    if Path(path).suffix==".zip":
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            raw=z.read("TES_symetrique_A38_2022DEF_fr.xlsx")
    require(hashlib.sha256(raw).hexdigest()==SHA,"SOURCE_HASH")
    w=openpyxl.load_workbook(io.BytesIO(raw),data_only=True)
    require(w.sheetnames==["Présentation du TES symétrique","TES de production domestique","TES des importations"],"SHEETS")
    p,d,m=w.worksheets
    require(p["C4"].value=="Année 2022" and p["C5"].value=="Version définitive","VINTAGE")
    rows=range(11,48); n=len(CODES)
    for sheet,col in [(d,3),(d,44),(d,85),(m,3),(m,9),(m,50)]:
        require([sheet.cell(i,col).value for i in rows]==CODES,"ROW_CODES")
    for sheet,start in [(d,4),(d,45),(m,10)]:
        require([sheet.cell(9,j).value for j in range(start,start+n)]==CODES,"COLUMN_CODES")
    def mat(s,r,c):
        vals=[[s.cell(i,j).value for j in c] for i in r]
        require(all(type(x) in (int,float) and np.isfinite(x) for row in vals for x in row),"MISSING_OR_NONNUMERIC")
        return np.array(vals,dtype=float)
    def vec(s,c): return mat(s,rows,[c]).ravel()
    V=mat(d,rows,range(4,41)); U=mat(d,rows,range(45,82)); M=mat(m,rows,range(10,47))
    q=V.sum(1); g=V.sum(0); y=vec(d,95); ym=vec(m,60); imp=vec(m,6)
    require(all(np.all(a>=0) for a in (V,U,M,y,ym,imp)) and np.all(q>0) and np.all(g>0),"SIGN_OR_ZERO")
    checks={}
    def equal(name,a,b):
        a,b=np.asarray(a),np.asarray(b)
        # Conservative bound for 37-term binary64 sums and independent subtotal storage.
        bound=128*np.finfo(float).eps*np.maximum(1,np.abs(a)+np.abs(b))
        err=np.abs(a-b)
        require(np.all(err<=bound),name)
        checks[name]={"max_abs_error":float(err.max()),"max_allowed":float(bound.max())}
    equal("production_rows",q,vec(d,41))
    equal("production_columns",g,mat(d,[48],range(4,41)).ravel())
    equal("domestic_uses",q,U.sum(1)+y)
    equal("domestic_intermediate_rows",U.sum(1),vec(d,82))
    equal("domestic_intermediate_columns",U.sum(0),mat(d,[48],range(45,82)).ravel())
    equal("import_uses",imp,M.sum(1)+ym)
    equal("import_intermediate_rows",M.sum(1),vec(m,47))
    equal("import_intermediate_columns",M.sum(0),mat(m,[48],range(10,47)).ravel())
    equal("import_origin",imp,vec(m,4)+vec(m,5))
    for name,a,b in [("total_output",q.sum(),d["AO48"].value),("total_domestic_intermediate",U.sum(),d["CD48"].value),("total_import_intermediate",M.sum(),d["CD50"].value),("total_import",imp.sum(),m["F48"].value),("total_domestic_final",y.sum(),d["CQ48"].value),("total_import_final",ym.sum(),m["BH48"].value)]:
        equal(name,a,b)
    require(all(d.cell(51,j).value is None for j in range(45,82)),"TAX_LAYOUT_CHANGED")
    remainder=g-U.sum(0)-M.sum(0)
    tax_total=float(d["CD51"].value)
    require(np.all(remainder>=0),"REMAINDER_SIGN")
    D=V.T/q; B=U/g; A=B@D
    require(np.max(A.sum(0))<1,"PRODUCTIVITY_BOUND")
    equal("market_share",D.sum(0),np.ones(n))
    I=np.eye(n)
    replay=np.linalg.solve(I-A,y)
    require(np.max(abs(replay-q))<1e-7,"BASELINE_REPLAY")
    A2=np.linalg.solve(V.T,U.T).T
    cases={}
    for code in ("JC","MA","NZ"):
        dy=np.zeros(n); dy[CODES.index(code)]=100
        dq=np.linalg.solve(I-A,dy); dg=D@dq
        mi=(M/g)@dg; residual=(remainder/g)@dg
        require(np.max(abs((I-A)@dq-dy))<1e-10 and abs(100-mi.sum()-residual)<1e-10,"SHOCK_BALANCE")
        require(np.all(dq>=0),"NEGATIVE_REQUIREMENT")
        alt=np.linalg.solve(I-A2,dy)
        # Independent Neumann series calculation, no inverse reused.
        term=dy.copy(); series=term.copy()
        for _ in range(128):
            term=A@term; series+=term
        require(np.max(abs(series-dq))<1e-10,"INDEPENDENT_SERIES")
        cases[code]={"gross_output_requirement":float(dq.sum()),"indirect_requirement":float(dq.sum()-100),"imported_intermediate_requirement":float(mi.sum()),"combined_gva_and_intermediate_product_taxes":float(residual),"alternative_product_technology_output":float(alt.sum()),"top_products":[[CODES[i],float(dq[i])] for i in np.argsort(-dq)[:6]],"gdp":None,"employment":None,"realized_output":None}
    return {"source":SOURCE,"sha256":SHA,"year":2022,"base":2020,"unit":"EUR million current basic prices","codes":CODES,"cell_ranges":{"V":"domestic!D11:AN47","U":"domestic!AS11:CC47","M":"imports!J11:AT47","y":"domestic!CQ11:CQ47","ym":"imports!BH11:BH47"},"checks":checks,"totals":{"gross_output":float(q.sum()),"domestic_intermediate":float(U.sum()),"imported_intermediate":float(M.sum()),"domestic_final":float(y.sum()),"imports":float(imp.sum()),"import_final":float(ym.sum()),"intermediate_product_taxes_aggregate":tax_total,"gva_implied_aggregate":float(remainder.sum()-tax_total),"off_diagonal_production":float(V.sum()-np.trace(V))},"model":{"assumption":"industry technology fixed market shares, conditional diagnostic","spectral_radius":float(max(abs(np.linalg.eigvals(A)))),"max_column_sum":float(max(A.sum(0))),"baseline_max_error":float(max(abs(replay-q))),"alternative_negative_coefficients":int(np.sum(A2<0)),"alternative_min_coefficient":float(A2.min()),"alternative_condition_number":float(np.linalg.cond(V))},"cases":cases,"status":"EMPIRICAL_DIAGNOSTIC_NOT_ENGINE_ADMISSION","publication":"BLOCK_PUBLICATION"}

if __name__=="__main__":
    print(json.dumps(audit(sys.argv[1]),indent=2,ensure_ascii=False))
