import io
import os
import sys
import unittest
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from semantic_audit import col_index,insee_profile,source_dpae_profile,discover_mmo,allowed

class AuditSemantics(unittest.TestCase):
    def test_excel_column(self):
        self.assertEqual(col_index('AMJ1'),1024)
        self.assertEqual(col_index('AA3'),27)
    def test_reject_nonworkbook(self):
        with self.assertRaises(ValueError):insee_profile(b'<html />')
    def test_sample_inline_and_numeric_workbook(self):
        wb=io.BytesIO()
        sheet=('<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
            '<row r="1"><c r="A1" t="inlineStr"><is><t>En milliers</t></is></c><c r="B1" t="inlineStr"><is><t>T2 2026</t></is></c></row>'
            '<row r="2"><c r="A2" t="inlineStr"><is><t>Ensemble</t></is></c><c r="B2"><v>27021.1</v></c></row>'
            '</sheetData></worksheet>')
        with zipfile.ZipFile(wb,'w') as z:
            z.writestr('xl/worksheets/sheet1.xml',sheet)
        p=insee_profile(wb.getvalue())
        self.assertEqual(p['sheets'][0]['physical_rows'],2)
        self.assertEqual(p['sheets'][0]['numeric_cells'],1)
        self.assertTrue(any('milliers' in x.lower() for x in p['sheets'][0]['unit_and_definition_clues']))
    def test_dpae_periods_flags_vintage(self):
        rows=['annee;dernier_jour_du_mois;nature_de_contrat;duree_de_contrat;dpae_brut;dpae_cvs']
        rows += [f'2025;2025-{m:02d}-30;CDI;Contrat de plus d\'un mois;{100+i};{100+i}' for i,m in enumerate([4,5,6,7,8,9]*20)]
        data=('\n'.join(rows)+'\n').encode()
        p=source_dpae_profile(data,'dernier_jour_du_mois',['nature_de_contrat','duree_de_contrat'],'2025-04','2025-09')
        self.assertEqual(p['total_rows'],120)
        self.assertEqual(len(p['historically_flagged_periods']),6)
        self.assertTrue(p['first_vintage_for_this_source'])
        q=source_dpae_profile(data,'dernier_jour_du_mois',['nature_de_contrat','duree_de_contrat'],'2025-04','2025-09',p)
        self.assertFalse(q['first_vintage_for_this_source'])
        self.assertFalse(q['changed_periods_against_previous_vintage'])
    def test_dpae_malformed(self):
        with self.assertRaises(ValueError):
            source_dpae_profile(b'dpae_brut;dpae_cvs\n1;2\n','dernier_jour_du_mois',['nature_de_contrat'],'2025-04','2025-09')
    def test_mmo_official_link(self):
        url='https://dares.travail-emploi.gouv.fr/donnees/les-mouvements-de-main-doeuvre'
        page=b'<a href="/sites/default/files/mmo-trimestriel.xlsx">Donnees trimestrielles - Mouvements de main-doeuvre</a>'
        r=discover_mmo(page,url)
        self.assertEqual(r['result'],'OFFICIAL_XLSX_CANDIDATES_NOT_DOWNLOADED')
    def test_no_guessed_url(self):
        self.assertEqual(discover_mmo(b'<a href="https://evil.com/fake.xlsx">MMO</a>','https://dares.travail-emploi.gouv.fr/a')['result'],'PENDING_EXACT_OFFICIAL_XLSX_LINK')
    def test_antibot_not_bypassed(self):
        self.assertEqual(discover_mmo('Vérification de sécurité captcha'.encode(),'https://dares.travail-emploi.gouv.fr/a')['result'],'BLOCKED_OFFICIAL_SITE_ANTIBOT')
    def test_hosts(self):
        self.assertTrue(allowed('https://www.insee.fr/x',{'www.insee.fr'}))
        self.assertFalse(allowed('http://www.insee.fr/x',{'www.insee.fr'}))
        self.assertFalse(allowed('https://www.insee.fr.evil.com/x',{'www.insee.fr'}))

if __name__=='__main__':unittest.main()
