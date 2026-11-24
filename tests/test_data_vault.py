import tempfile,unittest
from pipeline.data_vault import Vault,sha
from pipeline.data_observatory import read_registry
SPEC=next(s for s in read_registry() if s["id"]=="indeed_national_total_daily")
A=b"date,jobcountry,variable,indeed_job_postings_index_SA\n2026-01-01,FR,total postings,100\n"
B=A+b"2026-01-02,FR,total postings,101\n"
class VaultTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.v=Vault(self.tmp.name)
    def tearDown(self):self.v.close();self.tmp.cleanup()
    def test_stage_review_and_rollback(self):
        v=self.v;s=SPEC["id"]
        self.assertEqual(v.stage(SPEC,A)["status"],"STAGED")
        self.assertIsNone(v.active_hash(s))
        v.promote(s,sha(A),None,"INITIAL_REVIEW")
        v.stage(SPEC,B)
        self.assertEqual(v.read(s),A)
        self.assertEqual(v.stage(SPEC,B)["status"],"ALREADY_STAGED")
        with self.assertRaisesRegex(ValueError,"ACTIVE_CONFLICT"):v.promote(s,sha(B),None,"STALE_REVIEW")
        v.promote(s,sha(B),sha(A),"SECOND_REVIEW")
        self.assertEqual(v.read(s),B)
        v.promote(s,sha(A),sha(B),"ROLLBACK")
        self.assertEqual(v.read(s),A)
        self.assertEqual(v.read(s,sha(B)),B)
        self.assertEqual(v.verify()["objects"],2)
    def test_invalid_preserves_active(self):
        s=SPEC["id"];v=self.v
        v.stage(SPEC,A);v.promote(s,sha(A),None,"INITIAL_REVIEW")
        self.assertEqual(v.stage(SPEC,b"<html>bad</html>")["status"],"REJECTED")
        self.assertEqual(v.read(s),A)
        v.record_failure(s,"FETCH_FAILED")
        self.assertEqual(v.history(s)["events"][-1]["kind"],"CHECK_FAILED")
    def test_corrupt_rejected(self):
        v=self.v;s=SPEC["id"];v.stage(SPEC,A);v.promote(s,sha(A),None,"REVIEW")
        v.db.execute("UPDATE object SET raw=?",(B,))
        with self.assertRaisesRegex(ValueError,"INTEGRITY"):v.read(s)
    def test_reopen(self):
        v=self.v;s=SPEC["id"];v.stage(SPEC,A);v.promote(s,sha(A),None,"REVIEW")
        v.close();self.v=Vault(self.tmp.name);self.assertEqual(self.v.read(s),A)
    def test_reject_unknown_spec(self):
        with self.assertRaisesRegex(ValueError,"UNQUALIFIED_SOURCE"):self.v.stage({**SPEC,"url":"https://example.org"},A)
