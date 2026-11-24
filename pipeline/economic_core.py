"""G3.1 v0.1: conservative internal economic contracts, not an inference engine.
Pinned requirements, revisioned entities/claims, evidence, strict quantities and explicit coverage.
Only native descriptive observations and conditional fixtures are admitted in this slice.
"""
from dataclasses import dataclass,asdict
from decimal import Decimal
from pathlib import Path
from datetime import date
from collections import defaultdict,Counter
from types import MappingProxyType
import hashlib,json,re

ROOT=Path(__file__).resolve().parents[1]/"governance"
FILES=("economic_mechanisms_v2.json","investigation_result_v1.json","multi_order_prospective_v1.json")
TYPES=frozenset("TECHNOLOGY CONFIGURATION CAPABILITY ACTION TASK OCCUPATION SKILL PROCESS STEP RESOURCE SYSTEM ROLE ESTABLISHMENT FIRM GROUP PRODUCT MARKET SECTOR TERRITORY POPULATION ACTOR OBSERVATION SERIES DATASET VINTAGE PARAMETER SCENARIO MECHANISM DECISION".split())
UNITS=frozenset("EUR EUR_PER_UNIT EUR_PER_HOUR HOUR PERSON_HOUR PERSON FTE UNIT UNIT_PER_HOUR MINUTE_PER_UNIT FRACTION PERCENT INDEX NATIVE".split())
RELATIONS=frozenset("CLASSIFICATION MEASUREMENT DEPENDENCY ACCOUNTING ASSOCIATION CAUSAL_HYPOTHESIS CAUSAL_IDENTIFIED SCENARIO".split())
# This slice does not authorize causal estimates/validated forecasts, or qualified economic rules.
ADMITTED=frozenset("OBSERVATION DESCRIPTIVE_COMPARISON ACCOUNTING_IDENTITY MECHANISM_HYPOTHESIS CONDITIONAL_SCENARIO NON_IDENTIFIABLE".split())
DISPOSITIONS=frozenset("APPLIED_QUALIFIED HYPOTHESIS_ONLY NOT_APPLICABLE_JUSTIFIED BLOCKED_MISSING_DATA BLOCKED_METHOD_OR_RIGHTS PENDING_QUALIFICATION".split())
def require(ok,why):
    if not ok:raise ValueError(why)
def words(x):return isinstance(x,str) and bool(x.strip())
def texts(xs):return isinstance(xs,tuple) and all(words(s) for s in xs) and len(set(xs))==len(xs)
def sha(x):return isinstance(x,str) and re.fullmatch(r"[0-9a-f]{64}",x) is not None
def day(x):
    try:return isinstance(x,str) and date.fromisoformat(x).isoformat()==x
    except ValueError:return False
def ref(x):return isinstance(x,str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9:._/-]{0,255}@[1-9][0-9]*",x) is not None
def identity(i,r):
    require(type(r) is int and r>0 and ref(f"{i}@{r}"),"IDENTITY")
    return f"{i}@{r}"
def digest(b):return hashlib.sha256(b).hexdigest()
def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()
def unique(items,key):
    out={}
    for item in items:
        k=key(item);require(k not in out,"DUPLICATE_ID");out[k]=item
    return out

class Requirements:
    def __init__(self,root=ROOT):
        raw={f:(Path(root)/f).read_bytes() for f in FILES}
        self.pins=MappingProxyType({f:digest(b) for f,b in raw.items()})
        reg,result,pros=(json.loads(raw[f]) for f in FILES)
        layers=unique(reg["layers"],lambda x:x["id"])
        engines=unique(reg["engines"],lambda x:x["id"])
        mechanisms=unique(reg["mechanisms"],lambda x:x["id"])
        sections=unique(result["sections"],lambda x:x["id"])
        interfaces=unique(result["coverage"]["interfaces"],lambda x:x["id"])
        require(set(layers)==set(result["coverage"]["layers"]) and set(engines)==set(result["coverage"]["engines"]) and set(mechanisms)==set(result["coverage"]["mechanism_ids"]),"REGISTRY_DRIFT")
        require([{k:v for k,v in i.items() if k!="id"} for i in interfaces.values()]==reg["interfaces"],"INTERFACE_DRIFT")
        require(all(m["layer"] in layers and set(m["reference_seeds"])<=set(reg["references"]) for m in mechanisms.values()),"MECHANISM_REF")
        require(all(i["from"] in layers and i["to"] in layers for i in interfaces.values()),"INTERFACE_REF")
        require(set(result["coverage"]["dispositions"])==DISPOSITIONS and ADMITTED<=set(result["claim_types"]),"VOCABULARY_DRIFT")
        self.groups=MappingProxyType({k:frozenset(v) for k,v in (("mechanism",mechanisms),("layer",layers),("engine",engines),("interface",interfaces),("section",sections))})
        self.mechanisms=frozenset(mechanisms)
        self.scenario_fields=frozenset(pros["scenario_required"])
        self.path_fields=frozenset(pros["node_path_required"])
    @property
    def fingerprint(self):return digest(canonical(dict(self.pins)))

@dataclass(frozen=True)
class Scope:
    population:str
    geography:str
    classification:str
    period_start:str
    period_end:str
    price_basis:str
    def __post_init__(self):
        require(all(words(x) for x in (self.population,self.geography,self.classification,self.price_basis)) and day(self.period_start) and day(self.period_end) and self.period_start<=self.period_end,"SCOPE")

@dataclass(frozen=True)
class Evidence:
    id:str
    revision:int
    kind:str
    source:str
    locator:str
    sha256:str
    vintage:str
    collected_on:str
    published_on:str|None
    rights:str
    quality:str
    def __post_init__(self):
        identity(self.id,self.revision)
        require(self.kind in {"NATIVE_SOURCE","ASSUMPTION","REFERENCE","CALCULATION","REVIEW"} and all(words(x) for x in (self.source,self.locator,self.vintage)) and sha(self.sha256),"EVIDENCE")
        require(day(self.collected_on) and (self.published_on is None or day(self.published_on) and self.published_on<=self.collected_on),"EVIDENCE_TIME")
        require(self.rights in {"INTERNAL_ONLY","UNQUALIFIED","RESTRICTED"} and self.quality in {"DESCRIPTIVE_ONLY","ASSUMED","REFERENCE_ONLY","REVIEW_REQUIRED","RESTRICTED","WITHHELD"},"EVIDENCE_POLICY")
        require(self.kind!="ASSUMPTION" or self.quality=="ASSUMED","ASSUMPTION_QUALITY")
    @property
    def key(self):return identity(self.id,self.revision)

@dataclass(frozen=True)
class Quantity:
    value:Decimal|None
    unit:str
    native_unit:str|None=None
    lower:Decimal|None=None
    upper:Decimal|None=None
    def __post_init__(self):
        require(self.unit in UNITS and (words(self.native_unit) if self.unit=="NATIVE" else self.native_unit is None),"UNIT")
        require(all(x is None or isinstance(x,Decimal) and x.is_finite() for x in (self.value,self.lower,self.upper)),"NUMERIC")
        require((self.lower is None)==(self.upper is None),"BOUND_PAIR")
        if self.lower is not None:
            require(self.value is not None and self.lower<=self.value<=self.upper,"BOUNDS")
        if self.unit in {"FRACTION","PERCENT"}:
            cap=Decimal(1 if self.unit=="FRACTION" else 100)
            require(all(x is None or 0<=x<=cap for x in (self.value,self.lower,self.upper)),"RATIO_RANGE")

@dataclass(frozen=True)
class Entity:
    id:str
    revision:int
    kind:str
    label:str
    native_reference:str
    def __post_init__(self):
        identity(self.id,self.revision)
        require(self.kind in TYPES and words(self.label) and words(self.native_reference),"ENTITY")
    @property
    def key(self):return identity(self.id,self.revision)

@dataclass(frozen=True)
class Parameter:
    id:str
    revision:int
    scope:Scope
    quantity:Quantity
    basis:str
    evidence_refs:tuple
    meaning:str
    def __post_init__(self):
        identity(self.id,self.revision)
        require(isinstance(self.scope,Scope) and isinstance(self.quantity,Quantity) and self.basis in {"OBSERVED","ASSUMPTION","UNKNOWN"} and texts(self.evidence_refs) and words(self.meaning),"PARAMETER")
        require((self.quantity.value is None)==(self.basis=="UNKNOWN"),"UNKNOWN_NOT_ZERO")
        require(self.basis=="UNKNOWN" or bool(self.evidence_refs),"PARAMETER_EVIDENCE")
    @property
    def key(self):return identity(self.id,self.revision)

@dataclass(frozen=True)
class Claim:
    id:str
    revision:int
    claim_type:str
    statement:str
    decision_relevance:str
    scope:Scope
    quantity:Quantity|None
    evidence_refs:tuple
    mechanism_refs:tuple
    method_and_assumptions:str
    uncertainty_and_limits:str
    competing_explanations:str
    falsification_or_revision_trigger:str
    dependency_refs:tuple
    parameter_refs:tuple=()
    publication_status:str="BLOCK_PUBLICATION"
    def __post_init__(self):
        identity(self.id,self.revision)
        require(self.claim_type in ADMITTED and isinstance(self.scope,Scope) and (self.quantity is None or isinstance(self.quantity,Quantity)),"CLAIM_TYPE_SCOPE")
        require(all(words(x) for x in (self.statement,self.decision_relevance,self.method_and_assumptions,self.uncertainty_and_limits,self.competing_explanations,self.falsification_or_revision_trigger)),"CLAIM_FIELDS")
        require(all(texts(x) for x in (self.evidence_refs,self.mechanism_refs,self.dependency_refs,self.parameter_refs)),"CLAIM_REFS")
        require(self.publication_status=="BLOCK_PUBLICATION","PUBLICATION")
        require(self.claim_type!="NON_IDENTIFIABLE" or self.quantity is None or self.quantity.value is None,"NON_IDENTIFIABLE_NUMBER")
        require(self.claim_type!="MECHANISM_HYPOTHESIS" or self.quantity is None or self.quantity.value is None,"HYPOTHESIS_NUMBER")
        require(self.claim_type!="OBSERVATION" or bool(self.evidence_refs),"OBSERVATION_EVIDENCE")
        require(self.claim_type not in {"CONDITIONAL_SCENARIO","ACCOUNTING_IDENTITY","DESCRIPTIVE_COMPARISON"} or bool(self.evidence_refs or self.dependency_refs or self.parameter_refs),"DERIVATION_EVIDENCE")
    @property
    def key(self):return identity(self.id,self.revision)
    def result(self):
        # RESULT-001 fields exposed through a structural mapping, not free text inference.
        return {"id":self.id,"revision":self.revision,"claim_type":self.claim_type,"statement":self.statement,"decision_relevance":self.decision_relevance,"population":self.scope.population,"period":[self.scope.period_start,self.scope.period_end],"geography":self.scope.geography,"units_or_non_quantifiable":self.quantity.unit if self.quantity else "NON_QUANTIFIED","source_and_vintage_refs":self.evidence_refs,"mechanism_refs":self.mechanism_refs,"method_and_assumptions":self.method_and_assumptions,"uncertainty_and_limits":self.uncertainty_and_limits,"competing_explanations":self.competing_explanations,"falsification_or_revision_trigger":self.falsification_or_revision_trigger,"dependency_refs":self.dependency_refs,"publication_status":self.publication_status}

@dataclass(frozen=True)
class Assertion:
    id:str
    revision:int
    origin:str
    target:str
    relation:str
    claim_ref:str
    condition:str
    delay_steps:int|None
    direction:str="UNKNOWN"
    def __post_init__(self):
        identity(self.id,self.revision)
        require(ref(self.origin) and ref(self.target) and self.origin!=self.target and ref(self.claim_ref),"EDGE_ENDPOINT")
        require(self.relation in RELATIONS and self.relation!="CAUSAL_IDENTIFIED" and words(self.condition),"EDGE_RELATION")
        require(self.delay_steps is None or type(self.delay_steps) is int and self.delay_steps>=0,"DELAY")
        require(self.direction in {"POSITIVE","NEGATIVE","MIXED","UNKNOWN"},"DIRECTION")
    @property
    def key(self):return identity(self.id,self.revision)

class Graph:
    """Immutable records within a snapshot; no inferred links and no calculation by traversal."""
    def __init__(self,requirements,*,entities=(),evidence=(),parameters=(),claims=(),assertions=()):
        self.requirements=requirements
        for name,seq,cls in (("entities",entities,Entity),("evidence",evidence,Evidence),("parameters",parameters,Parameter),("claims",claims,Claim),("assertions",assertions,Assertion)):
            require(all(isinstance(x,cls) for x in seq),"RECORD_TYPE")
            setattr(self,name,MappingProxyType(unique(seq,lambda x:x.key)))
        require(sum(len(getattr(self,n)) for n in ("entities","evidence","parameters","claims","assertions"))==len(set().union(*(set(getattr(self,n)) for n in ("entities","evidence","parameters","claims","assertions")))),"CROSS_TYPE_ID")
        for p in self.parameters.values():
            require(set(p.evidence_refs)<=self.evidence.keys(),"PARAMETER_REF")
            ev=[self.evidence[k] for k in p.evidence_refs]
            if p.basis=="OBSERVED":
                require(bool(ev) and all(e.kind=="NATIVE_SOURCE" and e.quality=="DESCRIPTIVE_ONLY" and e.rights=="INTERNAL_ONLY" for e in ev),"OBSERVED_PARAMETER_BLOCKED")
            if p.basis=="ASSUMPTION":require(any(e.kind=="ASSUMPTION" for e in ev),"ASSUMPTION_REF")
        for c in self.claims.values():
            require(set(c.evidence_refs)<=self.evidence.keys() and set(c.dependency_refs)<=self.claims.keys() and set(c.parameter_refs)<=self.parameters.keys() and set(c.mechanism_refs)<=requirements.mechanisms,"CLAIM_REFERENCE")
            ev=[self.evidence[k] for k in c.evidence_refs]
            if c.claim_type=="OBSERVATION":
                require(not c.dependency_refs and not c.parameter_refs and all(e.kind=="NATIVE_SOURCE" and e.quality=="DESCRIPTIVE_ONLY" and e.rights=="INTERNAL_ONLY" for e in ev),"OBSERVATION_BLOCKED")
            if c.quantity is not None and c.quantity.value is not None:
                require(all(e.quality not in {"WITHHELD","RESTRICTED","REVIEW_REQUIRED"} and e.rights=="INTERNAL_ONLY" for e in ev),"NUMERIC_EVIDENCE_BLOCKED")
                require(all(self.parameters[k].quantity.value is not None for k in c.parameter_refs),"UNKNOWN_DEPENDENCY")
                require(all(self.claims[k].quantity is not None and self.claims[k].quantity.value is not None for k in c.dependency_refs),"UNKNOWN_DEPENDENCY")
        # Provenance graph must be acyclic (distinct from feedback in economic relationships).
        pending={k:len(c.dependency_refs) for k,c in self.claims.items()}
        children=defaultdict(list)
        for k,c in self.claims.items():
            for dep in c.dependency_refs:children[dep].append(k)
        queue=[k for k,n in pending.items() if n==0];seen=0
        while queue:
            k=queue.pop();seen+=1
            for child in children[k]:
                pending[child]-=1
                if pending[child]==0:queue.append(child)
        require(seen==len(pending),"PROVENANCE_CYCLE")
        expected={"CLASSIFICATION":{"OBSERVATION"},"MEASUREMENT":{"OBSERVATION"},"DEPENDENCY":{"MECHANISM_HYPOTHESIS","CONDITIONAL_SCENARIO"},"ACCOUNTING":{"ACCOUNTING_IDENTITY"},"ASSOCIATION":{"DESCRIPTIVE_COMPARISON"},"CAUSAL_HYPOTHESIS":{"MECHANISM_HYPOTHESIS"},"SCENARIO":{"CONDITIONAL_SCENARIO"}}
        for e in self.assertions.values():
            require(e.origin in self.entities and e.target in self.entities and e.claim_ref in self.claims,"EDGE_REFERENCE")
            require(self.claims[e.claim_ref].claim_type in expected[e.relation],"EDGE_CLAIM_TYPE")
    def neighbors(self,entity,direction="both"):
        require(entity in self.entities and direction in {"both","out","in"},"QUERY")
        return {"entity":entity,"direction":direction,"assertions":[asdict(e) for e in sorted(self.assertions.values(),key=lambda x:x.key) if (direction in {"out","both"} and e.origin==entity) or (direction in {"in","both"} and e.target==entity)],"inferred_causality":False,"publication":"BLOCK_PUBLICATION"}
    def snapshot(self):
        def enc(v):
            if isinstance(v,Decimal):return str(v)
            raise TypeError(type(v).__name__)
        obj={"requirements":dict(self.requirements.pins),"records":{n:[asdict(v) for k,v in sorted(getattr(self,n).items())] for n in ("entities","evidence","parameters","claims","assertions")}}
        return json.loads(json.dumps(obj,default=enc,allow_nan=False))
    @property
    def fingerprint(self):return digest(canonical(self.snapshot()))

@dataclass(frozen=True)
class Coverage:
    kind:str
    id:str
    disposition:str
    reason:str
    claim_refs:tuple=()
    def __post_init__(self):
        require(self.disposition in DISPOSITIONS and words(self.reason) and texts(self.claim_refs),"COVERAGE")
        # No mechanism certified qualified in this version. A later gate must explicitly enable this.
        require(self.disposition!="APPLIED_QUALIFIED","QUALIFICATION_GATE_NOT_IMPLEMENTED")
        require(self.disposition!="HYPOTHESIS_ONLY" or bool(self.claim_refs),"HYPOTHESIS_REF")

def validate_coverage(graph,entries):
    expected={(k,i) for k,ids in graph.requirements.groups.items() for i in ids}
    rows=unique(entries,lambda r:(r.kind,r.id))
    require(set(rows)==expected,"COVERAGE_MISSING_OR_UNKNOWN")
    for row in rows.values():
        require(set(row.claim_refs)<=graph.claims.keys(),"COVERAGE_CLAIM")
        if row.disposition=="HYPOTHESIS_ONLY":
            require(all(graph.claims[k].claim_type in {"MECHANISM_HYPOTHESIS","CONDITIONAL_SCENARIO"} for k in row.claim_refs),"COVERAGE_HYPOTHESIS")
            if row.kind=="mechanism":require(all(row.id in graph.claims[k].mechanism_refs for k in row.claim_refs),"COVERAGE_MECHANISM")
    return {"requirements_sha256":graph.requirements.fingerprint,"graph_sha256":graph.fingerprint,"entries":len(rows),"by_kind":{k:dict(Counter(r.disposition for r in rows.values() if r.kind==k)) for k in graph.requirements.groups},"scientific_coverage_validated":False,"publication":"BLOCK_PUBLICATION"}
