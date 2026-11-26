"""SEC-B3: inventory outbound CI paths and direct install commands at an immutable ref.
Static indicators only: no workflow execution, data reads, external installs, or log content.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
from tools.security_triage import current_blobs, revision, workflow_findings

ROOT=Path(__file__).resolve().parents[1]
UPLOAD=re.compile(r"^(\s*)(?:-\s*)?uses:\s*['\"]?actions/upload-artifact@([^\s'\"#]+)")
INSTALL=re.compile(r"\b(?:pip(?:3)?\s+install|python\s+-m\s+pip\s+install|npm\s+(?:install|ci)|apt(?:-get)?\s+install|playwright install)\b")
# This recognizes the repository's conventional literal step layout, not arbitrary YAML.
def inspect(text):
    lines=text.splitlines()
    uploads=[]
    for i,line in enumerate(lines):
        m=UPLOAD.match(line)
        if not m: continue
        use_indent=len(m[1])
        # A same-indent next 'uses' may be in another step; end on next step or job.
        end=i+1
        while end<len(lines):
            s=lines[end]
            if s.strip() and len(s)-len(s.lstrip())<=use_indent and not s.lstrip().startswith("#"):
                break
            end+=1
        block=lines[i+1:end]
        paths=[]; retention=None; hidden=None; missing=None
        for j,s in enumerate(block):
            p=re.match(r"^(\s*)path:\s*(.*?)\s*$",s)
            if p:
                val=p[2]
                if val in ("|","|-","|+",">",">-"):
                    indent=len(p[1])
                    for tail in block[j+1:]:
                        if tail.strip() and len(tail)-len(tail.lstrip())<=indent: break
                        if tail.strip():paths.append(tail.strip())
                elif val:paths.append(val.strip("'\""))
            r=re.match(r"\s*retention-days:\s*(\d+)\s*(?:#.*)?$",s)
            if r:retention=int(r[1])
            r=re.match(r"\s*include-hidden-files:\s*(.*)",s)
            if r:hidden=r[1].strip()
            r=re.match(r"\s*if-no-files-found:\s*(.*)",s)
            if r:missing=r[1].strip()
        # Inspect preceding properties for if: always(); default to unknown if not detected.
        before=[]
        for k in range(i-1,-1,-1):
            s=lines[k]
            if s.strip() and len(s)-len(s.lstrip())<use_indent:break
            before.append(s)
            if s.lstrip().startswith("- "):break
        uploads.append({"line":i+1,"ref":m[2],"paths":paths,
                        "path_parse_status":"LITERAL_OR_EXPRESSION" if paths else "UNRESOLVED",
                        "directory_or_glob_indicator":any(p.endswith("/") or any(c in p for c in "*?[]") for p in paths),
                        "dynamic_indicator":any("$" in p or "{" in p for p in paths),
                        "retention_days_literal":retention,
                        "hidden_files_setting":hidden,"missing_files_setting":missing,
                        "always_indicator":any("always()" in s for s in before)})
    installs=[]
    for i,line in enumerate(lines):
        if INSTALL.search(line):
            # Record only line and recognized direct requirement tokens; never emit whole shell command.
            packages=re.findall(r"(?<![\w.-])([A-Za-z0-9_.-]+==[0-9][A-Za-z0-9_.+-]*)",line)
            installs.append({"line":i+1,"direct_exact_versions":packages,
                             "browser_or_os_install_indicator":bool(re.search(r"playwright install|apt(?:-get)? install",line)),
                             "hash_required_indicator":"--require-hashes" in line})
    return uploads,installs

def build(ref):
    rev=revision(ref); current=current_blobs(rev); rows=[]
    for path in sorted(current):
        if not path.startswith(".github/workflows/") or not path.endswith((".yml",".yaml")):continue
        raw=subprocess.check_output(["git","show",rev+":"+path],cwd=ROOT)
        txt=raw.decode();u,i=inspect(txt);f=workflow_findings(path,txt)
        rows.append({"path":path,"sha256":hashlib.sha256(raw).hexdigest(),"uploads":u,"installs":i,
                     "write_indicator":f["write_indicator"],"push_main_indicator":f["push_main_indicator"],
                     "unresolved_action_refs":f["unpinned_remote_uses"],
                     "rights_review_status":"PENDING_SCOPED_REVIEW"})
    uploads=[u for r in rows for u in r["uploads"]];installs=[i for r in rows for i in r["installs"]]
    summary={"revision":rev,"workflows":len(rows),"artifact_workflows":sum(bool(r["uploads"]) for r in rows),
             "upload_steps":len(uploads),"unresolved_path_steps":sum(not u["paths"] for u in uploads),
             "broad_path_steps":sum(u["directory_or_glob_indicator"] for u in uploads),
             "dynamic_path_steps":sum(u["dynamic_indicator"] for u in uploads),
             "always_steps":sum(u["always_indicator"] for u in uploads),
             "literal_retention_missing_steps":sum(u["retention_days_literal"] is None for u in uploads),
             "install_workflows":sum(bool(r["installs"]) for r in rows),"install_indicators":len(installs),
             "direct_exact_versions":sorted({v for i in installs for v in i["direct_exact_versions"]}),
             "hash_required_indicators":sum(i["hash_required_indicator"] for i in installs),
             "browser_or_os_install_indicators":sum(i["browser_or_os_install_indicator"] for i in installs),
             "publication_authorized":False}
    return {"summary":summary,"workflows":rows,"limits":["Heuristic line parser, not YAML semantic or effective permission audit.",
            "Paths are public configuration, not proof of contents, confidentiality or legal rights.",
            "No logs, raw artifacts, packages or dependency vulnerabilities inspected by this inventory.",
            "Static package names/versions are not transitive locks or SCA."]}
def main():
    p=argparse.ArgumentParser();p.add_argument("--ref",required=True);p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();r=build(a.ref)
    a.output.write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8")
    print("SEC_B3_SUMMARY="+json.dumps(r["summary"],sort_keys=True))
if __name__=="__main__":main()
