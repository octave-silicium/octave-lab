"""PROSPECT-001 structural tranche. Explicit trajectories, competing paths, unknown effects.
No numerical propagation, probabilities, causal identification or simultaneous solver.
"""
from dataclasses import dataclass,asdict
from pathlib import Path
from collections import defaultdict
import json
from .economic_core import require,words,texts,identity,ref,sha,canonical,digest,unique,Scope
from .economic_paths import Scenario,Path as LegacyPath,trace

VERSION="0.3"
MODES={"NO_SHOCK","NO_ADOPTION","CONDITIONAL"}
STOPS={"NO_ONWARD_LINK","MISSING_EVIDENCE","METHOD_OR_RIGHTS","OUTSIDE_SCOPE","MATERIALITY_UNQUALIFIED","DEPTH_LIMIT","BUDGET_LIMIT","NO_ADOPTION","PENDING_QUALIFICATION"}
INTERACTIONS={"REINFORCING","COMPENSATING","THRESHOLD","STRATEGIC_RESPONSE","SHARED_EFFECT","MULTIPLE_SHOCKS","UNKNOWN"}
ACTORS={"ACTOR","FIRM","GROUP","ROLE","POPULATION","ESTABLISHMENT","SECTOR","MARKET","TERRITORY"}
FILES=("economic_core.py","economic_paths.py","economic_prospective.py","economic_calculations.py","economic_investigation.py")

def model_pins():
    root=Path(__file__).resolve().parent
    return {name:digest((root/name).read_bytes()) for name in FILES}

def refs(xs,table,why,nonempty=False):
    require(texts(xs) and (not nonempty or bool(xs)) and set(xs)<=table.keys(),why)

def scope_result(s):
    return asdict(s)

def transmission(e):
    return e.relation in {"SCENARIO","CAUSAL_HYPOTHESIS","DEPENDENCY"} and not e.condition.startswith("NON_TRANSMISSION:")

@dataclass(frozen=True)
class Trajectory:
    id:str
    revision:int
    mode:str
    baseline_ref:str|None
    decision:str
    scope:Scope
    initial_state_refs:tuple
    shock_refs:tuple
    intervention_refs:tuple
    assumption_refs:tuple
    horizons:tuple
    step_unit:str
    constraints_and_closure:str
    comparison_metrics:tuple
    uncertainty_method:str
    falsification_and_update_triggers:str
    @property
    def key(self):return identity(self.id,self.revision)

@dataclass(frozen=True)
class Context:
    actor_ref:str
    input_claim_refs:tuple
    assumption_refs:tuple
    horizon_or_unknown:str
    limitations:str

@dataclass(frozen=True)
class Branch:
    id:str
    revision:int
    scenario_ref:str
    shock_ref:str
    assertion_refs:tuple
    contexts:tuple
    stop_code:str
    stop_reason:str
    @property
    def key(self):return identity(self.id,self.revision)

@dataclass(frozen=True)
class Interaction:
    id:str
    revision:int
    kind:str
    path_refs:tuple
    claim_ref:str
    condition:str
    discriminating_test:str
    @property
    def key(self):return identity(self.id,self.revision)

@dataclass(frozen=True)
class Rival:
    path_ref:str
    test:str

def families():
    file=Path(__file__).resolve().parents[1]/"governance"/"multi_order_prospective_v1.json"
    return tuple(json.loads(file.read_text())["scenario_families"])

def build(graph,trajectories,branches,interactions=(),family_assessments=()):
    ss=unique(trajectories,lambda s:s.key);ps=unique(branches,lambda p:p.key)
    require(bool(ss) and all(isinstance(s,Trajectory) for s in ss.values()) and all(isinstance(p,Branch) for p in ps.values()),"PROSPECT_TYPES")
    require(len(ss)<=100 and len(ps)<=500,"PROSPECT_BUDGET")
    require(len({p.scenario_ref for p in ps.values()}-ss.keys())==0,"SCENARIO_REF")
    baseline=[s for s in ss.values() if s.mode=="NO_SHOCK"]
    require(len(baseline)==1,"SINGLE_NO_SHOCK_REFERENCE")
    base=baseline[0]
    pins=model_pins();scenario_rows=[];path_rows=[];prefix_next=defaultdict(set);prefix_stop=defaultdict(list)
    prefix_target={};seen_shocks=defaultdict(set);by_end=defaultdict(list);path_signatures=set()
    for s in sorted(ss.values(),key=lambda x:x.key):
        require(s.mode in MODES and isinstance(s.scope,Scope),"TRAJECTORY_SCOPE")
        require(all(words(x) for x in (s.decision,s.step_unit,s.constraints_and_closure,s.uncertainty_method,s.falsification_and_update_triggers)) and texts(s.horizons) and bool(s.horizons) and texts(s.comparison_metrics) and bool(s.comparison_metrics),"TRAJECTORY_FIELDS")
        refs(s.initial_state_refs,graph.claims,"INITIAL_STATE_REF",True)
        refs(s.shock_refs,graph.entities,"SHOCK_REF");refs(s.intervention_refs,graph.entities,"INTERVENTION_REF")
        refs(s.assumption_refs,graph.parameters,"ASSUMPTION_REF")
        require(all(graph.parameters[k].basis=="ASSUMPTION" and graph.parameters[k].scope==s.scope for k in s.assumption_refs),"TRAJECTORY_ASSUMPTION_SCOPE")
        require(all(graph.claims[k].scope==s.scope for k in s.initial_state_refs),"INITIAL_STATE_SCOPE")
        if s.mode=="NO_SHOCK":
            require(s.baseline_ref is None and not s.shock_refs and not s.intervention_refs,"NULL_SHOCK")
        else:
            require(s.baseline_ref==base.key and s.scope==base.scope and s.initial_state_refs==base.initial_state_refs and s.comparison_metrics==base.comparison_metrics and s.horizons==base.horizons and s.step_unit==base.step_unit,"BASELINE_COMPARABILITY")
            require(bool(s.shock_refs) and bool(s.assumption_refs),"SHOCK_ASSUMPTION_REQUIRED")
        if s.mode=="NO_ADOPTION":require(not s.intervention_refs,"NO_ADOPTION_INTERVENTION")
        scenario_rows.append({"id":s.id,"revision":s.revision,"scenario_ref":s.key,"mode":s.mode,"baseline_ref":s.baseline_ref,"decision_and_scope":{"decision":s.decision,"scope":scope_result(s.scope)},"initial_state_refs":list(s.initial_state_refs),"shock_and_intervention_refs":{"shocks":list(s.shock_refs),"interventions":list(s.intervention_refs)},"assumption_refs":list(s.assumption_refs),"model_versions":pins,"horizons":list(s.horizons),"step_unit":s.step_unit,"constraints_and_closure":s.constraints_and_closure,"comparison_metrics":list(s.comparison_metrics),"uncertainty_method":s.uncertainty_method,"falsification_and_update_triggers":s.falsification_and_update_triggers,"probability":None})
    for p in sorted(ps.values(),key=lambda x:x.key):
        s=ss[p.scenario_ref]
        require(p.shock_ref in s.shock_refs and s.mode!="NO_SHOCK","UNDECLARED_SHOCK")
        require(p.stop_code in STOPS and words(p.stop_reason),"STOP_REASON")
        require(isinstance(p.contexts,tuple) and isinstance(p.assertion_refs,tuple) and len(p.contexts)==len(p.assertion_refs),"STEP_CONTEXT")
        require((s.mode=="NO_ADOPTION")== (p.stop_code=="NO_ADOPTION"),"NO_ADOPTION_STOP")
        if s.mode=="NO_ADOPTION":require(not p.assertion_refs,"NO_ADOPTION_TRANSMISSION")
        sign=(s.key,p.shock_ref,p.assertion_refs)
        require(sign not in path_signatures,"DUPLICATE_PATH");path_signatures.add(sign)
        seen_shocks[s.key].add(p.shock_ref)
        legacy=Scenario(s.id,s.revision,s.baseline_ref,s.decision,s.assumption_refs,s.horizons,s.constraints_and_closure,s.uncertainty_method,s.falsification_and_update_triggers)
        checked=trace(graph,legacy,LegacyPath(s.key,p.shock_ref,p.assertion_refs,p.stop_reason))
        current=p.shock_ref;steps=[];prior_claim=None
        for i,(edge_key,ctx,tr) in enumerate(zip(p.assertion_refs,p.contexts,checked["steps"])):
            require(isinstance(ctx,Context) and ctx.actor_ref in graph.entities and graph.entities[ctx.actor_ref].kind in ACTORS,"AFFECTED_ACTOR")
            refs(ctx.input_claim_refs,graph.claims,"INPUT_CLAIMS",True)
            refs(ctx.assumption_refs,graph.parameters,"PATH_ASSUMPTION")
            require(set(ctx.assumption_refs)<=set(s.assumption_refs),"UNDECLARED_ASSUMPTION")
            require(ctx.horizon_or_unknown in s.horizons or ctx.horizon_or_unknown=="UNKNOWN","PATH_HORIZON")
            require(words(ctx.limitations),"PATH_LIMITATIONS")
            e=graph.assertions[edge_key];c=graph.claims[e.claim_ref]
            require(c.scope==s.scope and all(graph.claims[k].scope==s.scope for k in ctx.input_claim_refs),"PATH_CLAIM_SCOPE")
            require(bool(c.mechanism_refs) and set(c.parameter_refs)<=set(s.assumption_refs),"PATH_MECHANISM_OR_PARAMETER")
            require(c.key not in ctx.input_claim_refs and (prior_claim in ctx.input_claim_refs if prior_claim else set(ctx.input_claim_refs)<=set(s.initial_state_refs)),"PATH_CLAIM_CHAIN")
            require(c.claim_type in {"MECHANISM_HYPOTHESIS","CONDITIONAL_SCENARIO"},"PATH_EVIDENCE")
            prefix=(s.key,p.shock_ref,p.assertion_refs[:i]);prefix_target[prefix]=current;prefix_next[prefix].add(edge_key)
            steps.append({"scenario_id":s.key,"shock_ref":p.shock_ref,"graph_version":graph.fingerprint,"ordered_mechanism_refs":[list(graph.claims[graph.assertions[k].claim_ref].mechanism_refs) for k in p.assertion_refs[:i+1]],"assertion_ref":edge_key,"input_claim_refs":list(ctx.input_claim_refs),"output_claim_ref":c.key,"path_order":i+1,"affected_actor":ctx.actor_ref,"scope_and_units":{"scope":scope_result(c.scope),"unit":c.quantity.unit if c.quantity else "NON_QUANTIFIED"},"time_window_or_unknown":ctx.horizon_or_unknown,"elapsed_model_steps":tr["elapsed_model_steps"],"step_unit":s.step_unit,"condition_and_assumption_refs":{"condition":e.condition,"parameters":list(ctx.assumption_refs)},"evidence_type":c.claim_type,"direction_or_unknown":e.direction,"magnitude_or_unknown":None,"competing_paths":[],"limitations":ctx.limitations,"stop_reason_if_applicable":p.stop_reason if i==len(p.assertion_refs)-1 else None})
            prior_claim=c.key;current=e.target
        prefix=(s.key,p.shock_ref,p.assertion_refs);prefix_target[prefix]=current;prefix_stop[prefix].append((p.stop_code,p.stop_reason))
        by_end[(s.key,current)].append(p.key)
        path_rows.append({"path_ref":p.key,"scenario_ref":s.key,"shock_ref":p.shock_ref,"target":current,"steps":steps,"stop_code":p.stop_code,"stop_reason":p.stop_reason,"truncated":p.stop_code in {"DEPTH_LIMIT","BUDGET_LIMIT"},"computed_effect":None})
    for s in ss.values():require(seen_shocks[s.key]==set(s.shock_refs),"UNTRACED_SHOCK")
    # Retain every unexplored outgoing candidate at every represented prefix.
    outgoing=defaultdict(list)
    for e in graph.assertions.values():
        if transmission(e):outgoing[e.origin].append(e.key)
    frontier=[]
    for prefix,target in sorted(prefix_target.items()):
        sc,shock,edges=prefix;unused=sorted(set(outgoing[target])-prefix_next[prefix])
        stops=prefix_stop[prefix]
        require(not (stops and any(code=="NO_ONWARD_LINK" for code,_ in stops) and outgoing[target]),"FALSE_NO_ONWARD_LINK")
        for key in unused:
            frontier.append({"scenario_ref":sc,"shock_ref":shock,"prefix":list(edges),"target":target,"unexplored_assertion_ref":key,"disposition":"STOPPED_DECLARED" if stops else "PENDING_QUALIFICATION","reasons":[{"code":c,"reason":r} for c,r in stops] or [{"code":"PENDING_QUALIFICATION","reason":"Unexplored branch; effect unknown"}]})
    # Convergence is not evidence of competition, equivalence or additive magnitude.
    convergence=[{"scenario_ref":sc,"target":target,"paths":sorted(keys),"total_effect":None,"aggregation":"NOT_QUALIFIED"} for (sc,target),keys in sorted(by_end.items()) if len(keys)>1]
    inter=[]
    for item in sorted(unique(interactions,lambda i:i.key).values(),key=lambda i:i.key):
        require(isinstance(item,Interaction) and item.kind in INTERACTIONS and texts(item.path_refs) and len(item.path_refs)>=2 and set(item.path_refs)<=ps.keys() and item.claim_ref in graph.claims and words(item.condition) and words(item.discriminating_test),"INTERACTION")
        c=graph.claims[item.claim_ref]
        require(c.claim_type=="MECHANISM_HYPOTHESIS" and bool(c.mechanism_refs) and all(ss[ps[k].scenario_ref].scope==c.scope for k in item.path_refs),"INTERACTION_EVIDENCE")
        if item.kind=="MULTIPLE_SHOCKS":require(len({ps[k].shock_ref for k in item.path_refs})>=2,"MULTIPLE_SHOCKS_REQUIRED")
        inter.append({**asdict(item),"interaction_ref":item.key,"magnitude":None,"status":"HYPOTHESIS_ONLY"})
        for row in path_rows:
            if row["path_ref"] in item.path_refs:
                for step in row["steps"]:step["competing_paths"]=sorted(set(step["competing_paths"])|(set(item.path_refs)-{row["path_ref"]}))
    frows=unique(family_assessments,lambda x:x[0])
    require(set(frows)==set(families()),"FAMILY_COVERAGE")
    for family,(name,scenarios,reason) in frows.items():
        require(texts(scenarios) and set(scenarios)<=ss.keys() and words(reason),"FAMILY_ASSESSMENT")
    require(frows[families()[0]][1]==(base.key,),"REFERENCE_FAMILY")
    require(all(ss[k].mode=="NO_ADOPTION" for k in frows[families()[1]][1]),"NO_ADOPTION_FAMILY")
    result={"version":VERSION,"graph_sha256":graph.fingerprint,"requirement_sha256":graph.requirements.fingerprint,"model_versions":pins,"scenarios":scenario_rows,"paths":path_rows,"frontier":frontier,"convergences":convergence,"interactions":inter,"families":[{"family":name,"scenario_refs":list(frows[name][1]),"reason":frows[name][2]} for name in families()],"comparison":{"baseline_ref":base.key,"metrics":list(base.comparison_metrics),"horizons":list(base.horizons),"total_effect":None,"method":"COUNTERFACTUAL_DIFFERENCE_NOT_IMPLEMENTED","path_sum_allowed":False},"causal_validation":False,"publication":"BLOCK_PUBLICATION"}
    # Normalize tuple fields so JSON roundtrip remains exact.
    result=json.loads(canonical(result))
    return {"result":result,"sha256":digest(canonical(result))}

def inverse(bundle,target_ref,rivals):
    require(bundle["sha256"]==digest(canonical(bundle["result"])),"PROSPECT_HASH")
    rows={p["path_ref"]:p for p in bundle["result"]["paths"] if p["target"]==target_ref}
    rr=unique(rivals,lambda r:r.path_ref)
    require(len(rr)>=2 and set(rr)<=rows.keys() and all(words(r.test) for r in rr.values()),"RIVAL_TESTS")
    return {"target":target_ref,"candidate_paths":[{"path_ref":k,"discriminating_test":rr[k].test} for k in sorted(rr)],"unassessed_paths":sorted(rows.keys()-rr.keys()),"causal_inference":False,"publication":"BLOCK_PUBLICATION"}
