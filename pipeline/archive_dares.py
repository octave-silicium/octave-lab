"""Archive Dares monthly offers under confirmed Licence Ouverte v2.0 only.
Round-trip lossless .csv.gz; original bytes' SHA256 must equal live audited report.
This is raw data provenance, NOT permission for causal or cross-source analysis.
"""
import datetime as dt
import gzip
import hashlib
import io
import json
from pathlib import Path

from audit_multisource import read_limited, audit_csv, ROOT, OUT

SOURCE_ID = 'DS-004_dares_offers_monthly'
LICENSE_URL = 'https://www.etalab.gouv.fr/licence-ouverte-open-licence/'
DATASET_URL = 'https://www.data.gouv.fr/datasets/offres-collectees-et-satisfaites-par-france-travail-brutes-mensuelles'


def write_archive(raw, expected_sha, destination):
    sha = hashlib.sha256(raw).hexdigest()
    if sha != expected_sha:
        raise ValueError('SOURCE_VERSION_CHANGED_SINCE_AUDIT; no archive published')
    audit_csv(raw, ['Date', "Nombre d'offres d'emploi"])
    destination.mkdir(parents=True, exist_ok=False)
    filename = f'dares_ft_monthly_{sha[:12]}.csv.gz'
    path = destination / filename
    with path.open('wb') as h:
        with gzip.GzipFile(filename='', mode='wb', fileobj=h, compresslevel=9, mtime=0) as z:
            z.write(raw)
    with gzip.open(path, 'rb') as z:
        restored_hash = hashlib.sha256(z.read()).hexdigest()
    if restored_hash != expected_sha:
        raise ValueError('GZIP_ROUNDTRIP_SHA_MISMATCH')
    return filename, sha


def main():
    d = dt.datetime.now(dt.timezone.utc)
    folder = ROOT / 'snapshots' / 'dares-ft-monthly' / d.strftime('%Y-%m')
    if folder.exists():
        print('Existing monthly immutable Dares snapshot; not overwritten')
        return
    audit = json.loads(OUT.read_text(encoding='utf-8'))
    s = audit['sources'][SOURCE_ID]
    if s['result'] != 'FETCH_AND_SCHEMA_PASS':
        raise ValueError('Dares audit not passed')
    if 'Licence Ouverte v2.0' not in s['legal_state']:
        raise ValueError('License state not confirmed; not publishing raw')
    payload, _ = read_limited(s['source_url'])
    filename, sha = write_archive(payload, s['sha256'], folder)
    manifest = {
      'producer': s['publisher'], 'source_id': SOURCE_ID,
      'dataset_url': DATASET_URL, 'original_url': s['source_url'],
      'license': 'Licence Ouverte / Open Licence 2.0', 'license_url': LICENSE_URL,
      'attribution': 'Dares / France Travail ; OCTAVE LAB copy, not an official Dares release',
      'retrieved_at_utc': d.isoformat(),
      'sha256_uncompressed_original': sha, 'compressed_file': filename,
      'original_n_bytes': len(payload),
      'public_raw_allowed_with_attribution': True,
      'no_cross_source_join_without_mapping': True,
      'no_causal_inference': True
    }
    (folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (folder/'ATTRIBUTION.txt').write_text(
      'Source: Dares / France Travail — Offres collectées et satisfaites mensuelles\n'
      + DATASET_URL + '\nLicence Ouverte / Open Licence 2.0: '+LICENSE_URL+'\n'
      + 'Octave Lab archive les octets du CSV original sans modification; source non liée automatiquement à Indeed.\n',encoding='utf-8')
    print('Snapshot verified:',folder, 'SHA256',sha)

if __name__=='__main__':main()
