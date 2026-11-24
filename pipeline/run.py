"""OCTAVE LAB | Verified economic-data ingestion & occupational trend output.
Not a causal model. No synthetic datapoints are published by this pipeline.
Stdlib only, Python 3.11+. Live execution requires external network access.
"""
from __future__ import annotations
import argparse, calendar, csv, datetime as dt, hashlib, io, json, pathlib, urllib.request, zipfile
from collections import defaultdict
from statistics import median
from urllib.error import HTTPError, URLError

ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCES=json.loads((ROOT/'pipeline'/'sources.json').read_text(encoding='utf-8'))['sources']
MAX_BYTES=25*1024*1024
UA='OctaveLab-Research/0.2 (+https://github.com/hiring-lab/job_postings_tracker; attribution in reports)'


def validate_csv(data:bytes, source_id:str):
    head=data[:300].lstrip().lower()
    if head.startswith(b'<html') or head.startswith(b'<!doctype'):
        raise ValueError('HTML content received, CSV expected')
    text=io.StringIO(data.decode('utf-8-sig'))
    reader=csv.DictReader(text)
    fields=reader.fieldnames or []
    if not fields: raise ValueError('No CSV header')
    records=list(reader)
    if len(records)<10: raise ValueError(f'Only {len(records)} records')
    if source_id=='indeed_fr_sector':
        req={'date','jobcountry','display_name','variable','indeed_job_postings_index'}
        if not req.issubset(fields): raise ValueError(f'Missing fields: {req-set(fields)}')
        sectors={r['display_name'] for r in records if r['display_name']}
        dates={r['date'] for r in records if r['date']}
        if len(sectors)<5 or len(dates)<365: raise ValueError('Coverage too narrow for sector research')
        if not all(r['jobcountry']=='FR' for r in records): raise ValueError('Non-FR records')
    if source_id=='indeed_fr_national':
        req={'date','jobcountry','indeed_job_postings_index_SA','variable'}
        if not req.issubset(fields): raise ValueError(f'Missing fields: {req-set(fields)}')
    return {'rows':len(records),'columns':fields}


def fetch(source:dict, raw_dir:pathlib.Path):
    req=urllib.request.Request(source['url'],headers={'User-Agent':UA,'Accept':'*/*'})
    with urllib.request.urlopen(req, timeout=45) as r:
        content_type=r.headers.get('Content-Type','')
        data=r.read(MAX_BYTES+1)
        if len(data)>MAX_BYTES: raise ValueError('Source exceeds 25MB limit')
        etag=r.headers.get('ETag')
        last_modified=r.headers.get('Last-Modified')
    if source['format']=='xlsx':
        if not data.startswith(b'PK\x03\x04') or not zipfile.is_zipfile(io.BytesIO(data)):
            raise ValueError('Invalid xlsx magic or ZIP structure')
        meta={'bytes':len(data),'format':'xlsx','rows':'not parsed','columns':'not parsed'}
    else:
        meta=validate_csv(data,source['id'])
        meta.update({'bytes':len(data),'format':'csv'})
    digest=hashlib.sha256(data).hexdigest()
    ext=source['format']
    path=raw_dir/f"{source['id']}_{digest[:12]}.{ext}"
    path.write_bytes(data)
    return {**meta,'sha256':digest,'filename':str(path.relative_to(ROOT)),'url':source['url'],'etag':etag,'last_modified':last_modified,'license':source['license'],'public_redistribution':source['public_redistribution'],'downloaded_at':dt.datetime.now(dt.timezone.utc).isoformat()}


def quarter(date:dt.date): return f'{date.year}Q{(date.month-1)//3+1}'


def is_complete_quarter(observations: list[tuple[dt.date, float]], q: str) -> bool:
    """Require temporal coverage of the whole calendar quarter, not 60/90 days."""
    year, number = int(q[:4]), int(q[-1]); month = (number-1)*3+1
    start = dt.date(year,month,1)
    end_month = month+2
    end = dt.date(year,end_month,calendar.monthrange(year,end_month)[1])
    actual = {d for d,_ in observations}
    return (len(actual)>=85 and min(actual)<=start+dt.timedelta(days=4)
            and max(actual)>=end-dt.timedelta(days=4))



def analyze_sector(data:bytes, output_dir:pathlib.Path):
    rows=list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
    by=defaultdict(list)
    seen=set(); bad=[]
    for r in rows:
        if r['jobcountry']!='FR':continue
        # Main index: total postings. 'New postings' is a different statistical product.
        if r.get('variable')!='total postings':continue
        try:
            d=dt.date.fromisoformat(r['date']); val=float(r['indeed_job_postings_index'])
        except (ValueError,TypeError,KeyError): bad.append(r);continue
        key=(d,r['display_name'],'total postings')
        if key in seen: raise ValueError(f'Duplicate sector observation: {key}')
        seen.add(key)
        if not (0<val<10000): raise ValueError('Invalid index level')
        by[(r['display_name'], quarter(d))].append((d,val))
    if bad:raise ValueError(f'{len(bad)} invalid rows')
    if not by: raise ValueError('No valid total-postings observations for France')
    qdata=[]
    for (sector,q), vals in sorted(by.items()):
        if not is_complete_quarter(vals,q):continue
        qdata.append({'sector':sector,'quarter':q,'index_median':round(median(v for _,v in vals),3),'observation_days':len(vals), 'first_day':str(min(d for d,_ in vals)),'last_day':str(max(d for d,_ in vals))})
    qlookup={(x['sector'],x['quarter']):x for x in qdata}
    compared=[]
    for x in qdata:
        y=int(x['quarter'][:4]); q=x['quarter'][4:]
        older=qlookup.get((x['sector'],f'{y-1}{q}'))
        if not older:continue
        compared.append({**x,'yoy_change_pct':round(100*(x['index_median']/older['index_median']-1),2),'previous_year_index_median':older['index_median']})
    if not qdata: raise ValueError('No complete quarters found; suppressing sector publication')
    # Ensure the user never confuses the sector index with a count of jobs.
    for name,data_rows in [('indeed_sector_quarterly_observed.csv',qdata),('indeed_sector_yoy_comparison.csv',compared)]:
        if not data_rows: continue
        with (output_dir/name).open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=list(data_rows[0]));writer.writeheader();writer.writerows(data_rows)
    return {'valid_sector_rows':len(seen),'sectors':len({k[0] for k in by}),'quarterly_records':len(qdata),'yoy_comparisons':len(compared),'earliest':str(min(d for vals in by.values() for d,_ in vals)),'latest':str(max(d for vals in by.values() for d,_ in vals)), 'note':'Quarterly medians of a seasonally adjusted seven-day moving-average index; not independent observations or employment counts'}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--only-open',action='store_true',help='Only sources whose redistribution is confirmed open')
    ap.add_argument('--snapshot-dir',default=None,help='Relative path or existing directory for snapshots')
    args=ap.parse_args()
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    raw_dir=ROOT/(args.snapshot_dir or f'archive/raw/{stamp}')
    raw_dir.mkdir(parents=True,exist_ok=True)
    output_dir=ROOT/'outputs'/'live';output_dir.mkdir(parents=True,exist_ok=True)
    # Never leave obsolete derived outputs in place when a new run fails.
    for old in output_dir.glob('indeed_sector_*.csv'):
        old.unlink()
    status={'run_at':dt.datetime.now(dt.timezone.utc).isoformat(),'status':{},'source_registry_version':'pipeline/sources.json','no_causal_inference':True,'license_gate':True}
    for source in SOURCES:
        if args.only_open and not source['public_redistribution']:
            status['status'][source['id']]={'result':'SKIPPED_LICENSE_REVIEW','reason':source['license']}
            continue
        try:
            result=fetch(source,raw_dir)
            if source['id']=='indeed_fr_sector':
                data=(ROOT/result['filename']).read_bytes()
                result['analysis']=analyze_sector(data,output_dir)
            status['status'][source['id']]={'result':'OK',**result}
        except Exception as e:
            status['status'][source['id']]={'result':'BLOCKED','error':f'{type(e).__name__}: {e}'}
    failed_required=[src['id'] for src in SOURCES if src.get('required') and status['status'].get(src['id'],{}).get('result')!='OK']
    if failed_required:
        status['publish_gate']='BLOCKED: required original datasets not validated: '+', '.join(failed_required)
    else:
        status['publish_gate']='PASS_DESCRIPTIVE_ONLY: original histories archived and validated'
    (output_dir/'manifest.json').write_text(json.dumps(status,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(status,indent=2,ensure_ascii=False))
    if status['publish_gate'].startswith('BLOCKED'): raise SystemExit(2)

if __name__=='__main__':main()
