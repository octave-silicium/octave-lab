"""OCTAVE LAB | Lot 3: semantic profiles and vintage risk checks.

This script collects metadata and hashes, not numerical economic conclusions.
Only public source endpoints; no scraping of authenticated/private material.
Raw source files are never written into the repository. Python 3.11 stdlib.
"""
from __future__ import annotations
import csv
import datetime as dt
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / 'audits' / 'latest_lot3.json'
OLD_PATH = ROOT / 'audits' / 'latest_lot3.json'
MAX_DATA_BYTES = 24 * 1024 * 1024
XML = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
SOURCE_ENDPOINTS = {
  'insee_employment': 'https://www.insee.fr/fr/statistiques/fichier/2496914/econ-gen-empl-salarie-trim.xlsx',
  'urssaf_dpae_monthly': 'https://open.urssaf.fr/api/explore/v2.1/catalog/datasets/dpae-mensuelles-france-entiere/exports/csv?use_labels=false',
  'urssaf_dpae_na38': 'https://open.urssaf.fr/api/explore/v2.1/catalog/datasets/dpae-france-entiere-x-na38/exports/csv?use_labels=false',
  'dares_mmo_page': 'https://dares.travail-emploi.gouv.fr/donnees/les-mouvements-de-main-doeuvre',
}


def allowed(url, hosts):
    p = urllib.parse.urlparse(url)
    return p.scheme == 'https' and p.hostname in hosts and not p.username and not p.password


def download(url, hosts, max_bytes=MAX_DATA_BYTES):
    if not allowed(url, hosts):
        raise ValueError('URL_NOT_ALLOWLISTED')
    req = urllib.request.Request(url, headers={'User-Agent':'OCTAVE-LAB/0.7 (+https://github.com/octave-silicium/octave-lab)', 'Accept':'*/*'})
    with urllib.request.urlopen(req, timeout=65) as response:
        final = response.geturl()
        if not allowed(final, hosts):
            raise ValueError('REDIRECT_NOT_ALLOWLISTED')
        raw = response.read(max_bytes+1)
        if len(raw)>max_bytes:
            raise ValueError('SOURCE_TOO_LARGE')
        mime = response.headers.get('Content-Type','')
    return raw, {'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'content_type':mime,'url':final}


def col_index(reference):
    letters = re.match(r'([A-Z]+)',reference)
    if not letters: raise ValueError('INVALID_CELL_REFERENCE')
    acc=0
    for c in letters.group(1): acc=acc*26+(ord(c)-64)
    return acc


def read_shared(z):
    if 'xl/sharedStrings.xml' not in z.namelist(): return []
    root=ET.fromstring(z.read('xl/sharedStrings.xml'))
    return [''.join(node.text or '' for node in si.iter(XML+'t')) for si in root.iter(XML+'si')]


def sample_cell(c,shared):
    typ = c.attrib.get('t','n')
    if typ=='inlineStr':
        return ''.join(x.text or '' for x in c.iter(XML+'t'))
    v=c.find(XML+'v')
    if v is None or v.text is None: return None
    if typ=='s':
        idx=int(v.text)
        if idx>=len(shared):raise ValueError('BAD_SHARED_STRING_INDEX')
        return shared[idx]
    if typ in ('str','e','b'):return v.text
    try:return float(v.text)
    except ValueError:return v.text


def insee_profile(data):
    if not data.startswith(b'PK\x03\x04'):
        raise ValueError('NOT_XLSX')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if z.testzip() is not None:
            raise ValueError('BAD_ZIP_CHECKSUM')
        shared=read_shared(z)
        sheets=sorted(x for x in z.namelist() if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',x))
        if not sheets:raise ValueError('NO_SHEETS')
        result={'status':'SEMANTIC_PROFILING_ONLY','shared_string_entries':len(shared),'sheets':[],'economic_values_published':False}
        for sheet in sheets[:4]:
            root=ET.fromstring(z.read(sheet))
            rows=root.findall('.//'+XML+'sheetData/'+XML+'row')
            total_cells=0; nonempty=0; numeric=0; maximum_col=0
            header_summaries=[]; period_tokens=[]; text_tokens=[]; label_samples=[]
            for row in rows:
                number=int(row.attrib.get('r','0'))
                selected=[]
                for c in row.findall(XML+'c'):
                    total_cells+=1
                    ref=c.attrib.get('r','')
                    idx=col_index(ref)
                    maximum_col=max(maximum_col,idx)
                    val=sample_cell(c,shared)
                    if val is None:continue
                    nonempty+=1
                    if isinstance(val,float):numeric+=1
                    else:
                        s=str(val).strip()
                        if s and len(text_tokens)<500:text_tokens.append(s)
                        if re.search(r'(?:20[1-3][0-9]|19[89][0-9])',s) and len(period_tokens)<45:
                            period_tokens.append({'cell':ref,'label':s[:70]})
                        if idx<=4 and s and len(label_samples)<50:
                            label_samples.append({'row':number,'column':idx,'label':s[:110]})
                    if len(selected)<8 and number<=12 and idx<=25:
                        selected.append({'col':ref,'kind':'numeric' if isinstance(val,float) else 'label',
                                         'label':str(val)[:90] if isinstance(val,str) else None})
                if selected:header_summaries.append({'row':number,'cells':selected})
            if nonempty==0:raise ValueError('EMPTY_WORKBOOK')
            unit_clues=[x[:160] for x in text_tokens if any(t in x.lower() for t in ['millier','cvs','emplo','trimest','salari','secteur'])][:24]
            result['sheets'].append({
              'worksheet':sheet,'physical_rows':len(rows),'cells':total_cells,
              'nonempty_cells':nonempty,'numeric_cells':numeric,
              'max_column_number':maximum_col,'heading_samples':header_summaries[:12],
              'label_samples':label_samples[:35],'year_period_tokens':period_tokens[:40],
              'unit_and_definition_clues':unit_clues,
              'join_gate':'BLOCKED_PENDING_ROW_COLUMN_DICTIONARY_AND_UNIT_VALIDATION',
            })
        return result


def source_dpae_profile(raw, period_col, fields, flagged_start, flagged_end, previous=None):
    text=raw.decode('utf-8-sig')
    reader=csv.DictReader(io.StringIO(text),delimiter=';')
    names=reader.fieldnames or []
    if any(f not in names for f in fields+[period_col,'dpae_brut','dpae_cvs']):
        raise ValueError('DPAE_REQUIRED_COLUMNS_MISSING')
    periods=defaultdict(list)
    distinct={x:set() for x in fields}
    n=0; nonnumeric=0
    for row in reader:
        n+=1
        p=row[period_col]
        if period_col=='dernier_jour_du_mois':
            match=re.fullmatch(r'(\d{4})-(\d\d)-\d\d',p)
            if not match:raise ValueError('DPAE_MONTH_FORMAT')
            key=f'{match[1]}-{match[2]}'
        elif period_col=='dernier_jour_du_trimestre':
            match=re.fullmatch(r'(\d{4})-(\d\d)-\d\d',p)
            if not match:raise ValueError('DPAE_QUARTER_FORMAT')
            key=f'{match[1]}Q{(int(match[2])-1)//3+1}'
        else:raise ValueError('UNSUPPORTED_PERIOD')
        periods[key].append('|'.join(str(row.get(f,'')) for f in sorted(names)))
        for f in fields:
            if len(distinct[f])<250:distinct[f].add(row[f])
        for m in ('dpae_brut','dpae_cvs'):
            try:float(row[m].replace(',','.'))
            except (ValueError,AttributeError):nonnumeric+=1
    if n<100 or not periods:raise ValueError('DPAE_INCOMPLETE')
    # Canonical sorted period hashes prevent spurious alerts caused by row-order changes.
    hashes={p:hashlib.sha256('\n'.join(sorted(rows)).encode('utf-8')).hexdigest() for p,rows in periods.items()}
    flagged={p:{'row_count':len(rows),'sha256':hashes[p]} for p,rows in periods.items() if flagged_start<=p<=flagged_end}
    last = previous or {}
    prior=last.get('period_hashes',{})
    changed=[p for p in set(prior)&set(hashes) if prior[p]!=hashes[p]]
    return {'total_rows':n,'min_period':min(periods),'max_period':max(periods),
      'distinct_dimension_counts':{key:len(v) for key,v in distinct.items()},
      'measure_parse_warnings':nonnumeric,'period_count':len(periods),
      'historically_flagged_periods':flagged,
      'period_hashes':hashes,
      'changed_periods_against_previous_vintage':sorted(changed),
      'first_vintage_for_this_source':not bool(prior),
      'causality':'NONE','2025_anomaly_gate':'BLOCKED_UNTIL_CORRECTED_VINTAGE_AND_SCOPE_REVIEW',
      'next_requirement':'Obtain official pre/post correction vintages or an Urssaf correction notice; hashes do not establish accuracy.'}


class Anchors(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.target=None;self.text=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            self.target=dict(attrs).get('href');self.text=[]
    def handle_data(self,data):
        if self.target is not None:self.text.append(data)
    def handle_endtag(self,tag):
        if tag=='a' and self.target is not None:
            self.links.append((self.target,' '.join(self.text)))
            self.target=None;self.text=[]


def discover_mmo(page_bytes,page_url):
    # Do not solve/bypass anti-bot challenges. Only visible official links.
    html=page_bytes.decode('utf-8','replace')
    if ('vérification de sécurité' in html.lower() or 'captcha' in html.lower()):
        return {'result':'BLOCKED_OFFICIAL_SITE_ANTIBOT','reason':'Publisher challenge; no bypass attempted.'}
    parser=Anchors();parser.feed(html)
    candidates=[]
    for href,text in parser.links:
        url=urllib.parse.urljoin(page_url,href)
        if not allowed(url,{'dares.travail-emploi.gouv.fr'}):continue
        if '.xlsx' not in urllib.parse.urlsplit(url).path.lower():continue
        desc=(text+' '+url).lower()
        if any(w in desc for w in ['main-doeuvre','main-d','mmo','mouvements']):
            candidates.append({'url':url,'anchor_text':text.strip()[:180]})
    if not candidates:return {'result':'PENDING_EXACT_OFFICIAL_XLSX_LINK','reason':'No explicit XLSX linked on inspected official page; no guessed URL.'}
    return {'result':'OFFICIAL_XLSX_CANDIDATES_NOT_DOWNLOADED','candidates':candidates[:10],
        'reason':'Exact URL found in official page, but binary, license and workbook metadata still need validation.'}


def execute():
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    old={}
    if OLD_PATH.exists():
        try: old=json.loads(OLD_PATH.read_text('utf-8'))
        except (ValueError,OSError): pass
    sources={}
    # Isolate failures: one unavailable endpoint must not fabricate another dataset.
    for key,url in SOURCE_ENDPOINTS.items():
        hosts={'dares.travail-emploi.gouv.fr'} if key=='dares_mmo_page' else {'www.insee.fr'} if key=='insee_employment' else {'open.urssaf.fr'}
        try:
            data,evidence=download(url,hosts,max_bytes=8*1024*1024 if key=='dares_mmo_page' else MAX_DATA_BYTES)
            if key=='insee_employment':
                detail=insee_profile(data)
                result='XLSX_SEMANTIC_METADATA_PARSED'
            elif key=='dares_mmo_page':
                detail=discover_mmo(data,url)
                result=detail['result']
            else:
                col='dernier_jour_du_mois' if 'monthly' in key else 'dernier_jour_du_trimestre'
                dims=['nature_de_contrat','duree_de_contrat'] if 'monthly' in key else ['secteur_na38','nature_de_contrat','duree_de_contrat']
                start,end=('2025-04','2025-09') if 'monthly' in key else ('2025Q2','2025Q3')
                detail=source_dpae_profile(data,col,dims,start,end,old.get('sources',{}).get(key,{}).get('detail'))
                result='DPAE_PERIODS_AND_PROVENANCE_VALIDATED_NOT_ECONOMICALLY_CLEARED'
            sources[key]={'result':result,'evidence':evidence,'detail':detail,'ready_for_economic_join':False}
        except (OSError,ValueError,zipfile.BadZipFile,ET.ParseError,UnicodeError) as error:
            sources[key]={'result':'BLOCKED','error':f'{type(error).__name__}:{error}'[:350],'ready_for_economic_join':False}
    result={'observed_at_utc':now,'analysis_level':'DESCRIPTIVE_SOURCE_QUALIFICATION_ONLY','no_raw_data_published':True,
            'source_count':len(sources),'sources':sources,
            'publication_gate':'BLOCKED_ECONOMIC_JOIN_AND_CAUSALITY',
            'note':'DPAE 2025 hashes track revisions, not whether Urssaf has repaired source classification errors. Insee table headings do not establish units or interpretation.'}
    REPORT_PATH.parent.mkdir(parents=True,exist_ok=True)
    REPORT_PATH.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n','utf-8')
    print(json.dumps({k:v['result'] for k,v in sources.items()}))
    if all(v['result']=='BLOCKED' for v in sources.values()):
        raise SystemExit('No source qualified; output is blocked and does not contain synthetic data.')

if __name__=='__main__':execute()
