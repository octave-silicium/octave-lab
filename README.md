# OCTAVE LAB · Observatoire IA & transformations du travail

**Plateforme de renseignement économique en construction publique.** Objectif : observer et expliquer les transformations du travail, des capacités technologiques aux conséquences économiques. Périmètre initial : France. Le dépôt contient des pipelines et résultats descriptifs vérifiés, pas encore un explorateur professionnel ni un moteur causal validé.

## État vérifié au 24 novembre 2026

| Composant | État / preuve |
|---|---|
| Indeed France | Collecte historique vérifiée, [snapshot et manifeste](snapshots/indeed-fr/2026-11/) |
| Dares mensuel, Urssaf NA88, Eurostat IA | Collectes et schémas audités, [manifeste multisource](audits/latest_multisource.json) |
| Urssaf DPAE et Insee | [Audit emploi/embauches](audits/latest_lot2.json), [audit sémantique](audits/latest_lot3.json) |
| Insee trimestriel | [Série normalisée](data/curated/insee_employment_sector_quarterly.csv), [manifeste](data/curated/insee_employment_manifest.json) |
| Gouvernance | [Contrôles provisoires](pipeline/data_governance.py), [droits](governance/source_rights.json), [ruptures](governance/series_events.json) |
| PILOT-001 | [Rapport descriptif NACE J](research/PILOT-001/rapport.md), [manifeste](research/PILOT-001/pilot_manifest.json), [code](pipeline/pilot_ict.py) |
| Moteur métier–tâche–action–processus | [METH-003](docs/METH-003.md), spécification validée, non implémentée |
| Socle sémantique | [S1 v0.2.0](docs/SEMANTIC-V2.md) : 183 491 cellules archivées ; [v0.3.0](docs/SEMANTIC-V3.md) : 58 512 cellules transitoires, 118 tests du dépôt réussis ; [v0.4](docs/SEMANTIC-V4.md) : 9 jeux interrogeables en interne, 130 tests réussis ; stockage de production et qualification ouverts |
| Explorateur multisource | [G1 v0.3](docs/G1-EXPLORER.md) moteur local vérifié, 148 tests, chargement sélectif et vues enregistrées ; navigateur à confirmer ; [UX-001](docs/UX-001.md) standard de design, ergonomie et recette ; [BENCH-001](docs/BENCH-001.md) benchmark transversal |

79 sources/programmes candidats recensés, non 79 bases intégrées. PILOT-001 mobilise deux lignées principales (Urssaf et Eurostat), sans inférence causale. Les comparaisons DPAE touchées par les anomalies 2025 restent bloquées ; le périmètre des technologies IA Eurostat change en 2025. Les sources Dares MMO et les droits commerciaux concernés nécessitent encore qualification.

## Architecture et feuille de route

Six niveaux reliés : capacités IA, tâches/actions, métiers, entreprises/processus, marchés/chaînes de valeur, macroéconomie. Le [moteur de décomposition du travail](docs/METH-003.md) est transversal. Prochaine étape technique : explorateur interne G1 selon [UX-001](docs/UX-001.md), en maintenant ouverts les gates résiduels [S1](docs/SEMANTIC-V4.md). Voir [feuille de route et chantiers ouverts](docs/ROADMAP.md).

## Exécution GitHub Actions

- Collecte Indeed France : [workflow](.github/workflows/collect-public-sector.yml), déclenchement manuel ou hebdomadaire. Consulter `outputs/live/manifest.json` dans les artefacts ; `PASS_DESCRIPTIVE_ONLY` valide uniquement les séries descriptives. Le premier run réussi du mois archive les originaux et SHA256 dans `snapshots/indeed-fr/YYYY-MM/`.
- Audit multisource : [preuves](audits/latest_multisource.json). Emploi et embauches : [workflow](.github/workflows/audit-lot2.yml).
- Insee : [workflow mensuel](.github/workflows/collect-insee.yml).
- Pilote ICT : [workflow](.github/workflows/pilot-ict.yml), [exécution réussie](https://github.com/octave-silicium/octave-lab/actions/runs/45332943616).
- Pour les workflows d'archivage, les permissions d'écriture nécessaires sont limitées aux opérations prévues et dépendent des paramètres du dépôt.

## Exécution locale du collecteur initial

```bash
python -m unittest discover -s tests -v
python pipeline/run.py --only-open
```

Python 3.11+ ; accès réseau nécessaire pour les collectes. Les commandes ci-dessus ne constituent pas un test de toute la plateforme cible.

## Périmètre et garde-fous

- Les « secteurs » Indeed sont des familles professionnelles, pas des secteurs économiques NAF/NACE. Les annonces ne sont ni des embauches effectives ni des emplois supprimés.
- Comparer des trimestres complets, conserver les versions des sources, vérifier ruptures, unités, populations et nomenclatures. Pas de correspondance métier/secteur automatique.
- Distinguer exposition, capacité testée, adoption observée, substitution et impact estimé. Pas de causalité sans stratégie d'identification adaptée.
- Vérifier les licences jeu par jeu ; pas de diffusion de données brutes Urssaf ODbL ici, ni d'autorisation présumée d'un produit commercial dérivé. Aucun secret, donnée personnelle ou dossier client dans le dépôt public.
- Données absentes ou comparabilité insuffisante : afficher le blocage, jamais inventer un résultat.

## Sources et méthode

[Indeed Hiring Lab](https://github.com/hiring-lab/job_postings_tracker) · [FAQ Indeed](https://hiringlab.indeed.com/indeed-data-faq-2/) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · [Urssaf Open Data](https://open.urssaf.fr/) · [Dares](https://dares.travail-emploi.gouv.fr/) · [Insee](https://www.insee.fr/) · [Eurostat](https://ec.europa.eu/eurostat/) · [Méthodologie initiale](docs/METHODOLOGIE.md)

Projet **Octave Silicium**. Les observations factuelles, hypothèses et opinions sont distinguées.
