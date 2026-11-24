"""OCTAVE LAB — external-source access and schema audit (NOT an economic analysis).
No source-derived values are interpreted across populations; no raw data is published.
Stdlib Python 3.11+. All source responses are discarded after validation.
"""
import csv
import datetime as dt
import hashlib
import io
import json
import pathlib
import time
import urllib.request
import urllib.error
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'pipeline' / 'audit_multisource_sources.json'
OUT = ROOT / 'audits' / 'latest_multisource.json'
MAX_BYTES = 24 * 1024 * 1024
UA = 'OCTAVE-LAB/0.4 public statistical dataset metadata audit; https://github.com/octave-silicium/octave-lab'


def read_limited(url, opener=urllib.request.urlopen, limit=MAX_BYTES):
    """Read bounded response; reject HTML and non-200 HTTP status."""
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/csv,application/json,*/*'})
    with opener(req, timeout=55) as resp:
        status = getattr(resp, 'status', 200)
        if status != 200:
            raise ValueError(f'HTTP {status}')
        content = resp.read(limit + 1)
        if len(content) > limit:
            raise ValueError(f'BODY_TOO_LARGE_{limit}')
        headers = {'content_type': resp.headers.get('Content-Type', ''),
                   'etag': resp.headers.get('ETag'),
                   'last_modified': resp.headers.get('Last-Modified')}
    if content[:512].lstrip().lower().startswith((b'<html', b'<!doctype', b'<head')):
        raise ValueError('HTML returned instead of data')
    return content, headers


def audit_csv(content, required):
    # Do not permit silent loss of rows through charset replacement.
    last_error = None
    for enc in ('utf-8-sig', 'cp1252'):
        try:
            txt = content.decode(enc)
            break
        except UnicodeDecodeError as ex:
            last_error = ex
    else:
        raise ValueError('UNDECODABLE_SOURCE') from last_error
    sample = txt[:12000]
    try:
        sep = csv.Sniffer().sniff(sample, delimiters=';,\t|').delimiter
    except csv.Error:
        sep = ';' if sample.splitlines()[0].count(';') > sample.splitlines()[0].count(',') else ','
    rows = csv.DictReader(io.StringIO(txt), delimiter=sep)
    fields = [f.lstrip('\ufeff').strip() for f in (rows.fieldnames or []) if f]
    if len(fields) < 2:
        raise ValueError('CSV_SCHEMA_TOO_NARROW')
    if required and not set(required).issubset(fields):
        raise ValueError(f'MISSING_COLUMNS_{sorted(set(required)-set(fields))}')
    seen = 0
    for row in rows:
        if None in row:  # Too many data cells for header.
            raise ValueError('CSV_INCONSISTENT_COLUMNS')
        seen += 1
    if seen < 10:
        raise ValueError(f'INSUFFICIENT_ROWS_{seen}')
    return {'n_rows': seen, 'columns': fields, 'encoding': enc, 'delimiter': sep}


def audit_jsonstat(content, required):
    doc = json.loads(content.decode('utf-8-sig'))
    if not isinstance(doc, dict):
        raise ValueError('NOT_JSON_OBJECT')
    if not {'dimension','value'}.issubset(doc):
        raise ValueError('NOT_EUROSTAT_JSONSTAT')
    dims = doc.get('dimension', {})
    if not isinstance(dims, dict) or not set(required).issubset(dims):
        raise ValueError('MISSING_EUROSTAT_DIMENSIONS')
    values = doc.get('value', {})
    if not isinstance(values, dict) or not values:
        raise ValueError('EUROSTAT_NO_OBSERVATIONS')
    return {'dimensions': sorted(dims.keys()), 'n_nonmissing_values': len(values),
            'unit': 'as declared in dataset dimension; no implicit conversion'}


def validate(content, spec):
    if spec['format'] == 'csv':
        return audit_csv(content, spec.get('required_columns', []))
    if spec['format'] == 'jsonstat':
        return audit_jsonstat(content, spec.get('required_dimensions', []))
    raise ValueError('UNSUPPORTED_SOURCE_FORMAT')


def run(specs, opener=urllib.request.urlopen):
    result = {'run_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'purpose': 'SOURCE_ACCESS_AND_SCHEMA_AUDIT_ONLY',
              'source_registry': 'pipeline/audit_multisource_sources.json',
              'no_data_fusion': True, 'no_causal_inference': True,
              'raw_data_published': False, 'sources': {}}
    for s in specs:
        record = {'source_url': s['url'], 'publisher': s['publisher'],
                  'legal_state': s['legal_state'], 'dependency_cluster': s['dependency_cluster'],
                  'unit_of_observation': s['unit_of_observation'],
                  'allowed_to_publish_raw': False,
                  'publication_gate': 'BLOCKED_PENDING_SEMANTIC_AND_LEGAL_REVIEW'}
        err = None
        for attempt in range(2):
            try:
                payload, headers = read_limited(s['url'], opener=opener)
                checks = validate(payload, s)
                record.update({'result': 'FETCH_AND_SCHEMA_PASS',
                               'sha256': hashlib.sha256(payload).hexdigest(),
                               'n_bytes': len(payload), 'checks': checks, **headers})
                err = None
                break
            except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
                err = f'{type(exc).__name__}: {str(exc)[:260]}'
                if attempt == 0:
                    time.sleep(1)
        if err:
            record.update({'result': 'FETCH_OR_SCHEMA_FAILED', 'reason': err})
        result['sources'][s['id']] = record
    counts = Counter(s['result'] for s in result['sources'].values())
    result['summary'] = {'attempted': len(specs), 'passed': counts['FETCH_AND_SCHEMA_PASS'],
                         'failed': counts['FETCH_OR_SCHEMA_FAILED'],
                         'ready_for_economic_join': 0}
    return result


def main():
    specs = json.loads(SOURCES.read_text(encoding='utf-8'))['sources']
    report = run(specs)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report['summary']))
    for key, value in report['sources'].items():
        print(f'{key}: {value["result"]} ({value.get("reason", "validated bytes and schema")})')
    if report['summary']['passed'] == 0:
        raise SystemExit('No live source passed. Read audits/latest_multisource.json.')


if __name__ == '__main__':
    main()
