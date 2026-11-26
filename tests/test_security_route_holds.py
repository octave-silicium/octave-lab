"""Ensure the candidate quarantine workflows cannot execute the old data jobs."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
class RouteHoldTest(unittest.TestCase):
    def test_five_quarantined_routes_are_read_only_and_fail_closed(self):
        reg=json.loads((ROOT/"governance/security_write_routes_v1.json").read_text())
        rows=[x for x in reg["flows"] if x["decision"]=="QUARANTINE_CANDIDATE_STAGED"]
        self.assertEqual(len(rows),5)
        self.assertFalse(reg["publication_authorized"])
        for row in rows:
            with self.subTest(row=row["workflow"]):
                s=(ROOT/".github/workflows"/row["workflow"]).read_text()
                self.assertIn("contents: read",s)
                self.assertNotIn("contents: write",s)
                self.assertNotIn("git push",s)
                self.assertNotIn("uses:",s)
                self.assertNotIn("python ",s)
                self.assertIn("exit 1",s)
                self.assertIn("qualification-hold:",s)
                self.assertFalse(row["live_collection"])
    def test_indeed_is_separate(self):
        s=(ROOT/".github/workflows/collect-public-sector.yml").read_text()
        self.assertIn("indeed_public_bundle",s)
        self.assertNotIn("git push",s)
        self.assertIn("contents: read",s)
