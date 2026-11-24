"""OCTAVE LAB — Lot 2: source access, integrity, schema and scope audit.

No raw data is persisted or redistributed. Source audit is not approval for
cross-source joins, commercial re-use, inference or downstream publication.
Only Python stdlib dependencies. Run via GitHub Actions and review the manifest.
"""
import csv
import datetime as dt
import hashlib
import io
import json
import pathlib
import re
import urllib.request
import urllib.parse
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_FILE = ROOT / 'pipeline' / 'audit_lot2_sources.json'
MANIFEST = ROOT / 'audits' / 'latest_lot2.json'
LIMIT = 24 * 1024 * 1024
AGENT = 'OCTAVE-LAB/0.5 reproducible source audit (+https://github.com/octave-silicium/octave-lab)'
ALLOWED_HOSTS = {'open.urssaf.fr', 'www.insee.fr'}


def allowed_url(url):
    p = urllib.parse.urlparse(url)
    return p.scheme == 'https' and p.hostname in ALLOWED_HOSTS and not p.username


def fetch_bytes(url, opener=urllib.request.urlopen):
    if not allowed_url(url):
        raise ValueError('SOURCE_HOST_NOT_ALLOWLISTED')
    request = urllib.request.Request(url, headers={'User-Agent': AGENT,
                                                   'Accept': 'text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*'})
    with opener(request, timeout=70) as resp:
        if getattr(resp, 'status', 200) != 200:
            raise ValueError(f'HTTP_{resp.status}')
        final_url = resp.geturl() if hasattr(resp, 'geturl') else url
        # Follow only redirects to the original allowlisted provider domains.
        if not allowed_url(final_url):
            raise ValueError('UNSAFE_REDIRECT_DESTINATION')
        data = resp.read(LIMIT + 1)
        headers = {'content_type': resp.headers.get('Content-Type'),
                   'etag': resp.headers.get('ETag'),
                   'last_modified': resp.headers.get('Last-Modified'),
                   'final_url': final_url}
    if len(data) > LIMIT:
        raise ValueError(f'BODY_TOO_LARGE_{LIMIT}')
    if data[:400].lstrip().lower().startswith((b'<html', b'<!doctype', b'<head')):
        raise ValueError('HTML_INSTEAD_OF_DATA')
    return data, headers


def profile_csv(data, minimum_rows):
    try:
        text = data.decode('utf-8-sig')
        enc = 'utf-8-sig'
    except UnicodeDecodeError:
        text = data.decode('cp1252')
        enc = 'cp1252'
    first = text[:10000]
    try:
        sep = csv.Sniffer().sniff(first, delimiters=',;\t').delimiter
    except csv.Error:
        sep = ';' if first.splitlines()[0].count(';') > first.splitlines()[0].count(',') else ','
    source = csv.DictReader(io.StringIO(text), delimiter=sep)
    fields = [s.strip().lstrip('\ufeff') for s in (source.fieldnames or [])]
    if len(fields) < 3 or len(set(fields)) < len(fields):
        raise ValueError('INVALID_CSV_HEADER')
    n = 0
    empty = 0
    for row in source:
        if None in row: raise ValueError('INCONSISTENT_CSV_COLUMNS')
        n += 1
        if all(v is None or v.strip() == '' for v in row.values()): empty += 1
    if n < minimum_rows:
        raise ValueError(f'INSUFFICIENT_ROWS_{n}')
    lower = ' '.join(fields).lower()
    if not any(x in lower for x in ('dpae', 'embauch', 'contrat')):
        raise ValueError('DPAE_MEASURE_FIELD_NOT_FOUND')
    if not any(x in lower for x in ('annee', 'année', 'trimestre', 'date', 'mois', 'jour')):
        raise ValueError('PERIOD_COLUMN_NOT_FOUND')
    return {'rows': n, 'columns': fields, 'delimiter': sep, 'encoding': enc,
            'empty_rows': empty,
            'date_range': 'NOT_ASSERTED_UNTIL_SEMANTIC_DICTIONARY_REVIEW'}


def profile_xlsx(data, minimum_sheets):
    if not data.startswith(b'PK\x03\x04'):
        raise ValueError('NOT_XLSX_ZIP')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = set(z.namelist())
        if '[Content_Types].xml' not in names or 'xl/workbook.xml' not in names:
            raise ValueError('MISSING_XLSX_CORE_COMPONENTS')
        sheets = sorted(n for n in names if re.fullmatch(r'xl/worksheets/sheet\d+\.xml', n))
        if len(sheets) < minimum_sheets:
            raise ValueError('NO_WORKSHEETS')
        # Inspection of workbook metadata, not an economic interpretation.
        root = ET.fromstring(z.read('xl/workbook.xml'))
        ns = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        titles = [s.attrib.get('name', '') for s in root.findall('.//x:sheets/x:sheet', ns)]
        glimpses = []
        for name in sheets[:12]:
            xml = ET.fromstring(z.read(name))
            cell_count = len(xml.findall('.//x:sheetData/x:row/x:c', ns))
            rows = len(xml.findall('.//x:sheetData/x:row', ns))
            dimension = xml.find('x:dimension', ns)
            glimpses.append({'worksheet': name, 'dimension': dimension.attrib.get('ref') if dimension is not None else None,
                             'xml_rows': rows, 'xml_cells': cell_count})
        if not any(g['xml_cells'] for g in glimpses):
            raise ValueError('EMPTY_XLSX_SHEETS')
    return {'worksheets': len(sheets), 'sheet_names': titles, 'structure_preview': glimpses,
            'status': 'WORKBOOK_VALIDATED_VALUES_AND_UNITS_NOT_YET_PARSED'}


def inspect_one(spec, fetcher=fetch_bytes):
    base = {'url': spec.get('url'), 'documentation_url': spec['documentation_url'],
            'publisher': spec['publisher'], 'dependency_group': spec['dependency_group'],
            'concept': spec['concept'], 'population': spec['population'],
            'legal': spec['legal'], 'public_raw_archive': spec['public_raw_archive'],
            'caution': spec['caution'], 'economic_join_ready': False}
    if not spec.get('url'):
        return {**base, 'result': 'PENDING_EXACT_DOWNLOAD_URL',
                'reason': 'Published data page located, but stable official binary URL and licence not yet verified.'}
    try:
        content, headers = fetcher(spec['url'])
        if spec['format'] == 'csv':
            profile = profile_csv(content, spec['minimum_rows'])
        elif spec['format'] == 'xlsx':
            profile = profile_xlsx(content, spec['minimum_sheets'])
        else:
            raise ValueError('UNSUPPORTED_FORMAT')
        return {**base, 'result': 'FETCH_AND_STRUCTURE_PASS',
                'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest(),
                'profile': profile, **headers,
                'next_gate': 'MANUAL_CODEBOOK_SCOPE_LICENCE_REVIEW'}
    except (OSError, ValueError, zipfile.BadZipFile, ET.ParseError, UnicodeError) as e:
        return {**base, 'result': 'FETCH_OR_STRUCTURE_FAILED',
                'reason': f'{type(e).__name__}: {str(e)[:250]}',
                'next_gate': 'FIX_ENDPOINT_OR_VALIDATE_DOCUMENT_ACCESS'}


def run(specs, fetcher=fetch_bytes):
    results = {s['id']: inspect_one(s, fetcher) for s in specs}
    counts = Counter(r['result'] for r in results.values())
    return {
        'audit_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'status': 'ACCESS_AND_STRUCTURE_ONLY', 'no_raw_redistribution': True,
        'no_automatic_harmonisation': True, 'no_causal_attribution': True,
        'sources': results,
        'summary': {'candidate_sources': len(specs),
                    'passed': counts['FETCH_AND_STRUCTURE_PASS'],
                    'failed': counts['FETCH_OR_STRUCTURE_FAILED'],
                    'pending_exact_url': counts['PENDING_EXACT_DOWNLOAD_URL'],
                    'ready_for_economic_join': 0}
    }


def main():
    specs = json.loads(SOURCE_FILE.read_text(encoding='utf-8'))['sources']
    report = run(specs)
    MANIFEST.parent.mkdir(exist_ok=True)
    MANIFEST.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report['summary'], ensure_ascii=False))
    for sid, entry in report['sources'].items():
        print(sid, entry['result'], entry.get('reason', ''))
    if report['summary']['passed'] == 0:
        raise SystemExit('No dataset access verified, inspect manifest for exact failure reasons')


if __name__ == '__main__':
    main()
