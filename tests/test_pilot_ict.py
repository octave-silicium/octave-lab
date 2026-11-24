import sys
import unittest
import json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pipeline'))
from pilot_ict import quarterly_urssaf, quarterly_dpae, eurostat_value, eurostat_flag, eurostat_ict, numeric, read_csv

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
        rows=[{'annee':'2023','trimestre':'4','secteur_na38':'JC Activités informatiques','duree_de_contrat':"Contrat de plus d'un mois",'nature_de_contrat':'CDI','dpae_cvs':'100'}]
        with self.assertRaises(ValueError):quarterly_dpae(rows)
    def test_dpae_three_components_six_contract_cells(self):
        rows=[]
        for year in [2023,2024]:
            for code in ['JA','JB','JC']:
                for nature in ['CDI',"CDD de plus d'un mois"]:
                    rows.append({'annee':str(year),'trimestre':'4',
                        'secteur_na38':code+' Test',
                        'duree_de_contrat':"Contrat de plus d'un mois",
                        'nature_de_contrat':nature,'dpae_cvs':'10'})
        r=quarterly_dpae(rows)
        self.assertEqual(r['selected_periods']['2023Q4'],60)
        self.assertEqual(r['subsector_decomposition']['2024Q4'],{'JA':20,'JB':20,'JC':20})
    def test_eurostat_flatten(self):
        data={'id':['geo','time'],'size':[2,2],'dimension':{'geo':{'category':{'index':{'FR':0,'DE':1}}},'time':{'category':{'index':{'2024':0,'2025':1}}}},'value':{'0':11,'1':12,'2':31,'3':32}}
        self.assertEqual(eurostat_value(data,{'geo':'FR','time':'2025'}),12)
    def test_eurostat_missing_category_blocks(self):
        data={'id':['geo'],'size':[1],'dimension':{'geo':{'category':{'index':{'FR':0}}}},'value':{'0':12}}
        with self.assertRaises(ValueError):eurostat_value(data,{'geo':'US'})
    def test_eurostat_status_exact(self):
        data={'id':['geo','time'],'size':[1,2],'dimension':{'geo':{'category':{'index':{'FR':0}}},'time':{'category':{'index':{'2023':0,'2024':1}}}},'status':{'0':'b'}}
        self.assertEqual(eurostat_flag(data,{'geo':'FR','time':'2023'}),'b')
        self.assertEqual(eurostat_flag(data,{'geo':'FR','time':'2024'}),'')
    def test_eurostat_pilot_blocks_unqualified_change(self):
        codes={'geo':['FR'],'nace_r2':['J'],'indic_is':['E_AI_TANY'],'unit':['PC_ENT'],'size_emp':['GE10'],'freq':['A'],'time':['2023','2024','2025']}
        data={'id':list(codes),'size':[len(v) for v in codes.values()],'dimension':{k:{'category':{'index':{c:i for i,c in enumerate(v)}}} for k,v in codes.items()},'value':{'0':25,'1':40,'2':55},'status':{'0':'b'}}
        result=eurostat_ict(json.dumps(data).encode())
        self.assertEqual(result['source_flags']['2023'],'b')
        self.assertIsNone(result['change_2024_vs_2023_pp'])
        data['status']['1']='u'
        with self.assertRaises(ValueError):eurostat_ict(json.dumps(data).encode())
    def test_schema_fail(self):
        with self.assertRaises(ValueError): read_csv(b'foo;bar\n1;2\n',{'secteur_na88i'})
if __name__=='__main__': unittest.main()
