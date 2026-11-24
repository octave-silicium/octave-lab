"""Fail-closed licensing and series-rupture checks for OCTAVE LAB.

These are publication *preconditions*, NOT legal authorisations, source validity
certificates, harmonisation procedures, or causal identification.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RIGHTS_PATH = ROOT / "governance" / "source_rights.json"
BREAKS_PATH = ROOT / "governance" / "series_events.json"

def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def public_use_gate(source_id, purpose, *, attributed=False, adapted_database=False):
    """Return a decision dict. Always distinguish public use from internal use."""
    sources = _read(RIGHTS_PATH)["sources"]
    if source_id not in sources:
        return {"decision": "BLOCK", "reason": "Unknown source or licence."}
    if purpose == "internal_research":
        return {"decision": "ALLOW_INTERNAL", "reason": "No public re-use. Source rights still apply."}
    if purpose not in {"public_chart", "paid_report", "public_dataset_export"}:
        return {"decision": "BLOCK", "reason": "Unsupported use type."}
    licence = sources[source_id].get("license")
    if licence == "LO-2.0":
        if not attributed:
            return {"decision": "BLOCK", "reason": "Insee / Licence Ouverte 2.0 attribution is required."}
        return {"decision": "CONDITIONAL_OPEN_LICENSE_REUSE",
                "reason": "Attribution and faithful meaning required; economic quality/vintage gates still apply. No causal claim granted."}
    if licence != "ODbL-1.0":
        return {"decision": "BLOCK_LEGAL_REVIEW", "reason": "Unsupported or unqualified licence."}
    if not attributed:
        return {"decision": "BLOCK", "reason": "Source + ODbL licence notice missing."}
    if adapted_database:
        return {"decision": "BLOCK_LEGAL_REVIEW", "reason": "ODbL clauses 4.4-4.6: derivative database requires share-alike and access; no approved release plan."}
    if purpose == "public_dataset_export":
        return {"decision": "BLOCK_LEGAL_REVIEW", "reason": "Database exports require review of notices, distribution format and licence obligations."}
    return {"decision": "CONDITIONAL_PUBLIC_PRODUCED_WORK", "reason": "Original-source chart/report with full attribution; confirm it does not use a publicly-used adapted database."}

def _period_key(value):
    if match := re.fullmatch(r"(\d{4})Q([1-4])", value):
        return (int(match.group(1)), int(match.group(2)))
    if match := re.fullmatch(r"(\d{4})-(0[1-9]|1[0-2])", value):
        return (int(match.group(1)), int(match.group(2)))
    raise ValueError("Period must use YYYYQn or YYYY-MM")

def comparison_gate(series_id, from_period, to_period):
    """Never run historical comparison across documented definitional breaks."""
    start, end = _period_key(from_period), _period_key(to_period)
    if start > end:
        return {"decision": "BLOCK", "events": [], "reason": "Reversed period range."}
    events = [event for event in _read(BREAKS_PATH)["events"] if series_id in event["affected_series"]]
    if not events:
        return {"decision": "BLOCK_UNKNOWN_SERIES", "events": [], "reason": "No event review for requested series."}
    flags = []
    decision = "ALLOW_WITH_CAVEATS"
    for event in events:
        if "effective_period" in event:
            pivot = _period_key(event["effective_period"])
            hit = start < pivot <= end
        else:
            lower = _period_key(event["start_period"])
            upper = _period_key(event["end_period"])
            hit = start <= upper and end >= lower
        if not hit:
            continue
        flags.append(event["id"])
        if event["kind"] in {"DEFINITION_BREAK", "DATA_QUALITY_SUSPICION", "CLASSIFICATION_BREAK"}:
            decision = "BLOCK"
        elif decision != "BLOCK":
            decision = "REVIEW_REQUIRED"
    return {"decision": decision, "events": flags,
            "reason": ("Manual harmonisation and/or official method review required" if flags
                       else "No flagged crossing in the current registry; other data-quality tests still required.")}

if __name__ == "__main__":
    print(json.dumps({
        "urssaf_external_derived": public_use_gate("DS-015_urssaf_private_sector_na88", "paid_report", attributed=True, adapted_database=True),
        "urssaf_2022_to_2023": comparison_gate("urssaf_na88_effectifs_salaries_cvs", "2022Q4", "2023Q1"),
    }, ensure_ascii=False, indent=2))
