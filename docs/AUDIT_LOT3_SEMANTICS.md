# OCTAVE LAB · Lot 3 : qualification sémantique et surveillance des révisions

**Statut : procédure de preuve, pas publication d'une analyse économique ni autorisation juridique.**

## Objectifs vérifiables

1. Télécharger le classeur officiel Insee « Emploi salarié par secteur », dont les données sont annoncées en milliers, CVS et de fin de trimestre, puis inspecter réellement les cellules plutôt que se contenter de l'enveloppe ZIP.
2. Identifier l'étendue des historiques DPAE Urssaf (mensuels et NA38 trimestriels), surveiller les six mois avril-septembre 2025 et les deux trimestres Q2-Q3 2025 explicitement signalés par l'éditeur. Conserver uniquement des hachages de périodes normalisées, pas les lignes originales.
3. Rechercher un lien XLSX direct pour les mouvements de main-d'œuvre Dares **uniquement sur la page officielle et sans contourner une protection anti-robot**. Tant qu'un lien binaire officiel validé n'est pas obtenu, le gate reste bloqué.
4. Comparer les empreintes de chaque période DPAE entre collectes. Une version modifiée crée un indicateur de révision, sans présumer de sa justesse et sans « réparer » les données.

## Limites

- Les séries Insee d'estimations d'emploi combinent des sources Urssaf, Dares et Insee : la provenance statistique n'est pas indépendante des données sociales administratives.
- Le solde des entrées et sorties Dares MMO ne peut pas être présenté comme la différence d'emploi Insee.
- Les DPAE restent des **déclarations préalables**, pas des embauches réalisées vérifiées.
- L'ODbL reste applicable aux données Urssaf. Nous ne publions ni CSV brut, ni base reconstruite, ni données économiquement fusionnées.
- La première collecte de hachages constitue la *première vintage disponible chez nous*. Sans vintage d'avant les corrections de 2026, impossible de prouver a posteriori que les anomalies signalées en 2025 ont toutes été corrigées.
- Une série Insee typée numérique mais sans codebook et correspondance des unités n'est pas encore une série publiée utilisable dans l'explorateur.

## Barèmes

- `XLSX_SEMANTIC_METADATA_PARSED` : cellules et en-têtes réellement lus, mais unités/métiers et comparabilité non validés.
- `DPAE_PERIODS_AND_PROVENANCE_VALIDATED_NOT_ECONOMICALLY_CLEARED` : périodes et empreintes lues ; prudence 2025 maintenue.
- `PENDING_EXACT_OFFICIAL_XLSX_LINK` : lien exact non identifié, pas de collecte MMO.
- `BLOCKED_OFFICIAL_SITE_ANTIBOT` : protection du site rencontrée, aucun contournement.
- `BLOCKED` : échec du téléchargement, résultat non exploitable.

## Références

- Insee : https://www.insee.fr/fr/statistiques/2496914
- Urssaf : https://open.urssaf.fr/explore/dataset/dpae-mensuelles-france-entiere/ et https://open.urssaf.fr/explore/dataset/dpae-france-entiere-x-na38/
- Dares : https://dares.travail-emploi.gouv.fr/donnees/les-mouvements-de-main-doeuvre
- Historique Dares vs Insee : https://dares.travail-emploi.gouv.fr/enquete-source/les-mouvements-de-main-doeuvre
- Registres de ruptures et droits : `governance/series_events.json`, `governance/source_rights.json`

## Condition de passage

Toute conclusion chiffrée au niveau d'un secteur requiert : **codebook Insee identifié, périodes homogènes, licence qualifiée, jointure construite et auditée, révision des anomalies DPAE, et comparaison de données conceptuellement équivalentes**. L'exécution automatique seule ne franchit pas ce gate.
