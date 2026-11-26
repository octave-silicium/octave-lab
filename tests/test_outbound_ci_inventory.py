import unittest
from tools.outbound_ci_inventory import inspect

class OutboundInventoryTest(unittest.TestCase):
    def test_literal_and_multiline_paths(self):
        u,i=inspect("      - name: upload\n        if: always()\n        uses: actions/upload-artifact@v4\n        with:\n          path: |\n            a/\n            b.json\n          retention-days: 30\n      - run: something\n")
        self.assertEqual(u[0]["paths"],["a/","b.json"])
        self.assertTrue(u[0]["directory_or_glob_indicator"])
        self.assertTrue(u[0]["always_indicator"])
        self.assertEqual(u[0]["retention_days_literal"],30)
    def test_dynamic_and_single(self):
        u,i=inspect("      - uses: actions/upload-artifact@v4\n        with:\n          path: \${{ runner.temp }}/one.json\n")
        self.assertTrue(u[0]["dynamic_indicator"])
        self.assertIsNone(u[0]["retention_days_literal"])
    def test_missing_path_remains_unknown(self):
        u,_=inspect("      - uses: actions/upload-artifact@v4\n        with:\n          name: x\n      - run: anything\n")
        self.assertEqual(u[0]["path_parse_status"],"UNRESOLVED")
    def test_install_is_not_lock(self):
        _,i=inspect("      - run: python -m pip install numpy==2.2.6 openpyxl==3.1.5\n      - run: python -m playwright install --with-deps chromium")
        self.assertEqual(i[0]["direct_exact_versions"],["numpy==2.2.6","openpyxl==3.1.5"])
        self.assertFalse(i[0]["hash_required_indicator"])
        self.assertTrue(i[1]["browser_or_os_install_indicator"])
    def test_no_raw_install_command_returned(self):
        _,i=inspect("      - run: pip install pkg==1.0 --index-url https://invalid.example/private")
        self.assertNotIn("invalid.example",str(i))
