"""Capture exact source bytes and dossier, emit only authenticated encrypted CMS."""
import json,os,sys,io,tarfile,hashlib,tempfile,subprocess
from pathlib import Path
from .vertical_v2 import make_observations,build
from .vertical_v2b import build as eb
from .vertical_v2b2 import integrate,PIN
from .pilot_ict import retrieve
from .economic_core import canonical,digest,require
ROOT=Path(__file__).resolve().parents[1]
EXPECTED="494e22fefe8c1e2a0fc051404c569a452626551e766a6173db3ce7e01c1f28c9"
def main():
    os.umask(0o077)
    out=Path(sys.argv[1]).resolve()
    require(not out.exists() and not out.is_relative_to(ROOT),"OUTPUT_LOCATION")
    raw={}
    def capture(url):
        if url not in raw:raw[url]=retrieve(url)
        return raw[url]
    r=integrate(build(make_observations(capture)),eb(capture),json.loads(PIN.read_text()))
    require(r["sha256"]==EXPECTED,"DOSSIER_REPLAY_MISMATCH")
    require(len(raw)==9,"EXPECTED_SOURCE_COUNT")
    entries=[{"url":u,"sha256":digest(b),"bytes":len(b),"file":"raw/"+digest(b)+".bin"} for u,b in sorted(raw.items())]
    manifest={"receipt_sha256":r["sha256"],"sources":entries,"publication":"BLOCK_PUBLICATION"}
    with tempfile.TemporaryDirectory() as t:
        p=Path(t)/"bundle.tar.gz"
        with tarfile.open(p,"w:gz") as tf:
            def add(name,b):
                info=tarfile.TarInfo(name);info.size=len(b);info.mode=0o600;tf.addfile(info,io.BytesIO(b))
            add("v2b2.json",canonical(r));add("manifest.json",canonical(manifest))
            for u,b in sorted(raw.items()):add("raw/"+digest(b)+".bin",b)
        subprocess.run(["openssl","cms","-encrypt","-binary","-aes-256-gcm","-in",str(p),"-outform","DER","-out",str(out),str(ROOT/"governance/v3c_recipient.pem")],check=True,capture_output=True)
    print("V3C_SEALED "+json.dumps({"receipt_sha256":r["sha256"],"source_count":len(raw),"ciphertext_sha256":digest(out.read_bytes()),"ciphertext_bytes":out.stat().st_size,"publication":"BLOCK_PUBLICATION"}))
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("V3C_BLOCKED "+type(e).__name__,file=sys.stderr);sys.exit(1)
