"""Contribution intake: validate structure, never promote contributor statements to facts."""
from dataclasses import dataclass,asdict
from .economic_core import require,words,sha,identity,canonical,digest,unique,day
from .economic_operations import process_pin

@dataclass(frozen=True)
class Input:
    id:str
    step_id:str
    kind:str # DESCRIPTION, ASSUMPTION, MEASUREMENT
    statement:str
    unit:str|None=None
    value:str|None=None
    sample_size:int|None=None
    method:str|None=None
    evidence_sha256:str|None=None

@dataclass(frozen=True)
class Submission:
    id:str
    revision:int
    process_sha256:str
    contributor_alias:str
    professional_context:str
    geography:str
    observation_start:str
    observation_end:str
    scope:str
    rights:str
    consent_internal:bool
    no_identifying_or_confidential_data:bool
    limitations:str
    entries:tuple
    @property
    def key(self):return identity(self.id,self.revision)

def intake(process,s):
    s.key
    require(s.process_sha256==process_pin(process),"PROCESS_PIN")
    require(all(words(x) for x in (s.contributor_alias,s.professional_context,s.geography,s.scope,s.limitations)) and day(s.observation_start) and day(s.observation_end) and s.observation_start<=s.observation_end,"CONTEXT")
    require(s.rights=="INTERNAL_REVIEW_ONLY" and s.consent_internal is True and s.no_identifying_or_confidential_data is True,"CONSENT_RIGHTS")
    require(isinstance(s.entries,tuple) and 0<len(s.entries)<=500,"ENTRY_COUNT")
    steps={x.id for x in process.steps};rows=unique(s.entries,lambda x:x.id)
    for x in rows.values():
        require(words(x.id) and x.step_id in steps and x.kind in {"DESCRIPTION","ASSUMPTION","MEASUREMENT"} and words(x.statement),"ENTRY")
        if x.kind=="MEASUREMENT":
            from decimal import Decimal,InvalidOperation
            try:v=Decimal(x.value)
            except (InvalidOperation,TypeError,ValueError):raise ValueError("MEASUREMENT_VALUE")
            require(v.is_finite() and v>=0 and words(x.unit) and type(x.sample_size) is int and x.sample_size>0 and words(x.method) and sha(x.evidence_sha256),"MEASUREMENT_METADATA")
        else:
            require(x.sample_size is None and x.evidence_sha256 is None,"NONMEASUREMENT_EVIDENCE")
            require((x.unit is None)==(x.value is None),"VALUE_UNIT_PAIR")
    out={"submission_ref":s.key,"submission_sha256":digest(canonical(asdict(s))),"process_sha256":s.process_sha256,"counts":{k:sum(x.kind==k for x in rows.values()) for k in ("DESCRIPTION","ASSUMPTION","MEASUREMENT")},"status":"PENDING_INDEPENDENT_REVIEW","contributor_identity_verified":False,"evidence_bytes_verified":False,"measurement_qualified":False,"publication":"BLOCK_PUBLICATION","automatic_graph_promotion":False}
    return out
