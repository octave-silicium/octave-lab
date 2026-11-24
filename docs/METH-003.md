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

## Avancement G-M0 v0.2
[Contrats actions et crosswalks, qualification Europe](G2-EUROPE.md) : modèle initial testé sur fixtures, aucune action réelle ni correspondance validée. ROME/ESCO restent des référentiels distincts ; import ESCO prêt pour archive officielle, ROME accès à qualifier. 164 tests Python et audit d'accès réussis ; G-M0 partiel.

## Avancement G2 v0.4
[Explorateur des référentiels natifs](G2-WORK-EXPLORER.md) : ROME résolu dans son périmètre, ESCO hiérarchies et relations supplémentaires contrôlées sur le lot privé, matrices historiques FAP conservées ; O*NET/ROME HTTP vérifiés, aucune correspondance internationale ni action/processus validés. G-M0 partiel, G-M1 à construire.

## Avancement G2 v0.5
[W001](G2-PILOT-W001.md) : graphe inverse et premier processus candidat à chemins exclusifs, 6 actions et 5 transitions, ancrage O*NET vérifié ; 193 tests et HTTP O*NET/ROME réussis. SQL ESCO réel vérifié, pas HTTP. G-M0 partiel, G-M1 non franchi faute de revue indépendante, aucune observation, durée, capacité IA ou estimation économique validée. Protocole de revue humaine défini, benchmark BPMN/O*NET/NBER documenté.

## Avancement G2 v0.6
[G2-EXPERIMENT](G2-EXPERIMENT.md) : évaluations O*NET IM/RT/FT natives avec date/incertitude et masquage ; pas de durée. W001 synthétique : règles classiques comme 4e bras de comparaison, 16/16 sur cas construits, aucun humain/IA mesuré ; protocole et formulaire de revue vierge. G-M1/G-M2 non franchis.

## Avancement G2 v0.7
[G2-DOCUMENTS](G2-DOCUMENTS.md) : dossiers textuels synthétiques et règle conventionnelle prudente ; baseline v2 11/20 exacts et 9 abstentions, aucun faux accepté. Module temps mural/temps humain, supervision, correction et coût complet conditionnel aux données, valeurs manquantes non imputées. Jeu fermé, praticiens et résultats IA réels absents ; aucun impact validé.

## Avancement G2 v0.8
[G2-MODEL-COMPARISON](G2-MODEL-COMPARISON.md) : premier test de développement GPT-6.2 en contexte, 20/20 contre 16/20 classique, 4 cas supplémentaires texte libre ; non aveugle, aucune mesure réelle de temps/coût, aucune supériorité démontrée. Protocole de transfert indépendant et export candidat seul. G-M1/G-M2 ouverts, dépendances externes ; les scénarios économiques peuvent être développés conditionnellement sans franchir les gates.

## Décision de portée 24/11/2026 : ARCH-002 v2.0
La cible intégrale validée est [ARCH-002](ARCH-002.md) et son [registre machine-readable](../governance/economic_mechanisms_v2.json). Neuf couches, six moteurs et 64 mécanismes initiaux, statut exigences validées, méthodes/paramètres/implémentations à qualifier. Les six niveaux historiques, METH-003, BENCH-001 et gates G-M0…G-M5 restent applicables ; E-G0…E-G6 complémentaires non franchis. G3 est redéfini comme tranche micro→marché, G4 réseaux et agrégation, G5 validation/produit ; acquisition, G2 indépendant et déploiement en parallèle. Aucune preuve de différenciation ou impact nouveau.

## Exigence de restitution complète 24/11/2026
[RESULT-001](RESULT-001.md) et [contrat machine-readable](../governance/investigation_result_v1.json) sont normatifs : trois niveaux synchronisés (synthèse, dossier détaillé, preuve/reproduction), 18 sections obligatoires ou limite motivée, évaluation explicite de chaque mécanisme/couche/moteur/interface du registre épinglé, résultats non triviaux et interactions, scénarios opposés, seuils, hétérogénéité, réfutation et angles morts, décisions conditionnelles. Aucune omission silencieuse ni exhaustivité scientifique proclamée; pertinence et preuves priment sur volume. Contrat à implémenter dès première tranche G3 ; E-G5/E-G6 et gates UX non franchis.

## Prospective multi-ordres — précision du 24/11/2026
[PROSPECT-001](PROSPECT-001.md) et [contrat computationnel](../governance/multi_order_prospective_v1.json) précisent l'exigence transversale : O1/O2/O3/O4+ selon chemins qualifiés, ordre distinct d'horizon/scénario/preuve, branches concurrentes, réactions stratégiques, interactions et rétroactions, seuils et règles d'arrêt. Comparer trajectoires cohérentes, pas sommer les chemins; aucune extrapolation causale ou probabilité fictive. Restitution D12/D13/D15/D16/D17 et preuve D18, dès tranche G3 avec limitations explicites. Les six moteurs, neuf couches et 64 mécanismes initiaux sont conservés. Spécification uniquement, gates inchangés.
