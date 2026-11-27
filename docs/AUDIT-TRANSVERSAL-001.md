# AUDIT-TRANSVERSAL-001 | Pré-reprise G4 v0.7g
25/11/2026. Statut USER_APPROVED_REQUIREMENTS_METHOD_PENDING. Validation explicite utilisateur le 25/11/2026. Baseline main f08daac91393489194df67b3aea32907d8c2ef77. Décision: audit de couverture, aucune promotion de gate, aucune substitution des 9 couches/6 moteurs/64 mécanismes; les IDs AC sont des exigences d'architecture validées, non des méthodes, implémentations ou résultats scientifiques validés. Préserver LIMITATIONS-001 v1.0.10 et les IDs M/LIM existants.
## Diagnostic vérifié
ARCH-002 et registre: 64 exigences METHOD_PENDING, 13 interfaces spécifiées, 6 moteurs cibles partiels/non implémentés. LIMITATIONS-001: 51 familles, 26 PARTIAL, 20 OPEN, 3 BLOCKED, 2 PERMANENT. Les tests G4 v0.7f vérifient compensation régulière et rationnement conditionnel, pas économie couplée. G3.4 v0.2a comporte cash différencié et crédit engagé, v0.7d/e financement trésorerie/apports/dette et contreparties: l'autofinancement n'est pas absent; c'est le choix, l'hétérogénéité conjointe, la substitution et les interfaces qui sont sous-spécifiés. G3.4 entrée statique supposée financée; sortie sans liquidation. G2 validation indépendante ouverte. G4 stock financier F4/F5 non exigible; données trimestrielles RAW_PROFILE_ONLY. README et ROADMAP ne reflètent pas intégralement les derniers jalons. Documents consultés: README, ROADMAP, BENCH-001, ARCH-002, METH-003, G2-WORK-GRAPH, G3-RAMP, G3-MARKET-DYNAMICS, G3-MARKET-BOUNDARY, G4-SECTOR, RESULT-001, PROSPECT-001, registres JSON, ARCH-001 Drive et extraits DD-SHAPIRO-001. Audit documentaire, pas lecture exhaustive de tous les fichiers/lignes ni revue indépendante ou test de code nouveau.
## Registre des écarts et critères de recette
P0 = bloquant pour les conclusions concernées et le couplage, P1 = développement conditionnel selon matérialité. Sous-spécifié = présent implicitement mais manque contrat de couverture explicite; Partiel = preuve locale/limite connue; Déjà prévu = dette de réalisation, pas nouvel oubli. Sources de données candidates non admises.
### AC01 — Structures de financement et choix de sources (P0; Sous-spécifié)
Rattachement : M028/M029/M034/M055; LIM-F04/S09.
Exigence : Autofinancement (flux, non stock de cash), trésorerie, apports, dette bancaire et obligataire, leasing, crédit fournisseur, affacturage, subventions conditionnelles, financement intragroupe; substitution, coûts, disponibilité, dilution, maturités et fiscalité; pecking order comme hypothèse concurrente.
Recette minimale : Même entreprise/projet: dette nulle, apport seul, cash seul, mix, refus, substitution, absence de financement; somme sources=emplois; aucune dette fictive; même VAN projet hors financement.
Chantier / sources candidates : G3.3/G3.4/G4 v0.7g; SAFE, FARE/FIBEN, comptes financiers, droits à qualifier

### AC02 — Bilan et trésorerie complets (P0; Partiel)
Rattachement : M034/M055; LIM-F01/S09/S12.
Exigence : Actifs, passifs, capitaux propres, flux d'exploitation/investissement/financement, BFR, délais clients/fournisseurs, TVA, saisonnalité, engagements, provisions, restructuration, liquidité vs solvabilité vs défaut juridique, valeur de liquidation.
Recette minimale : Entreprise rentable en défaut de cash; déficitaire financée; dette zéro et factures dues; reprise d'actif et pertes appariées; bilan et cash sans doubles comptes.
Chantier / sources candidates : G3.3/G4; FARE, comptes publiés, délais paiement

### AC03 — Prix du risque et sélection du crédit (P0; Sous-spécifié)
Rattachement : M034/M039/M055; LIM-F04/S09.
Exigence : PD/LGD/EAD, collatéral, covenants, maturités, garanties, intérêts fixes/variables, refinancement, asymétrie informationnelle, rationnement par risque, fuite vers qualité, crowding out, debt overhang, arbitrage VAN/risque; pas de ratio universel.
Recette minimale : Comparer rationnement proportionnel, sélection, plafonds et absence de demande; même demande, décisions différentes; pertes attendues vs réalisées; stress taux/maturité.
Chantier / sources candidates : G4 v0.7g+; SAFE/BLS, AnaCredit accès restreint, BCE/ACPR

### AC04 — Intermédiation monétaire et financière (P0; Partiel)
Rattachement : M034/M055; LIM-F01/S12/S16.
Exigence : Banques multiples, dépôts, réserves/règlement, interbancaire, fonds propres, liquidité, passifs, banque centrale, non-banques, garanties, recapitalisation et résolution; actifs pondérés évolutifs; contagion directe et expositions communes, ventes forcées et haircuts.
Recette minimale : Règlement interbancaire, conservation des contreparties, stress liquidité sans insolvabilité, choc de capital sans fuite de dépôts, fire sale distincte du défaut; aucun stock utilisé comme exigibilité sans échéancier.
Chantier / sources candidates : G4; Eurostat cp, BCE BSI/MIR, EBA/ACPR agrégats

### AC05 — Population d'entreprises et distribution conjointe (P0; Sous-spécifié)
Rattachement : M029/M031/M034/M039/M054; LIM-F06/S04/S09.
Exigence : Taille, âge, activité, groupe/indépendant, productivité, capital, liquidité/dette, propriétaire, maturité IA, emploi et marchés; corrélations, poids et entrées/sorties; éviter entreprise moyenne et marges indépendantes.
Recette minimale : Deux populations aux mêmes moyennes mais dettes/productivité corrélées différemment; concentration, survie, emploi et adoption peuvent diverger; poids cohérents aux agrégats; cellules absentes inconnues.
Chantier / sources candidates : G3/G4; FARE/ESANE, SIDE, FIBEN, enquêtes TIC

### AC06 — Propriété économique et contrôle (P0; Sous-spécifié)
Rattachement : M039/M042/M051/M055; LIM-S16/F06.
Exigence : Matrice détenteur-émetteur, droits de vote vs cash flows, dilution, fonds/pensions et détention indirecte, capital coté/non coté, distributions, rachats et bénéfices réinvestis, contrôle ultime, investisseurs étrangers; pas de double comptage via fonds.
Recette minimale : Apport dilutif vs dette, même HHI ventes et propriété différente, chaîne de détention avec cycles, flux dividendes net des intermédiaires; parts top x et HHI sur base définie.
Chantier / sources candidates : G3/G4; comptes financiers, HFCS/DWA, LIFI accès à qualifier

### AC07 — Ménages hétérogènes et budgets (P0; Partiel)
Rattachement : M042/M051/M053/M057/M058; LIM-S10/S11/S12/S16.
Exigence : Revenus, patrimoine liquide/illiquide, dettes, logement, âge, statut emploi, taille ménage, transferts, impôts et propensions marginales à consommer/épargner distinctes; consommation essentielle et contrainte de crédit.
Recette minimale : Même revenu agrégé, distribution différente et consommation différente; baisse prix avec revenu diminué; propriétaires vs locataires; fermeture épargne/dette/patrimoine.
Chantier / sources candidates : G4; ERFS, Budget de famille, HFCS/DWA, comptes distribués

### AC08 — Marché du travail en stocks et flux (P0; Déjà prévu)
Rattachement : M049/M050/M052/M056; LIM-S15.
Exigence : Personnes/emplois/heures/ETP, multi-emploi, emploi salarié et indépendant, activité/inactivité, chômage durée, sous-emploi, retraite, migrations, pénuries, postes vacants, matching, négociation, contrats, rigidités et transitions.
Recette minimale : Choc heures sans licenciement, attrition, non-remplacement, départ retraite, pénurie évitée, création de postes et chômage simultanés; aucune personne comptée deux fois.
Chantier / sources candidates : G3/G4; enquête Emploi, DSN/Dares, France Travail, JOLTS benchmark

### AC09 — Reproduction de l'expertise et qualité de l'emploi (P0; Partiel)
Rattachement : M012/M024/M033/M050; LIM-F03/W02.
Exigence : Apprentissage par pratique, mentorat, filières junior/senior, compétences tacites, mobilité, effets de cohorte, obsolescence, formation, scarring, déqualification et qualité de travail.
Recette minimale : Suppression des juniors puis pénurie retardée de seniors; formation alternative qui compense; apprentissage IA complémentaire; distinguer hypothèse et résultat longitudinal.
Chantier / sources candidates : G2/G3/G4; cohortes et études terrain

### AC10 — Frontière technologique et offre d'IA (P1; Sous-spécifié)
Rattachement : M003/M004/M005/M006/M048; LIM-W08/S14.
Exigence : Coûts fixes/variables, tokens, utilisation, infrastructures, énergie, eau, semi-conducteurs, réseaux, robots, maintenance, accès, quotas, dépendance fournisseur, prix stratégiques, qualité, apprentissage et effets de rupture; agents et tâches physiques séparés.
Recette minimale : IA bon marché mais compute rare; fournisseur indisponible; capex/opex alternatifs, plateau et accélération, qualité qui s'améliore sans adoption.
Chantier / sources candidates : G2/G3/G4; benchmarks, factures, IEA, données fournisseurs

### AC11 — Mesure du travail réel et sélection (P0; Déjà prévu)
Rattachement : M007/M008/M009/M010/M011/M013; LIM-W01/W02/W03/W04/W09.
Exigence : Temps actif/mural, tâches non observées, tacite, correction, coordination, erreurs corrélées, autonomie, supervision, diversité des contextes, travail invisible, charge et qualité; sélection des tâches et utilisateurs.
Recette minimale : Bras humain, automatisation classique, IA, hybride; corpus indépendant, échec et abstention, coût de queue, cas hors distribution; pas de poids depuis O*NET seul.
Chantier / sources candidates : G2 priorité parallèle, praticiens et logs autorisés

### AC12 — Transformation structurelle et résilience (P1; Partiel)
Rattachement : M014/M015/M016/M017/M018/M020; LIM-W04/W05.
Exigence : Files non stationnaires, ressources jointes, pics, goulets mobiles, dépendances communes, redondance, continuité, reprise, dette technique, suppression du besoin et non seulement de l'étape.
Recette minimale : Gain local sans débit; défaillance corrélée; humain retiré mais contrôle ailleurs; refonte qui élimine la demande interne; choc et retour à service.
Chantier / sources candidates : G3 opérations; journaux anonymisés et stress tests

### AC13 — Incitations, inertie et comportement (P1; Sous-spécifié)
Rattachement : M021/M023/M024/M025/M026; LIM-W06.
Exigence : Effet de cliquet, budgets, protection du pouvoir, principal-agent, objectifs Goodhart, coûts politiques, responsabilité juridique, assurance, conflits et négociation; délais, refus ou abandon; distinguer preuve comportementale.
Recette minimale : Même technologie et VAN, adoption divergente par gouvernance; reporting augmente malgré gain; contrôle adapté et délégation totale sous conditions; contre-exemples à chaque règle.
Chantier / sources candidates : G3/TRANSFORM; études organisationnelles et terrain

### AC14 — Capital et décision d'investissement (P0; Partiel)
Rattachement : M027/M028/M030/M031/M032; LIM-F02/F04/F08/S09.
Exigence : Capital physique, logiciel, data, R&D, organisation, actifs complémentaires et irrécupérables, options réelles attendre/abandonner/phaser, dépréciation économique/obsolescence, maintenance, coûts d'opportunité, rendement et utilisation; OPEX abonnement vs CAPEX.
Recette minimale : VAN positive mais non financée, VAN négative malgré cash, report optimal sous incertitude, équipement livré non opérationnel, coût sunk non récupéré, redéploiement sans revenu inventé.
Chantier / sources candidates : G3.3/G4; comptes capital, investissements, coûts terrain

### AC15 — Marchés et stratégies (P1; Sous-spécifié)
Rattachement : M035/M037/M038/M040/M041; LIM-F05/F07/F08.
Exigence : Coût marginal vs moyen, prix à l'usage/abonnement/free, qualité et variété, discrimination, switching, réseau et multi-homing, oligopole, plateformes, monopsones, prix dynamiques, concurrence hors prix, rentes temporaires, innovation défensive.
Recette minimale : Même coût et pass-through variable; qualité accrue sans prix réduit; guerre des prix, prix stable et marge, entrée qui érode rente, marché bi-face; HHI non proxy de markup.
Chantier / sources candidates : G3.4; IPSE, prix et quantités, études marché

### AC16 — Demande, création/destruction de marché (P1; Partiel)
Rattachement : M036/M038/M041/M053; LIM-F07/F08/S10/S11.
Exigence : Rebond prix et revenus, élasticités croisées, budgets contraints, saturation, préférences humaines, temps disponible, biens nouveaux, non-marchand/gratuit, demande latente vs solvable, cannibalisation et internalisation.
Recette minimale : Baisse prix volume constant, rebond partiel, total, surcompensation; consommation décalée vers autres secteurs; produit gratuit non égal à zéro valeur; nouveau marché sans double compte.
Chantier / sources candidates : G3.4/G4; dépenses, quantités, enquêtes

### AC17 — Démographie économique et réallocation (P1; Partiel)
Rattachement : M039/M040/M054; LIM-F06/S04.
Exigence : Entrée financée ou non, croissance, pivot, cessation, liquidation, reprise, acquisition, changement de contrôle et réallocation intra/intersectorielle; dispersion et mauvaise allocation du capital; firmes zombies comme hypothèse.
Recette minimale : Sortie d'offre vs décès juridique, transfert d'actifs et salariés, acquisitions sans création de production, hausse productivité moyenne par composition vs progrès interne.
Chantier / sources candidates : G3.4/G4; SIDE, business demography, données groupes

### AC18 — Réseaux réels et chaînes mondiales (P0; Partiel)
Rattachement : M043/M044/M045/M046; LIM-S01/S02/S05/S06/S07/S08/S14.
Exigence : Matrice produit/branche, établissements, fournisseurs spécifiques et dépendances communes, stocks domestiques/finals, commandes différées, délais, substitutions imparfaites, prix et taux change, importations directes/indirectes, rerouting et commerce; topologie non identifiée par marges.
Recette minimale : Même marges, réseaux différents; choc offre vs demande; substitution non disponible, prix/stock/quantité conservés; production brute vs VA et contenu importé.
Chantier / sources candidates : G4; TES/FIGARO/ICIO, douanes, données fournisseurs

### AC19 — Territoires, mobilité, ressources (P1; Déjà prévu)
Rattachement : M047/M048/M050/M056; LIM-S14/S15.
Exigence : Télétravail, bassins d'emploi, logement, déplacements, mobilité résidentielle, spécialisation, infrastructures, externalités énergie/climat; chaînes géographiques et inégalités locales.
Recette minimale : Même choc national, bassins opposés; logement bloque mobilité; compute contraint régionalement; distinguer résidence/travail/siège, unités physiques et euros.
Chantier / sources candidates : G4; INSEE recensement, zones emploi, énergie

### AC20 — État, banque centrale et extérieur (P0; Sous-spécifié)
Rattachement : M051/M053/M055/M057/M058; LIM-S03/S11/S12/S16.
Exigence : Budgets publics, impôts sur bases distinctes, cotisations, dépenses/transferts, dette/intérêts, règles et stabilisateurs, taux et inflation, change, balance courante et financière; capacité publique, non-marchand et investissement; politiques conditionnelles.
Recette minimale : Budget public ferme, transferts financés vs déficit, dette et taux distincts, revenu disponible vs PIB, exportations et importations, aucune création de fonds sans contrepartie.
Chantier / sources candidates : G4; TEE, comptes publics, BCE et balance paiements

### AC21 — Économie post-travail et régimes institutionnels (P1; Sous-spécifié)
Rattachement : M042/M051/M053/M057/M058; LIM-S16.
Exigence : Revenu universel, impôt négatif, dividendes citoyens/fonds souverains, participation capital, réduction temps de travail, fiscalité travail/capital/rentes, services publics, transition et financement; incidence et réponses comportementales, croissance et prix; maintenir scénarios de travail persistant.
Recette minimale : Comparer mêmes ressources initiales et politiques avec bouclage budget/production; transferts sans création de VA; scénario abondance avec biens rares et scénario non-post-travail.
Chantier / sources candidates : G4/PROSPECT, DD-SHAPIRO-001; comptes distribués et évaluations de politiques

### AC22 — Valeur non marchande et bien-être (P1; Sous-spécifié)
Rattachement : M013/M041/M048/M051/M054/M056/M058; LIM-W09/S16.
Exigence : Temps libéré, production domestique et bénévolat, qualité, accès, santé/loisirs, prix hédoniques, nouveaux produits, biens gratuits et externalités; surplus consommateur et bien-être distincts PIB/revenus.
Recette minimale : Heures payées baissent mais production non marchande augmente; prix zéro sans valeur zéro; amélioration qualité sans hausse PIB mesuré; ne pas monétiser arbitrairement.
Chantier / sources candidates : G4/RESULT; emploi du temps, comptes satellites

### AC23 — Couplage état commun et fermeture (P0; Sous-spécifié)
Rattachement : M054/M055/M062/M063; LIM-S09/S12/T01.
Exigence : État partagé acteurs/produits/temps, stocks/flux/engagements, calendrier et ordre d'événements, prix/quantités/revenus/emplois/finance, décisions retardées, boucles et convergence, propagation des incertitudes et conservation; pas d'addition de trajectoires indépendantes.
Recette minimale : Replay choc nul, limites de chaque module, scénarios à financement zéro, rétroaction multi-période, ordre d'événement, non-convergence, permutation des acteurs, contreparties et balances consolidées.
Chantier / sources candidates : G3/G4 architecture E02/E05; priorité avant nouveaux modules

### AC24 — Identification et validation externe (P0; Déjà prévu à renforcer)
Rattachement : M059/M060/M061/M062/M063; LIM-T02/T03.
Exigence : Confusions conjoncturelles, tendances, anticipations, spillovers, sélection, causalité inverse, ruptures, biais survivant, composition, erreurs mesure, invariance des règles et transportabilité; modèles rivaux IO/SFC/ABM/partiel selon question.
Recette minimale : Holdout temporel et sectoriel, placebos et pré-tendances, contrefactuel sans IA, stress structurel, benchmark naïf, intervalles et sensibilité globale, NON_IDENTIFIABLE sans preuve.
Chantier / sources candidates : G1/G2/G3/G4/G5, travaux empiriques parallèles

### AC25 — Observatoire point-in-time et exploitation (P0; Partiel)
Rattachement : M059/M063/M064; LIM-S01/T04.
Exigence : Admission des sources, droits, coffre immutable, données de révision, manque non aléatoire, nomenclatures, dénominateurs, dérive, refresh, licences, agrégation, sécurité et coût; README/ROADMAP désynchronisés de G4.
Recette minimale : Reconstruction à date passée, source modifiée/indisponible, droits refusés, valeurs manquantes non zéro, cohérence version des docs; tests bout en bout UI/calcul/preuve.
Chantier / sources candidates : G1/P0/G5 en parallèle; sources et registre droits

### AC26 — Produit décisionnel et validation commerciale (P0; Déjà prévu à renforcer)
Rattachement : M064; LIM-T01/T04; RESULT/PROSPECT.
Exigence : Mandat décisionnel, matérialité, alternatives, coût erreur, preuve inspectable et scénarios opposés, pas d'inflation de métriques; usage réel et paiement, temps/qualité vs référence, revues externes, limites expliquées.
Recette minimale : Un dossier vertical réel avec décision modifiée ou non, baseline analyste, traçabilité intégrale, refus d'assertions non prouvées, entretien/client payant indépendant; pas de gate commercial par CI.
Chantier / sources candidates : G1/G5 parallèle, pilote sectoriel

### AC27 — Régimes alternatifs et anti-biais de thèse (P0; Sous-spécifié)
Rattachement : M028/M033/M039/M049/M055/M057/M062; LIM-T01/T03/S12.
Exigence : Automatisation rapide/lente/nulle, pénurie travail, réallocation, stagnation, abondance partielle, rupture, retour humain, coûts croissants, politiques alternatives; effets directionnels non imposés; horizons court/long et changements de régime.
Recette minimale : Au moins une branche réfutant chaque hypothèse centrale, pas de probabilité arbitraire; signes inversés sous paramètres admissibles, test de robustesse et critère de révision.
Chantier / sources candidates : PROSPECT transversal; aucune conclusion prédéterminée
## Architecture d'intégration et ordre de reprise validé
1. Avant extension de G4: contrat transversal état/acteur/temps et droits de propriété, typage stock/flux/exigibilité, sources/emplois et bilan, séparation règles comportementales et identités; grille de financement et profils conjoints au niveau entreprise; plan de mapping G3→G4 (AC01/02/05/06/23).
2. G4 v0.7g: qualifier matrice trimestrielle et vintages, relier rationnement au financement multi-source (cash/apport/dette/alternatives, refus, aucune dette), échéances, contraintes et décisions; démonstration multi-acteurs et test de régression existant. Ne pas imposer le crédit, ni réutiliser une capacité d'octroi comme octroi réel.
3. Boucler progressivement marchés, travail, ménages, Etat/extérieur et capital dans le même état (AC07/08/18/20/23), avec scénarios contradictoires et comptabilité commune. Ajouter mécanismes de second rang selon matérialité, sans empiler des moteurs.
4. En parallèle, P0 empirique et G2 indépendant: corpus/praticiens, qualification sources, calibration, tests hors échantillon et couverture de la distribution. Ne pas attendre le dernier jalon macro pour réaliser un dossier vertical réel et test de valeur B2B (AC11/24/25/26).
5. Avant chaque jalon: tableau mécanisme/interface/acteur/régime/échelle, statut, données, preuve, hypothèses, contre-exemple, test négatif, dépendances, règle de publication. Réconcilier avec M/LIM/SH et versionner sans fermeture silencieuse. Contrôle indépendant et recette générale avant prétendre à validation. G4 v0.7g reste à réaliser. Aucune promesse d'exhaustivité.
## Benchmarks de départ vérifiés (pas de calibration)
- Myers et Majluf : https://www.nber.org/papers/w1396 — AC01/03; choix financement sous asymétrie, pas hiérarchie imposée
- Bernanke, Gertler et Gilchrist : https://www.nber.org/papers/w6455 — AC03/04/05/23; accélérateur et accès hétérogène
- Caiani et al. : https://www.sciencedirect.com/science/article/abs/pii/S0165188915301020 — AC04/06/07/20/23; référence SFC-ABM, pas adoption automatique
- Acemoglu, Kong et Restrepo : https://www.nber.org/papers/w32872 — AC08/09/11/27; déplacement et nouvelles tâches
- Baqaee et Farhi : https://www.nber.org/papers/w27281 — AC18/23; complémentarités et non-linéarité
- IMF, Distributional Effects of Monetary Policy : https://www.elibrary.imf.org/view/journals/001/2021/201/article-A001-en.xml — AC07/20; hétérogénéité et canaux
- Hsieh et Klenow : https://www.nber.org/papers/w13290 — AC05/17; mauvaise allocation, pas paramètres transférables
- Lucas : https://doi.org/10.1016/S0167-2231%2876%2980003-6 — AC24/27; invariance sous changement de régime

## Décision d'intégration validée
[Registre canonique AC01–AC27](../governance/transversal_enrichment_v1.json) : 18 P0, 9 P1, liens contrôlés vers 60 mécanismes et 35 familles de limitations existants. Exigences complémentaires à M001–M064 et SH01–SH21, à évaluer explicitement pour chaque investigation et avant chaque jalon. Pas de nouveau moteur, aucune clôture, aucune promotion scientifique. Le raccordement automatique du registre aux contrôles exécutables reste à réaliser.


## POSTLAB-CONTRADICT-001 — Programme contradictoire post-travail (27/11/2026)
[Décision et matrice des 14 objections / 12 axes](POSTLAB-CONTRADICT-001.md), [registre machine-readable](../governance/postlab_contradictory_v1.json). Exigences utilisateur validées; méthode, preuves, paramètres et implémentation à qualifier. Raccord M/SH/AC/LIM, aucun nouveau moteur, aucun changement de statut ni gate promu. P0 substitution récursive, rentes, fiscalité, demande solvable et concentration; P1 raretés, capital humain, résilience, transmission et entretien; P2 motivation/statut/démographie exploratoires. Six scénarios concurrents composables, sans probabilité imposée. PRODUCT-FIRST et VERTICAL-001 V3e demeurent prioritaires, publication bloquée; pas de réouverture automatique de G4. BENCH-001, COMMON-STATE et PROSPECT/RESULT obligatoires. Les écarts deviennent chantiers à qualifier, pas résultats.


## POSTLAB-FOLLOWUP-001 — Contrôle obligatoire par jalon (27/11/2026)
[Procédure normative](POSTLAB-FOLLOWUP-001.md), [registre de suivi](../governance/postlab_followup_v1.json), [règles de reprise](../AGENTS.md). Les 297 lignes sont conservées et examinées avant/après chaque jalon; sélection originale, revue scientifique, données et droits, implémentation, calibration, validation sont des obligations de suivi, jamais implicites. Reçu de couverture obligatoire avant clôture, reports motivés et prochaine action; aucune promotion de gate. PRODUCT-FIRST et V3e inchangés. Le contrôle structurel ne remplace pas la qualification empirique.
