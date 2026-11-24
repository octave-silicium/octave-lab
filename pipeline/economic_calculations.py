"""Conservative conditional calculation receipts; no cross-scope or native-unit arithmetic."""
from dataclasses import dataclass,asdict
from decimal import Decimal,localcontext,ROUND_HALF_EVEN
from .economic_core import Quantity,require,identity,canonical,digest

# Explicit semantic operations, not merely dimension matching.
RULES={
    "LABOR_HOURS":(("MINUTE_PER_UNIT","UNIT"),"HOUR"),
    "LABOR_COST":(("HOUR","EUR_PER_HOUR"),"EUR"),
    "VARIABLE_COST":(("EUR_PER_UNIT","UNIT"),"EUR"),
    "UNIT_COST":(("EUR","UNIT"),"EUR_PER_UNIT"),
    "THROUGHPUT":(("UNIT","HOUR"),"UNIT_PER_HOUR"),
}
@dataclass(frozen=True)
class Calculation:
    id:str
    revision:int
    operation:str
    input_refs:tuple
    output_claim_ref:str
    @property
    def key(self):return identity(self.id,self.revision)

def calculate(graph,calc):
    calc.key
    require(calc.operation in RULES,"UNQUALIFIED_OPERATION")
    require(isinstance(calc.input_refs,tuple) and len(calc.input_refs)==2 and len(set(calc.input_refs))==2 and all(k in graph.parameters for k in calc.input_refs),"CALC_INPUTS")
    require(calc.output_claim_ref in graph.claims,"CALC_OUTPUT")
    a,b=(graph.parameters[k] for k in calc.input_refs)
    c=graph.claims[calc.output_claim_ref]
    types,out=RULES[calc.operation]
    require(c.claim_type=="CONDITIONAL_SCENARIO" and set(c.parameter_refs)==set(calc.input_refs) and not c.dependency_refs,"CALC_CONDITIONAL_ONLY")
    require(a.scope==b.scope==c.scope,"CALC_SCOPE")
    require(a.quantity.unit==types[0] and b.quantity.unit==types[1],"CALC_UNITS")
    require(a.basis=="ASSUMPTION" or b.basis=="ASSUMPTION","CALC_ASSUMPTION")
    require(all(p.quantity.value is not None and p.quantity.value>=0 and p.quantity.lower is None for p in (a,b)),"CALC_UNKNOWN_NEGATIVE_OR_BOUNDED")
    x,y=a.quantity.value,b.quantity.value
    with localcontext() as ctx:
        ctx.prec=34;ctx.rounding=ROUND_HALF_EVEN
        if calc.operation in {"UNIT_COST","THROUGHPUT"}:
            require(y>0,"ZERO_DENOMINATOR")
            value=x/y
        elif calc.operation=="LABOR_HOURS":value=x*y/Decimal(60)
        else:value=x*y
    require(c.quantity==Quantity(value,out),"CALC_RESULT_MISMATCH")
    return {"calculation_ref":calc.key,"operation":calc.operation,"input_refs":list(calc.input_refs),"output_claim_ref":c.key,"result":str(value),"unit":out,"precision":34,"rounding":"ROUND_HALF_EVEN","graph_sha256":graph.fingerprint,"publication":"BLOCK_PUBLICATION","evidence_type":"CONDITIONAL_SCENARIO"}
