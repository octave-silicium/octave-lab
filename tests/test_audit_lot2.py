import io
import sys
import json
import unittest
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pipeline'))
from audit_lot2 import profile_csv,profile_xlsx,allowed_url,inspect_one,run

DPAE_SPEC={
    'id':'DPAE_TEST','url':'https://open.urssaf.fr/api/test','documentation_url':'https://open.urssaf.fr/dataset',
    'publisher':'Urssaf','dependency_group':'URSSAF_ADMINISTRATIVE_DPAE',
    'concept':'Declarations de contrats','population':'France entiere','legal':'ODbL',
    'public_raw_archive':False,'caution':'2025 anomaly','format':'csv','minimum_rows':2}

class Lot2Tests(unittest.TestCase):
    def test_source_allowlist(self):
        self.assertTrue(allowed_url('https://open.urssaf.fr/api/a'))
        self.assertFalse(allowed_url('http://open.urssaf.fr/api/a'))
        self.assertFalse(allowed_url('https://evil.example.com/api/a'))
        self.assertFalse(allowed_url('https://open.urssaf.fr.evil.com/api/a'))
    def test_csv_valid(self):
        data=b'annee;trimestre;dpae_cvs\n2020;1;10\n2020;2;12\n'
        r=profile_csv(data,2);self.assertEqual(r['rows'],2)
    def test_csv_fails_empty(self):
        with self.assertRaises(ValueError):profile_csv(b'annee;trimestre;dpae_cvs\n',2)
    def test_csv_missing_measure_fails(self):
        with self.assertRaises(ValueError):profile_csv(b'annee;trimestre;stock\n2020;1;10\n2020;2;20',2)
    def test_xlsx_profile_valid(self):
        workbook='<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="Emploi" sheetId="1"/></sheets></workbook>'
        sheet='<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><dimension ref="A1:B2"/><sheetData><row r="1"><c r="A1"><v>1</v></c></row></sheetData></worksheet>'
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            z.writestr('[Content_Types].xml','<Types/>');z.writestr('xl/workbook.xml',workbook);z.writestr('xl/worksheets/sheet1.xml',sheet)
        r=profile_xlsx(out.getvalue(),1);self.assertEqual(r['worksheets'],1)
    def test_xlsx_reject_html(self):
        with self.assertRaises(ValueError):profile_xlsx(b'<html>Forbidden</html>',1)
    def test_pending_url_preserved(self):
        p={**DPAE_SPEC,'id':'DARES','url':None,'status':'PENDING_EXACT_DOWNLOAD_URL'}
        self.assertEqual(inspect_one(p)['result'],'PENDING_EXACT_DOWNLOAD_URL')
    def test_download_is_not_economic_join(self):
        def fetcher(url):return b'annee;trimestre;dpae_cvs\n2020;1;10\n2020;2;12\n', {'content_type':'text/csv'}
        r=inspect_one(DPAE_SPEC,fetcher);self.assertEqual(r['result'],'FETCH_AND_STRUCTURE_PASS');self.assertFalse(r['economic_join_ready'])
    def test_fail_closed(self):
        def fetcher(url):raise ValueError('HTML_INSTEAD_OF_DATA')
        r=inspect_one(DPAE_SPEC,fetcher);self.assertEqual(r['result'],'FETCH_OR_STRUCTURE_FAILED')
    def test_summary(self):
        def fetcher(url):return b'annee;trimestre;dpae_cvs\n2020;1;10\n2020;2;12\n', {'content_type':'text/csv'}
        r=run([DPAE_SPEC],fetcher);self.assertEqual(r['summary']['passed'],1);self.assertEqual(r['summary']['ready_for_economic_join'],0)
if __name__=='__main__':unittest.main()
