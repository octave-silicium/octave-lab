"""PILOT-W001: source-anchored candidate workflow, not an observed organization."""
from .work_actions import Action,Evidence,Modality
from .work_process import Process,Step,Transition
from .work_graph import build
import json
CODE="43-3031.00"
TASK_PREFIX="Check figures, postings, and documents"
def make(graph):
    p=graph.profile(CODE)
    matches=[t["task"] for t in p["tasks"] if t["task"]["label"].startswith(TASK_PREFIX)]
    if len(matches)!=1:raise ValueError("SOURCE_TASK_NOT_UNIQUE")
    task=matches[0];m=graph.manifest[task["source"]]
    ev=Evidence(m["url"],f'{task["source"]}.csv:{task["source_row"]}',m["sha256"],"REFERENCE")
    def step(i,verb,obj,inputs,outputs,acceptance,actor="Comptable fournisseur",system="ERP et pièces"):
        a=Action("octave:action:invoice-"+i,1,(task["id"],),verb,obj,"Contrôle d'une facture fournisseur dans un scénario B2B hypothétique",tuple(inputs),tuple(outputs),(acceptance,),Modality.DIGITAL,("Pièces accessibles et règles comptables définies","Aucune écriture ni paiement automatique autorisé dans ce pilote"),(ev,))
        return Step(i,a,actor,system)
    steps=(
        step("extract","Extraire","champs facture",["facture"],["champs"],"Champs requis associés à une preuve dans le document"),
        step("match","Rapprocher","facture et commande",["champs","commande","reception"],["ecarts"],"Comparaison des quantités, références et montants"),
        step("check","Vérifier","calculs et codes",["champs","ecarts","regles"],["decision"],"Écarts et règles violées explicités"),
        step("accept","Documenter","contrôle conforme",["decision"],["dossier_controle"],"Trace de contrôle disponible ; pas de paiement"),
        step("exception","Qualifier","anomalie",["decision","ecarts"],["dossier_anomalie"],"Motif et pièces manquantes explicités"),
        step("escalate","Transmettre","dossier anomalie",["dossier_anomalie"],["dossier_transmis"],"Réception par responsable à vérifier",system="File de revue"),
    )
    edges=tuple(Transition(*e) for e in [
        ("extract","match","Champs disponibles"),("match","check","Rapprochement réalisé"),
        ("check","accept","Conforme selon les règles"),("check","exception","Écart ou incertitude"),
        ("exception","escalate","Dossier constitué")])
    proc=Process("octave:process:invoice-control",1,"Facture avec commande et réception disponibles ; contrôle seulement, hors paiement, litiges et traitement complet des pièces absentes","extract",steps,edges,("accept","escalate"),("facture","commande","reception","regles"))
    return proc,task
if __name__=="__main__":
    p,t=make(build())
    print(json.dumps({"audit":p.audit(),"occupation":CODE,"task_id":t["id"],"task_row":t["source_row"],"source_sha256":p.steps[0].action.evidence[0].sha256,"source_task_verified":True},indent=2))
