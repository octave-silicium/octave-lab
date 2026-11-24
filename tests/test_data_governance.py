"""OCTAVE LAB governance controls. Standalone standard-library tests."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
from data_governance import public_use_gate, comparison_gate

class GovernanceTests(unittest.TestCase):
    def test_unknown_licence_fails_closed(self):
        self.assertEqual(public_use_gate("madeup", "paid_report", attributed=True)["decision"], "BLOCK")
    def test_internal_use(self):
        self.assertEqual(public_use_gate("DS-015_urssaf_private_sector_na88", "internal_research")["decision"], "ALLOW_INTERNAL")
    def test_public_attribution_required(self):
        self.assertEqual(public_use_gate("DS-015_urssaf_private_sector_na88", "public_chart")["decision"], "BLOCK")
    def test_public_unadapted_produced_work_conditional(self):
        self.assertEqual(public_use_gate("DS-015_urssaf_private_sector_na88", "public_chart", attributed=True)["decision"], "CONDITIONAL_PUBLIC_PRODUCED_WORK")
    def test_public_derivative_not_automatically_approved(self):
        self.assertEqual(public_use_gate("DS-015_urssaf_private_sector_na88", "paid_report", attributed=True, adapted_database=True)["decision"], "BLOCK_LEGAL_REVIEW")
    def test_public_export_requires_review(self):
        self.assertEqual(public_use_gate("DS-015_urssaf_private_sector_na88", "public_dataset_export", attributed=True)["decision"], "BLOCK_LEGAL_REVIEW")
    def test_apprentice_break(self):
        result=comparison_gate("urssaf_na88_effectifs_salaries_cvs","2022Q4","2023Q1")
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("URSSAF-APPRENTICES-2023Q1",result["events"])
    def test_homogeneous_period_not_automatically_certified(self):
        self.assertEqual(comparison_gate("urssaf_na88_effectifs_salaries_cvs","2023Q1","2024Q1")["decision"],"ALLOW_WITH_CAVEATS")
    def test_2021_method_review(self):
        self.assertEqual(comparison_gate("urssaf_na88_effectifs_salaries_brut","2020Q4","2021Q1")["decision"],"REVIEW_REQUIRED")
    def test_dpae_error_window(self):
        self.assertEqual(comparison_gate("urssaf_dpae_cdi_cdd_over_1_month","2025-02","2025-05")["decision"],"BLOCK")
    def test_future_naf_change(self):
        self.assertEqual(comparison_gate("naf_sector_series","2026Q4","2027Q1")["decision"],"BLOCK")
    def test_unknown_series_fails_closed(self):
        self.assertEqual(comparison_gate("a_new_series","2022Q1","2024Q1")["decision"],"BLOCK_UNKNOWN_SERIES")
    def test_bad_period(self):
        with self.assertRaises(ValueError):
            comparison_gate("urssaf_na88_effectifs_salaries_cvs","2023-33","2024-02")
if __name__=="__main__":
    unittest.main()
