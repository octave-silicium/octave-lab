"""Structural tests for engineering assurance register; not a release gate."""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "governance" / "engineering_assurance_v1.json"
REQUIRED = ["AUD-01","AUD-02","SEC-01","SEC-02","SEC-03","REL-01","ARC-01","ARC-02","QA-01","QA-02","QA-03","QA-04","DEV-01","DEV-02","DEV-03","PROD-01","PROD-02","COST-01","AI-01","AI-02","EVO-01","EVO-02","DATA-01","DATA-02","GOV-01"]

class EngineeringAssuranceTest(unittest.TestCase):
    def setUp(self):
        self.register = json.loads(PATH.read_text(encoding="utf-8"))

    def test_coverage_and_unique_ids(self):
        ids = [r["id"] for r in self.register["requirements"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(set(REQUIRED).issubset(ids))

    def test_traceability_and_evidence(self):
        for r in self.register["requirements"]:
            for field in ("source_ref", "requirement", "acceptance", "owner_ref"):
                self.assertTrue(r[field].strip(), (r["id"], field))
            self.assertIn(r["status"], {"OPEN", "PARTIAL", "BLOCKED", "VERIFIED"})
            self.assertIsInstance(r["evidence"], list)
            if r["status"] == "VERIFIED":
                self.assertTrue(r["evidence"], r["id"])

    def test_no_implicit_release(self):
        self.assertIs(self.register["publication_authorized"], False)
        self.assertIs(self.register["existing_gates_unchanged"], True)

if __name__ == "__main__":
    unittest.main()
