"""Bounded exclusive-path process model. Not a BPMN engine or a duration model."""
from dataclasses import dataclass
from collections import defaultdict
from .work_actions import Action,Status
import re

@dataclass(frozen=True)
class Step:
    id:str
    action:Action
    actor:str
    system:str
    def __post_init__(self):
        if not re.fullmatch(r"[a-z0-9-]+",self.id) or not self.actor.strip() or not self.system.strip():raise ValueError("STEP")

@dataclass(frozen=True)
class Transition:
    origin:str
    target:str
    condition:str
    def __post_init__(self):
        if not self.condition.strip():raise ValueError("CONDITION")

@dataclass(frozen=True)
class Process:
    id:str
    revision:int
    scope:str
    entry:str
    steps:tuple[Step,...]
    transitions:tuple[Transition,...]
    terminals:tuple[str,...]
    external_inputs:tuple[str,...]
    def __post_init__(self):
        if not re.fullmatch(r"octave:process:[a-z0-9-]+",self.id) or type(self.revision)!=int or self.revision<1 or not self.scope.strip():raise ValueError("PROCESS")
        ids={s.id for s in self.steps}
        if len(ids)!=len(self.steps) or self.entry not in ids or not self.terminals or not set(self.terminals)<=ids:raise ValueError("STEP_IDS")
        adj=defaultdict(list)
        pairs=set()
        for e in self.transitions:
            if e.origin not in ids or e.target not in ids or e.origin in self.terminals or (e.origin,e.target) in pairs:raise ValueError("EDGE")
            pairs.add((e.origin,e.target));adj[e.origin].append(e)
        if any(not adj[s] for s in ids-set(self.terminals)):raise ValueError("DEAD_END")
        if any(len({e.condition for e in edges})!=len(edges) for edges in adj.values()):raise ValueError("DUPLICATE_CONDITION")
        active=set();seen=set()
        def visit(s):
            if s in active:raise ValueError("CYCLE_UNSUPPORTED")
            if s in seen:return
            active.add(s)
            for e in adj[s]:visit(e.target)
            active.remove(s);seen.add(s)
        visit(self.entry)
        if seen!=ids:raise ValueError("UNREACHABLE_STEP")
        # Inputs must be supplied on every possible path, not merely somewhere in the graph.
        by_id={s.id:s for s in self.steps}
        budget=10000
        def dataflow(s,available):
            nonlocal budget
            budget-=1
            if budget<0:raise ValueError("PATH_LIMIT")
            a=by_id[s].action
            if not set(a.inputs)<=available:raise ValueError("MISSING_INPUT_"+s)
            available=available|set(a.outputs)
            for e in adj[s]:dataflow(e.target,available)
        dataflow(self.entry,set(self.external_inputs))
    def audit(self):
        return {"id":self.id,"revision":self.revision,"steps":len(self.steps),"transitions":len(self.transitions),"terminals":list(self.terminals),"status":"PROPOSED","human_review_required":True,"observed_process":False,"duration_estimate":None,"automation_score":None,"employment_impact":None,"limitations":["Exclusive paths only; conditions not executable or proven exhaustive","No loops or parallel synchronization","No process timing, probabilities or capacity model"],"publication":"BLOCK_PUBLICATION"}
