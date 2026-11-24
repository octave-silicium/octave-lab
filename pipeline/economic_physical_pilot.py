"""W002: physical dimensional inspection. Native O*NET anchor, synthetic workflow/inputs."""
from dataclasses import replace
from .work_actions import Action,Evidence,Modality
from .work_process import Process,Step,Transition
from .economic_core import Scope,require
from .economic_operations import process_pin
from .economic_events import Pool,Server,Visit,Execution,Case,Schedule
from .economic_transform import Change,Roles,Quality,Design,evaluate,compare_design
from .work_graph import build

CODE="51-9061.00"
TASK_PREFIX="Inspect, test, or measure materials, products, installations, or work for conformance to specifications"

def make(graph):
    profile=graph.profile(CODE)
    matches=[x["task"] for x in profile["tasks"] if x["task"]["label"].startswith(TASK_PREFIX)]
    require(len(matches)==1,"SOURCE_TASK_NOT_UNIQUE")
    t=matches[0];m=graph.manifest[t["source"]]
    ev=Evidence(m["url"],f'{t["source"]}.csv:{t["source_row"]}',m["sha256"],"REFERENCE")
    scope="Contrôle dimensionnel unitaire de pièces usinées, hors fabrication, retouche et libération réglementaire"
    inputs=("piece_identifiee","plan_tolerances","instrument_qualifie")
    def step(k,verb,obj,ins,outs,mod,actor,system):
        a=Action("octave:action:dim-"+k,1,(t["id"],),verb,obj,scope,tuple(ins),tuple(outs),("Résultat traçable selon le contrat du scénario",),mod,("Instrument et méthode qualifiés à vérifier; aucune libération réglementaire",),(ev,))
        return Step(k,a,actor,system)
    steps=(
      step("load","Positionner","pièce",inputs,("piece_positionnee",),Modality.PHYSICAL,"Opérateur","Poste de mesure"),
      step("measure","Mesurer","dimensions",("piece_positionnee","instrument_qualifie"),("mesures",),Modality.PHYSICAL,"Instrument","Instrument dimensionnel"),
      step("unload","Retirer","pièce",("piece_positionnee","mesures"),("piece_retiree",),Modality.PHYSICAL,"Opérateur","Poste de mesure"),
      step("interpret","Comparer","mesures aux tolérances",("mesures","plan_tolerances","piece_retiree"),("decision",),Modality.DIGITAL,"Contrôleur","Logiciel de mesure"),
      step("accept","Documenter","pièce conforme",("decision",),("rapport_conforme",),Modality.DIGITAL,"Contrôleur","Registre"),
      step("reject","Documenter","écart dimensionnel",("decision",),("rapport_ecart",),Modality.DIGITAL,"Contrôleur","Registre"))
    edges=tuple(Transition(*x) for x in (("load","measure","Pièce positionnée"),("measure","unload","Mesure terminée"),("unload","interpret","Pièce retirée"),("interpret","accept","Conforme"),("interpret","reject","Écart")))
    return Process("octave:process:dimensional-inspection",1,scope,"load",steps,edges,("accept","reject"),inputs),t

def variants(base):
    H=7200;scope=Scope("Atelier fictif, contrôle dimensionnel unitaire","FR","synthetic not representative","2026-01-01","2026-01-01","not monetized")
    output="Rapport traçable conforme ou écart, sans fabrication, retouche ou libération réglementaire"
    old={s.id:s for s in base.steps}
    def build_variant(mode,cycle=300,devices=1,critical=False):
        require(mode in {"human","digital","robot"} and type(cycle) is int and cycle>0 and type(devices) is int and 1<=devices<=4,"VARIANT")
        steps=list(base.steps);edges=base.transitions;changes=[Change((k,),(k,),"Étape conservée") for k in old]
        if mode!="human":
            merged=replace(old["interpret"].action,id="octave:action:dim-auto-interpret",verb="Comparer automatiquement",object="mesures et tolérances")
            steps=[replace(s,action=merged,actor="Système de décision",system="Logiciel") if s.id=="interpret" else replace(s,actor="Système de décision",system="Logiciel") if s.id in ("accept","reject") else s for s in steps]
        if mode=="robot":
            steps=[replace(s,actor="Robot",system="Manipulation automatisée") if s.id in ("load","unload") else s for s in steps]
        p=base if mode=="human" else Process("octave:process:dim-"+mode,1,base.scope,base.entry,tuple(steps),edges,base.terminals,base.external_inputs)
        pools=(Pool("operator","HUMAN",(Server("o1",((0,H),)),)),Pool("gauge","MACHINE",tuple(Server("g"+str(i),((0,H),)) for i in range(devices))),Pool("software","MACHINE",(Server("s1",((0,H),)),)),Pool("robot","MACHINE",(Server("r1",((0,H),)),)))
        mapping={"load":("robot" if mode=="robot" else "operator",60),"measure":("gauge",cycle),"unload":("robot" if mode=="robot" else "operator",30),"interpret":("operator" if mode=="human" else "software",90 if mode=="human" else 10),"accept":("operator" if mode=="human" else "software",30 if mode=="human" else 5),"reject":("operator" if mode=="human" else "software",60 if mode=="human" else 10)}
        cases=[];qualities=[]
        for i in range(36):
            k="reject" if i%6==0 else "accept"
            path=("load","measure","unload","interpret",k)
            correct=not(critical and i==0)
            cid="piece-%03d"%i
            cases.append(Case(cid,i*150,tuple(Execution(s,(Visit(*mapping[s]),)) for s in path),correct))
            qualities.append(Quality(cid,"HIGH" if i%6==0 else "STANDARD",correct,"NONE" if correct else "CRITICAL"))
        labels={"human":"Manipulation et décision humaines, mesure instrumentale","digital":"Décision et rapport automatisés, manipulation humaine","robot":"Manipulation et décision automatisées"}
        label=labels[mode]+f" ; {devices} instrument(s), cycle de mesure {cycle} s"+(" ; défaut critique supposé" if critical else "")
        sid=f"w002:{mode}-{cycle}-{devices}"+("-stress" if critical else "")
        s=Schedule(sid,1,label,scope,output,process_pin(p),H,95,100,pools,tuple(cases),"Scénario fictif; instrument autonome pendant mesure, chargement/déchargement séparés sans occupation simultanée; aucun essai réel.")
        roles=[]
        for k,(pool,_) in mapping.items():
            roles.append(Roles(k,() if k=="interpret" else (pool,),(pool,) if k=="interpret" else (),(),"Entreprise responsable (hypothèse)","Chaque passage"))
        d=Design(sid+":design",1,label,process_pin(base),process_pin(p),tuple(changes),tuple(roles),tuple(qualities),"UNKNOWN","Atelier fictif en France, hors secteur réglementé spécifique","Mesure et qualité non qualifiées, hypothèses symétriques","Repli, étalonnage, maintenance non simulés")
        return p,s,d
    return build_variant("human"),tuple(build_variant(*args) for args in (("digital",300,1),("robot",300,1),("robot",300,2),("robot",180,1),("robot",300,1,True)))

def audit(base,task):
    b,alts=variants(base)
    def row(r):
        z=r["event_receipt"]["result"]
        return {"label":r["label"],"arrivals":z["arrivals"],"completed_pieces":z["completed_cases"],"correct_completed_pieces":z["correct_completed_cases"],"unfinished_pieces":z["unfinished_cases"],"human_seconds":z["human_service_seconds"],"resources":z["resource_rows"],"critical_defects":r["critical_defects_assigned"]}
    x=evaluate(base,*b)["result"];rows={}
    for p,s,d in alts:
        receipt=compare_design(base,b[1],b[2],p,s,d)
        require(receipt==compare_design(base,b[1],b[2],p,s,d),"REPLAY")
        r=receipt["result"];rows[s.id]={"alternative":row(r["alternative"]["result"]),"quality_comparable":r["quality_comparable"],"delta":r["delta"],"sha256":receipt["sha256"]}
    return {"fixture":"W002_DIMENSIONAL_SYNTHETIC","native_task_id":task["id"],"native_task_row":task["source_row"],"source_sha256":base.steps[0].action.evidence[0].sha256,"process_sha256":process_pin(base),"baseline":row(x),"alternatives":rows,"publication":"BLOCK_PUBLICATION","scientific_gate_promoted":False}
if __name__=="__main__":
    import json
    p,t=make(build());print(json.dumps(audit(p,t),ensure_ascii=False,indent=2))
