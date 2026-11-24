"""Acceptance on actual archives and current five live responses; no raw data emitted."""
import csv,io,json,tempfile
from pathlib import Path
from .data_vault import Vault,sha
from .vault_ops import backup,restore,collect_due,retrieve,freshness
from .data_observatory import read_registry,ROOT
from .native_revisions import compare

def run():
    sources=read_registry()
    specs=[s for s in sources if s["kind"]=="live_native" or s["id"]=="indeed_national_total_daily"]
    data={}
    for s in specs:
        if s["kind"]=="live_native":data[s["id"]]=retrieve(s)
        else:
            h=s["baseline_sha256"]
            data[s["id"]]=(ROOT/"snapshots"/"indeed-fr"/"2026-11"/("indeed_fr_national_"+h[:12]+".csv")).read_bytes()
            assert sha(data[s["id"]])==h
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);v=Vault(root/"vault")
        r=collect_due(v,fetcher=lambda s:data[s["id"]],sources=specs)
        assert all(x["status"]=="STAGED" for x in r["results"])
        report={}
        for s in specs:
            sid=s["id"];raw=data[sid];h=sha(raw)
            v.promote(sid,h,None,"CI_ACCEPTANCE_ONLY")
            if s["kind"]=="live_native":
                # Re-encoding is a synthetic transformation of one real release, not a second producer vintage.
                if sid.startswith("eurostat"):
                    equivalent=json.dumps(json.loads(raw),sort_keys=True,ensure_ascii=False).encode()
                else:
                    reader=csv.reader(io.StringIO(raw.decode("utf-8-sig")),delimiter=";")
                    header=next(reader);rows=list(reader);out=io.StringIO(newline="")
                    writer=csv.writer(out,delimiter=";");writer.writerow(header);writer.writerows(reversed(rows));equivalent=out.getvalue().encode()
                cmp=compare(sid,raw,equivalent)
                assert cmp["added"]==cmp["removed"]==cmp["visible_value_changed"]==cmp["flag_changed"]==cmp["quality_changed"]==0
                report[sid]={"sha256":h,"native_key_equivalence":cmp}
        m=backup(v,root/"backup")
        v.close()
        v=Vault(root/"vault")
        assert all(not freshness(v,s)["due"] for s in specs)
        failed=collect_due(v,True,lambda s:b"<html>bad</html>",specs)
        assert all(x["status"]=="REJECTED" for x in failed["results"])
        assert all(sha(v.read(s["id"]))==sha(data[s["id"]]) for s in specs)
        restored=restore(root/"backup",root/"restored",m["database_sha256"])
        w=Vault(root/"restored")
        try:
            assert all(sha(w.read(s["id"]))==sha(data[s["id"]]) for s in specs)
            assert w.verify()==m["verification"]
        finally:w.close();v.close()
        return {"scope":"TEMPORARY_PRIVATE_CI","sources":len(specs),"native_revisions":report,"backup_sha256":m["database_sha256"],"backup_bytes":m["bytes"],"restored":restored["verification"],"reopen_schedule":"PASS","invalid_update_preserved_all_active":"PASS","real_second_vintage_tested":False,"raw_data_uploaded":False,"production_storage":False}
if __name__=="__main__":print(json.dumps(run(),indent=2))
