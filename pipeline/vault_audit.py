"""Use the existing real official archive; synthetic revisions only in unit tests."""
import json,tempfile
from pathlib import Path
from .data_vault import Vault,sha
from .data_observatory import read_registry,ROOT
def run():
    spec=next(s for s in read_registry() if s["id"]=="indeed_national_total_daily")
    digest=spec["baseline_sha256"]
    p=ROOT/"snapshots"/"indeed-fr"/"2026-11"/("indeed_fr_national_"+digest[:12]+".csv")
    raw=p.read_bytes()
    assert sha(raw)==digest
    with tempfile.TemporaryDirectory() as root:
        v=Vault(root);s=spec["id"]
        stage=v.stage(spec,raw)
        assert stage["status"]=="STAGED" and v.active_hash(s) is None
        v.promote(s,digest,None,"CI_REFERENCE_FIXTURE")
        assert v.stage(spec,raw)["status"]=="UNCHANGED_ACTIVE"
        assert v.stage(spec,b"<html>invalid</html>")["status"]=="REJECTED"
        v.close();v=Vault(root)
        assert sha(v.read(s))==digest
        report=v.verify();history=v.history(s)
        v.close()
        return {"scope":"TEMPORARY_CI_VAULT_REAL_ARCHIVED_INDEED","sha256":digest,"validated_rows":history["candidates"][0]["validation"]["coverage"]["selected_rows"],"reopen_and_integrity":"PASS","failed_update_preserved_active":True,"verification":report,"production_vault":False,"raw_data_uploaded":False}
if __name__=="__main__":print(json.dumps(run(),indent=2))
