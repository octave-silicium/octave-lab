import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tools.indeed_public_bundle import SOURCES,preflight,bundle

class IndeedBundleTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.out=self.root/"bundle"
        self.reg={"sources":[]};self.m={"publish_gate":"PASS_DESCRIPTIVE_ONLY: fixture",
            "license_gate":True,"no_causal_inference":True,"status":{}}
        for sid,url in SOURCES.items():
            row={"id":sid,"url":url,"license":"CC BY 4.0","public_redistribution":True,"format":"csv","required":True}
            self.reg["sources"].append(row)
            raw=b"date,index\n2026-01-01,100\n";h=hashlib.sha256(raw).hexdigest()
            name="archive/raw/20261126T000000Z/"+sid+"_"+h[:12]+".csv"
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            self.m["status"][sid]={**row,"result":"OK","sha256":h,"filename":name,"bytes":len(raw)}
        self.reg["sources"].append({"id":"restricted","public_redistribution":False})
        self.m["status"]["restricted"]={"result":"SKIPPED_LICENSE_REVIEW"}
        self.save()
    def save(self):
        for name,value in [("pipeline/sources.json",self.reg),("outputs/live/manifest.json",self.m)]:
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value))
    def test_exact_bundle(self):
        (self.root/"outputs/live/unapproved.csv").write_text("not included")
        r=bundle(self.root,self.out)
        self.assertEqual(r["files"],2)
        self.assertEqual(len(list(self.out.iterdir())),4)
        self.assertFalse(r["product_release_authorized"])
        self.assertTrue((self.out/"ATTRIBUTION.txt").is_file())
    def test_unapproved_open_source(self):
        self.reg["sources"][-1]["public_redistribution"]=True
        with self.assertRaises(ValueError):preflight(self.reg)
    def test_failed_gate(self):
        self.m["publish_gate"]="BLOCKED";self.save()
        with self.assertRaises(ValueError):bundle(self.root,self.out)
        self.assertFalse(self.out.exists())
    def test_tamper(self):
        p=self.root/self.m["status"]["indeed_fr_sector"]["filename"];p.write_bytes(b"changed")
        with self.assertRaises(ValueError):bundle(self.root,self.out)
        self.assertFalse(self.out.exists())
    def test_restricted_source(self):
        self.m["status"]["restricted"]["result"]="OK";self.save()
        with self.assertRaises(ValueError):bundle(self.root,self.out)
    def test_traversal(self):
        self.m["status"]["indeed_fr_sector"]["filename"]="../outside.csv";self.save()
        with self.assertRaises(ValueError):bundle(self.root,self.out)
    def test_symlink(self):
        p=self.root/self.m["status"]["indeed_fr_sector"]["filename"]
        q=self.root/"other.csv";p.rename(q);p.symlink_to(q)
        with self.assertRaises(ValueError):bundle(self.root,self.out)
    def test_stale_bundle(self):
        self.out.mkdir()
        with self.assertRaises(ValueError):bundle(self.root,self.out)
