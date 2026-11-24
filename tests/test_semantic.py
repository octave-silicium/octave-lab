import unittest
from dataclasses import replace
from decimal import Decimal
from pipeline.semantic import Observation, compare, release, validate_unique, read_insee, read_pilot, audit

H = 'a' * 64
V = '2026-11-24T05:23:22+00:00'


def obs(series='urssaf_na88_effectifs_salaries_cvs', period='2024Q4', method='v1', **kwargs):
    values = dict(series=series, sector='J', category_kind='SECTION', period=period, value=Decimal('42'), vintage=V, sha256=H, source_url='https://example.org/data', locator='fixture:1', method_vintage=method)
    values.update(kwargs)
    return Observation(**values)


class SemanticTests(unittest.TestCase):
    def test_invalid_numeric(self):
        for v in (Decimal('NaN'), Decimal('Infinity'), Decimal('-1'), 42):
            with self.subTest(v=v), self.assertRaises(ValueError):
                obs(value=v)

    def test_unknown_series(self):
        with self.assertRaises(ValueError):
            obs(series='unknown')

    def test_invalid_period(self):
        with self.assertRaises(ValueError):
            obs(period='2024Q5')

    def test_invalid_percent(self):
        with self.assertRaises(ValueError):
            obs(series='eurostat_ai_tany', period='2024', value=Decimal('101'))

    def test_invalid_provenance(self):
        for changes in ({'sha256':'bad'}, {'vintage':'2026-11-24'}, {'source_url':'http://example.org'}, {'locator':''}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                obs(**changes)

    def test_duplicate(self):
        a = obs()
        with self.assertRaises(ValueError):
            validate_unique([a, replace(a, sha256='b'*64)])

    def test_cross_measure_block(self):
        self.assertEqual(compare(obs(), obs(series='urssaf_dpae_na38_quarterly', period='2025Q4'))['reason'], 'SEMANTIC_MISMATCH')

    def test_cross_vintage_block(self):
        self.assertEqual(compare(obs(), obs(period='2025Q4', sha256='b'*64))['reason'], 'VINTAGE_MISMATCH')

    def test_order_block(self):
        self.assertEqual(compare(obs(), obs(period='2023Q4'))['reason'], 'PERIOD_ORDER')

    def test_method_break(self):
        a = obs(series='eurostat_ai_tany', period='2024')
        b = obs(series='eurostat_ai_tany', period='2025', method='expanded')
        self.assertEqual(compare(a, b)['reason'], 'METHOD_BREAK')

    def test_eurostat_review(self):
        self.assertEqual(compare(obs(series='eurostat_ai_tany', period='2023'), obs(series='eurostat_ai_tany', period='2024'))['decision'], 'REVIEW_REQUIRED')

    def test_urssaf_break(self):
        self.assertEqual(compare(obs(period='2022Q4'), obs(period='2023Q1'))['decision'], 'BLOCK')

    def test_dpae_break(self):
        s = 'urssaf_dpae_na38_quarterly'
        self.assertEqual(compare(obs(series=s, period='2024Q4'), obs(series=s, period='2025Q4'))['decision'], 'BLOCK')

    def test_urssaf_compatible(self):
        self.assertEqual(compare(obs(), obs(period='2025Q4'))['decision'], 'ALLOW_WITH_CAVEATS')

    def test_release_unknown(self):
        self.assertEqual(release(obs(series='eurostat_ai_tany', period='2024'), 'public_chart', attributed=True, adapted_database=False)['decision'], 'BLOCK_LEGAL_REVIEW')

    def test_release_adaptation_unknown_or_true(self):
        for adapted in (None, True):
            self.assertEqual(release(obs(), 'paid_report', attributed=True, adapted_database=adapted)['decision'], 'BLOCK_LEGAL_REVIEW')

    def test_release_urssaf_internal(self):
        self.assertEqual(release(obs(), 'internal_research')['decision'], 'ALLOW_INTERNAL')

    def test_release_urssaf_export(self):
        self.assertEqual(release(obs(), 'public_dataset_export', attributed=True, adapted_database=False)['decision'], 'BLOCK_LEGAL_REVIEW')

    def test_repo_adapters(self):
        a, b = read_insee(), read_pilot()
        self.assertTrue(a and b)
        self.assertTrue(all(o.evidence == 'DESCRIPTIVE_ONLY' for o in a+b))
        self.assertEqual(audit()['total'], len(a)+len(b))
        self.assertEqual(len({o.series for o in a+b}), 4)
        self.assertFalse(audit()['cross_source_join_permitted'])

if __name__ == '__main__':
    unittest.main()
