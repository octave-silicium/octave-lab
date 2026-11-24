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
