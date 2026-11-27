# POSTLAB-CONTRADICT-001 | Programme contradictoire post-travail
27/11/2026 — VALIDÉ par le propriétaire pour les exigences, méthodes et preuves à qualifier.

## Décision et périmètre
Les 14 objections sont conservées et traitées selon les 12 axes validés. La raréfaction du travail humain, la disparition de l'emploi salarial, l'abondance matérielle et la disparition des marchés sont des hypothèses distinctes. Ni complémentarité durable ni fin du travail ne sont imposées. Les résultats peuvent réfuter la thèse privilégiée. Le registre est une matrice de couverture complémentaire, non une liste de nouveaux moteurs ou une qualification des 140 dispositions.

## Baseline et portée de l'audit
Commit de référence e4f307e1edb6e190dfb097b6bcd602ffa2ce8f94; arborescence complète listée, registres M/SH/AC/LIM lus, documents ARCH-002, COMMON-STATE, ROADMAP, PROSPECT, G3-SKILLS, G4-SECTOR et modules clés inspectés. Audit documentaire ciblé, pas lecture exhaustive de chaque code, ZIP, workflow ou test; aucune CI relancée ici. Statuts PARTIAL_SYNTHETIC = capacité technique partielle, pas preuve empirique; GAP_EXPLICIT = traitement spécifique non identifié dans les éléments examinés, pas preuve d'absence universelle. Les sources candidates ne sont pas acquises ni validées par ce jalon.

## Matrice détaillée des objections
### HA01 — Raretés physiques résiduelles (P1)
Axes B4 | PARTIAL_SYNTHETIC
- Registres : M014, M045, M047, M048, M058, SH09, SH15, AC10, AC18, AC19, AC21, LIM-S06, LIM-S13, LIM-S14.
- Ancrage : pipeline/economic_sector_capacity.py; pipeline/economic_sector_prices.py
- Hypothèse : Contraintes énergie, foncier, matériaux et capacité limitent les volumes même si le travail unitaire diminue.
- Contrat calculatoire candidat : Capacité K, utilisation u, ressources R, prix relatifs, heures H; Q ≤ min(Ku,R/a); ne pas imposer coût nul.
- Données : TES/FIGARO, RTE, SDES, DVF, prix et capacités; droits à vérifier.
- Recette / réfutation : Comparer offre rigide et extensible, substitution et rebond; rareté persistante compatible avec H faible; vérifier ressources, unités et rationnement.

### HA02 — Prix, profits et assiettes fiscales (P0)
Axes B2, B1 | PARTIAL_SYNTHETIC
- Registres : M027, M035, M036, M037, M038, M042, M052, M053, M057, M058, SH10, SH12, SH14, SH18, AC15, AC16, AC20, AC21, LIM-F01, LIM-F05, LIM-S10, LIM-S12, LIM-S16.
- Ancrage : pipeline/economic_market.py; pipeline/economic_sector_prices.py; pipeline/economic_sector_income_feedback.py
- Hypothèse : Baisse des prix comprime ou déplace les profits et assiettes selon coûts, quantités, concurrence et propriété.
- Contrat calculatoire candidat : CA=pQ; résultat d'exploitation=CA−CI−D1−taxes nettes−amortissements selon périmètre; distinguer surplus brut, net, fiscal et cash.
- Données : Ésane/FARE, comptes nationaux, DGFiP, prix sectoriels.
- Recette / réfutation : Cas prix bas/marge haute, marge nulle, volumes et rentes alternatives; réconcilier valeur ajoutée, impôts, profits et transactions; ne pas taxer un surplus fictif.

### HA03 — Allocation des biens rares et gouvernance sans prix (P1)
Axes B4, C1 | PARTIAL_SYNTHETIC
- Registres : M014, M015, M023, M025, M037, M045, M047, M057, SH15, SH19, AC12, AC13, AC15, AC19, AC21, LIM-S06, LIM-S14, LIM-S16.
- Ancrage : pipeline/economic_market.py; pipeline/economic_sector_structural.py
- Hypothèse : Prix, quotas, files, loteries et droits peuvent coexister; aucun régime n'est présumé optimal.
- Contrat calculatoire candidat : Quantités allouées ≤ capacité; coûts d'attente et accès par cohorte; critères pluralistes et règles institutionnelles explicites.
- Données : Prix et quantités, délais, règles d'accès, données de rationnement; études de cas.
- Recette / réfutation : Comparer règles à offre identique, efficacité, équité, temps et capture; si préférences non mesurées refuser optimum; pas d'assimilation post-travail à abolition des marchés.

### HA04 — Logement, foncier et pouvoir d'achat territorial (P1)
Axes B4, B3 | GAP_EXPLICIT
- Registres : M047, M051, M053, M058, SH12, SH14, SH15, AC07, AC19, AC21, LIM-S11, LIM-S14, LIM-S16.
- Ancrage : pipeline/economic_sector_budget.py (budget agrégé, pas logement territorial)
- Hypothèse : Offre foncière rigide peut capitaliser les transferts et accroître les écarts réels.
- Contrat calculatoire candidat : Budget par cohorte et zone: Ydisp−loyer−dépenses essentielles; élasticités offre/demande locales et mobilité; distinguer loyer, prix d'actif et service.
- Données : DVF, SDES, observatoires de loyers, Insee Budget de famille, Filosofi.
- Recette / réfutation : Scénarios offre élastique/rigide, mobilité, redistribution uniforme/ciblée; mesurer incidence propriétaire/locataire, pas inflation mécanique.

### HA05 — Motivations et activité non rémunérée (P2)
Axes D1 | GAP_EXPLICIT
- Registres : M013, M051, M056, M064, SH19, AC22, AC27, LIM-W09, LIM-T03, LIM-T05.
- Ancrage : Pas de moteur comportemental qualifié identifié dans les fichiers examinés.
- Hypothèse : Perte de revenu, structure du temps et motivation intrinsèque distinctes; effets sur bien-être et engagement de signe inconnu.
- Contrat calculatoire candidat : Indicateurs temps, autonomie, compétence, lien, engagement, satisfaction; pas de fonction universelle ni coefficient inventé.
- Données : ESS, WVS, Eurofound, Emploi du temps, essais revenu garanti; Deci/Ryan, Jahoda.
- Recette / réfutation : Comparer emploi contraint, chômage involontaire, temps libéré avec sécurité; contrôler sélection et contexte; exclure extrapolation à société entière.

### HA06 — Atrophie cognitive et erreurs invisibles (P1)
Axes A3, C3, C2 | PARTIAL_SYNTHETIC
- Registres : M006, M011, M012, M017, M020, M025, SH04, AC09, AC11, AC12, LIM-W03, LIM-W04, LIM-F03.
- Ancrage : pipeline/economic_skills.py; pipeline/economic_operations.py
- Hypothèse : Perte de pratique et erreurs corrélées peuvent rendre la reprise humaine coûteuse.
- Contrat calculatoire candidat : Stock de compétence S(t+1)=(1−δ)S(t)+apprentissage sous contraintes; taux de reprise, temps de détection, erreurs corrélées; δ non estimé.
- Données : Tests de rétention, journaux incidents et contrôles, PIAAC, cas de formation; Bainbridge 1983.
- Recette / réfutation : Choc nul, apprentissage accéléré vs oubli, panne commune, contrôle indépendant, repli automatisé et humain; pas de baisse cognitive globale supposée.

### HA07 — Gouvernance, maintenance et décisions de production (P1)
Axes C1, C2 | PARTIAL_SYNTHETIC
- Registres : M020, M021, M023, M025, M028, M032, M041, SH19, AC06, AC12, AC13, AC14, AC21, LIM-W06, LIM-F04, LIM-S09, LIM-S16.
- Ancrage : pipeline/economic_shared_state.py; pipeline/economic_sector_capital.py
- Hypothèse : Maintien des droits de décision et entretien du capital sont nécessaires sans garantir emploi de masse.
- Contrat calculatoire candidat : Droits de décision séparés de la propriété financière; stock capital K(t+1)=K(t)−retraits+mise en service; budget maintenance, indisponibilité, contrôle/repli.
- Données : Comptes, gouvernance, maintenance et incidents; Ostrom/North comme pistes.
- Recette / réfutation : Comparer contrôle décentralisé, centralisé, humain et automatisé; maintenance sous-financée, coût du repli; pas de mandat politique implicite.

### HA08 — Financement du revenu universel et ordres de grandeur (P0)
Axes B1, B3 | PARTIAL_SYNTHETIC
- Registres : M042, M051, M052, M053, M055, M057, M058, SH10, SH12, SH13, SH18, AC06, AC07, AC20, AC21, AC23, LIM-S11, LIM-S12, LIM-S16, LIM-F01.
- Ancrage : pipeline/economic_sector_income_feedback.py; pipeline/economic_institutional_bridge.py; pipeline/economic_shared_state.py
- Hypothèse : Transferts soutenables dépendent de la base réelle/nominale, bénéficiaires, propriété, prix et financement.
- Contrat calculatoire candidat : Coût brut b×N×périodes; coût net=brut−prestations remplacées−recettes additionnelles effectivement modélisées; dette et actifs publics séparés, budget par acteur.
- Données : Insee TEE, Drees, DGFiP, Eurostat, OCDE; règles et droits.
- Recette / réfutation : Scénarios cotisations, fiscalité capital/consommation, dividende citoyen, fonds souverain, services en nature; identité budget/contreparties; pas de double financement ni montant futur garanti.

### HA09 — Concentration du capital et du contrôle (P0)
Axes C1, B2 | PARTIAL_SYNTHETIC
- Registres : M023, M037, M039, M040, M042, M051, M055, SH11, SH13, SH19, AC05, AC06, AC15, AC20, AC21, LIM-F05, LIM-F06, LIM-S16.
- Ancrage : pipeline/economic_market.py; pipeline/economic_shared_state.py (equity ≠ droits de vote)
- Hypothèse : Production abondante peut coexister avec concentration de propriété, fournisseurs et contrôle.
- Contrat calculatoire candidat : HHI=Σparts² par marché défini; concentration de patrimoine, bénéficiaire ultime, dépendance commune et vote distincts.
- Données : SIRENE, INPI, comptes consolidés, patrimoine, parts de marché et infra; accès/droits.
- Recette / réfutation : Concurrence, accès ouvert, intégration verticale, monopole; HHI seul ≠ pouvoir de marché; ne pas transformer actions financières en vote.

### HA10 — Fragilité systémique et défaillances communes (P1)
Axes C2 | PARTIAL_SYNTHETIC
- Registres : M006, M017, M020, M034, M043, M044, M045, M048, M055, SH09, SH15, AC03, AC04, AC12, AC18, AC23, LIM-W04, LIM-S06, LIM-S07, LIM-S08, LIM-S09, LIM-S14.
- Ancrage : pipeline/economic_financial_network.py; pipeline/economic_sector_structural.py; pipeline/economic_finance_work_scenarios.py
- Hypothèse : Dépendances communes peuvent amplifier chocs et coûts de continuité, même avec automatisation avancée.
- Contrat calculatoire candidat : Réseaux productifs, financiers, technologiques distincts; capacité de secours, temps de reprise, chocs corrélés; pertes par trajectoire et pas somme des chemins.
- Données : TES/FIGARO, données contreparties, incidents et fournisseurs critiques; Acemoglu/Carvalho.
- Recette / réfutation : Panne commune vs indépendante, substitution, stocks, liquidité, redondance; stress tests sans probabilités inventées, conservation stock/flux.

### HA11 — Incitations à innover et entretien long terme (P1)
Axes A2, B2, C2 | GAP_EXPLICIT
- Registres : M005, M023, M024, M028, M031, M038, M041, M055, SH06, SH08, SH09, SH19, AC10, AC13, AC14, AC15, AC16, AC21, LIM-F04, LIM-F08, LIM-W08, LIM-S09.
- Ancrage : pipeline/economic_sector_capital.py et economic_market.py (capital et marché, pas innovation endogène qualifiée)
- Hypothèse : Rendement privé, concurrence, financement public, recherche ouverte et motivation intrinsèque peuvent soutenir innovation/entretien; signe conditionnel.
- Contrat calculatoire candidat : Flux R&D/maintenance et capital immatériel, délais, retours privés/sociaux; pas de loi de progrès supposée.
- Données : Insee R&D, OCDE MSTI, comptes firmes, brevets et publications; Schumpeter/Aghion.
- Recette / réfutation : Comparer rente faible/forte, financement public/privé, open source, obsolescence et maintenance; mesurer qualité et délais, pas brevet=innovation.

### HA12 — Cohésion sociale et compétition de statut (P2)
Axes D1 | GAP_EXPLICIT
- Registres : M013, M023, M051, M056, M064, SH19, AC22, AC27, LIM-W09, LIM-T03, LIM-T05.
- Ancrage : Pas de module causal de statut/cohésion identifié.
- Hypothèse : La compétition positionnelle peut se déplacer vers attention, reconnaissance, patrimoine; aggravation non nécessaire.
- Contrat calculatoire candidat : Indices d'accès, confiance, participation, dispersion de statut et usage du temps; variables distinctes, pas score composite.
- Données : ESS, WVS, Eurofound, Emploi du temps; Hirsch/Festinger.
- Recette / réfutation : Comparer groupes/cohortes et trajectoires, contrôler sélection/confondants; aucune conclusion civilisationnelle à partir d'une corrélation.

### HA13 — Transmission intergénérationnelle du savoir (P1)
Axes C3, A3, A2 | PARTIAL_SYNTHETIC
- Registres : M009, M011, M012, M024, M033, M049, M050, SH02, SH04, SH17, AC08, AC09, AC11, LIM-F02, LIM-F03, LIM-S15.
- Ancrage : pipeline/economic_skills.py; docs/G3-SKILLS.md
- Hypothèse : Disparition de tâches juniors peut réduire le renouvellement des experts, ou IA accélérer l'apprentissage.
- Contrat calculatoire candidat : Stocks par compétence/expérience, entrants, sorties, promotion, mentorat, évaluation, oubli; demande distincte d'expertise et impact qualité/débit.
- Données : Dares, formations, recrutements par séniorité, PIAAC, panels de pratique; Brynjolfsson/Li/Raymond.
- Recette / réfutation : Rejouer gel/classique/accéléré; introduire oubli, évaluateur, pénurie→qualité, maintien volontaire; aucun temps universel ni prime salariale inventée.

### HA14 — Démographie et dynamiques culturelles (P2)
Axes D2 | GAP_EXPLICIT
- Registres : M047, M050, M051, M053, M056, M057, SH19, SH20, AC07, AC08, AC19, AC20, AC22, AC27, LIM-S14, LIM-S15, LIM-S16, LIM-T03, LIM-T05.
- Ancrage : Pas de projection fécondité/cohortes qualifiée identifiée.
- Hypothèse : Sécurité, logement, âge, normes, politiques et choix modifient fécondité et offre de travail; effet post-travail indéterminé.
- Contrat calculatoire candidat : Cohortes âge×temps, survie, naissances, migration; paramètres conditionnels et incertitude; pas d'attribution à appartenance culturelle.
- Données : Insee, Eurostat, ONU, HFD, enquêtes; qualification de la causalité séparée.
- Recette / réfutation : Rejouer variantes fécondité/migration/participation avec données et bornes; tester facteurs concurrents; ne pas prédire composition culturelle à partir d'intuitions.

## Douze axes et contrats
- **A1 Substitution dynamique capital-travail (P0)** : H=Q×h résiduelle + H nouvelles tâches/contrôle (sans double compte); H/temps ETP; coût complet, qualité, VAN et adoption; seuil gQ=gP si hypothèses uniformes. (M007, M008, M028, M030, M032, M033, M036, M049, M054, SH01, SH07, SH17, AC08, AC11, AC14, AC23, LIM-F04, LIM-S15).
- **A2 Automatisation récursive des nouveaux métiers (P0)** : Cohortes de tâches, flux création/disparition, durées et risques de transition; tester compensation durable, réautomatisation et biais des référentiels. (M005, M007, M009, M012, M041, M049, SH02, SH03, SH17, AC08, AC09, AC10, AC11, AC16, LIM-F02, LIM-F03, LIM-W08, LIM-S15).
- **A3 Dépréciation du capital humain (P1)** : Distinguer perte de pratique, obsolescence technique, prix de compétence; cohortes, transitions et coût de requalification. (M011, M012, M050, M052, SH04, AC09, LIM-F03, LIM-S15).
- **B1 Soutenabilité fiscale post-salariat (P0)** : Comptes stocks-flux, microsimulation si microdonnées admises, financement dette/actifs et incidence; recettes par assiette, prestations et déficit. (M052, M053, M055, M057, M058, SH12, SH13, SH18, AC20, AC21, AC23, LIM-S12, LIM-S16).
- **B2 Formation et déplacement des rentes (P0)** : Décomposer VA, coûts, marges, pouvoir de marché, rente foncière/IP/compute; profits et rentes ne sont pas synonymes. (M027, M035, M037, M038, M042, M051, SH10, SH11, SH14, AC06, AC15, AC16, LIM-F05, LIM-S10, LIM-S16).
- **B3 Demande solvable et distribution des revenus (P0)** : Budget/cohorte, propensions et courbes d'Engel si estimables, contraintes d'offre et épargne; boucles revenu→demande→production→revenu. (M042, M051, M052, M053, M058, SH08, SH10, SH12, AC07, AC16, AC20, AC21, LIM-S11, LIM-S12, LIM-S16).
- **B4 Raretés et inflation sectorielle (P1)** : Prix/quantités par secteur, foncier, énergie et capacité, coût réel du panier; comparer allocation et localisation. (M045, M047, M048, M058, SH09, SH14, SH15, AC18, AC19, LIM-S10, LIM-S13, LIM-S14).
- **C1 Concentration du capital et du pouvoir (P0)** : Propriété ultime, contrôle, dépendances, HHI et distribution; scénarios concurrentiels et institutionnels. (M023, M037, M039, M040, M042, M051, SH11, SH13, SH19, AC05, AC06, AC15, AC21, LIM-F06, LIM-S16).
- **C2 Résilience des réseaux productifs (P1)** : Chocs corrélés, réseaux multiples, capacité de repli, délais, coûts de maintenance et arbitrage robustesse/productivité. (M006, M017, M020, M043, M044, M045, M055, SH09, SH15, AC04, AC12, AC18, AC23, LIM-W04, LIM-S06, LIM-S09).
- **C3 Transmission intergénérationnelle (P1)** : Flux d'apprentissage et expertise, disponibilité mentor/évaluateur, impact opérationnel; mesure du stock critique. (M009, M012, M024, M033, M050, SH04, AC09, AC11, LIM-F03, LIM-S15).
- **D1 Motivation, statut et cohésion (P2)** : Études usage du temps/bien-être et comportements; motivation intrinsèque/extrinsèque; observation/scénarios qualitatifs par défaut. (M013, M023, M051, M056, SH19, AC22, AC27, LIM-W09, LIM-T03, LIM-T05).
- **D2 Démographie et culture (P2)** : Projections conditionnelles par cohortes; effets incertains de fécondité/migration, coûts et participation. (M047, M053, M056, M057, SH19, SH20, AC07, AC19, AC20, AC22, LIM-S14, LIM-S15, LIM-S16, LIM-T05).

## Scénarios concurrents
- S1 Complémentarité durable : Création de tâches et expansion de demande ≥ déplacement, sans postuler ce résultat.
- S2 Substitution progressive : Travail par unité diminue plus vite que demande et nouvelles tâches.
- S3 Substitution accélérée : Réautomatisation des tâches créées; vérifier contraintes et financement.
- S4 Crise de demande solvable : Revenus réels/transferts insuffisants, boucles dépenses/production.
- S5 Blocage structurel : Qualité, capital, réglementation, énergie ou expertise contraignent adoption.
- S6 Post-travail viable : Travail marginal, accès aux biens et distribution soutenables sous régimes alternatifs.
Référence sans choc et sans adoption obligatoires; scénarios composables, non exclusifs et non probabilisés. Trajectoires calculées à partir de COMMON-STATE avec contreparties et dates, pas addition de chemins. O0–O4+ et RESULT D12/D13/D15/D16/D17/D18; aucun ordre figé ni effet inventé.

## Validation et exécution
- Hypothèse testable
- Mécanismes et facteurs confondants
- Théories rivales
- Mesures et données admises
- Formalisation mathématique conditionnelle
- COMMON-STATE, unités et contreparties
- Scénarios contradictoires
- Validation, restitution, limites
- BENCH-001: 2–4 sources directes par mécanisme, contre-théories, estimand, régime, tests négatifs
- Admission sources et droits, millésimes, unité, couverture
- Rejeu historique point-in-time et comparaison indépendante; NON_IDENTIFIABLE si besoin
- Tests invariants, choc nul, absence adoption, seuils, interactions et non-convergence
- M0 identifié; M1 sources qualifiées; M2 formalisé; M3 données admises; M4 calibré; M5 validé indépendamment; M6 exploitable, aucune promotion automatique
- RESULT D12/D13/D15/D16/D17/D18 et PROSPECT O0–O4+; ordre relatif et délai distincts
- Préserver V3e et qualification juridique, technique, commerciale, publication bloquée
- P0: rattacher les axes aux investigations et gaps existants, choisir étude à valeur décisionnelle, P0 empirique/G2 en parallèle
- G3.3/3.4: emploi, nouvelles tâches, expertise, prix, concurrence; G4: revenus, fiscalité, propriété et raretés, hétérogénéité et fermeture état commun après priorité produit
- P1: résilience, foncier, maintenance et compétences; P2: observation et scénarios humains/démographiques; ne pas bloquer première vente
- G5: backtests, contre-exemples, restitution et revue indépendante, sans promotion de gate

## Références candidates, à qualifier via BENCH-001
- Acemoglu & Restrepo, Automation and New Tasks, NBER 25684
- Autor & Salomons; Baumol; Leontief; Godley & Lavoie; Acemoglu & Carvalho
- Schumpeter; Aghion; Hirsch; Ostrom; Herbert Simon; Bainbridge (Ironies of Automation, 1983)
- Becker; Heckman; Deci & Ryan; Jahoda; North; Olson; Festinger

Registre machine-readable : [postlab_contradictory_v1.json](../governance/postlab_contradictory_v1.json). Les sources détaillées, paramètres, interfaces exécutables et essais historiques restent à produire par claim et jalon. Aucune clôture de limitation ni gate promu.
