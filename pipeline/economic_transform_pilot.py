"""W001: explicitly generated alternative graphs. Synthetic timings/outcomes, no actual AI benchmark."""
from dataclasses import replace
from .economic_transform import *
from .economic_events import Pool,Server,Visit,Execution,Case
from .economic_events_pilot import fixture as event_fixture
from .work_process import Process,Step,Transition
from .invoice_pilot import make
from .work_graph import build

def variants(base):
    original={s.id:s for s in base.steps}
    b=event_fixture(base)[0]
    # Same cohort and risk categories in all variants. Imperfect human reference, not a gold standard.
    b=replace(b,label="Traitement et contrôle humains",quality_floor_num=95,cases=tuple(replace(c,correct=i!=59) for i,c in enumerate(b.cases)))
    def quality(s,critical=False):
        return tuple(Quality(c.id,"HIGH" if i%5==0 else "STANDARD",c.correct,"NONE" if c.correct else ("CRITICAL" if critical and i==0 else "NONCRITICAL")) for i,c in enumerate(s.cases))
    def roles(step,execution=(),verification=(),authorization=(),condition="Chaque passage par cette étape"):
        return Roles(step,execution,verification,authorization,"Entreprise responsable (hypothèse, attribution juridique non vérifiée)",condition)
    def design(p,s,changes,rr,critical=False):
        return Design(s.id+":design",1,s.label,process_pin(base),process_pin(p),changes,rr,quality(s,critical),"UNKNOWN","France, contrôle documentaire uniquement, hors paiement; obligations non vérifiées","Durées et qualité assignées, non mesurées, humains et machines mêmes critères","Arrêt/repli à qualifier, non simulé")
    br=tuple(roles(k,verification=("review",)) if k in ("check","exception") else roles(k,execution=("review",)) if k=="escalate" else roles(k,execution=("clerk",)) for k in original)
    bd=design(base,b,tuple(Change((k,),(k,),"Référence") for k in original),br)
    def alternative(mode,critical=False):
        require(mode in {"machine-control","human-release","sample","autonomy"},"MODE")
        merged=replace(original["extract"].action,id="octave:action:invoice-merged-control",verb="Extraire, rapprocher et vérifier",object="facture et pièces",inputs=base.external_inputs,outputs=("champs","ecarts","decision"),acceptance=("Trace des contrôles et écarts conservée",))
        steps=[Step("merged",merged,"Système automatisé","Traitement et vérification automatisés")]
        rr=[roles("merged",execution=("machine",),verification=("machine",))]
        changes=[Change(("extract","match","check"),("merged",),"Fusion de trois opérations; exécution et vérification automatisées")]
        for k in ("accept","exception","escalate"):
            old=original[k];human=mode!="autonomy" and k=="exception"
            pool="review" if human else "machine"
            steps.append(replace(old,actor="Humain" if human else "Système automatisé",system="Revue humaine" if human else "Traitement automatisé"))
            rr.append(roles(k,verification=(pool,) if k=="exception" else (),execution=() if k=="exception" else (pool,)))
            changes.append(Change((k,),(k,),"Maintien de la sortie; réallocation explicite de l'acteur"))
        edges=[Transition("merged","exception","Anomalie signalée"),Transition("exception","escalate","Dossier constitué")]
        extra=None
        if mode in {"human-release","sample"}:
            extra="authorize" if mode=="human-release" else "sample-check"
            action=replace(original["check"].action,id="octave:action:invoice-"+extra,verb="Autoriser" if mode=="human-release" else "Vérifier par échantillonnage",object="dossier normal",inputs=("decision",),outputs=("revue_normale",),acceptance=("Trace de la décision humaine",))
            steps.append(Step(extra,action,"Responsable humain","Revue"))
            rr.append(roles(extra,authorization=("review",) if mode=="human-release" else (),verification=("review",) if mode=="sample" else (),condition="Dossiers normaux uniquement" if mode=="human-release" else "Un dossier normal sur cinq selon règle explicite"))
            changes.append(Change((),(extra,),"Nouveau contrôle ou autorisation distincte"))
            edges.append(Transition("merged",extra,"Normal et soumis à revue"));edges.append(Transition(extra,"accept","Revue terminée"))
            # Require the authorization trace on the mandatory route, not on unsampled paths.
            if mode=="human-release":
                steps=[replace(s,action=replace(s.action,inputs=("decision","revue_normale"))) if s.id=="accept" else s for s in steps]
            else:edges.append(Transition("merged","accept","Normal non échantillonné"))
        else:edges.append(Transition("merged","accept","Normal"))
        p=Process("octave:process:invoice-"+mode,1,base.scope,"merged",tuple(steps),tuple(edges),("accept","escalate"),base.external_inputs)
        cases=[]
        for i,c in enumerate(b.cases):
            es=[Execution("merged",(Visit("machine",120),))]
            if i%5==0:
                es.extend((Execution("exception",(Visit("machine" if mode=="autonomy" else "review",180),)),Execution("escalate",(Visit("machine",30),))))
            else:
                if mode=="human-release" or mode=="sample" and i%5==1:es.append(Execution(extra,(Visit("review",60),)))
                es.append(Execution("accept",(Visit("machine",30),)))
            cases.append(Case(c.id,c.arrival,tuple(es),not(critical and i==0)))
        labels={"machine-control":"Vérification automatisée, intervention humaine sur anomalies","human-release":"Vérification automatisée, autorisation humaine des dossiers normaux","sample":"Vérification automatisée, contrôle humain d'un échantillon","autonomy":"Traitement et contrôle automatisés sans intervention humaine par dossier"}
        s=replace(b,id="w001:struct-"+mode+("-stress" if critical else ""),label=labels[mode]+(" — erreur critique supposée" if critical else ""),process_sha256=process_pin(p),cases=tuple(cases),assumption_note="Scénario synthétique; qualité assignée, aucune validation technique ou juridique.")
        return p,s,design(p,s,tuple(changes),tuple(rr),critical)
    return b,bd,tuple(alternative(m) for m in ("machine-control","human-release","sample","autonomy"))+(alternative("autonomy",True),)

def audit(base):
    b,bd,alternatives=variants(base)
    x=evaluate(base,base,b,bd)["result"];rows={}
    def summary(r):
        e=r["event_receipt"]["result"]
        return {"label":r["label"],"steps":r["step_count"],"completed":e["completed_cases"],"correct_completed":e["correct_completed_cases"],"human_seconds":e["human_service_seconds"],"human_touched_cases":r["human_touched_cases"],"human_verification_started_cases":r["human_verification_started_cases"],"human_authorization_started_cases":r["human_authorization_started_cases"],"quality_assigned":e["quality_assigned_cohort"],"critical_defects_assigned":r["critical_defects_assigned"],"quality_by_class":r["quality_by_class"],"deployment":r["deployment"]}
    for p,s,d in alternatives:
        r=compare_design(base,b,bd,p,s,d)
        assert r==compare_design(base,b,bd,p,s,d)
        rows[s.id]={"alternative":summary(r["result"]["alternative"]["result"]),"quality_comparable":r["result"]["quality_comparable"],"delta":r["result"]["delta"],"sha256":r["sha256"]}
    return {"fixture":"W001_STRUCTURAL_SYNTHETIC","baseline":summary(x),"alternatives":rows,"scientific_gate_promoted":False,"publication":"BLOCK_PUBLICATION"}
if __name__=="__main__":
    import json
    p,_=make(build());print(json.dumps(audit(p),ensure_ascii=False,indent=2))
