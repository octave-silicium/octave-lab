"""Internal investigation manifest; coverage and receipts are rechecked on replay."""
from dataclasses import dataclass,asdict
from .economic_core import require,words,texts,identity,digest,canonical,validate_coverage
from .economic_calculations import calculate
from .economic_paths import trace

@dataclass(frozen=True)
class Investigation:
    id:str
    revision:int
    question:str
    decision:str
    alternatives:tuple
    loss_function:str
    exclusions:str
    graph_sha256:str
    model_sha256:str
    @property
    def key(self):return identity(self.id,self.revision)

def assemble(inv,graph,coverage,calculations=(),scenario_paths=()):
    inv.key
    require(all(words(x) for x in (inv.question,inv.decision,inv.loss_function,inv.exclusions)) and texts(inv.alternatives) and len(inv.alternatives)>=2,"MANDATE")
    from .economic_core import sha
    require(sha(inv.model_sha256) and inv.graph_sha256==graph.fingerprint,"INVESTIGATION_PIN")
    audit=validate_coverage(graph,coverage)
    receipts=[calculate(graph,c) for c in calculations]
    outputs=[r["output_claim_ref"] for r in receipts]
    require(len(outputs)==len(set(outputs)),"DUPLICATE_CALC_OUTPUT")
    numeric={c.key for c in graph.claims.values() if c.claim_type=="CONDITIONAL_SCENARIO" and c.quantity is not None and c.quantity.value is not None}
    require(set(outputs)==numeric,"UNREPRODUCED_SCENARIO_NUMBER")
    paths=[]
    for scenario,path in scenario_paths:
        if scenario.baseline_ref is not None:require(scenario.baseline_ref in {s.key for s,p in scenario_paths} and scenario.baseline_ref!=scenario.key,"BASELINE_MISSING")
        paths.append(trace(graph,scenario,path))
    sections=[asdict(c) for c in coverage if c.kind=="section"]
    result={"mandate":asdict(inv),"requirements":dict(graph.requirements.pins),"coverage":sorted((asdict(c) for c in coverage),key=lambda x:(x["kind"],x["id"])),"sections":sorted(sections,key=lambda x:x["id"]),"coverage_audit":audit,"calculations":receipts,"paths":paths,"scientific_validation":False,"publication":"BLOCK_PUBLICATION"}
    return {"manifest":result,"manifest_sha256":digest(canonical(result))}

def verify_replay(expected,inv,graph,coverage,calculations=(),scenario_paths=()):
    require(expected==assemble(inv,graph,coverage,calculations,scenario_paths),"REPLAY_MISMATCH")
    return True
