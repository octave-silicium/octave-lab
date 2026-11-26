"""SEC-001-A: bounded, read-only triage of public Git content.
No credential value, matching line or secret location is emitted.
A zero count is not a security certificate. No project code is imported."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
MAX_BLOB=8*1024*1024
MAX_TOTAL=256*1024*1024
PINNED=re.compile(r"@[0-9a-fA-F]{40}$")
USES=re.compile(r"(?m)^\s*(?:-\s*)?uses:\s*['\"]?([^'\"\s#]+)")
SECRET_PATTERNS={
    "private_key_header":re.compile(rb"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"),
    "github_classic_token":re.compile(rb"(?<![A-Za-z0-9_])gh[pousr]_[A-Za-z0-9]{36,255}(?![A-Za-z0-9_])"),
    "github_fine_grained_token":re.compile(rb"(?<![A-Za-z0-9_])github_pat_[A-Za-z0-9_]{60,255}(?![A-Za-z0-9_])"),
    "openai_token_shape":re.compile(rb"(?<![A-Za-z0-9_])sk-(?:proj-|svcacct-)[A-Za-z0-9_-]{40,255}(?![A-Za-z0-9_-])"),
    "slack_token_shape":re.compile(rb"(?<![A-Za-z0-9_])xox[baprs]-[0-9A-Za-z-]{20,200}(?![A-Za-z0-9_-])"),
}
def git(*args, data=None):
    return subprocess.check_output(["git",*args],cwd=ROOT,input=data)
def revision(ref):
    return git("rev-parse","--verify",ref+"^{commit}").decode().strip()
def workflow_findings(path,text):
    actions=USES.findall(text)
    remote=[x for x in actions if not x.startswith(("./","docker://"))]
    # Regex routing only, not evaluation of YAML or effective permissions.
    return {"path":path,"remote_uses":remote,
            "unpinned_remote_uses":[x for x in remote if not PINNED.search(x)],
            "docker_uses":sum(x.startswith("docker://") for x in actions),
            "permission_declaration":bool(re.search(r"(?m)^\s*permissions\s*:",text)),
            "write_indicator":bool(re.search(r"(?m)^\s*(?:[\w-]+:\s*write|permissions:\s*write-all)\s*(?:#.*)?$",text)),
            "push_main_indicator":bool(re.search(r"git\s+push[^\n]*(?:HEAD:main|origin\s+main|refs/heads/main)",text)),
            "pull_request_target_indicator":bool(re.search(r"\bpull_request_target\b",text)),
            "artifact_indicator":"actions/upload-artifact@" in text,
            "dependency_install_indicator":bool(re.search(r"\b(?:pip(?:3)?\s+install|python\s+-m\s+pip\s+install|npm\s+(?:install|ci)|apt(?:-get)?\s+install)\b",text))}
def secret_types(raw):
    return {k for k,p in SECRET_PATTERNS.items() if p.search(raw)}
def current_blobs(ref):
    blobs={}
    for line in git("ls-tree","-rz","-l",ref).split(b"\0"):
        if not line:continue
        meta,path=line.split(b"\t",1)
        mode,kind,oid,size=meta.decode().split()
        if kind=="blob":
            blobs[path.decode("utf-8","surrogateescape")]=(oid,int(size))
    return blobs
def scan_history(ref,current,max_blob=MAX_BLOB,max_total=MAX_TOTAL):
    ids=sorted(set(git("rev-list","--objects","--no-object-names",ref).decode().splitlines()))
    # Only object identifiers and sizes. Never print filenames/lines of suspected credentials.
    checked=git("cat-file","--batch-check=%(objectname) %(objecttype) %(objectsize)",
                data=("\n".join(ids)+"\n").encode()).decode().splitlines()
    current_ids={oid for oid,_ in current.values()}
    blobs=[]
    for line in checked:
        parts=line.split()
        if len(parts)!=3:raise ValueError("Object missing in pinned history")
        oid,kind,size=parts
        if kind=="blob":blobs.append((oid,int(size)))
    # Current content gets first priority if bounds are reached.
    blobs.sort(key=lambda r:(r[0] not in current_ids,r[0]))
    totals=Counter(); hits_current=Counter(); hits_historical=Counter()
    scanned_bytes=0
    with subprocess.Popen(["git","cat-file","--batch"],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE) as proc:
        for oid,size in blobs:
            is_current=oid in current_ids
            if size>max_blob or scanned_bytes+size>max_total:
                totals["skipped_current" if is_current else "skipped_historical"]+=1
                continue
            proc.stdin.write((oid+"\n").encode());proc.stdin.flush()
            header=proc.stdout.readline().decode().split()
            if header!=[oid,"blob",str(size)]:raise ValueError("Unexpected object response")
            raw=proc.stdout.read(size)
            if len(raw)!=size or proc.stdout.read(1)!=b"\n":raise ValueError("Truncated object")
            scanned_bytes+=size
            totals["scanned_current" if is_current else "scanned_historical"]+=1
            hit=secret_types(raw)
            if hit:
                totals["candidate_current" if is_current else "candidate_historical"]+=1
                (hits_current if is_current else hits_historical).update(hit)
        proc.stdin.close()
        if proc.wait()!=0:raise ValueError("Git object scan failed")
    return {"reachable_unique_blobs":len(blobs),"current_unique_blobs":len(current_ids),"bytes_scanned":scanned_bytes,
            "scanned_current":totals["scanned_current"],"scanned_historical":totals["scanned_historical"],
            "skipped_current":totals["skipped_current"],"skipped_historical":totals["skipped_historical"],
            "candidate_current":totals["candidate_current"],"candidate_historical":totals["candidate_historical"],
            "current_pattern_counts":dict(hits_current),"historical_pattern_counts":dict(hits_historical),
            "scan_scope":"reachable blobs from pinned public commit; pattern triage, not credential validation"}
def build(ref):
    rev=revision(ref); current=current_blobs(rev)
    workflows=[]
    for path in sorted(current):
        if path.startswith(".github/workflows/") and path.endswith((".yml",".yaml")):
            workflows.append(workflow_findings(path,git("show",rev+":"+path).decode()))
    summary={"revision":rev,"workflow_count":len(workflows),
             "remote_action_occurrences":sum(len(w["remote_uses"]) for w in workflows),
             "unpinned_remote_action_occurrences":sum(len(w["unpinned_remote_uses"]) for w in workflows),
             "workflows_without_explicit_permission_indicator":sum(not w["permission_declaration"] for w in workflows),
             "workflows_write_indicator":sum(w["write_indicator"] for w in workflows),
             "workflows_direct_main_push_indicator":sum(w["push_main_indicator"] for w in workflows),
             "workflows_pull_request_target_indicator":sum(w["pull_request_target_indicator"] for w in workflows),
             "workflows_artifact_indicator":sum(w["artifact_indicator"] for w in workflows),
             "workflows_dependency_install_indicator":sum(w["dependency_install_indicator"] for w in workflows),
             "secret_scan":scan_history(rev,current),"qualification":"HEURISTIC_TRIAGE_ONLY",
             "publication_authorized":False}
    # No raw text, credentials, secret paths or private data in output. Workflow paths and
    # refs are already public; output only static indicators for planned hardening.
    return {"summary":summary,"workflow_routing":workflows,
            "limits":["Not semantic YAML, effective permission, artifact ACL, runtime or penetration audit.",
                      "Pattern detection is neither comprehensive nor confirmation of a valid credential.",
                      "History scope is pinned reachable ancestry, not all branches, deleted refs, private files or remote caches.",
                      "Skipped blobs remain unexamined; no claim of secret absence.",
                      "No release, license or client-data authorization."]}
def main():
    p=argparse.ArgumentParser();p.add_argument("--ref",required=True);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();r=build(a.ref)
    a.output.write_text(json.dumps(r,indent=2)+"\n")
    print("SEC_A_SUMMARY="+json.dumps(r["summary"],sort_keys=True))
if __name__=="__main__":main()
