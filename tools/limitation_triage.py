"""Deterministic candidate queue; never closes a limitation or asserts semantic equivalence."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import re
import unicodedata
from pathlib import Path

from pipeline.limitations_audit import inventory, git, REG

FAMILY = re.compile(r"\bLIM-[A-Z]\d{2}\b")
THEMES = {
    "SECURITY_RIGHTS": r"\b(?:sécurité|security|secret|chiffr\w*|confidential\w*|licen[cs]\w*|droits|odbl|publication|permission\w*|authent\w*|rgpd|privacy)\b",
    "EMPIRICAL_CAUSAL": r"\b(?:causal\w*|empiri\w*|calibr\w*|identification|backtest\w*|représentati\w*|independent|indépendan\w*|contrefactuel\w*|counterfactual\w*)\b",
    "DATA_SEMANTICS": r"\b(?:donnée\w*|data|source\w*|vintage\w*|millésime\w*|comparab\w*|nomenclature\w*|rupture\w*|coverage|couverture|mapping|jointure\w*)\b",
    "PRODUCT_OPERATIONS": r"\b(?:ux|accessibil\w*|client\w*|commercial\w*|déploiement|production|coffre|backup|restaur\w*|latence|interface\w*|workflow\w*)\b",
    "ECONOMIC_MODEL": r"\b(?:prix|demande|capital|emploi|salair\w*|revenu\w*|financ\w*|stock\w*|invest\w*|productiv\w*|coût\w*|capacity|capacit\w*|marché\w*|substitution|élasticit\w*)\b",
    "GOVERNANCE": r"\b(?:gate\w*|qualification|registre|review|revue|limitation\w*|obligation\w*|preuve\w*|evidence|acceptance|audit\w*)\b",
}
def normalized(text):
    # Preserve case, punctuation, numbers and word boundaries; do not infer semantic identity.
    return " ".join(unicodedata.normalize("NFC", text).split())

def group_key(text):
    return hashlib.sha256(normalized(text).encode("utf-8")).hexdigest()

def make_queue(candidates, entries):
    known = {e["id"] for e in entries}
    buckets = defaultdict(list)
    seen = set()
    for row in candidates:
        if row["id"] in seen:
            raise ValueError("duplicate candidate id")
        seen.add(row["id"])
        buckets[group_key(row["verbatim"])].append(row)
    groups = []
    for key, rows in sorted(buckets.items()):
        explicit = set()
        suggested = set()
        topics = set()
        for r in rows:
            explicit.update(FAMILY.findall(r["verbatim"]))
            suggested.update(r["suggested_families"])
            for topic, pattern in THEMES.items():
                if re.search(pattern, r["verbatim"], re.I):
                    topics.add(topic)
        unknown = explicit - known
        explicit_known = explicit & known
        if unknown:
            routing = "UNKNOWN_EXPLICIT_ID"
        elif explicit_known:
            routing = "EXPLICIT_REFERENCE_REVIEW"
        elif suggested:
            routing = "FILE_ASSOCIATION_ONLY"
        else:
            routing = "UNLINKED_REVIEW"
        priority = "P0_REVIEW" if unknown or "SECURITY_RIGHTS" in topics else (
            "P1_REVIEW" if routing == "UNLINKED_REVIEW" or "EMPIRICAL_CAUSAL" in topics else "P2_REVIEW")
        groups.append({
            "group_id": key, "normalized_text": normalized(rows[0]["verbatim"]),
            "members": [{"id": r["id"], "path": r["path"], "line": r["line"],
                         "heading": r["heading"], "verbatim": r["verbatim"],
                         "suggested_families": r["suggested_families"]} for r in rows],
            "explicit_families": sorted(explicit_known), "unknown_ids": sorted(unknown),
            "file_suggestions": sorted(suggested), "themes": sorted(topics),
            "routing": routing, "priority": priority, "semantic_status": "PENDING"
        })
    groups.sort(key=lambda x: (x["priority"], x["routing"], x["group_id"]))
    if {r["id"] for g in groups for r in g["members"]} != seen:
        raise ValueError("candidate loss")
    return groups

def build(ref):
    revision = git("rev-parse", "--verify", ref + "^{commit}").strip()
    entries = json.loads(git("show", revision + ":" + REG))["entries"]
    source = inventory(revision, entries)
    groups = make_queue(source["candidates"], entries)
    summary = {
        "revision": revision,
        "files": len(source["files"]),
        "candidates": len(source["candidates"]),
        "groups": len(groups),
        "duplicate_occurrences": len(source["candidates"]) - len(groups),
        "routing": dict(sorted(Counter(g["routing"] for g in groups).items())),
        "priority": dict(sorted(Counter(g["priority"] for g in groups).items())),
        "topics": dict(sorted(Counter(t for g in groups for t in g["themes"]).items())),
        "known_families": len(entries),
        "semantic_reviewed": 0,
        "semantic_pending": len(groups),
        "publication_authorized": False
    }
    return {"summary": summary, "source_files": source["files"], "groups": groups,
            "limits": ["Lexical inventory may miss implicit obligations.",
                       "Whitespace/NFC grouping is only a reading aid; all original contexts remain.",
                       "Explicit identifiers and file suggestions do not validate mappings.",
                       "Priority rules are conservative routing heuristics, not severity judgments.",
                       "No automatic contradiction, historical supersession, closure or release decision."]}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ref", required=True)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    report = build(args.ref)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("AUDIT_TRIAGE_SUMMARY=" + json.dumps(report["summary"], sort_keys=True))
if __name__ == "__main__":
    main()
