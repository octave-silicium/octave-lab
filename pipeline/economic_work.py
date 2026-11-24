"""Native O*NET to economic graph; proposed W001 never promoted to field observation."""
from datetime import datetime
from .economic_core import *
from . import work_graph as wg,invoice_pilot

def from_onet_profile(g,code,requirements=None,include_candidate=False):
    require(isinstance(g,wg.Graph),"ONET_GRAPH_REQUIRED")
    p=g.profile(code)
    nodes=[p["occupation"]]+[t["task"] for t in p["tasks"]]
    ids={n["id"] for n in nodes}
    require(len(ids)==len(nodes),"ONET_PROFILE_DUPLICATE")
    es=[];cs=[];edges=[];entities=[]
    def make_evidence(table,row):
        m=g.manifest[table];stamp=datetime.fromisoformat(m["retrieved_at"])
        require(stamp.tzinfo is not None,"ONET_VINTAGE")
        ident=digest(canonical([table,row,m["sha256"],m["retrieved_at"]]))
        ev=Evidence("onet:ev:"+ident,1,"NATIVE_SOURCE",m["url"],f"{table}.csv:{row}",m["sha256"],"O*NET "+wg.VERSION+" / "+m["retrieved_at"],stamp.date().isoformat(),None,"INTERNAL_ONLY","DESCRIPTIVE_ONLY")
        if ev.key not in {e.key for e in es}:es.append(ev)
        return ev,Scope("O*NET reference description, not workforce sample","US",wg.SCHEME,stamp.date().isoformat(),stamp.date().isoformat(),"NOT_APPLICABLE")
    for n in nodes:
        entities.append(Entity(n["id"],1,"OCCUPATION" if n["kind"]=="occupation" else "TASK",n["label"],n["id"]))
    for link in g.edges.values():
        if link["kind"]!="OCCUPATION_TASK" or link["from"] not in ids or link["to"] not in ids:continue
        ev,s=make_evidence(link["source"],link["source_row"])
        h=digest(canonical([link["from"],link["to"],ev.key]))
        c=Claim("onet:claim:"+h,1,"OBSERVATION","Native occupation-task relation","Reference classification only",s,None,(ev.key,),(),"O*NET native classification; scope date is intake, not survey date","Not a current observation of actual task time; US only","No crosswalk or automation inference","Revised reference version",())
        cs.append(c);edges.append(Assertion("onet:edge:"+h,1,link["from"]+"@1",link["to"]+"@1","CLASSIFICATION",c.key,"Native source relation",None))
    if include_candidate:
        require(code==invoice_pilot.CODE,"CANDIDATE_SCOPE")
        process,task=invoice_pilot.make(g)
        ev,s=make_evidence(task["source"],task["source_row"])
        # Proposed process is not itself a native source record.
        h=digest(canonical([process.id,process.revision,ev.key]))
        entities.append(Entity(process.id,process.revision,"PROCESS","Candidate W001 invoice control",process.scope))
        c=Claim("candidate:claim:"+h,1,"MECHANISM_HYPOTHESIS","Candidate decomposition of invoice control","Design for practitioner review",s,None,(ev.key,),(),"O*NET task anchor only; proposed workflow","Not observed, no timings or adoption estimates","Alternative workflows and missing inputs","Independent practitioner review",())
        cs.append(c)
        edges.append(Assertion("candidate:anchor:"+h,1,task["id"]+"@1",process.id+"@"+str(process.revision),"DEPENDENCY",c.key,"NON_TRANSMISSION: proposed decomposition",None))
        for step in process.steps:
            a=step.action
            entities.append(Entity(a.id,a.revision,"ACTION",a.verb+" "+a.object,a.context))
            edges.append(Assertion("candidate:step:"+h+":"+step.id,1,process.id+"@"+str(process.revision),a.id+"@"+str(a.revision),"DEPENDENCY",c.key,"NON_TRANSMISSION: proposed membership",None))
    return Graph(requirements or Requirements(),entities=entities,evidence=es,claims=cs,assertions=edges)
