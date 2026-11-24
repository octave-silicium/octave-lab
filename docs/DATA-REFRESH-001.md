# DATA-REFRESH-001 — Acquisition et actualisation
24/11/2026 — exigence utilisateur : maximiser la collecte et l'actualisation automatiques, idéalement toutes les sources, dans les conditions d'accès et de réutilisation autorisées. Le présent registre est une règle de conception, pas une preuve de fonctionnement périodique.
## Fichiers manuels prioritaires
- ESCO : https://esco.ec.europa.eu/fr/use-esco/download — ESCO dataset v1.2.1, Classification, fr, CSV, paquet ZIP original. Facultatifs : paquet en, fichier delta v1.2.1 indépendant de la langue, CSV. Lien par courriel après formulaire officiel. Une API web répond ; tester couverture, pagination, version effective, limites et concordance avec le ZIP avant de l'adopter pour les révisions. Voir https://esco.ec.europa.eu/en/use-esco/use-esco-services-api/esco-web-service-api.
- Dares MMO : https://dares.travail-emploi.gouv.fr/donnees/les-mouvements-de-main-doeuvre — Données trimestrielles - Mouvements de main-d'œuvre 2e trimestre 2026 (XLSX). Accès automatisé bloqué par vérification humaine dans les essais précédents. Rechercher canal officiel alternatif ; ne pas contourner.
- Dares FAP 2021, nouveaux candidats de rapprochement (page protégée lors de la vérification) : https://dares.travail-emploi.gouv.fr/donnees/la-nomenclature-des-familles-professionnelles-2021 — Arborescence FAP-2021, pour programme (CSV), Table de passage Rome vers FAP-2021, pour programme (CSV), Table de passage PCS-2020 vers FAP-2021 (XLSX), Table de passage Libellés PCS-2020 vers FAP-2021, pour programme (CSV), Matrices de bascule FAP-2009, PCS-2003 vers FAP-2021 (XLSX). Vérifier droits et millésimes des correspondances ; ne pas présumer compatibilité ROME 4.0. 
- ROME complet CSV et JSON : NE PAS demander à l'utilisateur, accès automatique réussi le 24/11/2026, parsing restant. O*NET et neuf jeux de G1 : accès automatisable démontré dans le périmètre historique, ne pas demander de copies.
## Registre de collecte à étendre aux 79 candidats de DATA-002
| Source | Accès constaté | Rafraîchissement cible (non activé par cette spécification) |
|---|---|---|
| Indeed France | Archives vérifiées | Vérification quotidienne du fichier officiel |
| Dares/France Travail offres | Archive officielle vérifiée | Vérification hebdomadaire, publication mensuelle |
| Insee emploi | Collecte vérifiée | Hebdomadaire, publication trimestrielle |
| Urssaf, 3 jeux | Collecte live vérifiée | Hebdomadaire, selon cadence de publication |
| Eurostat, 2 jeux IA | Collecte live vérifiée | Hebdomadaire, selon révision/publication |
| O*NET | 4 CSV versionnés collectés | Détection des releases hebdomadaire |
| ROME | 2 ZIP officiels reçus, non parsés | Détection de release hebdomadaire, récupération des exports |
| ESCO | Profil API, archive complète non acquise | Détection de version hebdomadaire, API complète à qualifier, manuel si nécessaire |
| Dares MMO et FAP | Accès protégé | Canal alternatif officiel à qualifier ; file d'attente manuelle |
| EURES tables France | Références officielles ESCO v1.0.9/v1.1 | Collecte à tester, version à qualifier ; https://esco.ec.europa.eu/en/use-esco/eures-countries-mapping-tables |
## Contrat de rafraîchissement
Par source : URL officielle, version/dernière publication, fréquence attendue de publication vs fréquence de vérification, droits, mode API/fichier/manuel, date dernier succès/essai, date des données, empreinte, schéma, couverture, flags, responsable et prochaine vérification. Priorité API officielle ou flux, fichier officiel stable, métadonnées/catalogues officiels ; si accès réservé, autorisation et secrets hors dépôt ; si CAPTCHA, action humaine ou canal autorisé. Pas d'automatisation de contournement. Détection par ETag/Last-Modified si fiables, sinon SHA256 du contenu et contrôle version/schéma ; ZIP peut changer de métadonnées sans changement de données. Vérifier avant promotion atomique, conserver vintage précédent autorisé, isoler fichiers invalides, distinguer données révisées et nouvelles, refus de substitution silencieuse. Journal, quotas/backoff, alertes de fraîcheur/échec, reprise manuelle et déduplication. Droits et confidentialité conditionnent coffre privé et diffusion ; jamais de commit des données restreintes. Indicateur : part des sources actives réellement rafraîchissables sans intervention, par importance et non nombre de candidats, échecs et retard ; aucun taux inventé. Les workflows existants ne prouvent pas une maintenance complète récurrente. Prochaine étape : implémenter un registre exécutable, planificateur et tests de non-régression, suivi de disponibilité et alertes.

24/11/2026 : archives ESCO FR/EN/delta, Dares MMO trimestriel/annuel + note et lot FAP reçus de l'utilisateur et importés localement dans leur périmètre vérifié (G2-LOCAL-INTAKE). Aucun téléchargement manuel indispensable restant pour ce lot. Prochaine priorité : automatisation autorisée et validation de révision ; aucun planificateur nouveau déclaré actif.

## Implémentation v0.1
[Data Observatory](DATA-OBSERVATORY.md) : registre 14 entrées, workflow quotidien configuré et recette réelle réalisée ; supervision de métadonnées, pas de promotion automatique. Insee échec réseau initial ; correction et recette complémentaire. Les rapports et résultats des runs sont référencés dans la documentation.
