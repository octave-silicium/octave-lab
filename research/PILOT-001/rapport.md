# OCTAVE LAB · PILOT-001 | Information et communication (NACE J)

**Statut : descriptif source par source. AUCUNE inférence causale ni jointure économique autorisée.**  
**Collecte UTC : 2026-11-24T05:23:22.263618+00:00**

## Question
Que disent trois indicateurs différents sur les entreprises du secteur information-communication français, sans confondre emploi, déclarations d'embauche et usage déclaré de l'IA ?

## 1 · Effectifs des employeurs (Urssaf, NA88 divisions 58-63)
- T4 2024 : **944 659** salariés CVS.
- T4 2025 : **924 452** salariés CVS.
- Variation annuelle descriptive : **-2,14 %**.
- T2 2026 vs T2 2025 : **-1,80 %**.
- Définition : secteur privé couvert par l'Urssaf ; activités d'employeurs NACE 58 à 63, non métiers du numérique. Première collecte, révisions à surveiller.

## 2 · Déclarations préalables à l'embauche (Urssaf, NA38 JA+JB+JC)
- T4 2023 : **73 972** déclarations CVS de CDI et CDD de plus d'un mois.
- T4 2024 : **63 568** déclarations CVS de même catégorie.
- Variation descriptive : **-14,06 %**.
- Les mois et trimestres 2025 restent exclus du calcul, en raison des anomalies déclaratives signalées par le producteur.
- Ces déclarations ne sont ni des embauches effectivement réalisées ni un solde net d'emploi.

## 3 · Adoption déclarée de l'IA (Eurostat, isoc_eb_ain2)
- 2023 : **29,56 %** des entreprises concernées (flag Eurostat b : rupture de série).
- 2024 : **41,76 %**.
- 2025 : **58,98 %**.
- **Rectificatif du 24/11/2026 : variation 2023-2024 non validée, revue méthodologique nécessaire.** Le flag b est confirmé dans le même fichier source (SHA256 identique) par le [run S1 v0.4](https://github.com/octave-silicium/octave-lab/actions/runs/45339526530). La différence arithmétique ne prouve pas une évolution comparable. **Pas de taux de croissance 2024-2025 publié** : le panier de technologies suivi s’élargit en 2025 (génération d’images, vidéos et sons).
- Champ : entreprises de 10 personnes occupées ou plus, section NACE J, France ; résultat d'enquête, non mesure de tâches remplacées.

Note méthodologique de l’enquête Eurostat : https://ec.europa.eu/eurostat/documents/3859598/22759373/KS-01-25-065-EN-N.pdf .

## 4 · Confrontation méthodologique
Ces trois indicateurs NE FORMENT PAS une analyse causale. L'Urssaf fournit une famille administrative liée de mesures d'effectifs et de déclarations ; Eurostat fournit une enquête d'entreprises. Une hausse d'adoption de l'IA ne démontre ni suppression d'emploi ni hausse de productivité. Le secteur J mélange services informatiques, édition, médias et télécommunications.

**Inférence légitime :** décrire les mouvements propres à chaque indicateur et vérifier si leurs trajectoires méritent enquête approfondie.

**Inférence interdite :** attribuer leurs divergences ou évolutions à l'IA, ou calculer un nombre de postes éliminés par l'IA à partir de ces séries.

## 5 · Provenance et réutilisation
- Source Urssaf Caisse nationale, « Effectifs salariés et masse salariale par secteur NA88 », licence **ODbL 1.0** : https://open.urssaf.fr/api/explore/v2.1/catalog/datasets/effectifs-salaries-et-masse-salariale-du-secteur-prive-france-entiere-x-na88/exports/csv?use_labels=false
- Source Urssaf Caisse nationale, « DPAE France entière x secteur NA38 », licence **ODbL 1.0** : https://open.urssaf.fr/api/explore/v2.1/catalog/datasets/dpae-france-entiere-x-na38/exports/csv?use_labels=false
- Licence ODbL : https://opendatacommons.org/licenses/odbl/1-0/ . Cette étude est une sortie illustrative compacte ; les bases dérivées et réutilisations commerciales doivent faire l'objet d'une validation juridique.
- Source Eurostat, « Artificial intelligence by NACE Rev.2 activity », code **isoc_eb_ain2** : https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/isoc_eb_ain2?geo=FR&lang=EN&sinceTimePeriod=2022
- Historique et empreintes SHA256 : `research/PILOT-001/pilot_manifest.json`.
- Méthode reproductible : `pipeline/pilot_ict.py`.

**Limites :** même groupe administratif pour les deux séries Urssaf ; pas d'effet causal ni de correspondance métier/branche, et nécessité de contrôler les révisions de séries et leur comparabilité.
