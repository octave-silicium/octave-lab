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

@dataclass(frozen=True)
class FirmTransition:
    scenario_ref:str
    base:object
    reference:tuple
    phases:dict
    baseline:object
    alternative:object
    rate:int=200
    terminal_assets:tuple=(0,0)

@dataclass(frozen=True)
class MarketTrajectory:
    scenario_ref:str
    dynamics:object

def assemble(inv,graph,coverage,calculations=(),scenario_paths=(),prospective=None,firm_transitions=(),market_trajectories=()):
    inv.key
    require(all(words(x) for x in (inv.question,inv.decision,inv.loss_function,inv.exclusions)) and texts(inv.alternatives) and len(inv.alternatives)>=2,"MANDATE")
    from .economic_core import sha
    require(sha(inv.model_sha256) and inv.graph_sha256==graph.fingerprint,"INVESTIGATION_PIN")
    coverage=tuple(coverage)
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
    prospective_result=None
    if prospective is not None:
        from .economic_prospective import build,model_pins
        require(not scenario_paths,"MIXED_PATH_CONTRACT")
        require(inv.model_sha256==digest(canonical(model_pins())),"MODEL_PIN_MISMATCH")
        prospective_result=build(graph,*prospective)
    firm_rows=[]
    if firm_transitions:
        require(prospective is not None,"FIRM_PROSPECTIVE_REQUIRED")
        from .economic_transition import assess
        from .economic_core import unique
        scenarios=unique(prospective[0],lambda s:s.key)
        for sc,item in unique(firm_transitions,lambda f:f.scenario_ref).items():
            require(isinstance(item,FirmTransition) and sc in scenarios,"FIRM_SCENARIO_REF")
            t=scenarios[sc];require(t.mode=="CONDITIONAL" and t.baseline_ref in scenarios and scenarios[t.baseline_ref].mode=="NO_SHOCK","FIRM_BASELINE")
            scope=item.reference[1].scope
            require(all(getattr(t.scope,k)==getattr(scope,k) for k in ("population","geography","classification","price_basis")) and t.scope.period_start<=scope.period_start<=scope.period_end<=t.scope.period_end and t.step_unit=="quarter" and str(len(item.alternative.quarters))+" quarters" in t.horizons,"FIRM_SCOPE_HORIZON")
            require(all(q.phase=="reference" and not q.phase_mix for q in item.baseline.quarters),"FIRM_NO_SHOCK_PHASE")
            receipt=assess(item.base,item.reference,item.phases,item.baseline,item.alternative,item.rate,item.terminal_assets)
            firm_rows.append({"scenario_ref":sc,"baseline_ref":t.baseline_ref,"sections":["D06","D07","D13","D15"],"receipt":receipt,"status":"CONDITIONAL_NOT_PROPAGATED","limitations":"Explicit synthetic operational and financial assumptions outside graph parameters; no causal or macro propagation."})
    market_rows=[]
    if market_trajectories:
        require(prospective is not None,"MARKET_PROSPECTIVE_REQUIRED")
        from .economic_market import trajectory
        from .economic_core import unique
        scenarios=unique(prospective[0],lambda s:s.key)
        for sc,item in unique(market_trajectories,lambda f:f.scenario_ref).items():
            require(isinstance(item,MarketTrajectory) and sc in scenarios,"MARKET_SCENARIO_REF")
            t=scenarios[sc];require(t.mode=="CONDITIONAL" and t.baseline_ref in scenarios and scenarios[t.baseline_ref].mode=="NO_SHOCK","MARKET_BASELINE")
            scope=item.dynamics.market.sellers[0].reference[1].scope
            require(all(getattr(t.scope,k)==getattr(scope,k) for k in ("population","geography","classification","price_basis")) and t.scope.period_start<=scope.period_start<=scope.period_end<=t.scope.period_end and t.step_unit=="quarter" and str(item.dynamics.quarters)+" quarters" in t.horizons,"MARKET_SCOPE_HORIZON")
            # Explicit no-adoption counterfactual, replayed with same opening finance and demand.
            from dataclasses import replace
            no_adopt=replace(item.dynamics,id=item.dynamics.id+":no-adoption",strategies=tuple(replace(s,earliest_adoption=0) for s in item.dynamics.strategies))
            market_rows.append({"scenario_ref":sc,"baseline_ref":t.baseline_ref,"sections":["D07","D08","D11","D13","D15"],"baseline":trajectory(no_adopt),"alternative":trajectory(item.dynamics),"status":"CONDITIONAL_NOT_PROPAGATED","limitations":"Rule-based market dynamics, not causal inference, not liquidation or macro closure."})
    sections=[asdict(c) for c in coverage if c.kind=="section"]
    result={"mandate":asdict(inv),"requirements":dict(graph.requirements.pins),"coverage":sorted((asdict(c) for c in coverage),key=lambda x:(x["kind"],x["id"])),"sections":sorted(sections,key=lambda x:x["id"]),"coverage_audit":audit,"calculations":receipts,"paths":paths,"prospective":prospective_result,"firm_transitions":firm_rows,"market_trajectories":market_rows,"scientific_validation":False,"publication":"BLOCK_PUBLICATION"}
    return {"manifest":result,"manifest_sha256":digest(canonical(result))}

def verify_replay(expected,inv,graph,coverage,calculations=(),scenario_paths=(),prospective=None,firm_transitions=(),market_trajectories=()):
    require(expected==assemble(inv,graph,coverage,calculations,scenario_paths,prospective,firm_transitions,market_trajectories),"REPLAY_MISMATCH")
    return True
