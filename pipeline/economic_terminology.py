"""Versioned FR presentation metadata, fail closed for unknown visible metrics."""
import json
from pathlib import Path
from .economic_core import require,digest,words

def present(result,keys):
    raw=(Path(__file__).resolve().parents[1]/"governance"/"terminology_fr_v1.json").read_bytes()
    g=json.loads(raw)
    out=[]
    for k in keys:
        require(k in g["entries"] and k in result,"UNEXPLAINED_METRIC")
        e=g["entries"][k]
        require(all(words(e.get(f)) for f in ("label","definition","unit","caution","technical_name","method_ref")),"TERMINOLOGY_FIELDS")
        out.append({"metric_id":k,"value":result[k],**e})
    return {"glossary_sha256":digest(raw),"language":"fr","items":out,"visible_notice":"Simulation conditionnelle, paramètres fictifs ; aucune mesure d'entreprise."}
