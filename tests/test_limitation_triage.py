import unittest
from tools.limitation_triage import make_queue, normalized

def candidate(i, text, suggested=()):
    return {"id": str(i), "path": "docs/test.md", "line": i, "heading": "# h",
            "verbatim": text, "suggested_families": list(suggested)}

class TriageTest(unittest.TestCase):
    def setUp(self):
        self.entries = [{"id":"LIM-D06"},{"id":"LIM-T04"}]

    def test_preserve_duplicates_and_context(self):
        rows = [candidate(1, "Droits  à vérifier", ["LIM-D06"]),
                candidate(2, "Droits à vérifier", ["LIM-T04"])]
        g = make_queue(rows, self.entries)
        self.assertEqual(len(g), 1)
        self.assertEqual(len(g[0]["members"]), 2)
        self.assertEqual(g[0]["file_suggestions"], ["LIM-D06", "LIM-T04"])
        self.assertEqual(g[0]["semantic_status"], "PENDING")

    def test_negation_and_numbers_not_merged(self):
        self.assertEqual(len(make_queue([candidate(1,"gate validé"),candidate(2,"gate non validé"),
                                         candidate(3,"gate validé 2")],self.entries)),3)

    def test_unknown_ids_and_unlinked(self):
        g = make_queue([candidate(1,"LIM-X99 reste ouvert"),
                        candidate(2,"LIM-D06 droits"),
                        candidate(3,"non validé")],self.entries)
        self.assertEqual({x["routing"] for x in g},{"UNKNOWN_EXPLICIT_ID","EXPLICIT_REFERENCE_REVIEW","UNLINKED_REVIEW"})
        self.assertTrue(all(x["semantic_status"]=="PENDING" for x in g))

    def test_duplicate_id_rejected(self):
        with self.assertRaises(ValueError):
            make_queue([candidate(1,"A"),candidate(1,"B")],self.entries)

if __name__ == "__main__":
    unittest.main()
