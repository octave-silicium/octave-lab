"""Regressions on legal and historical controls for lot 2 source series."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'pipeline'))
from data_governance import public_use_gate, comparison_gate

class Lot2Governance(unittest.TestCase):
    def test_na38_odbl_requires_attribution(self):
        self.assertEqual(public_use_gate('URSSAF_DPAE_NA38_QUARTERLY','public_chart')['decision'], 'BLOCK')
    def test_monthly_odbl_public_derived_requires_review(self):
        self.assertEqual(public_use_gate('URSSAF_DPAE_MONTHLY_NATIONAL','paid_report',attributed=True,adapted_database=True)['decision'],'BLOCK_LEGAL_REVIEW')
    def test_na38_april_2025_risk_blocked(self):
        self.assertEqual(comparison_gate('urssaf_dpae_na38_quarterly','2025Q1','2025Q3')['decision'], 'BLOCK')
    def test_monthly_april_2025_risk_blocked(self):
        self.assertEqual(comparison_gate('urssaf_dpae_monthly_over_1_month','2025-02','2025-04')['decision'], 'BLOCK')
    def test_mmo_revision_requires_review(self):
        self.assertEqual(comparison_gate('dares_mmo_hirings_quarterly','2022Q4','2023Q1')['decision'],'REVIEW_REQUIRED')

if __name__=='__main__': unittest.main()
