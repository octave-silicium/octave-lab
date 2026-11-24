# OCTAVE LAB | AUDIT-002 : emploi, déclarations d'embauche, mouvements de contrats

**Date : 24 novembre 2026. Statut : protocole d'audit technique exécuté, aucune réconciliation économique validée.**

## Verdict de l'exécution initiale

Source primaire de vérification : https://github.com/octave-silicium/octave-lab/blob/main/audits/latest_lot2.json  
Exécution : https://github.com/octave-silicium/octave-lab/actions/runs/45327898940

1. **Urssaf DPAE par secteur NA38** : téléchargement CSV original réussi ; 1 945 716 octets, 11 877 lignes, 10 colonnes. SHA256 `42cd99124b1ef5f0a39afc481c42e70d5adc0fbfb535a7cb53f2653dfd41f549`. Champs : activité (NA38), durée/nature de contrat, année, trimestre, date, dpae_brut, dpae_cvs. Attribution Urssaf, ODbL. Aucune donnée brute redistribuée.
2. **Urssaf DPAE mensuelles nationales** : téléchargement CSV original réussi ; 46 316 octets, 642 lignes, 7 colonnes. SHA256 `e0789b561ae47d5ce444e8f87f84fd2d076a3c460fba4a54f1cb6de7027a4a7b`. Répartition contrat, brut/CVS, mois/année. Attribution Urssaf, ODbL. Aucune donnée brute redistribuée.
3. **Insee emploi salarié sectoriel** : fichier XLSX officiel récupéré depuis https://www.insee.fr/fr/statistiques/fichier/2496914/econ-gen-empl-salarie-trim.xlsx ; 51 977 octets, ZIP valide et classeur Excel avec une feuille « Données ». SHA256 `a13c18d4fd17ff7684db8adb56e92642b31a345af529b46f68e8d0046e159a48`. **Contenu numérique, dictionnaire, unités et séries élémentaires NON encore vérifiés.** Source : https://www.insee.fr/fr/statistiques/2496914.
4. **Dares MMO** : fiche officielle et disponibilité annoncée d'un XLSX T2 2026 vérifiées ; URL de fichier directe stable et droits de réutilisation exacts non certifiés. **Fichier non téléchargé dans notre pipeline**, aucune valeur recopiée ni série improvisée. Source : https://dares.travail-emploi.gouv.fr/donnees/les-mouvements-de-main-doeuvre.

Résultat initial : 3 fichiers téléchargés et inspectés, 1 lien de fichier à qualifier, **zéro rapprochement économique validé**. Les deux fichiers Urssaf DPAE proviennent du même système administratif et ne constituent pas deux preuves indépendantes.

## Pourquoi ces indicateurs ne sont pas interchangeables

- **DPAE Urssaf** : déclarations préalables d'embauche, y compris déclarations qui ne débouchent pas nécessairement sur une entrée effective en emploi. Ne pas interpréter comme embauches réalisées ni comme variation du stock d'emplois.
- **MMO Dares** : mouvements de contrats comptés à date de mouvement dans le champ privé métropolitain hors agriculture, intérim et particuliers employeurs. Contrats multiples comptés ; entrées − sorties ≠ changement automatique du stock Insee.
- **Estimations Insee** : stocks salariés corrigés de la multiactivité, champ géographique différent, instant de comptage différent. Estimations révisables, données de trimestre en fin de période.
- **Nomenclature** : NA38 désigne les activités économiques des établissements, pas les métiers Indeed ou les catégories ROME.

## Contrôles incontournables à venir

| Gate | Critère | État |
|---|---|---|
| G1 Accès | Source originale reçue, format et empreinte valides | 3/4 PASS |
| G2 Dictionnaire | Variables, populations, unité et filtres expliqués avec exemples | PARTIEL |
| G3 Temporalité | Dates réelles, ruptures, vintage, fréquence, dernière observation | NON VALIDÉ |
| G4 Licence | Conformité commercialisation/redistribution pour chaque usage | ODbL CONDITIONNELLE ; Insee/MMO à vérifier |
| G5 Concordance | Même activité, population, géographie, période et couverture | NON VALIDÉ |
| G6 Triangulation | Contradictions, références et dépendance des producteurs | NON VALIDÉ |
| G7 Économétrie | Hypothèses alternatives, identification et stabilité | NON COMMENCÉ |

## Prochain protocole opérationnel

1. Traiter et historiser les **révisions Urssaf DPAE 2025**, avec contrôle des séries plus récentes avant toute conclusion CDI/CDD ou plus d'un mois.
2. Extraire la structure et les métadonnées du XLSX Insee, identifier l'intervalle réellement disponible et comparer sa documentation avec le fichier.
3. Localiser la ressource binaire MMO à partir du portail Dares sans contourner les mesures d'accès, puis auditer les révisions MMO 2023.
4. Construire un tableau de compatibilité indicateur-par-indicateur avant le moindre graphique fusionné ; aucune équivalence entre métiers Indeed et codes NA38.

**Verdict :** la couche de collecte et les premiers contrôles sont fonctionnels ; la validité des inférences et la publication de croisements ne sont pas acquises.
