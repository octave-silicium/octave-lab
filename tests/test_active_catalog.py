import tempfile,unittest
from pathlib import Path
from pipeline.data_vault import Vault,sha
from pipeline.data_observatory import read_registry
from pipeline.active_catalog import VaultExplorer
SPEC=next(s for s in read_registry() if s["id"]=="indeed_national_total_daily")
S=SPEC["id"]
A=b"date,jobcountry,variable,indeed_job_postings_index_SA\n2026-01-01,FR,total postings,100\n"
B=A+b"2026-01-02,FR,total postings,101\n"
class ActiveTests(unittest.TestCase):
    def test_session_pin_no_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            v=Vault(Path(d)/"vault")
            try:
                v.stage(SPEC,A)
                with self.assertRaisesRegex(ValueError,"NO_APPROVED"):VaultExplorer(Path(d)/"vault")
                v.promote(S,sha(A),None,"FIXTURE")
                x=VaultExplorer(Path(d)/"vault")
                self.assertEqual(len(x.sources()),1)
                v.stage(SPEC,B);v.promote(S,sha(B),sha(A),"FIXTURE")
                # Load lazily after promotion, but still read the original pinned version.
                g=x.discover(S,{})["series"][0]
                self.assertEqual(x.detail(S,g["id"])["total"],1)
                self.assertEqual(x.detail(S,g["id"])["snapshot_sha256"],sha(A))
                y=VaultExplorer(Path(d)/"vault")
                self.assertEqual(y.detail(S,g["id"])["total"],2)
                self.assertEqual(y.restore(S,g["id"],sha(A))["decision"],"VINTAGE_MISMATCH")
                self.assertEqual(x.restore(S,g["id"],sha(A))["decision"],"MATCH")
                with self.assertRaises(ValueError):x.discover("insee_employment",{})
            finally:v.close()
    def test_corrupted_object_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            v=Vault(Path(d)/"vault")
            try:
                v.stage(SPEC,A);v.promote(S,sha(A),None,"FIXTURE")
                x=VaultExplorer(Path(d)/"vault")
                v.db.execute("UPDATE object SET raw=?",(B,))
                with self.assertRaisesRegex(ValueError,"INTEGRITY"):x.discover(S,{})
            finally:v.close()
