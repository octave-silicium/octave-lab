import io
import sys
import unittest
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from ingest_insee import extract,MAIN_SECTORS

# Generate a miniature but semantically authentic Insee-wide spreadsheet.
LABELS=['Agriculture','Industrie','   dont industrie manufacturière','Construction',
        'Tertiaire marchand','   dont intérim1','Tertiaire non marchand','Ensemble','Secteur privé','Fonction publique']


def src(n=42,corrupt_qoq=False,corrupt_unit=False):
    from xml.sax.saxutils import escape
    def cell(col,row,value):
        letters='';number=col
        while number:number,rem=divmod(number-1,26);letters=chr(65+rem)+letters
        if isinstance(value,str):return f'<c r="{letters}{row}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
        return f'<c r="{letters}{row}"><v>{value}</v></c>'
    rows={r:[] for r in [3,4,5]+list(range(6,16))+[17,19]}
    rows[3].append(cell(1,3,'en millions' if corrupt_unit else 'en milliers'))
    rows[17].append(cell(1,17,'Note : données révisées ; données corrigées des variations saisonnières en fin de trimestre.'))
    rows[19].append(cell(1,19,'Champ : France hors Mayotte, personnes de 15 ans ou plus.'))
    vals=[200.0,2000.0,1200.0,900.0,8200.0,450.0,6000.0,17300.0,12000.0,5300.0]
    slopes=[1,1,1,1,1,1,1,5,3,2]
    for i,label in enumerate(LABELS):rows[i+6].append(cell(1,i+6,label))
    for q in range(n):
        year=2014+q//4;quarter=q%4+1;col=2+3*q
        rows[4].append(cell(col,4,f'{year}-T{quarter}'))
        for off,h in enumerate(['Évolution sur trois mois','Évolution sur un an','Emploi salarié']):
            rows[5].append(cell(col+off,5,h))
        for i,label in enumerate(LABELS):
            current=vals[i]+slopes[i]*q
            qoq=slopes[i]
            if corrupt_qoq and q==5 and i==0:qoq=12345
            yoy=slopes[i]*4
            rows[i+6].extend([cell(col,i+6,qoq),cell(col+1,i+6,yoy),cell(col+2,i+6,current)])
    xml='<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
    xml+=''.join(f'<row r="{r}">{"".join(items)}</row>' for r,items in rows.items())+'</sheetData></worksheet>'
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:z.writestr('xl/worksheets/sheet1.xml',xml)
    return out.getvalue()

class InseeNormalization(unittest.TestCase):
    def test_unit_must_be_stated_in_workbook(self):
        with self.assertRaises(ValueError):extract(src(corrupt_unit=True))
    def test_wide_table_is_reconstructed(self):
        rows,stats=extract(src(),strict_anchor=False)
        self.assertEqual(len(rows),420)
        self.assertEqual(stats['quarter_count'],42)
        self.assertEqual(stats['sector_count'],10)
        self.assertFalse(stats['economic_join_with_NA38'])
    def test_violations_block_publication(self):
        rows,stats=extract(src(corrupt_qoq=True),strict_anchor=False)
        self.assertEqual(stats['publication_gate'],'BLOCKED_ARITHMETIC_INCONSISTENCY')
    def test_unknown_latest_vintage_blocks(self):
        rows,stats=extract(src(),strict_anchor=True)
        self.assertEqual(stats['publication_gate'],'BLOCKED_HISTORIC_VINTAGE_REVIEW')

if __name__=='__main__':unittest.main()
