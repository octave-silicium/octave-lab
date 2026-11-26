import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("repository_inventory", Path(__file__).resolve().parents[1] / "tools" / "repository_inventory.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

class RepositoryInventoryTest(unittest.TestCase):
    def test_json_duplicates_and_invalid_constant(self):
        self.assertEqual(audit.json_no_duplicates(b'{"a":1,"a":2}'), 1)
        self.assertEqual(audit.json_no_duplicates(b'{"a":1,"b":{"a":2}}'), 0)
        with self.assertRaises(ValueError):
            audit.json_no_duplicates(b'{"a":NaN}')

    def test_links(self):
        self.assertEqual(list(audit.local_links("[x](foo.md#part) [y](https://example.org) [z](#anchor) [w](foo%20bar.md)")), ["foo.md", "foo bar.md"])

    def test_workflow_indicators(self):
        flags = audit.workflow_flags("permissions:\n  contents: write\n- uses: actions/checkout@v4\n- uses: owner/action@" + "a"*40 + "\n- uses: ./local\nrun: git push origin HEAD:main")
        self.assertEqual(flags["external_uses"], 2)
        self.assertEqual(flags["unpinned_uses"], 1)
        self.assertTrue(flags["write_permission_indicator"])
        self.assertTrue(flags["push_main_indicator"])
        self.assertFalse(audit.workflow_flags("permissions:\n  contents: read\n")["write_permission_indicator"])

if __name__ == "__main__":
    unittest.main()
