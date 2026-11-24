# OCTAVE LAB | Due diligence stratégique et scientifique

**David Shapiro, Post-Labor Economics et Universal High Income**

Étude du 25 novembre 2026. Analyse indépendante, sans modification de nos référentiels au moment de l'étude. Intégration documentaire autorisée par l'utilisateur le 25 novembre 2026.

Note archivistique : transcription documentaire de la réponse validée, avec les graphiques, diagrammes et contrôles interactifs représentés par leurs données, libellés, équations et paramètres. Les références web de la conversation sont remplacées lorsque possible par des liens bibliographiques explicites ; les chiffres de l'étude initiale sont conservés comme résultats historiques, non comme nouvelle vérification. Les précisions de mise en œuvre et le statut de preuve sont séparés dans DD-SHAPIRO-001-INTEGRATION.md. Aucun résultat empirique nouveau ni gate franchi par l'archivage.

## 1. État des lieux : notre point de départ

J'ai repris notre architecture maître sur Drive, les référentiels GitHub ARCH-002, PROSPECT-001, RESULT-001, le registre des mécanismes économiques et les derniers résultats de développement.

La distinction fondamentale à préserver est la suivante : **Octave Lab est un système d'investigation économique. Post-Labor Economics est principalement une démarche de recherche et une théorie de la transition vers une économie moins dépendante du travail humain.**

La disparition massive du travail constitue une trajectoire que nous devons pouvoir étudier, mais pas une conclusion que notre logiciel doit nécessairement produire.

### Notre niveau réel d'avancement

9 couches analytiques ; 6 moteurs spécifiés ; 64 mécanismes référencés ; 13 interfaces économiques ; 18 sections de restitution ; dernière recette technique G3 : 331 tests.

| Couche | Couverture actuelle |
|---|---|
| L01 – Technologie | Capacités, performances, coûts, conditions d'automatisation |
| L02 – Travail | Métiers, tâches, actions, compétences et substitutions |
| L03 – Opérations | Ressources, qualité, débit, contraintes et simulations |
| L04 – Organisation | Refonte, coordination, responsabilités et contrôle |
| L05 – Entreprise et capital | Coûts, revenus, investissements et rentabilité |
| L06 – Marchés et concurrence | Prix, demande, rentes et réactions concurrentielles |
| L07 – Secteurs et territoires | Chaînes de valeur, commerce et contraintes sectorielles |
| L08 – Travail et macroéconomie | Emploi, revenus, productivité, redistribution et institutions |
| L09 – Validation et prospective | Contrefactuels, réfutation, incertitude et alertes |

Les premières couches disposent déjà de composants exécutables. Les couches de marché et de macroéconomie restent principalement spécifiées. Nos simulations sont encore largement conditionnelles à des paramètres fictifs.

Sources internes : [architecture ARCH-002](ARCH-002.md), [registre des mécanismes](../governance/economic_mechanisms_v2.json), [architecture maître Drive](https://docs.google.com/document/d/15i4amgtwR6GWVyU-30I1NhNhFYLDnqjSrqdUhwHfjK8/edit).

**Cette distinction entre couverture conceptuelle, implémentation informatique et validation scientifique sera maintenue tout au long de la comparaison.**

## 2. Première découverte importante sur l'écosystème Shapiro

Le dépôt PostLaborEconomics est beaucoup plus proche d'une bibliothèque de recherche que d'un logiciel économique comparable à Octave Lab.

Son propre README précise que les rapports sont issus d'outils de recherche approfondie par IA, dirigés par l'auteur et exécutés automatiquement. Ils servent notamment à préparer ses livres.

103 rapports annoncés dans le README ; 41 graphiques annoncés.

L'inventaire du dépôt révèle également une bibliothèque textuelle, des travaux sur les revenus des ménages, trois livres blancs référencés et des scripts principalement consacrés à la publication et à la conversion documentaire.

Cela représente un corpus potentiellement très utile. Mais il ne faut pas confondre 103 rapports documentaires avec 103 contributions scientifiques originales évaluées par des pairs.

[README original de PostLaborEconomics](https://github.com/daveshap/PostLaborEconomics/blob/main/README.md)

## 3. Cartographie de l'écosystème : qui produit quoi ?

J'ai identifié une distinction importante entre les différentes ressources que tu m'as transmises.

| Ressource | Nature | Intérêt pour Octave Lab |
|---|---|---|
| [PostLaborEconomics – GitHub](https://github.com/daveshap/PostLaborEconomics) | Bibliothèque de rapports, graphiques et recherches assistées par IA | Inventaire de concepts et de références |
| [Site de recherche de Shapiro](https://daveshap.github.io/PostLaborEconomics/) | Publication organisée de ses travaux | Compréhension de sa théorie |
| [Labor Zero](https://daveshap.github.io/PostLaborEconomics/laborzero/) | Livre et documents complémentaires | Cadre de réflexion sur le travail et la propriété |
| [Universal High Income](https://github.com/daveshap/UniversalHighIncome) | Simulateur de revenus des ménages et livre blanc | Scénarios de redistribution et de détention du capital |
| [Substack](https://daveshap.substack.com/) | Analyses, opinions et estimations économiques | Identification de nouvelles hypothèses |
| [PostLaborEconomics.com/data](https://www.postlaboreconomics.com/data/) | Publication de données et d'indicateurs | Benchmark de veille et de visualisation |

Attention au dernier site : il indique explicitement s'inspirer du terme popularisé par Shapiro sans reprendre nécessairement ses conclusions. Je n'ai pas établi que Shapiro en soit le propriétaire ou le responsable éditorial. Il faut donc l'évaluer séparément.

### Les huit familles de recherche recensées par Shapiro

| Famille | Rapports |
|---|---:|
| Fondements de Post-Labor Economics | 13 |
| Pyramide du pouvoir | 12 |
| Gouvernance et contrat social | 10 |
| Revenus et propriété du capital | 18 |
| IA, automatisation et robotique | 17 |
| Travail, emplois et salaires | 15 |
| Histoire et transformations économiques | 12 |
| Société, culture et bien-être | 6 |

Répartition des 103 rapports selon le [site de recherche de Shapiro](https://daveshap.github.io/PostLaborEconomics/research/). Il ne s'agit pas de 103 études empiriques indépendantes.

### Évaluation de David Shapiro

Je le positionne comme un auteur, technologue et prospectiviste indépendant qui développe une synthèse personnelle de plusieurs disciplines économiques.

Ses points forts sont la transversalité, l'identification de problèmes de long terme, la réflexion sur les conséquences distributives et la capacité à rendre accessibles des scénarios complexes.

Sa faiblesse principale est que sa thèse d'une économie post-travail structure fortement les hypothèses qu'il explore. Je n'ai pas identifié de validation académique indépendante de cette théorie dans son ensemble.

Son travail mérite d'être étudié sérieusement, mais ses conclusions doivent rester contestables. La véritable valeur de son corpus réside davantage dans les problèmes qu'il pose que dans les réponses numériques qu'il propose.

# 4. Investigation prioritaire : les 3 à 6 millions d'emplois américains manquants

## 4.1. Verdict provisoire sur la publication du 24 novembre 2026

J'ai retrouvé une reprise indexée de son affirmation évoquant un déficit de 3 à 6 millions d'emplois, associé au découplage entre activité économique, emploi et heures travaillées.

En revanche, je n'ai pas pu récupérer le rapport original correspondant précisément à cette publication, ni son jeu de données figé, ni le code ayant produit cette fourchette.

**Non vérifiable en l'état — Résultat exact de Shapiro du 24 novembre.**

Cela ne signifie pas que le résultat soit faux. Cela signifie que nous ne pouvons pas encore reproduire son estimation exacte.

J'ai donc effectué une **contre-analyse indépendante sur des données réelles**, afin de tester la plausibilité de son ordre de grandeur et sa sensibilité aux hypothèses historiques.

## 4.2. Ce que disent réellement les données américaines

Pour cette première contre-analyse, j'ai utilisé les tableaux officiels BLS et BEA accessibles directement ou via FRED, jusqu'au deuxième trimestre 2026. Les versions consultées sont celles disponibles en juillet et août 2026, et non un millésime complet arrêté au 24 novembre.

Entre le quatrième trimestre 2022 et le deuxième trimestre 2026 :

- PIB réel américain : +8,94 %.
- Emplois salariés non agricoles : +3,03 %.

Sources : BEA, série [GDPC1](https://fred.stlouisfed.org/series/GDPC1), et BLS, série [PAYEMS](https://fred.stlouisfed.org/series/PAYEMS), convertie en moyennes trimestrielles.

Sur le périmètre distinct mais cohérent du secteur marchand non agricole mesuré par le BLS :

| Indicateur | Évolution cumulée |
|---|---:|
| Production réelle | +10,03 % |
| Productivité horaire | +9,06 % |
| Heures travaillées | +0,89 % |

T4 2022 – T2 2026. Calcul à partir des indices officiels [BLS](https://www.bls.gov/productivity/), base 2017.

Le découplage descriptif entre production et heures est donc bien visible. Il serait absurde de l'ignorer. En revanche, sa contribution proprement attribuable à l'IA reste à identifier.

## 4.3. Premier test de robustesse réalisé par Octave Lab

J'ai calculé la relation historique entre croissance du PIB réel et croissance de l'emploi salarié pour trois fenêtres antérieures à la pandémie.

Le principe est de mesurer une élasticité historique : lorsque le PIB augmente de 1 %, de combien l'emploi augmentait-il sur la période retenue ?

J'ai ensuite appliqué ces élasticités à la croissance effective du PIB entre fin 2022 et mi-2026.

| Fenêtre | Élasticité historique | Écart d'emploi (millions) |
|---|---:|---:|
| 2007–2019 | 0,428 | 1,078 |
| 2010–2019 | 0,697 | 4,809 |
| 2015–2019 | 0,570 | 3,044 |

Calcul indépendant, données BEA/BLS. Écart entre emploi contrefactuel et emploi observé. Ce ne sont pas des emplois détruits ni des estimations causales.

Le résultat est particulièrement instructif : en modifiant uniquement la fenêtre de référence, nous passons d'environ **1,08 million à 4,81 millions** d'emplois manquants.

J'ai également testé une extrapolation de la croissance historique de l'emploi, sans utiliser le PIB pour prédire celui-ci.

| Période de référence | Modèle lié au PIB | Extrapolation de la tendance d'emploi |
|---|---:|---:|
| 2007–2019 | +1,08 M manquants | −0,47 M |
| 2010–2019 | +4,81 M manquants | +4,48 M manquants |
| 2015–2019 | +3,04 M manquants | +3,63 M manquants |

Une valeur négative signifie que l'emploi observé dépasse le niveau impliqué par le modèle.

Et si nous changeons le point de départ du contrefactuel en passant de fin 2022 à fin 2019, les écarts deviennent respectivement 2,52, 8,97 et 5,91 millions.

La sensibilité est donc majeure, y compris au point d'ancrage du contrefactuel.

### Verdict de cette contre-analyse

La fourchette avancée par Shapiro est **plausible dans certaines spécifications, mais extrêmement dépendante du modèle de référence**.

Mon calcul ne reproduit pas son rapport original. Il démontre qu'un écart de plusieurs millions d'emplois par rapport à une trajectoire historique est possible, tout en démontrant la fragilité d'une estimation unique.

Je propose d'en faire un premier cas de référence pour notre futur moteur contrefactuel, mais certainement pas un chiffre vedette publié sans réserves.

## 4.4. Comment reproduire et améliorer ce calcul

Pour assurer la traçabilité, voici les valeurs utilisées dans mon calcul indépendant. Les emplois sont exprimés en millions, en moyenne trimestrielle, et le PIB réel en milliards de dollars chaînés de 2017, en rythme annualisé.

| Trimestre | PIB réel | Emplois salariés non agricoles |
|---|---:|---:|
| T4 2007 | 16 915,191 | 138,287 |
| T4 2010 | 16 960,864 | 130,733 |
| T4 2015 | 18 892,206 | 142,821 |
| T4 2019 | 20 985,448 | 151,640 |
| T4 2022 | 22 278,345 | 154,174 |
| T2 2026 | 24 270,599 | 158,847 |

Sources primaires : [BEA – PIB réel](https://fred.stlouisfed.org/series/GDPC1) et [BLS – emploi salarié non agricole](https://fred.stlouisfed.org/series/PAYEMS).

L'élasticité historique est calculée à partir des deux extrémités de chaque fenêtre :

β = ln(E_fin/E_début) / ln(PIB_fin/PIB_début).

Le niveau d'emploi contrefactuel est ensuite :

E_t^CF = E_0 × (PIB_t/PIB_0)^β.

L'écart d'emploi correspond à la différence entre ce niveau théorique et le niveau effectivement observé.

Il s'agit d'un test de sensibilité descriptif, exécuté ici indépendamment du logiciel Octave Lab, et non d'une régression économétrique déjà intégrée à notre moteur. Les fenêtres ont été choisies pour comparer plusieurs configurations historiques. Leur dispersion ne constitue pas un intervalle de confiance statistique.

## 4.5. Ce que nous apprend une autre étude de Shapiro

J'ai également retrouvé son analyse publiée le 10 février 2026, dans laquelle il estimait les pertes d'emplois liées à l'IA en 2025 à environ 200 000 à 300 000, en mobilisant deux approches principales.

| Approche | Principe | Problème méthodologique |
|---|---|---|
| Licenciements annoncés | Soustraire des licenciements totaux les causes identifiées et les niveaux habituels | Le résidu inexpliqué n'est pas nécessairement attribuable à l'IA |
| Productivité et heures | Estimer le travail qui aurait été nécessaire avec une productivité historique | Les équivalents en travail ne sont pas des personnes licenciées |

La deuxième approche s'appuie notamment sur une hausse annuelle de productivité de 1,9 % au troisième trimestre 2025, associée à une hausse de production de 2,8 % et des heures travaillées de 0,9 %.

Le choix de la productivité de référence change radicalement l'interprétation :

| Croissance de productivité supposée sans le choc | Surcroît de productivité observé |
|---|---:|
| 1,5 % | +0,4 point |
| 1,7 % | +0,2 point |
| 2,0 % | −0,1 point |

Avec la dernière hypothèse, le raisonnement par excès de productivité ne produit même plus un déficit positif.

Shapiro reconnaît lui-même des limites d'attribution dans cette analyse. Mais la convergence de plusieurs estimations réalisées avec des assistants IA ne constitue pas une validation indépendante, particulièrement lorsque les estimations partagent des données et des hypothèses similaires.

Ce travail antérieur ne permet pas de valider son affirmation du 24 novembre. Il nous renseigne cependant sur les méthodes qu'il utilise et sur les précautions indispensables pour construire nos propres contrefactuels.

## 4.6. Le mécanisme fondamental à isoler

La décomposition suivante doit être au cœur de notre analyse macroéconomique :

Y = P × H ; H = N × h.

Y : production économique réelle ; P : productivité horaire (production par heure travaillée) ; H : volume de travail (nombre total d'heures travaillées) ; N : nombre de travailleurs ; h : durée moyenne du travail.

À périmètre statistique identique, la production dépend donc de trois grandeurs : la productivité horaire, le nombre de travailleurs et leur durée moyenne de travail.

Il faut impérativement harmoniser les périmètres avant de procéder à cette décomposition. Les emplois salariés du BLS, le nombre de personnes employées et les heures travaillées dans le secteur marchand ne couvrent pas exactement les mêmes populations.

Nous devons ensuite distinguer six phénomènes qui peuvent produire des résultats agrégés similaires :

| Phénomène | Signature statistique à rechercher |
|---|---|
| Destruction d'emplois | Hausse des licenciements ou des suppressions de postes |
| Emplois non créés | Ralentissement des créations relativement à une référence |
| Non-remplacement des départs | Séparations normales et diminution des embauches |
| Réduction du temps de travail | Baisse des heures moyennes |
| Transfert d'activité | Baisse de l'emploi local et hausse chez d'autres acteurs |
| Modification de l'offre de travail | Évolution démographique, participation ou immigration |

Le terme « emplois manquants » masque potentiellement ces six mécanismes.

**C'est précisément leur séparation qui peut devenir une première source de différenciation d'Octave Lab.**

## 4.7. Les données les plus récentes renforcent-elles ce signal ?

Les publications de novembre 2026, postérieures au millésime utilisé dans mon test, montrent que le sujet reste d'actualité.

| Indicateur récent | Résultat |
|---|---:|
| Croissance du PIB réel au T3 2026 | +3,4 % annualisés |
| Productivité horaire du secteur marchand non agricole au T3 | +3,6 % annualisés |
| Production de ce même secteur au T3 | +3,7 % annualisés |
| Heures travaillées dans ce secteur au T3 | +0,1 % annualisés |
| Emploi salarié en octobre 2026 | +165 000 sur un mois |
| Taux de chômage en octobre 2026 | 4,1 % |

Sources : BEA, estimation avancée du PIB ; BLS, publications des 5 et 6 novembre 2026. Ces observations historiques de l'étude sont à repointer aux publications millésimées exactes avant réemploi.

Ces données sont compatibles avec une progression de l'activité économique beaucoup plus rapide que celle du volume de travail. Elles montrent également que découplage ne signifie pas nécessairement diminution absolue de l'emploi.

Je n'ai pas recalculé l'ensemble des trajectoires précédentes avec un millésime statistique intégral arrêté au 24 novembre. Mélanger les nouvelles observations avec d'anciennes séries historiques révisées introduirait un problème supplémentaire de comparabilité.

## 4.8. L'hypothèse du gel anticipatoire des recrutements

C'est probablement l'un des axes les plus intéressants pour nous.

Une entreprise n'a pas nécessairement besoin d'avoir automatisé une tâche pour décider de ne plus recruter sur cette tâche. L'anticipation de capacités technologiques futures peut modifier dès aujourd'hui ses décisions d'investissement et de recrutement.

Anticipation d'une nouvelle capacité technologique (la direction estime qu'une activité sera prochainement automatisable) → Révision des budgets de recrutement (les ouvertures de postes sont différées ou annulées) → Non-remplacement des départs (les effectifs diminuent progressivement, sans vague de licenciements) → Déploiement effectif de l'IA (la capacité technologique est ensuite intégrée aux opérations) → Transformation durable du travail (les emplois, les compétences et l'organisation évoluent).

Trajectoire hypothétique à confronter à des données d'entreprise. L'ordre de ces événements peut varier.

Des recherches récentes nous donnent déjà de bonnes raisons d'étudier cette hypothèse, mais aussi de ne pas la généraliser.

- Le Census Bureau, dans You're (not) Hired en avril 2026, observe notamment une détérioration relative des embauches et des remplacements de départs concernant les jeunes travailleurs dans les activités exposées à l'IA. Les auteurs identifient aussi des tendances antérieures à ChatGPT et examinent les effets de la politique monétaire.
- Une étude de la Federal Reserve du 27 mars 2026 ne trouve pas de diminution générale des offres d'emploi dans les entreprises et secteurs adoptant davantage l'IA.
- La BCE observe en mars 2026 des intentions de recrutement plutôt favorables chez certaines entreprises européennes prévoyant d'investir dans l'IA. En revanche, les entreprises qui l'utilisent spécifiquement pour réduire leurs coûts de main-d'œuvre présentent des résultats différents.
- Les travaux de la Federal Reserve publiés le 17 novembre 2026 identifient une augmentation des disparités dans les perspectives de retrouver un emploi depuis 2023, en lien avec leurs mesures d'exposition et d'adoption de l'IA.

**Proposition d'enrichissement :** ajouter explicitement les anticipations technologiques dans les mécanismes M029, M033, M049 et M060 déjà existants.

Il faudra distinguer la date d'anticipation, la décision budgétaire, la date d'investissement, la mise en production et le moment où les effets sur l'emploi deviennent observables.

Cela ne nécessite pas un nouveau moteur.

## 4.9. Protocole de réplication scientifique complet

Voici les méthodes que je propose pour notre moteur contrefactuel.

| Modèle | Utilité |
|---|---|
| Tendances historiques | Référence simple et transparente |
| Élasticités emploi-production | Comparaison des relations économiques |
| Régressions dynamiques | Prendre en compte les décalages temporels |
| Détection de ruptures structurelles | Tester si les relations historiques changent réellement |
| Modèles à facteurs et projections locales | Étudier les contributions de plusieurs chocs |
| Décomposition sectorielle | Séparer les transformations internes et les déplacements entre secteurs |
| Études d'événements et groupes témoins | Examiner l'effet de l'adoption technologique lorsqu'un dispositif d'identification crédible existe |

Les facteurs concurrents doivent inclure le vieillissement, l'immigration, la participation au marché du travail, les taux d'intérêt, le cycle économique, les effets de la pandémie, les changements de composition sectorielle, les délocalisations et les révisions statistiques.

Nous devrons également soumettre ces modèles à des tests sur des périodes antérieures à l'IA générative. Un modèle qui aurait déjà annoncé plusieurs millions d'emplois manquants en 2015 ou en 2019 ne constitue pas, à lui seul, un bon détecteur d'une rupture liée à l'IA.

**Verdict final à ce stade :**

| Affirmation | Verdict |
|---|---|
| Découplage récent entre production et heures travaillées | Observé |
| Déficit d'emplois de plusieurs millions relativement à certaines trajectoires historiques | Plausible mais sensible aux hypothèses |
| Estimation exacte de Shapiro du 24 novembre | Non vérifiable faute de rapport et données d'origine |
| 3 à 6 millions d'emplois détruits par l'IA | Non démontré |
| Contribution de l'IA au ralentissement des recrutements dans certaines activités | Hypothèse soutenue par plusieurs travaux, à qualifier selon les populations |
| Destruction nette massive à l'échelle de toute l'économie | Non établie par les éléments examinés |

# 5. Audit d'Universal High Income

J'ai inspecté la documentation technique du simulateur et son code JSX, notamment la fonction annuelle de simulation et ses paramètres par défaut.

C'est ici que la distinction entre outil pédagogique et modèle économique devient particulièrement importante.

Le projet se définit lui-même comme un modèle simplifié destiné à l'exploration de scénarios, et non comme une prévision économétrique.

Sources : [documentation technique](https://github.com/daveshap/UniversalHighIncome/blob/main/simulations/readme.md), [code du simulateur](https://github.com/daveshap/UniversalHighIncome/blob/main/simulations/uhi_simulator.jsx).

## 5.1. Architecture réelle du simulateur

Trajectoire d'automatisation supposée (vitesse choisie par l'utilisateur) → croissance du PIB imposée par une formule et diminution des revenus du travail imposée par une formule → neuf sources de revenus : revenus du travail, protection sociale, revenu universel, dividendes du fonds souverain, participation salariale au capital, dotations en capital à la naissance, redevances sur les données et l'IA, dividendes carbone, investissements privés → majoration du pouvoir d'achat (baisse des prix supposée) → revenu effectif du ménage représentatif.

L'idée intéressante est de dissocier les revenus des ménages de leur seule participation au marché du travail.

En revanche, les interactions économiques qui déterminent ces revenus sont très largement simplifiées ou absentes.

## 5.2. Paramètres et hypothèses

| Variable | Valeur initiale ou règle par défaut |
|---|---|
| PIB de référence | 29 000 milliards de dollars |
| Nombre de ménages | 131 millions, constant |
| Revenu médian de référence | 83 730 dollars |
| Taux initial d'automatisation | 5 %, avant la première itération |
| Vitesse d'automatisation | 2,5 % |
| Croissance économique de base | 2 % |
| Automatisation maximale | 95 % |
| Revenu universel mensuel | 2 000 dollars par adulte |
| Fonds souverain initial | 100 milliards de dollars |
| Contribution au fonds | 1,5 % du PIB, ajustée par un coefficient |
| Rendement annuel du fonds | 7 % |
| Distribution annuelle du fonds | 3 % |
| Baisse maximale des coûts de la vie paramétrée | 35 % |

Ces paramètres ne sont pas tous des observations empiriques. Plusieurs déterminent directement le résultat souhaité du scénario.

## 5.3. Reconstitution indépendante des équations

J'ai réexécuté une transcription indépendante des équations du simulateur avec ses paramètres par défaut.

| Année | Politiques de redistribution et baisse des prix activées | Scénario « No Action » |
|---|---:|---:|
| 2025 | 83 393 $ | 82 604 $ |
| 2035 | 120 894 $ | 72 931 $ |
| 2045 | 138 661 $ | 64 433 $ |
| 2060 | 178 059 $ | 59 263 $ |

Résultats de ma reconstitution des équations de Shapiro. Ils ne constituent ni une projection indépendante de l'économie américaine ni une validation du modèle.

| Variable | 2035 | 2045 | 2060 |
|---|---:|---:|---:|
| Automatisation supposée | 31,5 % | 52,2 % | 74,4 % |
| PIB calculé, milliers de milliards $ | 38,0 | 51,5 | 87,8 |
| Fonds souverain, milliers de milliards $ | 6,4 | 16,9 | 49,2 |
| Revenus annuels du travail | 54 470 $ | 41 271 $ | 24 979 $ |
| Revenu total avant majoration du pouvoir d'achat | 109 082 $ | 114 553 $ | 132 512 $ |
| Revenu effectif après majoration | 120 894 $ | 138 661 $ | 178 059 $ |

La comparaison des deux scénarios est visuellement spectaculaire. Malheureusement, une bonne partie de cet écart est construite par les hypothèses elles-mêmes.

## 5.4. Les problèmes identifiés dans le code

### A. Le découplage entre PIB et revenus du travail est imposé

Dans le modèle, l'automatisation augmente mécaniquement la croissance du PIB et diminue mécaniquement les revenus du travail.

Le résultat ne provient donc pas d'une simulation des décisions des entreprises, du comportement des marchés, de la création de nouveaux produits ou des arbitrages capital-travail.

Les mécanismes de complémentarité et de création nette d'emplois ne disposent pas d'une représentation suffisante pour contredire la trajectoire principale.

### B. La disparition des revenus du travail n'entraîne pas de crise de la demande

C'est une contradiction importante avec le récit économique de Post-Labor Economics.

Dans la simulation, la trajectoire du PIB est identique dans le scénario de redistribution et dans celui sans intervention.

La diminution du revenu des ménages ne provoque aucune diminution endogène de la consommation, de la demande adressée aux entreprises, des investissements ou de l'emploi.

**Le modèle ne permet donc pas de démontrer que la redistribution est indispensable à la stabilité macroéconomique.**

Il ne simule pas précisément le mécanisme qui permettrait de le démontrer.

### C. Le financement de la redistribution n'est pas bouclé

La capacité fiscale est représentée par un coefficient simplifié, augmenté lorsque certaines taxes sont activées.

Or les transferts distribués doivent être financés par des impôts, des revenus patrimoniaux, une diminution d'autres dépenses, de la dette ou une combinaison de ces mécanismes.

Avec ses hypothèses par défaut, le revenu universel atteint 33 480 dollars annuels par ménage représentatif. En multipliant ce montant par les 131 millions de ménages supposés, cela représente environ **4 386 milliards de dollars de dépenses annuelles**.

Le modèle ne démontre pas que les recettes fiscales supplémentaires permettent effectivement de financer ce montant ainsi que les autres interventions.

### D. La baisse des prix est supposée plutôt que produite

Le simulateur majore le pouvoir d'achat selon le niveau d'automatisation atteint.

Il ne calcule pas cette baisse des prix à partir des coûts marginaux, des contraintes d'offre, de la concurrence, des marges ou de la composition du panier de consommation.

De plus, le scénario sans intervention désactive également cette baisse des prix. Il mélange donc deux expériences :

- L'effet des politiques de redistribution.
- L'effet des gains de pouvoir d'achat liés à une baisse supposée des prix.

Ces deux dimensions devraient être testées indépendamment.

### E. La distribution réelle des revenus est absente

Un ménage représentatif ne permet pas d'étudier correctement la concentration de la propriété productive.

Il est statistiquement incorrect de supposer que l'addition de composantes médianes reproduit nécessairement le revenu médian total.

Il faudrait représenter différents types de ménages, leurs revenus salariaux, leurs actifs, leurs dettes, leurs droits sociaux et leur exposition aux différents prix.

### F. J'ai également identifié des incohérences d'implémentation

La première année est déjà soumise à l'augmentation de l'automatisation et à la croissance du PIB. La situation initiale de 2025 affichée dans la simulation n'est donc pas strictement celle décrite par les constantes de référence.

La progression présentée comme une courbe en S utilise une formule dont les incréments diminuent avec le niveau d'automatisation positif. Elle ne reproduit pas véritablement une diffusion logistique classique.

Enfin, la normalisation utilisée ne permet pas d'atteindre exactement la valeur maximale normalisée de 1 lorsque l'automatisation atteint son plafond de 95 %. Cela affecte notamment le niveau résiduel des revenus du travail.

Ces problèmes sont secondaires par rapport à l'absence de bouclage économique, mais ils confirment la nécessité de vérifier le code plutôt que de se fier uniquement à sa documentation.

## 5.5. Ce qu'il faut retenir d'Universal High Income

| Composant | Décision proposée |
|---|---|
| Diversification des sources de revenus | Intégrer conceptuellement |
| Accumulation du capital dans le temps | Approfondir |
| Fonds souverains et dividendes citoyens | Expérimenter |
| Dotations patrimoniales à la naissance | Conserver comme scénario institutionnel |
| Participation des salariés au capital | Intégrer aux variantes de partage de valeur |
| Revenus liés à la propriété collective | Approfondir |
| Trajectoire mécanique de disparition des salaires | Écarter comme règle générale |
| Croissance du PIB indépendante de la demande | Écarter |
| Baisse uniforme des prix | Écarter |
| Coefficient fiscal sans budget équilibré | Écarter |
| Ménage représentatif unique | Remplacer par des cohortes de ménages |
| Interface interactive de scénarios | Retenir comme benchmark pédagogique |

Une précision juridique importante : le dépôt UniversalHighIncome est sous licence CC BY-NC-ND 4.0. Nous ne devons pas reprendre son code dans un produit commercial sans autorisation appropriée. Nous pouvons étudier les concepts économiques et développer nos propres modèles indépendamment.

**Verdict : intéressant pour explorer les instruments de redistribution, insuffisant pour simuler de manière cohérente une économie post-travail.**

# 6. Les travaux les plus intéressants de Shapiro pour Octave Lab

Au-delà de son simulateur et de ses estimations d'emploi, plusieurs parties de son corpus méritent une attention particulière.

## 6.1. La distinction entre le besoin fonctionnel et le besoin d'intervention humaine

Dans son livre blanc [Derived and Essential Demand](https://daveshap.github.io/PostLaborEconomics/whitepapers/derived-and-essential-demand.html), Shapiro s'intéresse notamment à la nature du travail qui conserverait une valeur économique lorsque les machines pourront produire le résultat fonctionnel recherché.

Cette distinction est particulièrement intéressante pour nous.

Prenons quatre activités :

| Activité | Résultat fonctionnel recherché | Valeur spécifique de l'intervention humaine |
|---|---|---|
| Traduction | Comprendre un texte | Potentiellement faible pour une traduction courante |
| Analyse médicale | Obtenir un diagnostic fiable | Confiance, responsabilité et accompagnement |
| Concert | Écouter de la musique | Présence humaine et expérience collective |
| Artisanat | Obtenir un objet | Provenance, authenticité, personnalisation |

Le point essentiel est que **la valeur d'un produit ou d'un service ne dépend pas toujours exclusivement de sa performance fonctionnelle**.

Une machine peut devenir techniquement supérieure sans supprimer intégralement la demande pour la prestation humaine.

Il faut néanmoins mesurer cette préférence. Le fait qu'un consommateur préfère théoriquement un humain ne signifie pas qu'il soit disposé à payer dix fois plus cher pour cette intervention.

### Intégration proposée

Enrichir M011, M019, M035, M036, M038 et M041 avec une composante explicite de préférence pour la provenance humaine :

- Différence de prix acceptable.
- Substituabilité entre prestations humaines et automatisées.
- Valeur de la confiance, de l'authenticité et de la responsabilité.
- Sensibilité de cette préférence au revenu du consommateur.
- Évolution de la préférence lorsque la qualité des machines augmente.

Cela apporterait une dimension supplémentaire à nos simulations de marché, notamment pour les métiers du lien, les professions intellectuelles, l'artisanat et les activités créatives.

## 6.2. La non-rivalité partielle de l'intelligence artificielle

Un autre thème traité dans son corpus est la différence économique entre l'automatisation physique et l'automatisation numérique.

Une machine industrielle ne peut généralement pas être utilisée simultanément pour une infinité d'opérations. Un logiciel peut être répliqué à grande échelle, mais son exécution mobilise encore des infrastructures, de l'énergie et des ressources de calcul.

Nous devons donc distinguer :

| Composante | Nature économique |
|---|---|
| Modèle entraîné | Actif reproductible |
| Infrastructure de calcul | Ressource limitée |
| Exécution d'une tâche | Consommation de ressources |
| Données exclusives | Actif potentiellement différenciant |
| Résultat numérique | Potentiellement reproductible à faible coût |
| Intervention physique | Contrainte matérielle et géographique |

Cette distinction est déjà partiellement couverte par M003, M004, M031, M040 et M048. Elle mérite cependant une formulation plus explicite dans nos modèles de coûts et de diffusion.

Elle explique notamment pourquoi certaines transformations numériques peuvent être beaucoup plus rapides que les transformations industrielles, sans pour autant supposer que les coûts marginaux deviennent systématiquement nuls.

## 6.3. L'entreprise sans salariés

Le rapport Zero-Labor Enterprises explore l'hypothèse d'une entreprise dont l'effectif tend vers zéro à mesure que les fonctions sont automatisées.

Cette idée recouvre largement TRANSFORM-001 et les mécanismes M007, M018, M022, M030 et M033.

Notre travail apporte déjà une nuance indispensable : une entreprise sans salariés ne constitue pas nécessairement une chaîne de valeur sans travail humain.

Elle peut dépendre de fournisseurs, d'infrastructures, de prestataires externes, de maintenance, d'auditeurs et de responsables légaux.

Octave Lab devra donc pouvoir distinguer le travail humain :

- Directement employé par l'entreprise.
- Externalisé auprès de prestataires.
- Incorporé dans les services technologiques achetés.
- Mobilisé périodiquement pour la surveillance et la maintenance.
- Nécessaire en amont et en aval de la chaîne de valeur.

C'est un enrichissement des interfaces existantes entre L04, L05 et L07, et non un nouveau module.

## 6.4. La propriété productive et les revenus du capital

C'est probablement la contribution conceptuelle la plus intéressante de Shapiro pour nos couches macroéconomiques.

Deux indicateurs proposés dans son corpus méritent d'être étudiés.

**Economic Agency Index — composition des revenus des ménages**

Distinguer les revenus du travail, ceux issus du patrimoine et ceux issus des transferts publics.

**Inclusive Capital Income Ratio (ICIR) — diffusion des revenus du capital**

Chercher à mesurer dans quelle mesure les revenus provenant du capital productif bénéficient à une population étendue, plutôt qu'à une minorité de propriétaires.

Ces propositions figurent dans les rapports Towards an Economic Agency Index et Inclusive Capital Income Ratio, disponibles dans le [corpus textuel original](https://github.com/daveshap/PostLaborEconomics/tree/main/Research_txt).

Elles ne constituent pas des découvertes économiques entièrement nouvelles. La comptabilité nationale, les travaux sur la distribution fonctionnelle des revenus et les comptes patrimoniaux couvrent déjà une partie importante de ces questions.

L'intérêt réside dans leur combinaison pour étudier une transformation technologique majeure.

Cependant, je déconseille de reprendre directement l'ICIR : sa définition laisse subsister des ambiguïtés concernant le caractère inclusif des revenus, leur distribution et le dénominateur utilisé.

### Ce qu'Octave Lab devrait mesurer à la place

Composition et distribution des revenus (indicateurs proposés, sans données fictivement présentées comme observées) :

- Revenus du travail : salaires et composante travail des revenus des indépendants.
- Revenus du patrimoine : dividendes, intérêts, revenus locatifs et autres revenus du capital.
- Transferts publics : prestations sociales, pensions et dispositifs de redistribution.
- Prélèvements : impôts et cotisations selon le périmètre statistique retenu.
- Revenu disponible réel : ressources effectivement disponibles, corrigées de l'évolution des prix.
- Patrimoine productif détenu : actifs, dettes et concentration de la propriété.

Décomposition par niveau de revenu, patrimoine, âge, territoire et type de ménage.

Il ne faut surtout pas tout fusionner dans un score unique. Un ménage vivant principalement de ses actifs, un retraité bénéficiant d'une pension et un ménage dépendant de prestations sous conditions de ressources n'ont pas la même situation économique.

**Nous devons conserver les dimensions séparées pour comprendre les mécanismes.**

## 6.5. Les trois nouveaux livres blancs

| Document | Contenu annoncé | Intérêt prioritaire |
|---|---|---|
| [Derived and Essential Demand](https://daveshap.github.io/PostLaborEconomics/whitepapers/derived-and-essential-demand.html) | 161 pages sur la demande de travail humain | Élevé pour G3.4 |
| [Household Income Interventions](https://daveshap.github.io/PostLaborEconomics/whitepapers/household-income-interventions.html) | Catalogue annoncé de 213 interventions économiques | Élevé pour G4 |
| [Metrics Reference](https://daveshap.github.io/PostLaborEconomics/whitepapers/metrics-reference.html) | 764 pages et 140 chapitres consacrés aux indicateurs | Très élevé pour notre registre de données |

Ces trois documents justifient une lecture approfondie et une vérification de leurs références primaires. Je les ai identifiés et cartographiés, mais je ne prétends pas avoir audité intégralement leurs centaines de pages dans cette première étude.

Les 140 indicateurs constituent notamment un corpus à confronter systématiquement à notre propre registre. Leur nombre n'est évidemment pas un objectif à reproduire : chaque indicateur devra répondre à une question économique précise.

## 6.6. Le site PostLaborEconomics.com

Indépendamment de la question de son attribution à Shapiro, ce site propose une démarche intéressante de mesure de la production d'intelligence artificielle.

Il développe notamment le concept de Gross Intelligence Product, qui combine plusieurs grandeurs :

GIP_c,t = E_c,t × C_t × Q_t.

- E : énergie consommée par l'IA.
- C : capacité de calcul par unité d'énergie.
- Q : performance estimée par unité de calcul.

Il prévoit également un indicateur destiné à mesurer la part des heures rémunérées dont le résultat aurait été produit par une IA.

L'idée est séduisante. La difficulté est considérable.

Un volume de calcul n'est pas une mesure de valeur économique créée. Un million de requêtes inutiles peut consommer davantage de ressources qu'une requête permettant une découverte scientifique majeure.

Je recommande de retenir cette approche comme **indicateur expérimental de capacité et d'usage**, mais de refuser toute assimilation directe avec le PIB ou la production économique utile.

# 7. Confrontation aux meilleures recherches économiques

Il serait particulièrement dangereux de construire Octave Lab uniquement à partir d'auteurs convaincus de la disparition prochaine du travail.

Notre bibliothèque scientifique doit contenir les mécanismes contradictoires et permettre de les confronter.

## 7.1. Les références théoriques fondamentales

| Chercheur | Travaux | Apport pour Octave Lab |
|---|---|---|
| Daron Acemoglu et Pascual Restrepo | [Automation and New Tasks](https://www.nber.org/papers/w25684) | Substitution et création de nouvelles tâches |
| David Autor et collaborateurs | [New Frontiers](https://www.nber.org/papers/w30389) | Apparition historique de nouvelles activités |
| James Bessen | [AI and Jobs: The Role of Demand](https://www.nber.org/papers/w24235) | Demande, élasticité et emploi |
| Philippe Aghion, Benjamin Jones et Charles Jones | [Artificial Intelligence and Economic Growth](https://www.nber.org/papers/w23928) | Croissance limitée par les activités difficiles à améliorer |
| Daron Acemoglu | [The Simple Macroeconomics of AI](https://www.nber.org/papers/w32487) | Passage des économies de coûts par tâche à la productivité agrégée |
| Acemoglu, Autor et Johnson | [Building Pro-Worker Artificial Intelligence](https://www.nber.org/papers/w34854) | Complémentarité, acquisition d'expertise et création de tâches |

Ces travaux fournissent une assise théorique plus solide que la simple hypothèse d'une diminution mécanique du travail humain à mesure que l'intelligence artificielle progresse.

## 7.2. Les résultats empiriques contemporains

| Étude | Résultat pertinent | Limite |
|---|---|---|
| Brynjolfsson, Li et Raymond | Gains de productivité dans le support client | Un contexte opérationnel particulier |
| Stanford, Canaries in the Coal Mine, août 2026 | Écart relatif d'emploi de 19 % pour les jeunes de 22 à 25 ans dans les professions exposées | Ne constitue pas une estimation des emplois détruits dans l'économie entière |
| Humlum et Vestergaard | Changements organisationnels, mais effets précoces limités sur plusieurs résultats du marché du travail danois | Horizon court et contexte institutionnel spécifique |
| Hampole et collaborateurs | Substitution de certaines tâches compensée en partie par une augmentation de la demande de travail dans les entreprises adoptantes | Période principalement antérieure à la diffusion massive des IA génératives |
| BRI, janvier 2026 | Hausse estimée de productivité de 4 % dans les entreprises européennes étudiées, associée à davantage de capital plutôt qu'à une suppression immédiate d'emplois | Effets de court terme |
| Federal Reserve, mars 2026 | Pas de diminution générale détectée des offres d'emploi dans les entreprises plus fortement adoptantes | Adoption et offres d'emploi imparfaitement mesurées |
| OIT, revue empirique 2026 | Transformation des tâches plus documentée que destruction massive d'emplois | Littérature encore récente |

Le message scientifique est limpide : **les effets de l'IA sur le travail sont réels, mais profondément hétérogènes.**

Le fait que les effets agrégés restent limités aujourd'hui ne démontre pas qu'ils le resteront demain. Inversement, l'accélération des capacités technologiques ne démontre pas que leurs effets économiques futurs auront nécessairement le signe ou l'amplitude prévus par Shapiro.

## 7.3. Le mécanisme qui pourrait contredire sa thèse : la demande

Démonstration interactive du raisonnement de Bessen appliqué à une situation simplifiée, transcrite : simulation illustrative à qualité constante, sans contraintes supplémentaires.

- Hausse de la productivité du travail p : curseur 0 à 200 %, pas 5, valeur initiale 50 %.
- Hausse de la production effectivement demandée v : curseur 0 à 300 %, pas 5, valeur initiale 25 %.
- Volume de travail initial : 100. Nouveau volume de travail : 100 × (1+v/100)/(1+p/100).
- À p=50 %, v=25 %, résultat 83,333 ; variation −16,667 %. Seuil de compensation : v=p.
- Réinitialiser aux paramètres initiaux.

Une hausse de la demande de p % compenserait exactement le gain de productivité sélectionné, dans ce modèle élémentaire. Le volume de travail n'est pas directement un nombre d'emplois.

Une technologie peut donc réduire le travail nécessaire pour chaque unité produite tout en augmentant le volume total de travail, à condition que la demande augmente suffisamment.

L'apparition de nouveaux produits, l'ouverture de nouveaux marchés ou la solvabilisation d'une demande précédemment inaccessible peuvent également modifier le résultat.

Ce sont des mécanismes que notre architecture couvre déjà, mais auxquels G3.4 devra donner une véritable existence computationnelle.

# 8. Comparaison systématique avec notre architecture

L'examen des 64 mécanismes du registre ARCH-002 montre que l'essentiel du corpus de Shapiro possède déjà un point de rattachement dans Octave Lab.

La nouveauté se situe principalement dans certaines articulations et certains indicateurs, plutôt que dans de nouveaux mécanismes fondamentaux.

| Domaine | Mécanismes existants | Évaluation |
|---|---|---|
| Capacités techniques, robotique et coût de l'IA | M001–M006 | Couvert |
| Substitution, complémentarité, nouvelles tâches | M007–M010 | Couvert |
| Expertise, juniors, responsabilité | M011–M013 | Enrichissement nécessaire |
| Contraintes opérationnelles et résilience | M014–M020 | Notre architecture est plus détaillée |
| Organisation, pouvoir et coordination | M021–M026 | Couvert, formalisation à poursuivre |
| Investissement, adoption et capital-travail | M027–M034 | Couvert, G3.3 en développement |
| Prix, concurrence, élasticité et rentes | M035–M042 | Couvert, G3.4 à développer |
| Chaînes de valeur et commerce | M043–M048 | Couvert, enrichissement des contraintes matérielles |
| Emploi, mobilité et recrutement | M049–M050 | Enrichissement prioritaire |
| Répartition des revenus et négociation | M051–M052 | Enrichissement prioritaire |
| Redistribution et consommation | M053 | Enrichissement substantiel |
| Productivité agrégée et finance | M054–M055 | Enrichissement méthodologique |
| Démographie | M056 | Couvert |
| Institutions, fiscalité et propriété | M057 | Enrichissement substantiel |
| Inflation et pouvoir d'achat | M058 | Enrichissement nécessaire |
| Anomalies, contrefactuels et preuve causale | M059–M064 | Méthodes à implémenter et valider |

Cette cartographie constitue un examen de couverture conceptuelle, pas une certification des méthodes ou de l'état d'implémentation des 64 mécanismes.

## 8.1. Les domaines où notre approche est architecturalement plus exigeante

**Décomposition du travail**

Shapiro raisonne souvent en catégories agrégées. Octave Lab descend jusqu'aux actions élémentaires, aux contraintes des processus et aux ressources nécessaires à leur réalisation.

**Adoption économique**

Une activité techniquement automatisable n'est pas nécessairement rentable à automatiser. Nos développements G3.2 et G3.3 commencent déjà à matérialiser cette distinction.

**Trajectoires concurrentes**

Notre architecture autorise des scénarios de substitution, de complémentarité, de non-adoption et de création d'emplois.

**Traçabilité scientifique**

Chaque résultat doit conserver ses hypothèses, ses sources, son périmètre, ses limites et ses conditions de réfutation.

Il s'agit d'avantages architecturaux vérifiables dans nos spécifications et certains composants existants. Il serait prématuré d'en conclure que la qualité empirique ou commerciale de notre plateforme est déjà supérieure.

## 8.2. Nos véritables angles morts

J'en retiens huit qui méritent un traitement explicite.

| Angle mort | Pourquoi il importe |
|---|---|
| Anticipations technologiques | Les décisions d'emploi peuvent précéder les gains techniques |
| Formation dynamique de l'expertise | La disparition des tâches juniors peut modifier les compétences disponibles plusieurs années plus tard |
| Préférence pour les prestations humaines | L'automatisation fonctionnelle ne supprime pas toujours la demande humaine |
| Propriété productive | La distribution de la richesse ne se résume pas à la distribution des salaires |
| Bouclage des revenus et de la consommation | Les gains microéconomiques modifient les débouchés futurs |
| Transition fiscale | Les recettes publiques changent avec la structure des revenus et de l'activité |
| Rentes de rareté | Les gains technologiques peuvent se déplacer vers le foncier, l'énergie ou d'autres ressources limitées |
| Réactions institutionnelles | Les politiques publiques et les rapports de négociation influencent la diffusion technologique |

Tous peuvent être rattachés aux couches et mécanismes existants. Je ne recommande aucun septième moteur.

# 9. Matrice de décision et de priorisation

Les priorités ci-dessous sont déterminées par la valeur analytique supplémentaire, la disponibilité potentielle des données et les dépendances techniques.

P0 : à examiner dès maintenant en parallèle. P1 : prochaines tranches G3. P2 : développement G4. P3 : recherche exploratoire.

| Apport potentiel | Preuves et origine | Couverture actuelle | Décision |
|---|---|---|---|
| Découplage production-emploi-heures | BLS, BEA ; affirmation Shapiro non reproduite | M049, M054, M059–063 | Approfondir · P0 |
| Emplois non créés et non-remplacement | Census, Federal Reserve | M033, M049 | Intégrer · P0 |
| Gel anticipatoire des recrutements | Hypothèse, signaux empiriques partiels | M029, M033, M060 | Expérimenter · P0 |
| Formation de l'expertise | Autor, Stanford et travaux sur les tâches | M012, M024, M050 | Approfondir · P1 |
| Préférence pour le travail humain | Shapiro, économie de la demande | M011, M019, M036 | Expérimenter · P1 |
| Non-rivalité et coût de réplication | Économie des biens numériques | M003, M031, M040 | Intégrer · P1 |
| Entreprise sans salariés | Hypothèse de Shapiro | M018, M022, M030 | Conserver comme scénario · P1 |
| Effets rebond et saturation | Bessen, économie de la demande | M036, M041 | Approfondir · P1 |
| Goulots à l'échelle sectorielle | Baumol, Aghion et Jones | M043, M045, M048 | Approfondir · P2 |
| Distribution des revenus du capital | FMI, BEA, Fed, Shapiro | M042, M051–053 | Intégrer · P2 |
| Concentration du patrimoine productif | Comptes patrimoniaux | M051, M055 | Intégrer · P2 |
| Revenu universel et fiscalité | FMI, expériences historiques, UHI | M053, M057 | Expérimenter · P2 |
| Fonds souverains et dividendes | Programmes existants, UHI | M055, M057 | Expérimenter · P2 |
| Diminution sectorielle des prix | Modèles de marché | M035, M037, M058 | Approfondir · P1/P2 |
| Dépendances énergétiques et matérielles | Données physiques et économiques | M045, M048 | Approfondir · P2 |
| Mesure de production d'intelligence | Indicateur expérimental externe | M001–006, M048, M059 | Expérimenter · P3 |
| Effondrement inévitable des revenus salariaux | Hypothèse prospective | Scénarios PROSPECT-001 | Écarter comme règle générale |
| Croissance et déflation imposées par UHI | Paramétrage du simulateur | M054, M058 | Écarter |

## 9.1. Données, faisabilité et risques des enrichissements retenus

| Enrichissement | Données nécessaires | Faisabilité et dépendances | Risque majeur |
|---|---|---|---|
| Contrefactuels d'emploi | PIB, heures, emplois, millésimes statistiques | Élevée pour le descriptif ; G1, E03, E04 | Choix opportuniste de la référence |
| Flux de recrutement | Embauches, séparations, âge et métier | Moyenne ; G1, G2, G3.3 | Confondre annonces et embauches |
| Anticipations | Intentions, budgets, dates d'adoption | Moyenne à faible sans partenaires | Causalité inverse |
| Expertise | Cohortes, promotions, compétences, formation | Moyenne ; G2 et G3.3 | Déduire l'expertise de l'âge |
| Préférence humaine | Prix, choix des clients, qualité comparable | Moyenne, enquêtes ou transactions | Confondre préférence déclarée et achat réel |
| Transmission aux prix | Coûts, prix, volumes, concurrence | Moyenne ; G3.3 et G3.4 | Supposer une transmission intégrale |
| Propriété productive | Actifs, dettes, revenus et détention du capital | Élevée au niveau agrégé ; G4 | Confondre patrimoine et revenu |
| Redistribution | Recettes publiques, transferts, consommation | Moyenne ; G4 | Double comptage ou financement fictif |
| Rentes de rareté | Énergie, immobilier, infrastructures, matières | Moyenne ; G3.4 et G4 | Omettre les contraintes physiques |
| Production d'intelligence | Calcul, énergie, usage et résultats | Faible pour la valeur économique | Confondre activité informatique et utilité |

La valeur des apports les plus importants réside dans leur articulation. Un indicateur supplémentaire isolé a souvent peu d'intérêt. Un indicateur qui permet de discriminer deux scénarios économiques opposés peut avoir une valeur considérable.

# 10. Nouvelles sources de données à qualifier

Nous disposons déjà d'un socle de données françaises et européennes. L'étude américaine doit nous permettre d'enrichir notre registre de sources sans abandonner cette priorité géographique.

| Source | Informations utiles |
|---|---|
| [FRED et ALFRED](https://alfred.stlouisfed.org/) | Séries économiques et millésimes historiques |
| [BLS – JOLTS](https://www.bls.gov/jlt/) | Embauches, départs, licenciements et postes vacants |
| [Census – QWI](https://lehd.ces.census.gov/data/) | Flux d'emploi par catégories de travailleurs et entreprises |
| [Census – BTOS](https://www.census.gov/hfp/btos/) | Adoption technologique et situation des entreprises |
| [BEA – Distribution of Personal Income](https://www.bea.gov/data/special-topics/distribution-of-personal-income) | Distribution des revenus des ménages |
| [Federal Reserve – DFA](https://www.federalreserve.gov/releases/z1/dataviz/dfa/) | Distribution du patrimoine et des actifs |
| [Insee – Comptes par catégories de ménage](https://www.insee.fr/fr/statistiques/8988803) | Revenus, transferts et distribution en France |
| [Insee – Distribution du patrimoine](https://www.insee.fr/fr/statistiques/2388851) | Détention des actifs et inégalités patrimoniales |
| Dares, Urssaf, France Travail | Embauches, mouvements de main-d'œuvre, demande de travail |
| OCDE, Eurostat, OIT | Comparaisons internationales harmonisées |
| FMI, BCE et BRI | Modèles macroéconomiques, financement et politiques publiques |

La bonne nouvelle est que les statistiques publiques françaises contiennent déjà des ressources très pertinentes pour approfondir les questions de Shapiro.

L'Insee a notamment développé des comptes distribués permettant de réattribuer certains revenus et bénéfices aux différentes catégories de ménages et d'étudier les effets de la redistribution.

Les comptes américains du BEA sur les revenus et ceux de la Federal Reserve sur le patrimoine permettent également de dépasser le ménage représentatif unique d'Universal High Income.

Ces sources sont identifiées pour qualification. Elles ne sont pas toutes intégrées au pipeline Octave Lab, et leurs conditions d'accès, granularités, licences et possibilités de rapprochement restent à vérifier.

# 11. Cas d'application concrets de bout en bout

C'est ici que cette due diligence prend véritablement sa valeur.

## Cas A — Le paradoxe des juniors

**Décision étudiée :** une entreprise a-t-elle intérêt à réduire fortement ses recrutements de débutants ?

- Données : évolution des recrutements par métier et ancienneté (Dares, QWI, offres d'emploi et données d'entreprise).
- Premier ordre : automatisation des tâches juniors (identification des tâches réellement substituables).
- Deuxième ordre : diminution des recrutements et coûts de formation (effet sur les dépenses et la structure des équipes).
- Troisième ordre : modification du renouvellement des experts (moins de personnes acquièrent certaines compétences).
- Ordres suivants : rareté de l'expertise, évolution des salaires et nouvelles stratégies (externalisation, formation assistée par IA, automatisation supplémentaire ou réorganisation).

Il faut aussi explorer la trajectoire opposée : l'IA accélère suffisamment l'apprentissage pour réduire le temps nécessaire à l'acquisition de l'expertise.

Nous pourrions modéliser des cohortes de travailleurs et leurs transitions vers différents niveaux de compétence, en fonction du recrutement, de la formation et de l'expérience pratique.

**Valeur décisionnelle :** anticiper les pénuries de compétences, dimensionner les recrutements et identifier les investissements de formation nécessaires.

## Cas B — Les métiers du lien : refuge ou marché saturé ?

Une partie du travail intellectuel est automatisée. Des travailleurs se réorientent vers les soins, l'accompagnement, l'éducation et les services de proximité.

Le raisonnement classique consiste à supposer que ces activités absorberont les emplois perdus ailleurs.

Mais notre modèle examinerait simultanément les deux côtés du marché :

| Offre de travail | Demande de services |
|---|---|
| Reconversion professionnelle | Revenus disponibles |
| Qualifications nécessaires | Préférence humaine |
| Capacité de formation | Prix acceptable |
| Mobilité géographique | Financement public |
| Pression sur les salaires | Substituts technologiques |

Un secteur peut être difficile à automatiser tout en étant économiquement incapable d'absorber une arrivée massive de travailleurs.

À l'inverse, une demande précédemment rationnée peut devenir solvable grâce à des gains de productivité ailleurs dans l'économie.

**Valeur décisionnelle :** distinguer les métiers techniquement protégés des marchés véritablement porteurs.

## Cas C — Automatisation, baisse des prix et capture de valeur

Reprenons notre processus W002 de contrôle dimensionnel.

Le moteur G3.3 a déjà montré, dans ses simulations conditionnelles, qu'une automatisation peut libérer du travail et pourtant dégrader la rentabilité.

G3.4 devra prolonger cette investigation :

Réduction du coût de production → maintien des prix et augmentation des marges / diminution des prix et augmentation des ventes / réaction des concurrents / internalisation par les clients → modification de la structure du marché → demande de travail / concentration des entreprises / revenus des fournisseurs / pouvoir d'achat des clients.

Un gain de productivité peut être capté par l'entreprise, ses clients, ses fournisseurs technologiques, ses salariés ou les administrations publiques.

Nous devrons suivre ces transferts sans compter plusieurs fois la même valeur.

**Valeur décisionnelle :** déterminer non seulement quelles activités seront automatisées, mais quels acteurs conserveront un avantage économique après diffusion de la technologie.

## Cas D — La société post-travail : qui bénéficie des gains ?

Prenons une hypothèse fictive, uniquement pour démontrer le problème distributif.

Répartition d'une production économique supplémentaire : exemple simplifié, production initiale de 100, puis 120. Deux groupes de bénéficiaires, sans État ni fiscalité dans ce premier calcul.

- Revenus du travail après transformation S : curseur de 0 à 120, pas 5, initial 70.
- Part des revenus du capital revenant au groupe de travailleurs c : curseur de 0 à 100 %, pas 5, initial 20 %.
- Revenus du groupe de travailleurs = S + (120−S) × c/100 ; autres propriétaires du capital = 120 − revenus du groupe.
- Valeurs initiales : 80 et 40 ; réinitialiser à 70 et 20 %.

La production totale reste égale à 120. Sa distribution varie. Ce modèle ne détermine pas encore la consommation, les prix ou les effets macroéconomiques.

La croissance de la production ne garantit pas une augmentation des revenus pour tous. Mais une diminution des salaires n'implique pas non plus nécessairement une diminution du revenu disponible si les revenus patrimoniaux et les transferts évoluent.

C'est ce que nous devrons étudier avec de véritables comptes économiques équilibrés, en introduisant les différentes catégories de ménages, l'État, les entreprises, le financement, la consommation et les prix.

Le FMI constitue ici une référence plus solide pour les méthodes de simulation distributive et fiscale que le simulateur UHI lui-même.

# 12. La capacité prospective : Shapiro contre Octave Lab

Notre approche multi-ordres nous permet de dépasser la simple extrapolation technologique.

| Niveau | Observable aujourd'hui | Travail prospectif |
|---|---|---|
| Capacités des machines | Performances mesurées | Frontières technologiques futures |
| Adoption | Usages, investissements et enquêtes | Vitesse de diffusion conditionnelle |
| Tâches et processus | Mesures opérationnelles | Refonte, substitution et complémentarité |
| Entreprises | Coûts, effectifs et résultats | Investissement, rentabilité et restructuration |
| Marchés | Prix, volumes et concurrence | Élasticités, nouveaux usages, concentration |
| Secteurs | Production, échanges et emploi | Transmission par les chaînes de valeur |
| Macroéconomie | PIB, productivité et revenus | Trajectoires économiques cohérentes |
| Institutions | Fiscalité, propriété et protection sociale | Réactions politiques et scénarios alternatifs |

## Les trajectoires que nous devons maintenir ouvertes

- **Substitution massive** : diminution durable de la demande de travail, concentration du capital et nécessité éventuelle de nouveaux mécanismes distributifs.
- **Complémentarité dominante** : hausse de la productivité, création de tâches et augmentation de la demande de certaines compétences.
- **Rebond de la demande** : baisse des coûts, nouveaux marchés et compensation partielle ou totale des gains de travail.
- **Transition asymétrique** : secteurs numériques fortement transformés tandis que les activités physiques restent contraintes.
- **Concentration économique** : diffusion technologique inégale, disparition d'entreprises et captation des gains par certains acteurs.
- **Adoption freinée** : contraintes financières, organisationnelles, réglementaires, énergétiques ou matérielles.
- **Économie de propriété élargie** : accès accru aux revenus du capital et transformation de la composition des revenus.
- **Rupture institutionnelle** : modification importante de la fiscalité, des droits de propriété et des mécanismes de redistribution.

PROSPECT-001 prévoit déjà l'essentiel de ces familles. L'enrichissement consiste à renforcer leurs variables, leurs rétroactions, leurs conditions de réalisation et leurs signaux empiriques.

Aucun horizon, aucune probabilité et aucun niveau d'adoption ne doit être inventé pour donner artificiellement une apparence scientifique à ces trajectoires.

# 13. Opportunités de différenciation pour Octave Lab

Après cette première étude, je vois cinq propositions de valeur particulièrement fortes.

## 13.1. Un observatoire des emplois non créés

La majorité des débats publics se focalise sur les licenciements. Nous pourrions construire une analyse plus informative du ralentissement des créations d'emplois, des embauches et des remplacements de départs.

Les résultats devraient être présentés sous plusieurs références statistiques, avec historique des révisions, facteurs concurrents et niveaux de preuve.

Public cible : directions RH, institutions, investisseurs et analystes sectoriels.

## 13.2. Un observatoire du renouvellement de l'expertise

La question intéressante n'est pas uniquement de savoir combien de postes juniors disparaîtront.

C'est de comprendre si certaines entreprises seront encore capables de produire suffisamment d'experts lorsque les générations expérimentées quitteront le marché du travail, ou si les nouvelles technologies rendront cette formation beaucoup plus rapide.

Public cible : entreprises, écoles, branches professionnelles et organismes de formation.

## 13.3. Une cartographie de la capture des gains de productivité

Pour une activité donnée, identifier les bénéficiaires potentiels de la transformation : valeur économique créée par la transformation → salariés, actionnaires, clients, fournisseurs d'IA, fournisseurs d'infrastructures, administrations publiques.

Répartition à calculer selon les mécanismes de prix, de négociation, de concurrence et de fiscalité. Aucun pourcentage présupposé.

Nous pourrons également identifier les acteurs qui perdent de la valeur, les rentes qui disparaissent et celles qui apparaissent.

C'est probablement l'une des fonctionnalités les plus intéressantes pour des investisseurs et des dirigeants.

## 13.4. Un moteur d'analyse des marchés économiquement protégés

Il ne suffira pas de classer les métiers selon leur exposition à l'IA.

Il faudra mesurer conjointement :

- La substituabilité technique.
- La rentabilité de l'automatisation.
- Les contraintes physiques et réglementaires.
- La demande solvable.
- La concurrence future.
- La disposition des clients à payer pour un humain.

Cela permettrait d'éviter les raisonnements simplistes sur les « métiers d'avenir ».

## 13.5. Un laboratoire de politiques économiques cohérentes

Revenu universel, participation au capital, fonds souverain, baisse du temps de travail, fiscalité et dividendes citoyens pourraient être étudiés au sein d'un même cadre.

La condition impérative serait de conserver des budgets équilibrés ou des déficits explicitement financés, des comptes patrimoniaux cohérents et des scénarios de comportement des ménages et des entreprises.

L'objectif ne serait pas de défendre une politique particulière, mais de déterminer ses conditions de faisabilité et ses conséquences économiques.

# 14. Démonstrations publiques à forte valeur

Pour ton projet de développement public sur X, je privilégierais trois démonstrations successives.

**Démonstration 1 — Les millions d'emplois manquants**

Une analyse reproductible, interactive, permettant de changer le modèle contrefactuel, la fenêtre historique et le millésime des données.

Preuve recherchée : robustesse méthodologique et capacité à réfuter une affirmation spectaculaire.

**Démonstration 2 — De la tâche automatisée au marché transformé**

Une activité réelle, qualifiée par des professionnels, analysée depuis ses opérations jusqu'aux coûts, aux prix et aux conséquences sur l'emploi.

Preuve recherchée : capacité à articuler microéconomie, organisation et marché.

**Démonstration 3 — Qui empoche les gains de l'IA ?**

Comparaison de trajectoires avec forte concurrence, concentration, hausse des revenus du capital ou redistribution élargie.

Preuve recherchée : cohérence des transferts économiques et pertinence des scénarios multi-ordres.

Pour chacune, la valeur devra être évaluée par la reproductibilité des résultats, la capacité à distinguer des hypothèses concurrentes, les décisions qu'elle permet d'améliorer et l'intérêt effectif des utilisateurs professionnels.

Une belle visualisation ne constitue pas une preuve de supériorité scientifique. Une démonstration capable de changer une décision importante sur la base de résultats vérifiables, en revanche, commence à en constituer une.

# 15. Recommandations d'intégration

**Je recommande de conserver intégralement notre architecture actuelle et notre feuille de route principale.**

Cette due diligence ne justifie aucune refonte générale.

Elle justifie des enrichissements ciblés, que je propose de répartir comme suit.

| Priorité | Chantier | Enrichissement |
|---|---|---|
| P0 | Acquisition et qualification des données | Séries US, millésimes, flux d'emploi, audit des contrefactuels |
| P1 | G3.3 – Entreprises | Anticipations, recrutements, renouvellement des compétences, réaffectation |
| P1 | G3.4 – Marchés | Préférence humaine, demande induite, saturation, transmission des gains, rentes |
| P2 | G4 – Secteurs et macroéconomie | Distribution du capital, comptes des ménages, fiscalité, redistribution, rétroactions |
| P2 | G5 – Investigation et validation | Décomposition des anomalies, hypothèses rivales, tests causaux et signaux avancés |
| P3 | Recherche exploratoire | Mesures de production d'intelligence et trajectoires post-travail extrêmes |

### Ce que je déconseille formellement

Reprendre Universal High Income comme moteur macroéconomique, construire un score général de disparition des emplois, inventer un taux d'automatisation de l'économie, présupposer une déflation généralisée, imposer la disparition du salariat ou ajouter des composants politiques et blockchain sans valeur analytique démontrée.

Ces choix augmenteraient considérablement la complexité du projet sans renforcer nécessairement sa fiabilité.

# 16. État de la due diligence et limites

| Travail | État |
|---|---|
| Relecture de l'architecture et du registre Octave Lab | Réalisée sur les référentiels principaux consultés |
| Inventaire du corpus GitHub de Shapiro | Réalisé |
| Lecture intégrale des 103 rapports | Non réalisée |
| Identification des trois livres blancs | Réalisée |
| Vérification de leurs références chapitre par chapitre | Non réalisée |
| Récupération du rapport original du 24 novembre | Non obtenue |
| Contre-analyse historique indépendante | Réalisée |
| Modélisation multivariée et validation causale | Non réalisée |
| Inspection du moteur JSX d'UHI | Réalisée |
| Reconstitution indépendante de ses équations | Réalisée |
| Validation exhaustive de l'ensemble des simulateurs et publications | Non réalisée |
| Confrontation à la littérature économique | Première sélection substantielle réalisée |
| Matrice d'intégration et de priorisation | Présentée pour validation |

Je n'ai pas établi de critique académique indépendante portant directement sur l'estimation exacte de Shapiro du 24 novembre. Les études contradictoires mobilisées ici portent sur les mécanismes économiques et les effets observés de l'IA, et non sur la réplication de ce rapport précis.

Je n'ai modifié **aucun document maître, aucun registre, aucun module et aucun fichier GitHub** pendant cette due diligence.

L'analyse complète des rapports et la qualification des données constituent encore un travail de recherche important. Je préfère conserver cette limite explicite plutôt que prétendre avoir scientifiquement audité des milliers de pages.

# 17. Mon verdict stratégique

Je ne vois pas David Shapiro comme un concurrent direct d'Octave Lab à ce stade.

Je vois plutôt un auteur qui a constitué une vaste bibliothèque intellectuelle autour d'une hypothèse économique majeure, avec une capacité intéressante à vulgariser les conséquences distributives d'une automatisation avancée.

Son apport le plus précieux pour nous est **d'élargir l'investigation au-delà du marché du travail : propriété productive, origine des revenus, pouvoir économique, demande solvable et évolution des institutions**.

Notre avantage potentiel réside ailleurs : partir des transformations concrètes du travail, identifier leurs conditions d'apparition, calculer leurs conséquences économiques et confronter les trajectoires obtenues aux données.

Je retiendrais donc Shapiro comme source d'hypothèses, de concepts, de scénarios et d'indicateurs à challenger. Pas comme autorité scientifique déterminant les conclusions de notre système.

**L'ambition d'Octave Lab doit être de pouvoir démontrer dans quelles conditions Shapiro a raison, dans quelles conditions il a tort, et quels signaux permettent de distinguer ces futurs avant qu'ils ne deviennent évidents pour tout le monde.**
