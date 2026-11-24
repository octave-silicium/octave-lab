import gzip
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pipeline'))
from archive_dares import write_archive

class DaresArchiveTests(unittest.TestCase):
    def test_lossless_gzip_roundtrip(self):
        raw=b'Date;Nombre d\'offres d\'emploi\n'+b'2025-01;100\n'*12
        sha=hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            name,found=write_archive(raw,sha,Path(tmp)/'arch')
            self.assertEqual(sha,found)
            with gzip.open(Path(tmp)/'arch'/name,'rb') as f:
                self.assertEqual(f.read(),raw)
    def test_modified_bytes_rejected(self):
        raw=b'Date;Nombre d\'offres d\'emploi\n'+b'2025-01;100\n'*12
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'SOURCE_VERSION_CHANGED'):
                write_archive(raw,'0'*64,Path(tmp)/'arch')

if __name__=='__main__':unittest.main()
