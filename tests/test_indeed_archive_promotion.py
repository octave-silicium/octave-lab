"""Offline regression using the already public, pinned November snapshot.
Never writes repository data, never uses network, never uploads source bytes."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from tools.indeed_public_bundle import bundle
from tools.indeed_archive_promotion import promote,inspect_candidate
from pipeline.semantic_v2 import iter_indeed

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/"snapshots/indeed-fr/2026-11"

class ArchiveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.root=Path(cls.tmp.name)
        cls.manifest=json.loads((OLD/"manifest.json").read_text())
        (cls.root/"pipeline").mkdir()
        shutil.copyfile(ROOT/"pipeline/sources.json",cls.root/"pipeline/sources.json")
        (cls.root/"outputs/live").mkdir(parents=True)
        (cls.root/"outputs/live/manifest.json").write_text(json.dumps(cls.manifest))
        for sid in ("indeed_fr_sector","indeed_fr_national"):
            p=cls.root/cls.manifest["status"][sid]["filename"]
            p.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(OLD/p.name,p)
        cls.candidate=cls.root/"candidate"
        bundle(cls.root,cls.candidate)
        cls.approved=hashlib.sha256((cls.candidate/"manifest.json").read_bytes()).hexdigest()
        cls.result=promote(cls.root,cls.candidate,cls.approved)

    def test_offline_restore_and_existing_reader(self):
        self.assertEqual(self.result["decision"],"LOCAL_SNAPSHOT_PREPARED")
        expected=sum(1 for _ in iter_indeed(ROOT))
        self.assertGreater(expected,0)
        self.assertEqual(sum(1 for _ in iter_indeed(self.root)),expected)
        new=json.loads((self.root/"snapshots/indeed-fr/2026-11/manifest.json").read_text())
        for sid in ("indeed_fr_sector","indeed_fr_national"):
            for key in ("sha256","bytes","rows","columns","downloaded_at"):
                self.assertEqual(new["status"][sid][key],self.manifest["status"][sid][key])
        self.assertEqual(new["status"]["indeed_fr_sector"]["analysis"],self.manifest["status"]["indeed_fr_sector"]["analysis"])

    def test_idempotent_and_legacy_snapshot(self):
        self.assertEqual(promote(self.root,self.candidate,self.approved)["decision"],"ALREADY_ARCHIVED")
        # Existing legacy repository snapshot can be recognized without overwriting.
        # Use a temp checkout rather than touching the real one.
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp)
            shutil.copytree(OLD,r/"snapshots/indeed-fr/2026-11")
            self.assertEqual(promote(r,self.candidate,self.approved)["decision"],"ALREADY_ARCHIVED")

    def test_unreviewed_digest(self):
        with self.assertRaises(ValueError):inspect_candidate(self.candidate,"0"*64)

    def test_extra_file(self):
        extra=self.candidate/"unexpected.txt";extra.write_text("fixture")
        try:
            with self.assertRaises(ValueError):inspect_candidate(self.candidate,self.approved)
        finally:extra.unlink()

    def test_conflict_and_existing_preserved(self):
        target=self.root/"snapshots/indeed-fr/2026-11/manifest.json"
        old=target.read_bytes()
        try:
            m=json.loads(old);m["status"]["indeed_fr_sector"]["sha256"]="0"*64
            target.write_text(json.dumps(m))
            before=target.read_bytes()
            with self.assertRaises(ValueError):promote(self.root,self.candidate,self.approved)
            self.assertEqual(target.read_bytes(),before)
        finally:target.write_bytes(old)

    def test_lock(self):
        lock=self.root/"snapshots/indeed-fr/.2026-11.lock";lock.mkdir()
        try:
            with self.assertRaises(FileExistsError):promote(self.root,self.candidate,self.approved)
        finally:lock.rmdir()
