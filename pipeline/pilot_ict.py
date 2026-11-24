"""OCTAVE LAB PILOT-001 | ICT industry (NACE section J), descriptive evidence only.

Reference implementation: fail closed, no occupational/industrial joins, no causal inference.
Source bytes are downloaded transiently. Only a compact produced-work summary is
published, with Urssaf ODbL source attribution and explicit legal review caveats.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import pathlib
import re
import urllib.parse
import urllib.request
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCES = {
    'urssaf_headcount': 'https://open.urssaf.fr/api/explore/v2.1/catalog/datasets/effectifs-salaries-et-masse-salariale-du-secteur-prive-france-entiere-x-na88/exports/csv?use_labels=false',
    'urssaf_dpae': 'https://open.urssaf.fr/api/explore/v2.1/catalog/datasets/dpae-france-entiere-x-na38/exports/csv?use_labels=false',
    'eurostat_ai': 'https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/isoc_eb_ain2?geo=FR&lang=EN&sinceTimePeriod=2022',
}
ALLOWED_HOSTS = {'open.urssaf.fr', 'ec.europa.eu'}
USER_AGENT = 'OCTAVE-LAB/0.6 (https://github.com/octave-silicium/octave-lab)'
MAX_BYTES = 16 * 1024 * 1024


def retrieve(source_url):
    u = urllib.parse.urlsplit(source_url)
    if u.scheme != 'https' or u.hostname not in ALLOWED_HOSTS or u.username or u.password:
        raise ValueError('UNTRUSTED_SOURCE_URL')
    req = urllib.request.Request(source_url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=70) as resp:
        final = urllib.parse.urlsplit(resp.geturl())
        if final.scheme != 'https' or final.hostname not in ALLOWED_HOSTS:
            raise ValueError('UNTRUSTED_REDIRECT')
        data = resp.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES or not data:
        raise ValueError('EMPTY_OR_OVERSIZE_SOURCE')
    if data.lstrip().lower().startswith((b'<html', b'<!doctype')):
        raise ValueError('HTML_NOT_DATA')
    return data


def read_csv(data, required):
    text = data.decode('utf-8-sig')
    sep = ';' if text.splitlines()[0].count(';') > text.splitlines()[0].count(',') else ','
    reader = csv.DictReader(io.StringIO(text), delimiter=sep)
    if not required.issubset(set(reader.fieldnames or [])):
        raise ValueError('UNEXPECTED_CSV_SCHEMA')
    return list(reader)


def numeric(s):
    x = s.strip().replace(' ', '').replace('\u202f', '').replace(',', '.')
    if x in ('', 'NA', '..', ':'):
        raise ValueError('MISSING_QUANTITATIVE_OBSERVATION')
    return float(x)


def quarterly_urssaf(rows, required_periods=('2024Q4', '2025Q4', '2025Q2', '2026Q2')):
    """Section J is NACE 58-63 here; assure exactly six nonoverlapping NA88 divisions."""
    periods = defaultdict(dict)
    for row in rows:
        label = row['secteur_na88i'].strip()
        m = re.match(r'^(5[89]|6[0-3])(?:\s|$)', label)
        if not m:
            continue
        code = m.group(1)
        p = f"{int(row['annee'])}Q{int(row['trimestre'])}"
        if p not in required_periods:
            continue
        if code in periods[p]:
            raise ValueError('NON_UNIQUE_NA88_SECTOR_PERIOD')
        periods[p][code] = numeric(row['effectifs_salaries_cvs'])
    result = {}
    expected = {'58', '59', '60', '61', '62', '63'}
    for p in required_periods:
        if set(periods[p]) != expected:
            raise ValueError(f'MISSING_NA88_DIVISIONS:{p}:{sorted(periods[p])}')
        result[p] = round(sum(periods[p].values()), 1)
    return {
      'unit': 'employee count, seasonally adjusted, private sector',
      'classification': 'NACE Rev2 section J, six NA88 divisions 58-63',
      'geography': 'France entière (Urssaf scope)',
      'selected_periods': result,
      'change_2025Q4_vs_2024Q4_pct': round(100*(result['2025Q4']/result['2024Q4']-1),2),
      'change_2026Q2_vs_2025Q2_pct': round(100*(result['2026Q2']/result['2025Q2']-1),2),
      'method': 'Sum exactly one row for each NA88 division 58,59,60,61,62,63; no occupational mapping.',
      'quality_gate': 'PRELIMINARY: sector mapping checked; revision and ODbL product gates pending',
    }


def quarterly_dpae(rows, required_periods=('2023Q4','2024Q4')):
    """NACE J = three nonoverlapping NA38 categories JA, JB, JC.

    JA edition/audiovisual, JB telecom, JC IT services. Require both contract
    types for every component, same-season comparison before DPAE 2025 errors.
    """
    periods = defaultdict(dict)
    sectors = {'JA','JB','JC'}
    contracts = {'CDI', "CDD de plus d'un mois"}
    for row in rows:
        sector_label = row['secteur_na38'].strip()
        sector = sector_label.split(' ')[0]
        if sector not in sectors:
            continue
        if row['duree_de_contrat'].strip() != "Contrat de plus d'un mois":
            continue
        contract = row['nature_de_contrat'].strip()
        if contract not in contracts:
            continue
        p = f"{int(row['annee'])}Q{int(row['trimestre'])}"
        if p not in required_periods:
            continue
        key = (sector, contract)
        if key in periods[p]:
            raise ValueError('DUPLICATE_NA38_COMPONENT_CONTRACT')
        periods[p][key] = numeric(row['dpae_cvs'])
    result = {}
    sector_detail = {}
    expected = {(sector,contract) for sector in sectors for contract in contracts}
    for p in required_periods:
        if set(periods[p]) != expected:
            missing = sorted(expected-set(periods[p]))
            raise ValueError(f'MISSING_NA38_COMPONENTS:{p}:{missing}')
        result[p] = round(sum(periods[p].values()))
        sector_detail[p] = {sec:round(sum(v for (s,c),v in periods[p].items() if s == sec)) for sec in sorted(sectors)}
    return {
       'unit': 'DPAE declarations for CDI and CDD >1 month, seasonally adjusted',
       'classification': 'NA38 JA (editing/audio-visual), JB (telecom), JC (IT); three components of NACE J',
       'geography': 'France entière, Urssaf DPAE field',
       'selected_periods': result,
       'subsector_decomposition': sector_detail,
       'change_2024Q4_vs_2023Q4_pct': round(100*(result['2024Q4']/result['2023Q4']-1),2),
       'method': 'Sum exactly 3 NA38 components times 2 nonoverlapping contract types, no 2025 periods',
       'quality_gate': 'PRELIMINARY: first-vintage descriptive only; not actual hires and not net employment',
    }


def get_index(category):
    idx = category['index']
    return idx if isinstance(idx, dict) else {k:i for i,k in enumerate(idx)}


def eurostat_offset(dataset, selectors):
    """JSON-stat flattened position, no nearest-match on indicator, unit or NACE."""
    ids = dataset['id']
    sizes = dataset['size']
    if not len(ids) == len(sizes):
        raise ValueError('BROKEN_JSONSTAT_DIMENSIONS')
    offset = 0
    for dim,size in zip(ids,sizes):
        d = dataset['dimension'][dim]
        indexes = get_index(d['category'])
        code = selectors[dim]
        if code not in indexes:
            raise ValueError(f'MISSING_CATEGORY:{dim}:{code};options={list(indexes)[:18]}')
        offset = offset * size + indexes[code]
    return offset


def eurostat_value(dataset, selectors):
    offset = eurostat_offset(dataset, selectors)
    value = dataset.get('value', {})
    result = value.get(str(offset)) if isinstance(value, dict) else value[offset]
    if result is None:
        raise ValueError('MISSING_EUROSTAT_VALUE')
    return float(result)


def eurostat_flag(dataset, selectors):
    offset = eurostat_offset(dataset, selectors)
    statuses = dataset.get('status', {})
    if isinstance(statuses, dict):
        flag = statuses.get(str(offset), '')
    elif isinstance(statuses, list):
        flag = statuses[offset] if offset < len(statuses) else ''
    else:
        raise ValueError('UNKNOWN_EUROSTAT_STATUS_SCHEMA')
    if flag is None:
        flag = ''
    if not isinstance(flag, str):
        raise ValueError('INVALID_EUROSTAT_STATUS')
    return flag


def eurostat_ict(data):
    j = json.loads(data)
    required = {'geo':'FR','nace_r2':'J','indic_is':'E_AI_TANY','unit':'PC_ENT'}
    # Only accept explicit 10+ enterprise scope; do not infer from ignored size dimension.
    size_codes = get_index(j['dimension']['size_emp']['category'])
    matches = [code for code in ['GE10', '10_C_EMP', 'GE10_C_EMP'] if code in size_codes]
    if len(matches)!=1:
        raise ValueError('UNRESOLVED_ENTERPRISE_SIZE:'+str(list(size_codes)))
    required['size_emp'] = matches[0]
    if 'freq' in j['id']:
        required['freq'] = 'A'
    values={}; flags={}
    for year in ('2023','2024','2025'):
        selectors = {**required,'time':year}
        flags[year] = eurostat_flag(j,selectors)
        if flags[year] not in {'', 'b'}:
            raise ValueError('PILOT_PUBLICATION_BLOCKED_FLAG_REVIEW')
        values[year] = eurostat_value(j,selectors)
    return {
      'indicator_code':'E_AI_TANY',
      'indicator_label':j['dimension']['indic_is']['category'].get('label',{}).get('E_AI_TANY'),
      'unit':'% enterprises using at least one AI technology',
      'population':'Enterprises with 10+ persons employed in NACE Rev2 section J, France; survey sample, not all employers',
      'classification':'NACE Rev2 section J',
      'selected_years':values,
      'source_flags':flags,
      'change_2024_vs_2023_pp':None,
      'change_2024_vs_2023_gate':'REVIEW_REQUIRED: inspect source flags and comparability; no validated change',
      'change_2025_vs_2024_pp':None,
      'comparability_warning':'2025 AI technology basket adds generative image/video/audio category vs prior years; do not interpret 2024-2025 difference as same-definition growth without official bridge.',
      'quality_gate':'SURVEY_DESCRIPTION_ONLY: no inference on automation, job losses or firm productivity',
      'selected_codes':required,
    }


def run(fetcher=retrieve):
    source_bytes = {key:fetcher(url) for key,url in SOURCES.items()}
    sha = {key:hashlib.sha256(b).hexdigest() for key,b in source_bytes.items()}
    urssaf = quarterly_urssaf(read_csv(source_bytes['urssaf_headcount'], {'secteur_na88i','annee','trimestre','effectifs_salaries_cvs'}))
    dpae = quarterly_dpae(read_csv(source_bytes['urssaf_dpae'], {'secteur_na38','annee','trimestre','duree_de_contrat','nature_de_contrat','dpae_cvs'}))
    euro = eurostat_ict(source_bytes['eurostat_ai'])
    return {
      'run_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
      'study':'PILOT-001', 'sector':'Information et communication (NACE Rev2 J)',
      'scope':'Source-specific descriptive observations; no numeric cross-source merging',
      'selected_studies': {'private_employment':urssaf,'dpae':dpae,'ai_adoption':euro},
      'sources':{k:{'url':url,'sha256':sha[k]} for k,url in SOURCES.items()},
      'limitations':[
        'Urssaf employment and DPAE come from one administrative family, not independent causal replications.',
        'Eurostat ICT adoption is an enterprise survey covering 10+ persons and NACE J, not employment or occupational exposure.',
        'Insee tertiary marchand is broader than NACE J; it cannot substitute for an independent ICT headcount.',
        'Indeed technical occupations do not equal NACE J employers; no crosswalk has been approved.',
        '2025 DPAE are withheld due to published contract-duration error warnings.',
        'Eurostat E_AI_TANY AI technology basket expanded in 2025 to include generating image/video/sound; 2025 level is not strict like-for-like adoption change.',
        'Information and communication covers publishing, media and telecoms, not just software firms.',
        'ODbL 1.0: attribution and derivative-database obligations; commercial product review not complete.',
      ],
      'evidence_gate':'DESCRIPTIVE_SIDEBY_SIDE_ONLY',
      'business_licence_gate':'NOT_APPROVED_FOR_COMMERCIAL_DERIVED_DATABASE',
      'causal_claims_permitted':False,
      'methodology':'pipeline/pilot_ict.py',
    }


def fr_int(value):
    return f"{value:,.0f}".replace(",", "\u202f")

def fr_number(value, sign=False):
    return (f"{value:+.2f}" if sign else f"{value:.2f}").replace(".", ",")

def build_report(result):
    u=result['selected_studies']['private_employment']; d=result['selected_studies']['dpae']; e=result['selected_studies']['ai_adoption']
    return f'''# OCTAVE LAB · PILOT-001 | Information et communication (NACE J)

**Statut : descriptif source par source. AUCUNE inférence causale ni jointure économique autorisée.**  
**Collecte UTC : {result['run_at_utc']}**

## Question
Que disent trois indicateurs différents sur les entreprises du secteur information-communication français, sans confondre emploi, déclarations d'embauche et usage déclaré de l'IA ?

## 1 · Effectifs des employeurs (Urssaf, NA88 divisions 58-63)
- T4 2024 : **{fr_int(u['selected_periods']['2024Q4'])}** salariés CVS.
- T4 2025 : **{fr_int(u['selected_periods']['2025Q4'])}** salariés CVS.
- Variation annuelle descriptive : **{fr_number(u['change_2025Q4_vs_2024Q4_pct'],True)} %**.
- T2 2026 vs T2 2025 : **{fr_number(u['change_2026Q2_vs_2025Q2_pct'],True)} %**.
- Définition : secteur privé couvert par l'Urssaf ; activités d'employeurs NACE 58 à 63, non métiers du numérique. Première collecte, révisions à surveiller.

## 2 · Déclarations préalables à l'embauche (Urssaf, NA38 JA+JB+JC)
- T4 2023 : **{fr_int(d['selected_periods']['2023Q4'])}** déclarations CVS de CDI et CDD de plus d'un mois.
- T4 2024 : **{fr_int(d['selected_periods']['2024Q4'])}** déclarations CVS de même catégorie.
- Variation descriptive : **{fr_number(d['change_2024Q4_vs_2023Q4_pct'],True)} %**.
- Les mois et trimestres 2025 restent exclus du calcul, en raison des anomalies déclaratives signalées par le producteur.
- Ces déclarations ne sont ni des embauches effectivement réalisées ni un solde net d'emploi.

## 3 · Adoption déclarée de l'IA (Eurostat, isoc_eb_ain2)
- 2023 : **{fr_number(e['selected_years']['2023'])} %** des entreprises concernées.
- 2024 : **{fr_number(e['selected_years']['2024'])} %**.
- 2025 : **{fr_number(e['selected_years']['2025'])} %**.
- Flags Eurostat : {', '.join(year + ': ' + (flag or 'aucun flag') for year, flag in e['source_flags'].items())}. Le code b signale une rupture de série. **Variation 2023-2024 non validée, en revue méthodologique** ; aucune hausse chiffrée présentée comme comparable. **Pas de taux de croissance 2024-2025 publié** : le panier de technologies suivi s’élargit en 2025 (génération d’images, vidéos et sons).
- Champ : entreprises de 10 personnes occupées ou plus, section NACE J, France ; résultat d'enquête, non mesure de tâches remplacées.

Note méthodologique de l’enquête Eurostat : https://ec.europa.eu/eurostat/documents/3859598/22759373/KS-01-25-065-EN-N.pdf .

## 4 · Confrontation méthodologique
Ces trois indicateurs NE FORMENT PAS une analyse causale. L'Urssaf fournit une famille administrative liée de mesures d'effectifs et de déclarations ; Eurostat fournit une enquête d'entreprises. Une hausse d'adoption de l'IA ne démontre ni suppression d'emploi ni hausse de productivité. Le secteur J mélange services informatiques, édition, médias et télécommunications.

**Inférence légitime :** décrire les mouvements propres à chaque indicateur et vérifier si leurs trajectoires méritent enquête approfondie.

**Inférence interdite :** attribuer leurs divergences ou évolutions à l'IA, ou calculer un nombre de postes éliminés par l'IA à partir de ces séries.

## 5 · Provenance et réutilisation
- Source Urssaf Caisse nationale, « Effectifs salariés et masse salariale par secteur NA88 », licence **ODbL 1.0** : {SOURCES['urssaf_headcount']}
- Source Urssaf Caisse nationale, « DPAE France entière x secteur NA38 », licence **ODbL 1.0** : {SOURCES['urssaf_dpae']}
- Licence ODbL : https://opendatacommons.org/licenses/odbl/1-0/ . Cette étude est une sortie illustrative compacte ; les bases dérivées et réutilisations commerciales doivent faire l'objet d'une validation juridique.
- Source Eurostat, « Artificial intelligence by NACE Rev.2 activity », code **isoc_eb_ain2** : {SOURCES['eurostat_ai']}
- Historique et empreintes SHA256 : `research/PILOT-001/pilot_manifest.json`.
- Méthode reproductible : `pipeline/pilot_ict.py`.

**Limites :** même groupe administratif pour les deux séries Urssaf ; pas d'effet causal ni de correspondance métier/branche, et nécessité de contrôler les révisions de séries et leur comparabilité.
'''


def main():
    r=run()
    target=ROOT/'research'/'PILOT-001'
    target.mkdir(parents=True,exist_ok=True)
    (target/'pilot_manifest.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (target/'rapport.md').write_text(build_report(r),encoding='utf-8')
    print(json.dumps({'gate':r['evidence_gate'],'sources':list(r['sources']), 'annual_headcount_change_pct':r['selected_studies']['private_employment']['change_2025Q4_vs_2024Q4_pct'], 'ai_adoption_2025':r['selected_studies']['ai_adoption']['selected_years']['2025']}, ensure_ascii=False))

if __name__=='__main__':
    main()
