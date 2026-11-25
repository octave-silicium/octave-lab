import unittest,json
from unittest.mock import patch
from pipeline.vertical_v12 import metadata,parse,ANCHOR
class CorrectedVintageTests(unittest.TestCase):
    def test_metadata(self):
        m={"dataset_id":"dpae-france-entiere-x-na38","metas":{"default":{"description":"30 octobre 2026 traitements correctifs secteur privé non-fonctionnaires","modified":"2026-10-30"}}}
        self.assertTrue(metadata(json.dumps(m).encode())["corrected_private_scope_notice"])
        m["metas"]["default"]["description"]="old"
        with self.assertRaisesRegex(ValueError,"CORRECTION_NOTICE"):metadata(json.dumps(m).encode())
    def test_unreviewed_vintage(self):
        with self.assertRaisesRegex(ValueError,"UNREVIEWED_VINTAGE"):parse(b"new")
    def test_national_anchor_and_complete_panel(self):
        rows=[]
        from pipeline.vertical_v12 import PERIODS,GROUPS,CONTRACTS
        for p in PERIODS:
            for g in GROUPS:
                for c in CONTRACTS:
                    rows.append({"annee":p[:4],"trimestre":p[-1],"secteur_na38":g+" test","nature_de_contrat":c,"duree_de_contrat":"Contrat de plus d'un mois","dpae_cvs":"10"})
        for c in CONTRACTS:
            rows.append({"annee":"2026","trimestre":"3","secteur_na38":"ZZ test","nature_de_contrat":c,"duree_de_contrat":"Contrat de plus d'un mois","dpae_cvs":str(ANCHOR[c]-30)})
        with patch("pipeline.vertical_v12.digest",return_value="42cd99124b1ef5f0a39afc481c42e70d5adc0fbfb535a7cb53f2653dfd41f549"),patch("pipeline.vertical_v12.read_csv",return_value=rows):
            r=parse(b"fixture");self.assertEqual(len(r["levels"]),31);self.assertEqual(len(r["comparisons"]),27)
            rows[-1]["dpae_cvs"]="0"
            with self.assertRaisesRegex(ValueError,"NATIONAL_ANCHOR_MISMATCH"):parse(b"fixture")
