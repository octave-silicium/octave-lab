import unittest,io,zipfile,tempfile
from pathlib import Path
from decimal import Decimal
from dataclasses import replace
from pipeline.european_work import EscoGraph,import_esco,digest,access_audit
from pipeline.work_actions import Action,Status,Modality,Evidence,Crosswalk
O="http://data.europa.eu/esco/occupation/11111111-1111-1111-1111-111111111111"
S="http://data.europa.eu/esco/skill/22222222-2222-2222-2222-222222222222"
def files():
    return {"occupations_fr":f"conceptUri,preferredLabel\n{O},Métier fictif\n".encode(),"skills_fr":f"conceptUri,preferredLabel,skillType\n{S},Compétence fictive,skill/competence\n".encode(),"occupationSkillRelations":f"occupationUri,skillUri,relationType\n{O},{S},essential\n".encode()}
class EuropeanTests(unittest.TestCase):
    def test_native_not_task(self):
        g=EscoGraph(files(),{});p=g.profile(O)
        self.assertEqual(len(p["skills"]),1);self.assertEqual(p["tasks"],[]);self.assertEqual(p["crosswalks"],[])
    def test_dangling(self):
        f=files();f["occupationSkillRelations"]=f["occupationSkillRelations"].replace(b"22222222",b"33333333")
        with self.assertRaisesRegex(ValueError,"DANGLING"):EscoGraph(f,{})
    def test_zip_integrity(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,"w") as z:
            for k,v in files().items():z.writestr(k+".csv",v)
        raw=b.getvalue()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"test.zip";p.write_bytes(raw)
            self.assertEqual(import_esco(p,digest(raw)).audit()["edges"],1)
            with self.assertRaisesRegex(ValueError,"INTEGRITY"):import_esco(p,"0"*64)
    def test_access_failure(self):
        def fail(*a):raise OSError("fixture")
        d=access_audit(fail);self.assertEqual(d["rome"]["status"],"BLOCKED");self.assertEqual(d["esco"]["api_probe"]["status"],"UNAVAILABLE")
class ActionTests(unittest.TestCase):
    def setUp(self):
        self.e=Evidence("fixture","row 1","a"*64,"REFERENCE")
        self.a=Action("octave:action:fixture",1,("fixture:task:1",),"Inspecter","document","contexte fictif",("document",),("contrôle",),("critère",),Modality.DIGITAL,(),(self.e,))
    def test_no_inferred_scores(self):
        self.assertIsNone(self.a.readiness()["automation_score"])
        self.assertIsNone(self.a.duration_seconds)
    def test_review_gate(self):
        with self.assertRaisesRegex(ValueError,"REVIEW_REQUIRED"):replace(self.a,status=Status.EXPERT_REVIEWED)
        with self.assertRaisesRegex(ValueError,"OBSERVATION_REQUIRED"):replace(self.a,status=Status.OBSERVED)
    def test_duration_gate(self):
        with self.assertRaisesRegex(ValueError,"DURATION_EVIDENCE"):replace(self.a,duration_seconds=Decimal(12))
        e=Evidence("fixture","run 1","b"*64,"MEASUREMENT")
        self.assertTrue(replace(self.a,duration_seconds=Decimal(12),duration_evidence=e).readiness()["duration_known"])
    def test_mapping_review(self):
        with self.assertRaisesRegex(ValueError,"REVIEW_REQUIRED"):Crosswalk("onet:a","esco:b","EXACT",self.e,status="EXPERT_REVIEWED")
