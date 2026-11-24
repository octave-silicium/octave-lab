"""OCTAVE LAB | Insee employment by sector.

Strictly reconstruct the official Insee XLSX matrix to a versioned long-form CSV.
No claim about an AI impact, a NAF occupation crosswalk or causal employment change.
Python standard library only. Revisions and failed validation block publication.
"""
from __future__ import annotations
import csv
import datetime as dt
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

from semantic_audit import download, read_shared, sample_cell, col_index, XML, SOURCE_ENDPOINTS

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / 'data' / 'curated'
REPORT = OUTPUT_DIR / 'insee_employment_manifest.json'
CSV_FILE = OUTPUT_DIR / 'insee_employment_sector_quarterly.csv'
INSEE_URL = SOURCE_ENDPOINTS['insee_employment']
INSEE_LICENCE = 'Licence Ouverte / Open Licence 2.0 (Etalab)'
LICENCE_URL = 'https://www.insee.fr/fr/information/2008466?page=copyright.htm'
DATASET_URL = 'https://www.insee.fr/fr/statistiques/2496914'
METRICS = ['Évolution sur trois mois','Évolution sur un an','Emploi salarié']
MAIN_SECTORS = ['Agriculture','Industrie','Construction','Tertiaire marchand','Tertiaire non marchand']


def read_matrix(data:bytes):
    if not data.startswith(b'PK\x03\x04'):
        raise ValueError('INSEE_BAD_MAGIC')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if archive.testzip():raise ValueError('INSEE_ZIP_CRC_FAILED')
        strings=read_shared(archive)
        root=ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
        matrix={}
        for row in root.findall('.//'+XML+'sheetData/'+XML+'row'):
            cells={}
            for c in row.findall(XML+'c'):
                value=sample_cell(c,strings)
                if value is not None:cells[col_index(c.attrib['r'])]=value
            if cells:matrix[int(row.attrib['r'])]=cells
        if not matrix:raise ValueError('EMPTY_INSEE_MATRIX')
    return matrix


def _quarter_step(q):
    m=re.fullmatch(r'(\d{4})-T([1-4])',q)
    if not m: raise ValueError(f'BAD_QUARTER_{q}')
    return int(m[1])*4 + int(m[2])-1


def extract(raw:bytes, *, strict_anchor=True):
    mat=read_matrix(raw)
    if 'en milliers' not in str(mat.get(3,{}).get(1,'')).casefold():
        raise ValueError('INSEE_UNIT_NOT_CONFIRMED_IN_WORKBOOK')
    if not str(mat.get(17,{}).get(1,'')).startswith('Note : données révisées'):
        raise ValueError('INSEE_SCOPE_AND_REVISION_NOTE_NOT_CONFIRMED')
    if 'France hors Mayotte' not in str(mat.get(19,{}).get(1,'')):
        raise ValueError('INSEE_GEOGRAPHIC_SCOPE_NOT_CONFIRMED')
    periods=[]
    for col,value in mat.get(4,{}).items():
        if isinstance(value,str) and re.fullmatch(r'\d{4}-T[1-4]',value):periods.append((col,value))
    periods.sort()
    if len(periods)<40 or periods[0][1]!='2014-T1':
        raise ValueError('INSEE_QUARTER_SERIES_TOO_SHORT_OR_CHANGED')
    for k,(col,quarter) in enumerate(periods):
        if _quarter_step(quarter)!=_quarter_step(periods[0][1])+k:
            raise ValueError('INSEE_QUARTER_GAP_OR_DUPLICATE')
        if [mat.get(5,{}).get(col+i) for i in range(3)]!=METRICS:
            raise ValueError(f'INSEE_MEASURE_HEADERS_CHANGED_{quarter}')
    cats=[]
    for row in range(6,16):
        value=mat.get(row,{}).get(1)
        if not isinstance(value,str) or not value.strip():
            raise ValueError(f'INSEE_CATEGORY_MISSING_{row}')
        cats.append((row,value.strip()))
    if len(set(v for _,v in cats))!=10 or not all(s in [n for _,n in cats] for s in MAIN_SECTORS+['Ensemble','Secteur privé','Fonction publique']):
        raise ValueError('INSEE_CATEGORIES_UNRECOGNISED')
    # The two 'dont' rows are included in a larger sector; never add twice.
    out=[];lookup={};errors=[]
    for c,quarter in periods:
        for row,category in cats:
            vals=[]
            for i in range(3):
                v=mat.get(row,{}).get(c+i)
                if not isinstance(v,(int,float)) or not math.isfinite(v):
                    raise ValueError(f'INSEE_MISSING_NONNUMERIC_{category}_{quarter}_{i}')
                vals.append(float(v))
            record={'quarter':quarter,'sector_label':category,
                'change_qoq_thousands':vals[0], 'change_yoy_thousands':vals[1],
                'employees_thousands':vals[2],
                'category_kind':('SUBCATEGORY' if category.lstrip().startswith('dont ') else 'BROAD_SECTOR' if category in MAIN_SECTORS else 'AGGREGATE'),
                'geography':'France hors Mayotte','unit':'thousands of employees',
                'seasonal_adjustment':'CVS','source':'Insee','underlying_source_sha256':hashlib.sha256(raw).hexdigest()}
            out.append(record)
            lookup[(category,quarter)]=record
    # Internal arithmetic and the five broad sectors must be coherent.
    for idx,(_,quarter) in enumerate(periods):
        total=lookup[('Ensemble',quarter)]['employees_thousands']
        sector_sum=sum(lookup[(s,quarter)]['employees_thousands'] for s in MAIN_SECTORS)
        priv_public=lookup[('Secteur privé',quarter)]['employees_thousands']+lookup[('Fonction publique',quarter)]['employees_thousands']
        if abs(total-sector_sum)>0.6:
            errors.append({'type':'BROAD_SECTOR_TOTAL_MISMATCH','quarter':quarter,'discrepancy_thousands':round(total-sector_sum,3)})
        if abs(total-priv_public)>0.4:
            errors.append({'type':'PRIVATE_PUBLIC_TOTAL_MISMATCH','quarter':quarter,'discrepancy_thousands':round(total-priv_public,3)})
        for _,category in cats:
            this=lookup[(category,quarter)]
            if idx>=1:
                prev=lookup[(category,periods[idx-1][1])]
                diff=round((this['employees_thousands']-prev['employees_thousands'])-this['change_qoq_thousands'],4)
                if abs(diff)>0.21:errors.append({'type':'QUARTER_DELTA_MISMATCH','quarter':quarter,'sector':category,'difference_thousands':diff})
            if idx>=4:
                prev=lookup[(category,periods[idx-4][1])]
                diff=round((this['employees_thousands']-prev['employees_thousands'])-this['change_yoy_thousands'],4)
                if abs(diff)>0.21:errors.append({'type':'YEAR_DELTA_MISMATCH','quarter':quarter,'sector':category,'difference_thousands':diff})
    # Frozen primary-source known anchor from publication dated 28 August 2026.
    baseline=lookup.get(('Ensemble','2026-T2'),{}).get('employees_thousands')
    historical_anchor_ok=baseline is not None and abs(baseline-27021.1)<=0.15
    gates={
      'quarter_count':len(periods),'sector_count':len(cats),'data_rows':len(out),
      'first_quarter':periods[0][1],'last_quarter':periods[-1][1],
      'reported_arithmetic_anomalies':len(errors),'anomalies_sample':errors[:20],
      'primary_source_2026_T2_total_anchor_27021_1_thousands':{'observed':baseline,'matches_original_release':historical_anchor_ok},
      'raw_sha256':hashlib.sha256(raw).hexdigest(),
      'publisher':'Insee', 'geography':'France hors Mayotte', 'unit':'thousands of employees',
      'denominator':'employees aged 15+ at end of quarter','temporal_adjustment':'seasonally adjusted (CVS)',
      'data_are_stock_not_hiring_flows':True,
      'method_vintage':'2026-08-28 first reference edition; future revisions require review',
      'economic_join_with_NA38':False, 'independent_of_urssaf':False,
      'license':INSEE_LICENCE,'license_url':LICENCE_URL,'dataset_url':DATASET_URL
    }
    if errors:
        gates['publication_gate']='BLOCKED_ARITHMETIC_INCONSISTENCY'
    elif strict_anchor and not historical_anchor_ok:
        gates['publication_gate']='BLOCKED_HISTORIC_VINTAGE_REVIEW'
    else:
        gates['publication_gate']='PASS_INSEE_DESCRIPTIVE_ONLY'
    return out,gates


def publish():
    observed=dt.datetime.now(dt.timezone.utc).isoformat()
    raw,evidence=download(INSEE_URL,{'www.insee.fr'})
    entries,stats=extract(raw)
    stats.update({'observed_at_utc':observed,'download_evidence':evidence})
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n','utf-8')
    if stats['publication_gate']!='PASS_INSEE_DESCRIPTIVE_ONLY':
        print('Insee data publication blocked:',stats['publication_gate']);return False
    fields=list(entries[0])
    with CSV_FILE.open('w',newline='',encoding='utf-8') as fh:
        writer=csv.DictWriter(fh,fieldnames=fields);writer.writeheader();writer.writerows(entries)
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m')
    path=ROOT/'snapshots'/'insee-sector'/stamp
    path.mkdir(parents=True,exist_ok=True)
    source_name=f'insee_sector_{evidence["sha256"][:12]}.xlsx'
    if not (path/source_name).exists():
        (path/source_name).write_bytes(raw)
    (path/'ATTRIBUTION.txt').write_text(
        'Source : Insee, Emploi salarié par secteur, '+DATASET_URL+'\n'
        'Licence Ouverte / Open License 2.0 (Etalab): '+LICENCE_URL+'\n'
        'Transformation: OCTAVE LAB, data/curated/insee_employment_sector_quarterly.csv\n'
        'Publication initiale de référence : 28/08/2026. Les valeurs sont en milliers et CVS, France hors Mayotte.\n','utf-8')
    (path/'manifest.json').write_text(json.dumps({'source_name':source_name,'original_sha256':evidence['sha256'],
        'downloaded_at_utc':observed,'license':INSEE_LICENCE,'source':DATASET_URL,'publication_gate':stats['publication_gate'],
        'quarters':stats['quarter_count'],'sector_categories':stats['sector_count'],'derived_observations':stats['data_rows']},indent=2,ensure_ascii=False)+'\n','utf-8')
    print('Insee validated and archived:',stats['data_rows'],'observations',evidence['sha256'][:12]);return True

if __name__=='__main__':
    if not publish():sys.exit('Insee pipeline: manual review required; validated dataset not replaced.')
