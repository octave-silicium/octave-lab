import unittest
from pipeline.native_revisions import compare
from test_semantic_v3 import euro
class NativeRevisionTests(unittest.TestCase):
    def test_eurostat_masks_and_flags(self):
        a=euro({"0":25,"2":55},{"1":"u","2":"b"})
        b=euro({"0":26,"1":20,"2":60},{"1":"u","2":"b"})
        r=compare("eurostat_nace",a,b)
        self.assertEqual(r["visible_value_changed"],2)
        self.assertEqual(r["numeric_comparison_withheld"],1)
        self.assertEqual(r["quality_changed"],1)
        self.assertEqual(r["publication"],"BLOCK_PUBLICATION")
    def test_urssaf_native_keys(self):
        a=("grand_secteur_d_activite;secteur_na38i;secteur_na88i;annee;trimestre;dernier_jour_du_trimestre;effectifs_salaries_brut;effectifs_salaries_cvs\nJ;JC;62;2024;4;2024-12-31;100;99,5\n").encode()
        b=a.replace(b";100;99,5",b";101;99,5")
        r=compare("urssaf_na88",a,b)
        self.assertEqual((r["shared"],r["visible_value_changed"],r["visible_value_unchanged"]),(2,1,1))
    def test_sparse_add_remove(self):
        r=compare("eurostat_size",euro({"0":25},{ }),euro({"1":30},{}))
        self.assertEqual((r["added"],r["removed"],r["shared"]),(1,1,0))
