# OCTAVE LAB — État et feuille de route
Référence publique au 24 novembre 2026. Le statut d'une décision ne vaut pas preuve de fonctionnement.

## État de départ
- G0 : prototype et pipeline descriptif existants. Indeed France : collecte historique vérifiée ; Dares, Urssaf et Eurostat : audits techniques réalisés. Insee : normalisation de séries trimestrielles.
- 79 entrées candidates recensées ; ni 79 bases intégrées, ni 79 lignées indépendantes.
- [PILOT-001](../research/PILOT-001/rapport.md) : observations descriptives sur NACE J ; deux lignées principales (Urssaf et Eurostat). Pas de preuve causale.
- [Gouvernance](../pipeline/data_governance.py) : contrôles provisoires de droits et ruptures ; leur intégration systématique aux futures sorties reste à faire.
- METH-003 : décision validée, première implémentation partielle G2.

## Ordre de développement validé
| Jalon | Résultat attendu | Statut initial |
|---|---|---|
| S0 | Synchronisation README, spécification METH-003, état et feuille de route | VÉRIFIÉ |
| S1 / G1 | Contrats sémantiques communs : mesure, unité, population, dimensions et référentiels versionnés, période/vintage, provenance, licence, comparabilité, preuve ; préparer G-M0 | PARTIELLEMENT VÉRIFIÉ : [S1 v0.4](SEMANTIC-V4.md), 130 tests, neuf jeux interrogeables ; coffre de production, droits, qualification géographique et comparabilité restent ouverts |
| S2 / G1 | Explorateur multisource : recherche, filtres de couverture, historiques, comparaison conditionnelle, provenance et exports autorisés ; exigences [UX-001](UX-001.md), gates UX-G0 à UX-G4 | [G1 v0.4](G1-EXPLORER.md) table de confrontation et pistes natives implémentées ; v0.4 vérifié en Chromium sur quatre tailles, audit esthétique et gates restants ouverts |
| S3 / G2 | Qualification ROME/ESCO/O*NET, ontologie G-M0 et petit pilote G-M1 ; processus réel, vérification humaine | [G2 v0.1](G2-WORK-GRAPH.md) socle O*NET vérifié ; [G2 v0.2](G2-EUROPE.md) import ESCO et contrat d'action testés, accès européens audités, 164 tests ; G-M0 partiel, fichiers réels Europe et processus non validés |
| S4 / G3–G5 | Investigations, tests G-M2–G-M5, approfondissement sectoriel et moteur économique, validation empirique puis extension progressive | Validé, non implémenté |
| S5 | Démonstration publique reproductible et validation de la demande professionnelle | À préparer |

Les travaux transversaux continuent en parallèle ; les jalons ne certifient pas tous les gates de données. Architecture cible : capacités IA → tâches/actions → métiers → entreprises/processus → marchés/chaînes de valeur → macroéconomie.

## Registre des chantiers ouverts
| ID | Sujet | Statut / critère de clôture |
|---|---|---|
| OPEN-01 | DPAE 2025 | BLOQUÉ pour comparaisons touchées ; vintages et correction déclarative à vérifier |
| OPEN-02 | Dares MMO | BLOQUÉ : récupérer par accès officiel le fichier, qualifier licence et schéma |
| OPEN-03 | Triangulation | PROPOSÉ/à vérifier : troisième lignée suffisamment indépendante et compatible ; trois fichiers ne constituent pas trois preuves |
| OPEN-04 | Sources candidates | En cours : qualification progressive des 79 entrées, droits, couverture, fréquences |
| OPEN-05 | Benchmark d'excellence scientifique, architecture et UX, notamment US | Exigence transversale validée : [BENCH-001](BENCH-001.md) ; audits détaillés et adoption des méthodes restent à qualifier |
| OPEN-06 | ODbL | BLOQUÉ pour les usages publics/commerciaux concernés non qualifiés ; revue par cas d'usage |
| OPEN-07 | Pilote NACE J | En cours : décomposition JA/JB/JC, série d'emploi compatible indépendante, flags et adoption à définition stable |
| OPEN-08 | Validation commerciale | À tester : demande B2B distincte de l'audience X |
| OPEN-09 | Nomenclatures et ruptures | En cours : révisions, apprentis, DSN, NAF 2025 à partir de 2027 ; mappings explicites |

## Discipline
VALIDÉ = décision approuvée ; IMPLÉMENTÉ = code présent ; VÉRIFIÉ = preuve d'exécution et critères satisfaits ; BLOQUÉ = obstacle documenté ; PROPOSÉ = piste non approuvée. Les états peuvent coexister à des niveaux différents. Chaque jalon clôturé exige preuves, limites, chantiers ouverts et cohérence entre documentation stratégique et dépôt. Les analyses descriptives, hypothèses et conclusions causales restent séparées.

## Actualisation des sources
[DATA-REFRESH-001](DATA-REFRESH-001.md) : maximiser l'automatisation licite ; registre de fraîcheur, validation et versionnement à implémenter. ROME ZIP CSV/JSON récupérés automatiquement (parsing à faire), ESCO ZIP et Dares protégés en file manuelle.

G2 v0.3 : [lot utilisateur importé localement](G2-LOCAL-INTAKE.md), ESCO bilingue, FAP natif et probabilités PCS, MMO ; G-M0 partiel, pas de raccordement à l'API ni de publication.

Consolidation infrastructure : [Data Observatory v0.1](DATA-OBSERVATORY.md), registre et workflow configurés, première exécution réelle, inventaire ROME vérifié ; stockage/promotion/raccordement à réaliser avant explorateur des métiers.

Consolidation v0.2 : [coffre local et pont privé G2](DATA-VAULT.md) ; stockage durable, orchestration/promotion et raccordement HTTP restent ouverts. Explorateur métier après consolidation.

Consolidation v0.3 : [maintenance locale](DATA-MAINTENANCE.md) sauvegarde/restauration et révisions sept jeux, calendrier persistant, API G2 opt-in. Stockage durable et activation planifiée, rattachement des versions actives au catalogue et validation scientifique restent ouverts.

Consolidation v0.4 : catalogue sur actifs approuvés, recette intégrale neuf jeux réussie (186 tests) ; [runbook](RUNBOOK-001.md). Gate production non atteint, choix d'hôte distinct. Reprise de G-M0 (liens ROME et tables complémentaires), puis explorateur métiers et pilote processus, sans bloquer sur hébergement ni élargissement des 79 candidats.

G2 v0.4 : [référentiels natifs et explorateur métiers](G2-WORK-EXPLORER.md), 141 163 liens ROME résolus, lot privé ESCO/FAP enrichi, 188 tests et HTTP O*NET/ROME vérifiés ; UI à valider sur navigateur, pas de score ni équivalence internationale. Reprise pilote actions/processus après qualification des parcours.

G2 v0.5 : [navigation inverse et W001](G2-PILOT-W001.md), 193 tests, HTTP O*NET/ROME vérifiés, SQL ESCO réel, premier processus proposé lié à une tâche native. G-M1 ouvert, revue par praticiens non faite ; prochaine étape : paquet de revue et qualification du protocole de mesure, données task ratings et tests de capacité distincts.

G2 v0.6 : [ratings et protocole expérimental](G2-EXPERIMENT.md), 165 780 ratings O*NET intégrés, navigateur v0.5 vérifié, baseline W001 synthétique 16/16 ; revue humaine et essais comparatifs réels non réalisés, G-M1/G-M2 ouverts.

G2 v0.7 : [documents et coût complet](G2-DOCUMENTS.md), 20 dossiers synthétiques hétérogènes, baseline v2 11/20, module coût/temps testé, v2.1 et support jeu indépendant vérifiés. G-M1/G-M2 ouverts, priorité essai fermé indépendant et collecte mesures humaines/IA.

G2 v0.8 : [comparateur et transfert expérimental](G2-MODEL-COMPARISON.md), soumission GPT-6.2 en contexte sur jeu connu 20/20 vs 16/20, aucune validation indépendante. Dépendances externes de G-M1/G-M2 explicites ; poursuivre scénarios économiques conditionnels sans résultat inventé.

## Décision de portée 24/11/2026 : ARCH-002 v2.0
La cible intégrale validée est [ARCH-002](ARCH-002.md) et son [registre machine-readable](../governance/economic_mechanisms_v2.json). Neuf couches, six moteurs et 64 mécanismes initiaux, statut exigences validées, méthodes/paramètres/implémentations à qualifier. Les six niveaux historiques, METH-003, BENCH-001 et gates G-M0…G-M5 restent applicables ; E-G0…E-G6 complémentaires non franchis. G3 est redéfini comme tranche micro→marché, G4 réseaux et agrégation, G5 validation/produit ; acquisition, G2 indépendant et déploiement en parallèle. Aucune preuve de différenciation ou impact nouveau.

## Exigence de restitution complète 24/11/2026
[RESULT-001](RESULT-001.md) et [contrat machine-readable](../governance/investigation_result_v1.json) sont normatifs : trois niveaux synchronisés (synthèse, dossier détaillé, preuve/reproduction), 18 sections obligatoires ou limite motivée, évaluation explicite de chaque mécanisme/couche/moteur/interface du registre épinglé, résultats non triviaux et interactions, scénarios opposés, seuils, hétérogénéité, réfutation et angles morts, décisions conditionnelles. Aucune omission silencieuse ni exhaustivité scientifique proclamée; pertinence et preuves priment sur volume. Contrat à implémenter dès première tranche G3 ; E-G5/E-G6 et gates UX non franchis.

## Prospective multi-ordres — précision du 24/11/2026
[PROSPECT-001](PROSPECT-001.md) et [contrat computationnel](../governance/multi_order_prospective_v1.json) précisent l'exigence transversale : O1/O2/O3/O4+ selon chemins qualifiés, ordre distinct d'horizon/scénario/preuve, branches concurrentes, réactions stratégiques, interactions et rétroactions, seuils et règles d'arrêt. Comparer trajectoires cohérentes, pas sommer les chemins; aucune extrapolation causale ou probabilité fictive. Restitution D12/D13/D15/D16/D17 et preuve D18, dès tranche G3 avec limitations explicites. Les six moteurs, neuf couches et 64 mécanismes initiaux sont conservés. Spécification uniquement, gates inchangés.

## G3.1 v0.1 — Economic Core
[Documentation](G3-ECONOMIC-CORE.md), [audit](../audits/economic_core_v01_verified.json), 224 tests et pont G1 Eurostat NACE vérifiés (12 400 cellules, 6 593 admises, 5 807 bloquées). Contrats versionnés, graphe de provenance, 110 entrées de couverture et chemins structurels; aucun calcul d'effet ni validation causale. E-G0 partiel. Suite : compléter jonctions et contrats minimaux puis G3.2 transformation opérationnelle, tranche verticale; G2 indépendant, données et déploiement restent ouverts.

## G3.1 v0.2 — ponts et calculs conditionnels
[Documentation](G3-ECONOMIC-BRIDGE.md) : implémentation pont archives/vault, profil O*NET/W001 candidat, cinq opérations conditionnelles et manifeste interne reproductible. Recette CI réussie : 229 tests, Eurostat, O*NET officiel et coffre Indeed temporaire ; [audit](../audits/economic_bridge_v02_verified.json). Aucun gate promu. Suite : compléter PROSPECT-001 et lancer G3.2 sur W001.

## G3.1 v0.3 — Prospective structural contracts
[Documentation](G3-PROSPECTIVE-ENGINE.md) : scénario de référence et alternatives, ordre et délai distincts, acteurs, chemins concurrents, interactions, frontière et arrêt, dix familles évaluées, replay épinglé. Pas de propagation chiffrée ni gate scientifique. Recette CI réussie : 249 tests, [audit](../audits/economic_prospective_v03_verified.json). Prochaine tranche G3.2 W001 opérationnelle.

## G3.2 v0.1 — Operational transformation
[Documentation](G3-OPERATIONS.md) : enveloppe déterministe de capacité/charge et qualité, benchmark MIT/NIST/SimPy, W001 synthétique. Recette CI réussie : 263 tests ; [audit](../audits/economic_operations_v01_verified.json). E-G1 non franchi. Suite : files/calendriers et reprises, refonte structurelle, intégration investigation puis G3.3/G3.4.

## Exigence transversale — clarté terminologique et pédagogie (24/11/2026)
Décision utilisateur : [UX-001](UX-001.md) et [RESULT-001](RESULT-001.md) complétés. Intitulés clairs pour tous, aide contextuelle discrète et accessible, registre terminologique commun, détails progressifs, unités/périmètres et réserves visibles, contrôle de compréhension non spécialiste. Appliquer dès les nouveaux écrans et restitutions ; audit/rétrofit des écrans existants avant recette publique. Implémentation UI et recette à faire ; G3.2 v0.2 reste la prochaine tranche scientifique.

## G3.2 v0.2 — Simulation des opérations dans le temps
[Documentation](G3-EVENTS.md) : événements discrets à entrées explicites, calendriers, ressources partagées, reprises bornées, arrivées groupées, files et censures, comparaison qualité et cohorte, glossaire FR initial. Recette réussie : 281 tests, [audit](../audits/economic_events_v02_verified.json) ; pas de validation terrain. Suite : refonte structurelle, deuxième processus, raccordement puis G3.3/G3.4.


## Précision utilisateur — régimes de contrôle et responsabilité (24/11/2026)
[TRANSFORM-001](TRANSFORM-001.md) : distinguer exécution, vérification, autorisation et responsabilité à chaque action/point de contrôle; familles composables jusqu'à autonomie nominale complète, contrôle humain non présumé permanent, qualification technique et réglementaire par contexte, criticité et repli. Exploration de variantes paramétrables selon matérialité, limites explicites, pas d'exhaustivité combinatoire. Zéro erreur observée ≠ risque nul; fiabilité parfaite hypothétique admise en scénario. W001 redesign historique = assistance IA et contrôle humain accéléré, pas refonte. G3.2 v0.3 : implémentation progressive et tests, exigences scientifiques inchangées.

## G3.2 v0.3 — Refonte structurelle, première tranche
[Documentation](G3-TRANSFORM.md) : fusion effective et rôles distincts, variants W001 machine/autorisation/échantillon/autonomie et défaut critique, qualité symétrique humain-machine. Recette réussie : 294 tests, [audit](../audits/economic_transform_v03_verified.json). TRANSFORM-001 précisé. Suite : second processus, politiques de file, synchronisation, sensibilité et raccordement avant G3.3/G3.4.

## G3.2 v0.4a — Deuxième processus et contributions
[W002](G3-PHYSICAL.md) : contrôle dimensionnel industriel, même moteur, ancrage O*NET, contraintes instrumentales, variantes numériques et physiques, stress. [CONTRIB-001](CONTRIB-001.md) admission interne et revue indépendante. Recette réussie : 303 tests, [audit](../audits/economic_physical_v04a_verified.json) ; aucun gate scientifique. Suite : politiques de file, synchronisation, audits/repli, liaison investigation, G3.3/G3.4.

## G3.2 v0.4b — Parallélisme et ressources conjointes
[Documentation](G3-PARALLEL.md) : sous-tâches parallèles dans une étape, jointures, ressources atomiques, deux politiques de priorité, audits périodiques, indisponibilité et réallocation statique hypothétiques. Recette à confirmer. Contrat limité, criticité/repli dynamique et intégration RESULT/PROSPECT ouverts ; G3.3 prochain moteur économique après jonction minimale.
