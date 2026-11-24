"""Structural prospective paths, not numerical propagation or causal identification."""
from dataclasses import dataclass
from .economic_core import require,words,texts,ref,identity
@dataclass(frozen=True)
class Scenario:
    id:str
    revision:int
    baseline_ref:str|None
    scope:str
    assumptions:tuple
    horizons:tuple
    constraints:str
    uncertainty:str
    revision_trigger:str
    def __post_init__(self):
        identity(self.id,self.revision)
        require(self.baseline_ref is None or ref(self.baseline_ref),"BASELINE_REF")
        require(all(words(x) for x in (self.scope,self.constraints,self.uncertainty,self.revision_trigger)) and texts(self.assumptions) and texts(self.horizons) and bool(self.horizons),"SCENARIO_FIELDS")
    @property
    def key(self):return identity(self.id,self.revision)
@dataclass(frozen=True)
class Path:
    scenario_ref:str
    shock_entity:str
    assertion_refs:tuple
    stop_reason:str
    def __post_init__(self):
        require(ref(self.scenario_ref) and ref(self.shock_entity) and isinstance(self.assertion_refs,tuple) and all(ref(x) for x in self.assertion_refs) and words(self.stop_reason),"PATH_FIELDS")
def trace(graph,scenario,path):
    require(path.scenario_ref==scenario.key and path.shock_entity in graph.entities,"PATH_SCOPE")
    require(set(scenario.assumptions)<=graph.parameters.keys(),"SCENARIO_PARAMETER")
    require(len(path.assertion_refs)<=100,"PATH_LIMIT")
    current=path.shock_entity;visited={current:0};elapsed=0;order=0;steps=[]
    for key in path.assertion_refs:
        require(key in graph.assertions,"PATH_EDGE")
        e=graph.assertions[key]
        require(e.origin==current,"PATH_DISCONTINUITY")
        # Accounting or classification edges aren't causal transitions.
        require(e.relation in {"SCENARIO","CAUSAL_HYPOTHESIS","DEPENDENCY"} and not e.condition.startswith("NON_TRANSMISSION:"),"NON_TRANSMISSION_EDGE")
        order+=1
        elapsed=None if elapsed is None or e.delay_steps is None else elapsed+e.delay_steps
        if e.target in visited:
            require(elapsed is not None and visited[e.target] is not None and elapsed>visited[e.target],"FEEDBACK_REQUIRES_EXPLICIT_LAG")
        visited[e.target]=elapsed;current=e.target
        steps.append({"order":order,"assertion_ref":key,"claim_ref":e.claim_ref,"target":current,"elapsed_model_steps":elapsed,"status":"STRUCTURAL_HYPOTHESIS_ONLY"})
    return {"scenario":scenario.key,"shock":path.shock_entity,"graph_sha256":graph.fingerprint,"steps":steps,"stop_reason":path.stop_reason,"computed_effect":None,"causal_validation":False,"publication":"BLOCK_PUBLICATION"}
