# OCTAVE LAB · Gouvernance des licences et ruptures statistiques

**Version de protocole : 24/11/2026. Statut : garde-fous techniques installés ; validation juridique B2B et homogénéisation des données NON réalisées.**

## 1. ODbL Urssaf

La source officielle indique une réutilisation commerciale possible, sous les conditions ODbL 1.0 : attribution, mentions de licence, et partage à l'identique d'une base de données dérivée utilisée publiquement. Les clauses 4.4 à 4.6 peuvent imposer la mise à disposition de la base dérivée ou des modifications nécessaires pour la reconstruire. Les créations produites (graphiques, textes) et les bases collectives ont un traitement distinct selon la licence.

- Conditions du fournisseur : https://open.urssaf.fr/terms/terms-and-conditions/
- Texte de la licence : https://opendatacommons.org/licenses/odbl/1-0/
- Dataset : https://open.urssaf.fr/explore/dataset/effectifs-salaries-et-masse-salariale-du-secteur-prive-france-entiere-x-na88/
- Registre : governance/source_rights.json
- Aucun produit OCTAVE LAB fondé sur une base dérivée Urssaf n'est juridiquement validé à ce stade.
- Interne : traitement autorisé sous conditions de licence, avec contrôle des accès, traçabilité et origine.
- Public : notice source/licence visible dans chaque graphique ou rapport. Les exports de bases et analyses construites depuis une base adaptée sont bloqués jusqu'à une revue juridique spécifique et un plan de mise à disposition conforme.

**Exemple d'attribution (à adapter à la sortie réelle)** : « Source : Urssaf Caisse nationale, Effectifs salariés et masse salariale trimestriels du secteur privé par secteur NA88, millésime consulté le [date], licence ODbL 1.0 [lien]. Transformations : OCTAVE LAB [lien méthode]. »

### Décision juridique nécessaire avant un SaaS payant
Faire statuer un juriste spécialisé droit des bases de données sur la structure exacte : chaque table, jointure, export, API, graphique et rapport, avec scripts de transformation, description du partage et licences des données ajoutées. La simple séparation physique des tables n'efface pas les obligations ODbL. Une demande d'interprétation des conditions peut être adressée à la PRADA Urssaf mentionnée dans les CGU ; cela ne remplace pas la revue juridique contractuelle.

## 2. Ruptures et révisions

Les événements sont dans governance/series_events.json (date, champs atteints, source primaire, décision, statut et condition de réouverture).

- Effectifs salariés Urssaf : publication T1 2023, apprentis inclus désormais dans les effectifs salariés. Une variation de 2022Q4 à 2023Q1 est BLOQUÉE, faute de série à définition homogène / pont validé. La masse salariale est volontairement hors de ce blocage automatique tant que son champ n'a pas été audité.
- Compilation DSN finalisée T1 2021 : changement méthodologique à expertiser, pas coefficient de correction automatique.
- DPAE : modification de formulaire fin mars 2025, erreurs déclaratives et période avril-septembre 2025 officiellement signalée ; publication reprise en octobre 2026. Les versions corrigées doivent être comparées à la source originelle pour déverrouiller l'usage public des mois concernés.
- NAF : basculement prévu vers NAF 2025 pour codes APE au 01/01/2027. Contrôle par millésime et tables officielles ; jointure « métier Indeed = activité NAF » interdite.

Sources :
- https://open.urssaf.fr/explore/dataset/effectifs-salaries-et-masse-salariale-du-secteur-prive-france-entiere-x-na88/custom/
- https://open.urssaf.fr/explore/dataset/dpae-mensuelles-france-entiere/export/
- https://www.insee.fr/fr/information/8181066

### Protocole de validation statistique
1. Archiver les originaux, SHA256, date de collecte, date de référence et millésime de publication ; historiser les révisions.
2. Inspecter couverture, valeurs manquantes, doublons, colonnes, unités, champs inclus et brut/CVS.
3. Appliquer les ruptures déclarées par producteur et les changements de nomenclatures ; afficher leur position sur les graphiques.
4. Stopper toute comparaison qui traverse une rupture de définition ou une période de qualité incertaine. Présenter des segments homogènes tant qu'un rapprochement documenté n'est pas possible.
5. Si le producteur fournit des séries rétro-projetées ou un chevauchement, quantifier l'écart sur un échantillon, documenter le modèle de correction et conduire une analyse de sensibilité ; pas de coefficient automatique.
6. Comparer un indicateur indépendant compatible pour les conclusions économiques, en distinguant source indépendante et même origine administrative.
7. Seul un réviseur habilité peut approuver un contournement, avec preuves et tests dans Git. Aucune IA n'invente les coefficients ou la causalité.

## 3. Codes et limites du garde-fou

- pipeline/data_governance.py : décisions conservative de licence et comparabilité.
- tests/test_data_governance.py : tests automatisés de blocages et d'autorisation conditionnelle.
- Un code « ALLOW_WITH_CAVEATS » ne certifie pas la qualité statistique ou l'absence de rupture inconnue.
- Un code « CONDITIONAL_PUBLIC_PRODUCED_WORK » ne constitue pas une autorisation légale sur un produit réel.
- Le contrôle des ruptures ne porte actuellement que sur des séries explicitement inscrites ; l'inconnue est BLOQUÉE par défaut.
