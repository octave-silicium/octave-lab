import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipeline'))
from audit_multisource import audit_csv, audit_jsonstat, read_limited, run


class SourceAuditTests(unittest.TestCase):
    def test_semicolon_csv(self):
        data=b'annee;trimestre;effectifs_salaries_brut;effectifs_salaries_cvs\n'+b'2025;1;10;10\n'*12
        r=audit_csv(data,['annee','trimestre','effectifs_salaries_brut','effectifs_salaries_cvs'])
        self.assertEqual(r['n_rows'],12)
        self.assertEqual(r['delimiter'],';')

    def test_html_rejected(self):
        class R:
            status=200; headers={}
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self,n): return b'<html>ban</html>'
        with self.assertRaisesRegex(ValueError,'HTML'):
            read_limited('https://example.org',opener=lambda *a, **kw: R())

    def test_bad_csv_missing_field(self):
        with self.assertRaisesRegex(ValueError,'MISSING_COLUMNS'):
            audit_csv(b'a,b\n'+b'1,2\n'*12,['other'])

    def test_jsonstat(self):
        d={'dimension':{'geo':{'category':{'index':{'FR':0}}},'time':{'category':{'index':{'2025':0}}}},'value':{'0':20.0}}
        r=audit_jsonstat(json.dumps(d).encode(),['geo','time'])
        self.assertEqual(r['n_nonmissing_values'],1)

    def test_no_fake_success(self):
        d={'dimension':{'geo':{}},'value':{}}
        with self.assertRaises(ValueError):audit_jsonstat(json.dumps(d).encode(),['geo','time'])

    def test_failed_fetch_is_recorded(self):
        spec=[{'id':'x','url':'https://a','publisher':'p','legal_state':'l','dependency_cluster':'d','unit_of_observation':'u','format':'csv'}]
        def bad(*args, **kwargs):raise OSError('offline')
        with unittest.mock.patch('audit_multisource.time.sleep',lambda _:None):
            r=run(spec,opener=bad)
        self.assertEqual(r['summary']['passed'],0)
        self.assertEqual(r['sources']['x']['result'],'FETCH_OR_SCHEMA_FAILED')


if __name__=='__main__':unittest.main()
