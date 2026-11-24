import json
import unittest
from dataclasses import replace
from decimal import Decimal
from pipeline import semantic_v3 as s

V="2026-11-24T06:00:00+00:00"
H="a"*64

def euro(values=None,status=None):
    ids=["geo","freq","indic_is","nace_r2","size_emp","unit","time"]
    codes=[["FR"],["A"],["E_AI_TANY"],["J"],["GE10"],["PC_ENT"],["2023","2024","2025"]]
    return json.dumps(dict(id=ids,size=[len(c) for c in codes],dimension={d:{"category":{"index":{x:i for i,x in enumerate(c)}}} for d,c in zip(ids,codes)},value={"0":25,"2":55} if values is None else values,status={"1":"u","2":"b"} if status is None else status)).encode()

def c(source="urssaf_na88",period="2024Q4",**kw):
    d=dict(source=source,period=period,dimensions=(("secteur","J"),),measure="effectifs_salaries_cvs",unit="employees",value=Decimal("42"),flag="",sha256=H,vintage=V,locator="fixture")
    d.update(kw)
    return s.Cell(**d)

class LiveContracts(unittest.TestCase):
    def test_flags_and_missing(self):
        rows,meta=s.read_euro("eurostat_nace",euro(),V)
        self.assertEqual(len(rows),3)
        self.assertEqual((rows[1].value,rows[1].flag),(None,"u"))
        self.assertEqual(rows[2].flag,"b")
        self.assertEqual(meta["absent_unflagged"],0)

    def test_sparse_absent(self):
        rows,meta=s.read_euro("eurostat_size",euro({"0":1},{}),V)
        self.assertEqual(len(rows),1)
        self.assertEqual(meta["absent_unflagged"],2)

    def test_dense(self):
        rows,_=s.read_euro("eurostat_size",euro([1,None,3],["",None,"e"]),V)
        self.assertEqual([r.value for r in rows],[Decimal(1),Decimal(3)])

    def test_wrong_offset(self):
        with self.assertRaises(ValueError):
            s.read_euro("eurostat_nace",euro({"3":2}),V)

    def test_invalid_percent(self):
        with self.assertRaises(ValueError):
            s.read_euro("eurostat_nace",euro({"0":101},{}),V)

    def test_native_dimensions(self):
        rows,_=s.read_euro("eurostat_nace",euro(),V)
        self.assertEqual(dict(rows[0].dimensions)["size_emp"],"GE10")

    def test_query_exact(self):
        rows,_=s.read_euro("eurostat_nace",euro(),V)
        idx=s.Index(rows)
        self.assertEqual(idx.query("eurostat_nace",{"geo":"FR"},limit=1)["total"],3)
        self.assertTrue(idx.query("eurostat_nace",{"geo":"FR"},limit=1)["truncated"])
        self.assertEqual(idx.query("eurostat_nace",{"geo":"DE"})["total"],0)
        with self.assertRaises(ValueError):
            idx.query("eurostat_nace",{"occupation":"J"})

    def test_duplicate(self):
        with self.assertRaises(ValueError):
            s.Index([c(),c()])

    def test_urssaf_schema(self):
        raw=("grand_secteur_d_activite;secteur_na38i;secteur_na88i;annee;trimestre;dernier_jour_du_trimestre;effectifs_salaries_brut;effectifs_salaries_cvs\n"
             "J;JC;62;2024;4;2024-12-31;100;99,5\n").encode()
        rows,meta=s.read_urssaf("urssaf_na88",raw,V)
        self.assertEqual([x.value for x in rows],[Decimal(100),Decimal("99.5")])
        self.assertEqual(meta["source_rows"],1)

    def test_breaks(self):
        self.assertEqual(s.compare(c(period="2022Q4"),c(period="2023Q1")),"BLOCK")
        a=c(source="urssaf_dpae_na38",period="2024Q4")
        self.assertEqual(s.compare(a,replace(a,period="2025Q4")),"BLOCK")
        self.assertEqual(s.compare(c(),c(period="2027Q1")),"BLOCK_CLASSIFICATION")

    def test_no_flagged_comparison(self):
        a=c()
        self.assertEqual(s.compare(a,replace(a,period="2025Q4",flag="p")),"BLOCK_MISSING_OR_FLAG_REVIEW")

    def test_euro_break(self):
        a=c(source="eurostat_nace",period="2024")
        self.assertEqual(s.compare(a,replace(a,period="2025")),"BLOCK_2025_DEFINITION_REVIEW")

    def test_no_cross_source(self):
        self.assertEqual(s.compare(c(),c(source="urssaf_dpae_na38",period="2025Q4")),"BLOCK_SEMANTIC_OR_VINTAGE")

    def test_release_block(self):
        self.assertEqual(s.publication_gate(c(),"public_chart"),"BLOCK_PUBLICATION")

if __name__=="__main__":
    unittest.main()
