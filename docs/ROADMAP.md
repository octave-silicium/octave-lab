# OCTAVE LAB — État et feuille de route
Référence publique au 24 novembre 2026. Le statut d'une décision ne vaut pas preuve de fonctionnement.

## État de départ
- G0 : prototype et pipeline descriptif existants. Indeed France : collecte historique vérifiée ; Dares, Urssaf et Eurostat : audits techniques réalisés. Insee : normalisation de séries trimestrielles.
- 79 entrées candidates recensées ; ni 79 bases intégrées, ni 79 lignées indépendantes.
- [PILOT-001](../research/PILOT-001/rapport.md) : observations descriptives sur NACE J ; deux lignées principales (Urssaf et Eurostat). Pas de preuve causale.
- [Gouvernance](../pipeline/data_governance.py) : contrôles provisoires de droits et ruptures ; leur intégration systématique aux futures sorties reste à faire.
- METH-003 : décision validée, moteur non implémenté.

## Ordre de développement validé
| Jalon | Résultat attendu | Statut initial |
|---|---|---|
| S0 | Synchronisation README, spécification METH-003, état et feuille de route | VÉRIFIÉ |
| S1 / G1 | Contrats sémantiques communs : mesure, unité, population, dimensions et référentiels versionnés, période/vintage, provenance, licence, comparabilité, preuve ; préparer G-M0 | PARTIELLEMENT VÉRIFIÉ : [S1 v0.4](SEMANTIC-V4.md), 130 tests, neuf jeux interrogeables ; coffre de production, droits, qualification géographique et comparabilité restent ouverts |
| S2 / G1 | Explorateur multisource : recherche, filtres de couverture, historiques, comparaison conditionnelle, provenance et exports autorisés ; exigences [UX-001](UX-001.md), gates UX-G0 à UX-G4 | Validé, non implémenté ; conception premium et critères de recette inscrits |
| S3 / G2 | Qualification ROME/ESCO/O*NET, ontologie G-M0 et petit pilote G-M1 ; processus réel, vérification humaine | Validé, non implémenté |
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
