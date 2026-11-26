"""Read-only inventory of a pinned Git tree. No imports of project code or network.
Heuristic triage is not semantic, legal, scientific or security certification."""
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import PurePosixPath, Path
import posixpath
import re
import subprocess
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]

def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)

def json_no_duplicates(raw):
    duplicates = []
    def hook(pairs):
        d = {}
        for k, v in pairs:
            if k in d:
                duplicates.append(k)
            d[k] = v
        return d
    def invalid_constant(_):
        raise ValueError("nonstandard JSON constant")
    json.loads(raw, object_pairs_hook=hook, parse_constant=invalid_constant)
    return len(duplicates)

def local_links(text):
    for link in re.findall(r"\]\(([^)\s]+)\)", text):
        target = unquote(link.strip("<>").split("#", 1)[0])
        if target and not re.match(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//)", target):
            yield target

def workflow_flags(text):
    actions = re.findall(r"(?m)^\s*(?:-\s*)?uses:\s*['\"]?([^'\"\s#]+)", text)
    external = [a for a in actions if not a.startswith(("./", "docker://"))]
    return {
        "external_uses": len(external),
        "unpinned_uses": sum(not re.search(r"@[0-9a-fA-F]{40}$", a) for a in external),
        "write_permission_indicator": bool(re.search(r"(?m)^\s*(?:[\w-]+:\s*write|permissions:\s*write-all)\s*(?:#.*)?$", text)),
        "push_main_indicator": bool(re.search(r"git\s+push[^\n]*(?:HEAD:main|origin\s+main|refs/heads/main)", text)),
        "artifact_indicator": "actions/upload-artifact@" in text,
    }

def inventory(ref):
    commit = git("rev-parse", "--verify", ref + "^{commit}").decode().strip()
    tree = git("rev-parse", commit + "^{tree}").decode().strip()
    entries = []
    issues = []
    modules = {}
    flags = []
    raw_entries = git("ls-tree", "-r", "-z", "-l", commit).split(b"\0")
    for item in raw_entries:
        if not item:
            continue
        metadata, name = item.split(b"\t", 1)
        mode, kind, oid, size = metadata.decode().split()
        path = name.decode("utf-8", "surrogateescape")
        if kind != "blob":
            entries.append({"path": path, "mode": mode, "kind": kind, "oid": oid})
            continue
        raw = git("cat-file", "blob", oid)
        if len(raw) != int(size):
            raise ValueError("blob size mismatch")
        entry = {"path": path, "mode": mode, "kind": kind, "oid": oid, "bytes": len(raw),
                 "sha256": hashlib.sha256(raw).hexdigest()}
        entries.append(entry)
        suffix = PurePosixPath(path).suffix.lower()
        if suffix == ".py":
            try:
                node = ast.parse(raw, filename=path)
                imports = set()
                for n in ast.walk(node):
                    if isinstance(n, ast.Import):
                        imports.update(a.name for a in n.names if a.name.startswith("pipeline"))
                    if isinstance(n, ast.ImportFrom):
                        if n.level:
                            if path.startswith("pipeline/"):
                                prefix = "pipeline" + ("." + n.module if n.module else "")
                                imports.add(prefix)
                        elif n.module and n.module.startswith("pipeline"):
                            imports.add(n.module)
                modules[path] = sorted(imports)
            except (SyntaxError, ValueError) as e:
                issues.append({"path": path, "kind": "python_parse", "line": getattr(e, "lineno", None)})
        if suffix == ".json":
            try:
                duplicates = json_no_duplicates(raw)
                if duplicates:
                    issues.append({"path": path, "kind": "json_duplicate_keys", "count": duplicates})
            except (ValueError, UnicodeError):
                issues.append({"path": path, "kind": "json_parse"})
        if path.startswith(".github/workflows/") and suffix in (".yml", ".yaml"):
            flags.append({"path": path, **workflow_flags(raw.decode("utf-8", errors="replace"))})
        if suffix == ".md":
            entry["local_links"] = list(local_links(raw.decode("utf-8", errors="replace")))
    paths = {e["path"] for e in entries}
    for entry in entries:
        for link in entry.pop("local_links", []):
            target = posixpath.normpath(posixpath.join(posixpath.dirname(entry["path"]), link)) if not link.startswith("/") else link.lstrip("/")
            if target not in paths and not any(p.startswith(target.rstrip("/") + "/") for p in paths):
                issues.append({"path": entry["path"], "kind": "local_link_candidate", "target": target})
    summary = {
        "commit": commit, "tree": tree, "entries": len(entries),
        "blobs": sum(e["kind"] == "blob" for e in entries),
        "bytes": sum(e.get("bytes", 0) for e in entries),
        "by_group": dict(sorted(Counter(e["path"].split("/")[0] if "/" in e["path"] else "root" for e in entries).items())),
        "python_files": sum(e["path"].endswith(".py") for e in entries),
        "json_files": sum(e["path"].endswith(".json") for e in entries),
        "markdown_files": sum(e["path"].endswith(".md") for e in entries),
        "workflows": len(flags),
        "workflow_external_uses": sum(f["external_uses"] for f in flags),
        "workflow_unpinned_uses": sum(f["unpinned_uses"] for f in flags),
        "workflows_write_indicators": sum(f["write_permission_indicator"] for f in flags),
        "workflows_push_main_indicators": sum(f["push_main_indicator"] for f in flags),
        "workflows_artifact_indicators": sum(f["artifact_indicator"] for f in flags),
        "issues_by_kind": dict(sorted(Counter(i["kind"] for i in issues).items())),
        "qualification": "STRUCTURAL_ONLY",
        "publication_authorized": False,
    }
    return {"summary": summary, "files": entries, "static_pipeline_imports": modules,
            "workflow_triage": flags, "issues": issues,
            "limits": ["No runtime import or tests of project modules in this inventory.",
                       "Workflow indicators are regex triage, not YAML semantic validation or exploit findings.",
                       "Import graph is partial; dynamic imports and non-Python dependencies are not resolved.",
                       "Markdown links may include examples and generated outputs; candidates need review.",
                       "No secret scan, history, private archives, licenses or empirical validation."]}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = inventory(args.ref)
    args.output.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print("AUDIT_MASTER_SUMMARY=" + json.dumps(report["summary"], sort_keys=True))

if __name__ == "__main__":
    main()
