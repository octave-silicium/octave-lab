import sys
import unittest
import json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pipeline'))
from pilot_ict import quarterly_urssaf, quarterly_dpae, eurostat_value, numeric, read_csv

class PilotTests(unittest.TestCase):
    def test_number(self):
        self.assertEqual(numeric('1 250,2'),1250.2)
    def test_sector_six_nonoverlap(self):
        rows=[]
        for yr,q in [(2024,4),(2025,4),(2025,2),(2026,2)]:
            for c in ['58','59','60','61','62','63']:
                rows.append({'annee':str(yr),'trimestre':str(q),'secteur_na88i':c+' Test','effectifs_salaries_cvs':'10'})
        result=quarterly_urssaf(rows)
        self.assertEqual(result['selected_periods']['2025Q4'],60)
    def test_duplicate_sector_fails(self):
        rows=[]
        for c in ['58','59','60','61','62','63']:
            rows.append({'annee':'2024','trimestre':'4','secteur_na88i':c+' Test','effectifs_salaries_cvs':'10'})
        rows.append(rows[0].copy())
        with self.assertRaises(ValueError):quarterly_urssaf(rows)
    def test_dpae_requires_both_contracts(self):
        rows=[{'annee':'2023','trimestre':'4','secteur_na38':'JZ Test','duree_de_contrat':"Contrat de plus d'un mois",'nature_de_contrat':'CDI','dpae_cvs':'100'}]
        with self.assertRaises(ValueError):quarterly_dpae(rows)
    def test_eurostat_flatten(self):
        data={'id':['geo','time'],'size':[2,2],'dimension':{'geo':{'category':{'index':{'FR':0,'DE':1}}},'time':{'category':{'index':{'2024':0,'2025':1}}}},'value':{'0':11,'1':12,'2':31,'3':32}}
        self.assertEqual(eurostat_value(data,{'geo':'FR','time':'2025'}),12)
    def test_eurostat_missing_category_blocks(self):
        data={'id':['geo'],'size':[1],'dimension':{'geo':{'category':{'index':{'FR':0}}}},'value':{'0':12}}
        with self.assertRaises(ValueError):eurostat_value(data,{'geo':'US'})
    def test_schema_fail(self):
        with self.assertRaises(ValueError): read_csv(b'foo;bar\n1;2\n',{'secteur_na88i'})
if __name__=='__main__': unittest.main()
