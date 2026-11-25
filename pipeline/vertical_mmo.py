"""Pinned original Dares workbooks, internal research only."""
import hashlib,json,re,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction as F
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
SCOPE='France métropolitaine, privé hors agriculture, intérim et particuliers employeurs; tous établissements; JZ NAF rév.2'
PINS={'quarterly':'bece71e53408056ce1c1b7f1d95f39ae491dc945c82caa760abe49eead0dfb92','annual':'5fc7008ad02322a5bd708f9cfc8f06ed24fce81a36c8ae6a6c59356024f4c3cf'}
COMMON={'D':'Embauches','E':'Embauches en CDI','F':'Embauches en CDD','G':'Fins de contrat','H':'Démissions'}
EXTRA={'quarterly':{'I':'Ruptures conventionnelles','J':"Fins de période d'essai",'K':'Départs en retraite','L':'Fins de CDD','M':'CDD arrivés à terme','N':"CDD de moins d'un mois arrivés à terme",'O':"CDD de plus d'un mois arrivés à terme",'P':'Ruptures anticipées de CDD','Q':'Fins de CDI','R':'Démissions de CDI'},'annual':{'I':'Licenciements économiques','J':'Licenciements non économiques','K':'Ruptures conventionnelles...11','L':"Fins de période d'essai",'M':'Départs en retraite','O':'Fins de CDD','P':'CDD arrivés à terme','Q':"CDD de moins d'un mois arrivés à terme",'R':"CDD de plus d'un mois arrivés à terme",'S':'Ruptures anticipées de CDD','T':'Fins de CDI','U':'Démissions de CDI','V':'Licenciements économiques de CDI','W':'Licenciements non économiques de CDI'}}
KEYS={'D':'hires','E':'cdi_hires','F':'cdd_hires','G':'ends','H':'resignations'}
def require(ok,msg):
    if not ok:raise ValueError(msg)
def hash_bytes(b):return hashlib.sha256(b).hexdigest()
def digest(x):return hash_bytes(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())
def records(path,kind):
    path=Path(path);raw=path.read_bytes();require(hash_bytes(raw)==PINS[kind],'UNREVIEWED_WORKBOOK')
    with zipfile.ZipFile(path) as z:
        require(z.testzip() is None,'BAD_ZIP')
        sheet='MMO_trimestriels_A17' if kind=='quarterly' else 'MMO_annuels'
        w=ET.fromstring(z.read('xl/workbook.xml'));sh=[x for x in w.findall('.//m:sheet',NS) if x.get('name')==sheet];require(len(sh)==1,'SHEET')
        rid=sh[0].get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        rel=[x for x in ET.fromstring(z.read('xl/_rels/workbook.xml.rels')) if x.get('Id')==rid];require(len(rel)==1,'REL')
        target=rel[0].get('Target');require(re.fullmatch(r'worksheets/sheet\d+\.xml',target) is not None,'TARGET')
        ss=[''.join(t.text or '' for t in x.findall('.//m:t',NS)) for x in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        rows=[]
        for row in ET.fromstring(z.read('xl/'+target)).findall('.//m:row',NS):
            d={}
            for c in row.findall('m:c',NS):
                v=c.findtext('m:v',None,NS)
                if v is None:continue
                col=re.match(r'^[A-Z]+',c.get('r')).group();require(col not in d,'DUPLICATE_CELL')
                d[col]=ss[int(v)] if c.get('t')=='s' else v
            rows.append((int(row.get('r')),d))
    headers={**COMMON,**EXTRA[kind]};h=rows[0][1];require(all(h.get(k)==v for k,v in headers.items()),'HEADER')
    out={}
    for n,d in rows[1:]:
        if d.get('B')!='Ensemble des établissements' or d.get('C')!='JZ - Information et communication':continue
        p=d['A'];require(p not in out,'DUPLICATE_PERIOD')
        vals={KEYS.get(k,k):int(d[k]) if k in d else None for k in headers}
        if int(p[:4])>=2019:
            require(all(v is not None and v>=0 for v in vals.values()),'MISSING_OR_NEGATIVE')
            require(abs(vals['hires']-vals['cdi_hires']-vals['cdd_hires'])<=1,'HIRING_ROUNDING')
        out[p]={'row':n,'values':vals,'contract_balance':vals['hires']-vals['ends'] if vals['hires'] is not None and vals['ends'] is not None else None}
    expected=tuple(f'{y}-T{q}' for y in range(2017,2027) for q in range(1,5) if y<2026 or q<=2) if kind=='quarterly' else tuple(map(str,range(2007,2026)))
    require(set(out)==set(expected),'PERIOD_COVERAGE')
    return {'sheet':sheet,'sha256':PINS[kind],'headers':{KEYS.get(k,k):v for k,v in headers.items()},'periods':out}
def compare(a,b):
    x,y=a['values'],b['values'];return {k:{'delta':y[k]-v,'pct':str(F(100*(y[k]-v),v)) if v else None} for k,v in x.items() if v is not None and y.get(k) is not None}
def build(q,a):
    r={k:records(p,k) for k,p in [('quarterly',q),('annual',a)]}
    for k,s in r.items():
        periods=s['periods'];s['comparisons']=[{'from':p,'to':t,'changes':compare(periods[p],periods[t])} for t in sorted(periods) if int(t[:4])>=2020 and (p:=str(int(t[:4])-1)+t[4:]) in periods]
    payload={'study':'VERTICAL-001','phase':'V2b3-MMO','scope':SCOPE,'sources':r,'publication':'BLOCK_PUBLICATION','causal_identification':'NOT_IDENTIFIED','limits':['Contract counts not unique people; balance not net employment change.','Quarterly A17 layoffs not separately available; annual series not spliced or summed with quarterly.','Dares DSN lineage shared partly with other administrative statistics; not independent evidence of causality.','Same corrected workbook only, revisions possible; source rights pending.']}
    return {'result':payload,'sha256':digest(payload)}
