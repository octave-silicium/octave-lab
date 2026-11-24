"""METH-003 typed proposed actions and review gates. No AI scoring."""
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
import re

class Status(str,Enum):
    PROPOSED="PROPOSED"
    EXPERT_REVIEWED="EXPERT_REVIEWED"
    OBSERVED="OBSERVED"
class Modality(str,Enum):
    DIGITAL="DIGITAL"
    PHYSICAL="PHYSICAL"
    INTERPERSONAL="INTERPERSONAL"
    MIXED="MIXED"
    UNKNOWN="UNKNOWN"

@dataclass(frozen=True)
class Evidence:
    reference:str
    locator:str
    sha256:str
    kind:str
    def __post_init__(self):
        if not self.reference.strip() or not self.locator.strip() or not re.fullmatch(r"[0-9a-f]{64}",self.sha256) or self.kind not in {"REFERENCE","EXPERT_REVIEW","FIELD_OBSERVATION","MEASUREMENT"}:raise ValueError("EVIDENCE")

@dataclass(frozen=True)
class Action:
    id:str
    revision:int
    parent_refs:tuple[str,...]
    verb:str
    object:str
    context:str
    inputs:tuple[str,...]
    outputs:tuple[str,...]
    acceptance:tuple[str,...]
    modality:Modality
    constraints:tuple[str,...]
    evidence:tuple[Evidence,...]
    status:Status=Status.PROPOSED
    duration_seconds:Decimal|None=None
    duration_evidence:Evidence|None=None
    def __post_init__(self):
        if not re.fullmatch(r"octave:action:[a-z0-9-]+",self.id) or type(self.revision) is not int or self.revision<1:raise ValueError("IDENTITY")
        if not all(isinstance(s,str) and s.strip() for s in (self.verb,self.object,self.context)) or not self.parent_refs or not self.inputs or not self.outputs or not self.acceptance:raise ValueError("ACTION_FIELDS")
        if not all(isinstance(s,str) and s.strip() for s in self.parent_refs+self.inputs+self.outputs+self.acceptance+self.constraints):raise ValueError("ACTION_FIELDS")
        if not isinstance(self.status,Status) or not isinstance(self.modality,Modality) or not self.evidence:raise ValueError("STATUS_OR_EVIDENCE")
        kinds={e.kind for e in self.evidence}
        if self.status==Status.EXPERT_REVIEWED and "EXPERT_REVIEW" not in kinds:raise ValueError("REVIEW_REQUIRED")
        if self.status==Status.OBSERVED and "FIELD_OBSERVATION" not in kinds:raise ValueError("OBSERVATION_REQUIRED")
        if self.duration_seconds is not None:
            if not isinstance(self.duration_seconds,Decimal) or not self.duration_seconds.is_finite() or self.duration_seconds<=0 or self.duration_evidence is None or self.duration_evidence.kind!="MEASUREMENT":raise ValueError("DURATION_EVIDENCE")
        elif self.duration_evidence is not None:raise ValueError("MISSING_DURATION")
    def readiness(self):
        return {"action":self.id,"status":self.status.value,"duration_known":self.duration_seconds is not None,"automation_score":None,"employment_impact":None,"gate":"REVIEW_REQUIRED" if self.status==Status.PROPOSED else "NOT_A_CAPABILITY_TEST"}

@dataclass(frozen=True)
class Crosswalk:
    source_ref:str
    target_ref:str
    relation:str
    evidence:Evidence
    reviewer:str|None=None
    status:str="PROPOSED"
    def __post_init__(self):
        if not self.source_ref.strip() or not self.target_ref.strip() or self.source_ref==self.target_ref or self.relation not in {"EXACT","BROADER","NARROWER","RELATED","UNRESOLVED"}:raise ValueError("CROSSWALK")
        if self.status not in {"PROPOSED","SOURCE_DOCUMENTED","EXPERT_REVIEWED"}:raise ValueError("CROSSWALK_STATUS")
        if self.status=="SOURCE_DOCUMENTED" and self.evidence.kind!="REFERENCE":raise ValueError("SOURCE_REQUIRED")
        if self.status=="EXPERT_REVIEWED" and (not self.reviewer or self.evidence.kind!="EXPERT_REVIEW"):raise ValueError("REVIEW_REQUIRED")
