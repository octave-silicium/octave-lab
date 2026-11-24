"""W002 concurrency, joint occupancy and scheduled system audit; all inputs invented."""
from dataclasses import replace
from .economic_parallel import *
from .economic_events import Server
from .economic_physical_pilot import make
from .work_graph import build

def fixture(process):
    H=7200;scope=Scope("Atelier fictif W002","FR","synthetic","2026-01-01","2026-01-01","not monetized")
    pools=(Pool("operator","HUMAN",(Server("o1",((0,H),)),)),Pool("gauge","MACHINE",(Server("g1",((0,H),)),)),Pool("software","MACHINE",(Server("s1",((0,H),)),)),Pool("robot","MACHINE",(Server("r1",((0,H),)),)))
    def make_plan(name,robot=False,parallel=False,audit=False,policy="READY_FIFO",outage=False,fallback=False):
        jobs=[]
        for i in range(24):
            actor="robot" if robot else "operator";end="reject" if i%6==0 else "accept"
            # Joint operation during attended measurement, no claimed model of
            # instrument ownership between load/measure/unload across jobs.
            tasks=[Task("load","load",(),60,((actor,1),("gauge",1))),Task("measure","measure",("load",),240,(("gauge",1),)),Task("unload","unload",("measure",),30,((actor,1),("gauge",1)))]
            # Separate checks of metadata and measured dimensions, synchronized
            # before reporting. Both are synthetic subtasks of interpretation.
            tasks.extend((Task("metadata","interpret",("unload",),40,(("software",1),)),Task("tolerance","interpret",("unload",) if parallel else ("metadata",),50,((("operator" if fallback else "software"),1),))))
            tasks.append(Task("report",end,("metadata","tolerance"),20,(("software",1),)))
            jobs.append(Job("piece-%03d"%i,i*200,0 if i%6==0 else 10,"PRODUCTION",tuple(tasks),True))
        if audit:
            for i,start in enumerate((900,3600)):
                jobs.append(Job("audit-%d"%i,start,1,"AUDIT",(Task("review","periodic-audit",(),300,(("operator",1),("software",1))),),None,start+900))
        pp=pools
        if parallel:pp=tuple(replace(p,servers=(Server("s1",((0,H),)),Server("s2",((0,H),)))) if p.id=="software" else p for p in pp)
        if outage:
            pp=tuple(replace(p,servers=tuple(replace(s,windows=((0,2400),(4200,H))) for s in p.servers)) if p.id=="gauge" else p for p in pp)
        return Plan("w002:parallel-"+name,1,scope,"Rapport conforme ou écart; pas de libération réglementaire",process_pin(process),H,policy,pp,tuple(jobs),95,100,"Scénario fictif. Étapes physiques sur poste avec tampon/fixtures indépendants, pas de réservation continue de pièce ni d'affinité instrument; chaque chargement/retrait exige opérateur ou robot et instrument simultanément. Audits scriptés, pas validation de sécurité.")
    return make_plan("base"),(make_plan("robot",robot=True),make_plan("parallel",robot=True,parallel=True),make_plan("audit",robot=True,parallel=True,audit=True),make_plan("priority",robot=True,parallel=True,audit=True,policy="PRIORITY_FIRST"),make_plan("outage",robot=True,parallel=True,audit=True,policy="PRIORITY_FIRST",outage=True),make_plan("fallback",robot=True,parallel=True,audit=True,policy="PRIORITY_FIRST",outage=True,fallback=True))

def audit(process):
    base,alts=fixture(process)
    fields=("completed_cases","unfinished_cases","human_service_seconds","audit_human_seconds","production_human_seconds","audit_due_count","audit_on_time_count","audit_missed_count","mean_completed_elapsed_seconds","total_ready_task_wait_seconds")
    rows={}
    for p in alts:
        r=compare(process,base,p);require(r==compare(process,base,p),"REPLAY")
        z=r["result"];rows[p.id]={"alternative":{k:z["alternative"]["result"][k] for k in fields},"quality_comparable":z["quality_comparable"],"audit_obligations_met_both":z["audit_obligations_met_both"],"sha256":r["sha256"]}
    return {"fixture":"W002_PARALLEL_SYNTHETIC","baseline":{k:simulate(process,base)["result"][k] for k in fields},"alternatives":rows,"publication":"BLOCK_PUBLICATION","scientific_gate_promoted":False}
if __name__=="__main__":
    import json
    p,_=make(build());print(json.dumps(audit(p),ensure_ascii=False,indent=2))
