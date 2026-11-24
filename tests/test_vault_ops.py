import tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone,timedelta
from pipeline.data_vault import Vault,sha
from pipeline.vault_ops import backup,restore,collect_due,freshness
from pipeline.data_observatory import read_registry
SPEC=next(s for s in read_registry() if s["id"]=="indeed_national_total_daily")
A=b"date,jobcountry,variable,indeed_job_postings_index_SA\n2026-01-01,FR,total postings,100\n"
B=A+b"2026-01-02,FR,total postings,101\n"
class OpsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.v=Vault(self.root/"live")
    def tearDown(self):self.v.close();self.tmp.cleanup()
    def test_backup_restore_isolated(self):
        v=self.v;s=SPEC["id"];v.stage(SPEC,A);v.promote(s,sha(A),None,"REVIEW")
        v.stage(SPEC,B)
        m=backup(v,self.root/"backup")
        v.promote(s,sha(B),sha(A),"REVIEW")
        r=restore(self.root/"backup",self.root/"restored",m["database_sha256"])
        self.assertEqual(r["active"][s],sha(A))
        self.assertEqual(v.read(s),B)
        copy=Vault(self.root/"restored")
        try:self.assertEqual(copy.read(s),A);self.assertEqual(copy.read(s,sha(B)),B)
        finally:copy.close()
        with self.assertRaises(FileExistsError):restore(self.root/"backup",self.root/"restored",m["database_sha256"])
    def test_tamper(self):
        m=backup(self.v,self.root/"backup")
        p=self.root/"backup"/"vault.sqlite"
        p.write_bytes(p.read_bytes()+b"tamper")
        with self.assertRaisesRegex(ValueError,"BACKUP_INTEGRITY"):restore(p.parent,self.root/"restored",m["database_sha256"])
        self.assertFalse((self.root/"restored").exists())
    def test_durable_schedule_and_failure(self):
        v=self.v;s=SPEC["id"]
        first=collect_due(v,fetcher=lambda _:A,sources=[SPEC])
        self.assertEqual(first["results"][0]["status"],"STAGED")
        v.promote(s,sha(A),None,"REVIEW")
        v.close();self.v=v=Vault(self.root/"live")
        self.assertEqual(collect_due(v,fetcher=lambda _:self.fail("network not due"),sources=[SPEC])["results"][0]["status"],"NOT_DUE")
        def fail(_):raise OSError()
        self.assertEqual(collect_due(v,True,fail,[SPEC])["results"][0]["status"],"FETCH_FAILED")
        self.assertEqual(v.read(s),A)
        state=freshness(v,SPEC)
        self.assertEqual(state["alert"],"CHECK_FAILED");self.assertFalse(state["due"])
        self.assertTrue(freshness(v,SPEC,datetime.now(timezone.utc)+timedelta(hours=7))["due"])
        self.assertEqual(collect_due(v,True,lambda _:B,[SPEC])["results"][0]["revisions"]["added"],1)
        self.assertEqual(v.read(s),A)
