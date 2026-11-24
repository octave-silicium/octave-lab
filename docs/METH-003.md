# METH-003 — Décomposition du travail
Décision validée le 24 novembre 2026. Statut : SPÉCIFICATION CIBLE ; première implémentation partielle [G2 v0.1](G2-WORK-GRAPH.md), socle natif O*NET vérifié, G-M0 partiel. Version publique 1.0.

## Objet
Pilier transversal aux six niveaux d'analyse : capacités IA, tâches, métiers, entreprises/processus, marchés/chaînes de valeur, macroéconomie. Étudier les mécanismes opérationnels et leurs conséquences économiques, sans déduire des pertes d'emploi de scores d'exposition.

## Ontologie et données
Profession (code, référentiel, version) → tâche (importance, fréquence, durée, contexte) → action élémentaire (verbe, objet, contexte, entrées, sorties, qualité) → processus (ordre, dépendances, exceptions, goulots, acteurs, systèmes) → transformation (automatisation, augmentation, déplacement, reconfiguration, nouvelle tâche) → effet économique à tester (heures, qualité, coût complet, volumes, prix, marges, emploi, valeur captée).
Relations many-to-many, couverture et non-univocité explicites. Identifiant stable, provenance/licence, contraintes et connaissances implicites, outils physiques et numériques, confidentialité, sécurité, réglementation, modalités, dépendances humaines, poids et origine, version, statut proposé/validé/testé. Distinguer actions observées ou référencées et hypothèses reconstruites par IA.

## Évaluation
- Capacité technique : version/date du modèle, outils, autonomie, contexte, coût, latence, réussite, qualité, dispersion et échecs ; tests répétés avec critères humains.
- Faisabilité opérationnelle : intégration, accès, supervision, conformité, fiabilité, exceptions et responsabilité.
- Adoption : preuves de déploiement et intensité observées, distinctes de l'exposition.
- Substitution, complémentarité et reconfiguration : coût complet humain + IA, tâches nouvelles, contrôle, décalages et demande induite.
Une notation générative n'est qu'une hypothèse. Les poids mesurés (durée, fréquence, importance, part économique) sont versionnés ; sinon scénarios et intervalles, pas de précision inventée. Rapporter dispersion, hétérogénéité et sensibilité aux poids. Reconstituer les processus complets : les dépendances et les goulots peuvent annuler les gains isolés.

## Pont économique
Capacités → tâches → processus → productivité/coût unitaire → décision de firme → emploi, salaires, prix et marges → concurrence, demande et capture de valeur. Chaque transition exige observation, identification ou paramètre de scénario documenté. Aucune somme d'actions automatisables ne donne un pourcentage de postes supprimés.

## Référentiels candidats et droits
ROME, ESCO, O*NET, ISCO/SOC et observations de terrain : qualifier versions, couverture, méthodes, mappings et droits avant réutilisation. OEM/Coface constitue une inspiration méthodologique publique, non une source de données ou de pondérations propriétaires acquises.

## Gates
| Gate | Critère de passage | Statut |
|---|---|---|
| G-M0 | Ontologie et dictionnaire versionnés, relations many-to-many, couverture et droits confirmés | À construire |
| G-M1 | Petit pilote métier ; fiches inspectables, vérification humaine, accord inter-évaluateurs, erreurs/inconnus | À construire |
| G-M2 | Tests répétés de capacités sur actions, coûts complets et limites | À construire |
| G-M3 | Processus de bout en bout, goulots, complémentarité, sensibilité | À construire |
| G-M4 | Raccordement aux observations économiques ; identification et revue adaptées pour causalité | À construire |
| G-M5 | Exports autorisés, provenance, reproductibilité point-in-time, avertissements et corrections | À construire |

Risques : biais des descriptions, généralisation, poids fictifs, dérive de modèles, dépendances, demande, correspondances ROME/ESCO/O*NET/NAF, confidentialité, propriété intellectuelle et absence de validation humaine/causale. Étiqueter explicitement exposition, capacité testée, adoption observée ou impact estimé. La qualification et l'ontologie préliminaire accompagnent G1 ; le socle natif O*NET 31.0 est vérifié dans son périmètre ; aucun modèle d'action, processus ou impact validé n'est revendiqué.
