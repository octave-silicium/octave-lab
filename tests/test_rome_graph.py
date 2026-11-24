import unittest
from pipeline.rome_graph import Graph,KEYS
class RomeGraphTests(unittest.TestCase):
    def test_native_reference_and_unknown(self):
        tables={k:[] for k in KEYS}
        tables["referentiel_code_rome"]=[(2,{"code_rome":"M1203"})]
        tables["referentiel_competence"]=[(2,{"code_ogr":"1"})]
        tables["liens_rome_referentiels"]=[(2,{"code_rome":"M1203","code_ogr":"1"}),(3,{"code_rome":"M1203","code_ogr":"2"})]
        g=Graph(tables,{"sha256":"a"*64},"fixture")
        self.assertEqual(g.audit()["link_status"],{"NATIVE_REFERENCED":1,"UNRESOLVED_ITEM":1})
        self.assertEqual(g.profile("M1203")["links"][1]["references"],[])
        self.assertEqual(g.profile("M1203")["tasks"],[])

    def test_identity_and_appellation_exact_pair(self):
        tables={k:[] for k in KEYS}
        tables["referentiel_code_rome"]=[(2,{"code_rome":"M1203","code_ogr":"100"})]
        tables["referentiel_appellation"]=[(2,{"code_ogr":"200","code_rome":"M1203"}),(3,{"code_ogr":"201","code_rome":"X9999"})]
        tables["liens_rome_referentiels"]=[(2,{"code_rome":"M1203","code_ogr":"100","code_compo_bloc":"1","code_rubrique":""}),(3,{"code_rome":"M1203","code_ogr":"200","code_compo_bloc":"2","code_rubrique":""}),(4,{"code_rome":"M1203","code_ogr":"201","code_compo_bloc":"2","code_rubrique":""})]
        g=Graph(tables,{"sha256":"a"*64},"fixture")
        self.assertEqual(g.audit()["link_status"],{"NATIVE_REFERENCED":2,"UNRESOLVED_ITEM":1})
        p=g.profile("M1203")
        self.assertEqual(p["links"][0]["references"][0]["table"],"referentiel_code_rome")
        self.assertEqual(p["links"][1]["references"][0]["table"],"referentiel_appellation")
        self.assertEqual(p["links"][2]["references"],[])
