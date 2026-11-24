"""S1 v0.1: source-specific observation contracts, not an economic join engine."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit
import csv
import json
import re
from .data_governance import comparison_gate, public_use_gate

VERSION = "0.1.0"
ROOT = Path(__file__).resolve().parents[1]
# measure, unit, population, geography, frequency, adjustment, taxonomy,
# definition, rights registry ID, dependency family (not independent evidence)
CONTRACTS = {
    "insee_employment": ("employee_stock", "thousand_employees", "employees_15plus_end_quarter", "FR_excl_Mayotte", "Q", "CVS", "INSEE_source_labels_2026-08-28", "employment_level", "INSEE_EMPLOI_SECTORIEL_TRIMESTRIEL", "FR_admin_mixed"),
    "urssaf_na88_effectifs_salaries_cvs": ("employee_stock", "employees", "private_sector_end_quarter", "FR_Urssaf_scope", "Q", "CVS", "NACE_Rev2_section_via_NA88", "employment_level", "DS-015_urssaf_private_sector_na88", "FR_admin_mixed"),
    "urssaf_dpae_na38_quarterly": ("hiring_declarations", "declarations", "CDI_and_CDD_over_one_month", "FR_Urssaf_DPAE_scope", "Q", "CVS", "NACE_Rev2_section_via_NA38", "declarations_not_hires", "URSSAF_DPAE_NA38_QUARTERLY", "FR_admin_mixed"),
    "eurostat_ai_tany": ("ai_adoption", "percent_enterprises", "enterprises_10plus_survey", "FR_Eurostat_scope", "A", "not_applicable", "NACE_Rev2_section", "E_AI_TANY", None, "Eurostat_ICT_survey"),
}
FIELDS = ("measure", "unit", "population", "geography", "frequency", "adjustment", "taxonomy", "definition", "rights_id", "dependency_family")


@dataclass(frozen=True)
class Observation:
    series: str
    sector: str
    category_kind: str
    period: str
    value: Decimal
    vintage: str  # timestamp of retrieval, not publication date
    sha256: str  # hash of original source bytes, not this derived record
    source_url: str
    locator: str  # record in source-specific artifact
    method_vintage: str
    evidence: str = "DESCRIPTIVE_ONLY"

    def __post_init__(self):
        if self.series not in CONTRACTS or self.evidence != "DESCRIPTIVE_ONLY":
            raise ValueError("UNKNOWN_CONTRACT_OR_EVIDENCE")
        c = self.contract
        if not self.sector.strip() or not self.locator.strip() or not self.method_vintage.strip():
            raise ValueError("MISSING_METADATA")
        if self.series == "insee_employment":
            if self.category_kind not in {"BROAD_SECTOR", "SUBCATEGORY", "AGGREGATE"}:
                raise ValueError("UNKNOWN_CATEGORY_KIND")
        elif self.sector != "J" or self.category_kind != "SECTION":
            raise ValueError("UNSUPPORTED_SECTOR")
        if not re.fullmatch(r"[0-9]{4}Q[1-4]" if c["frequency"] == "Q" else r"[0-9]{4}", self.period):
            raise ValueError("INVALID_PERIOD")
        if not isinstance(self.value, Decimal) or not self.value.is_finite() or self.value < 0:
            raise ValueError("INVALID_VALUE")
        if c["unit"] == "percent_enterprises" and self.value > 100:
            raise ValueError("INVALID_PERCENT")
        if not re.fullmatch(r"[0-9a-f]{64}", self.sha256):
            raise ValueError("INVALID_SHA256")
        u = urlsplit(self.source_url)
        if u.scheme != "https" or not u.hostname or u.username or u.password:
            raise ValueError("INVALID_SOURCE_URL")
        if datetime.fromisoformat(self.vintage.replace("Z", "+00:00")).tzinfo is None:
            raise ValueError("VINTAGE_MUST_HAVE_TIMEZONE")

    @property
    def contract(self):
        return dict(zip(FIELDS, CONTRACTS[self.series]))

    @property
    def key(self):
        return self.series, self.sector, self.category_kind, self.period, self.vintage, self.sha256


def decimal_value(x):
    try:
        return Decimal(str(x))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("INVALID_VALUE") from exc


def validate_unique(records):
    seen = set()
    for o in records:
        # One observation per logical cell per retrieval; conflicting hashes also fail.
        key = o.key[:-1]
        if key in seen:
            raise ValueError("DUPLICATE_OBSERVATION")
        seen.add(key)
    return records


def read_insee(root=ROOT):
    folder = root / "data/curated"
    manifest = json.loads((folder / "insee_employment_manifest.json").read_text())
    if manifest["publication_gate"] != "PASS_INSEE_DESCRIPTIVE_ONLY" or manifest["method_vintage"] != "2026-08-28 first reference edition; future revisions require review":
        raise ValueError("INSEE_GATE_NOT_PASSED")
    expected = {"geography": "France hors Mayotte", "unit": "thousands of employees", "seasonal_adjustment": "CVS", "source": "Insee", "underlying_source_sha256": manifest["raw_sha256"]}
    records = []
    with (folder / "insee_employment_sector_quarterly.csv").open(encoding="utf-8", newline="") as f:
        for n, r in enumerate(csv.DictReader(f), 2):
            if any(r[k] != v for k, v in expected.items()):
                raise ValueError("INSEE_METADATA_MISMATCH")
            if not re.fullmatch(r"[0-9]{4}-T[1-4]", r["quarter"]):
                raise ValueError("INVALID_SOURCE_PERIOD")
            records.append(Observation("insee_employment", r["sector_label"], r["category_kind"], r["quarter"].replace("-T", "Q"), decimal_value(r["employees_thousands"]), manifest["observed_at_utc"], manifest["raw_sha256"], manifest["download_evidence"]["url"], f"data/curated/insee_employment_sector_quarterly.csv:{n}", manifest["method_vintage"]))
    if not records or len(records) != manifest["data_rows"]:
        raise ValueError("INSEE_ROW_COUNT_MISMATCH")
    return validate_unique(records)


def read_pilot(root=ROOT):
    path = "research/PILOT-001/pilot_manifest.json"
    m = json.loads((root / path).read_text())
    if m["evidence_gate"] != "DESCRIPTIVE_SIDEBY_SIDE_ONLY" or m["causal_claims_permitted"] is not False or m["sector"] != "Information et communication (NACE Rev2 J)":
        raise ValueError("PILOT_CONTRACT_MISMATCH")
    records = []
    for section, series, source, field, unit in (
        ("private_employment", "urssaf_na88_effectifs_salaries_cvs", "urssaf_headcount", "selected_periods", "employee count, seasonally adjusted, private sector"),
        ("dpae", "urssaf_dpae_na38_quarterly", "urssaf_dpae", "selected_periods", "DPAE declarations for CDI and CDD >1 month, seasonally adjusted"),
        ("ai_adoption", "eurostat_ai_tany", "eurostat_ai", "selected_years", "% enterprises using at least one AI technology"),
    ):
        s, src = m["selected_studies"][section], m["sources"][source]
        if section == "private_employment" and (s["classification"], s["geography"]) != ("NACE Rev2 section J, six NA88 divisions 58-63", "France entière (Urssaf scope)"):
            raise ValueError("PILOT_EMPLOYMENT_SCOPE_MISMATCH")
        if section == "dpae" and (s["classification"], s["geography"]) != ("NA38 JA (editing/audio-visual), JB (telecom), JC (IT); three components of NACE J", "France entière, Urssaf DPAE field"):
            raise ValueError("PILOT_DPAE_SCOPE_MISMATCH")
        if s["unit"] != unit:
            raise ValueError("PILOT_UNIT_MISMATCH")
        if section == "ai_adoption" and s["selected_codes"] != {"geo":"FR", "nace_r2":"J", "indic_is":"E_AI_TANY", "unit":"PC_ENT", "size_emp":"GE10", "freq":"A"}:
            raise ValueError("PILOT_EUROSTAT_CODES_MISMATCH")
        if not s[field]:
            raise ValueError("EMPTY_PILOT_SECTION")
        for p, v in s[field].items():
            method = "AI basket pre-2025" if section == "ai_adoption" and p < "2025" else "AI basket 2025+ (expanded)" if section == "ai_adoption" else "PILOT-001 first observed vintage"
            records.append(Observation(series, "J", "SECTION", p, decimal_value(v), m["run_at_utc"], src["sha256"], src["url"], f"{path}#/selected_studies/{section}/{field}/{p}", method))
    return validate_unique(records)


def compare(a, b):
    """A gate, not a publication authorization; no numerical joins."""
    if (a.series, a.sector, a.category_kind) != (b.series, b.sector, b.category_kind):
        return {"decision": "BLOCK", "reason": "SEMANTIC_MISMATCH"}
    if (a.vintage, a.sha256) != (b.vintage, b.sha256):
        return {"decision": "BLOCK", "reason": "VINTAGE_MISMATCH"}
    if a.period >= b.period:
        return {"decision": "BLOCK", "reason": "PERIOD_ORDER"}
    if a.method_vintage != b.method_vintage:
        return {"decision": "BLOCK", "reason": "METHOD_BREAK"}
    if a.series == "eurostat_ai_tany":
        return {"decision": "REVIEW_REQUIRED", "reason": "Eurostat survey flags and definition require review"}
    return comparison_gate(a.series, a.period, b.period)


def release(o, purpose, *, attributed=False, adapted_database=None):
    """Unknown legal status or adapted-database status never grants release."""
    rid = o.contract["rights_id"]
    if not rid:
        return {"decision": "BLOCK_LEGAL_REVIEW", "reason": "Unqualified rights in machine registry"}
    if purpose != "internal_research" and adapted_database is not False:
        return {"decision": "BLOCK_LEGAL_REVIEW", "reason": "No verified non-adapted use"}
    return public_use_gate(rid, purpose, attributed=attributed, adapted_database=adapted_database is True)


def audit(root=ROOT):
    records = validate_unique(read_insee(root) + read_pilot(root))
    counts = {s: sum(o.series == s for o in records) for s in CONTRACTS}
    return {"contract_version": VERSION, "counts": counts, "total": len(records), "status": "SOURCE_SPECIFIC_DESCRIPTIVE_ONLY", "causal_claims_permitted": False, "cross_source_join_permitted": False, "full_source_qualification": False}


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
