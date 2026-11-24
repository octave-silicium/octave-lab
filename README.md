# OCTAVE LAB · Observatoire IA & transformations du travail

**Prototype de pipeline de données économiques français, en construction publique.** Ce dépôt contient un collecteur de séries historiques d'annonces d'emploi Indeed, des validations automatiques et un calcul descriptif par famille professionnelle. Il **ne démontre pas** l'effet causal de l'IA sur l'emploi.

## Statut

- Source primaire : Indeed Hiring Lab, France, indicateurs quotidiens CVS depuis février 2020, licence CC BY 4.0.
- Sorties : archive des octets originaux avec empreintes SHA256 et métadonnées, médianes de trimestres complets, variations sur un an par famille de métiers, manifeste d'exécution.
- La collecte du fichier source n'est déclarée réussie **que si** GitHub Actions produit un manifeste `PASS_DESCRIPTIVE_ONLY` et les fichiers téléchargés sont présents.
- **Données non disponibles** = échec documenté et **aucun graphique sectoriel présenté comme réel**.

## Exécution GitHub Actions

Après ajout de ce code au dépôt :

1. Dans **Settings → Actions → General**, autoriser les actions nécessaires et, pour l'archivage automatique, choisir les droits du jeton de workflow **Read and write permissions** (si GitHub le permet). Les paramètres peuvent différer selon les politiques de compte.
2. Ouvrir **Actions → Collecte Indeed France** et cliquer sur **Run workflow**. Le déclencheur manuel et le déclencheur hebdomadaire sont dans `.github/workflows/collect-public-sector.yml`.
3. Consulter `outputs/live/manifest.json` dans les artefacts du run. La sortie `PASS_DESCRIPTIVE_ONLY` indique seulement une validation des séries descriptives, pas une validation de conclusions économiques sur l'IA.
4. Le premier run réussi d'un mois archive les fichiers originaux Indeed avec manifeste SHA256 sous `snapshots/indeed-fr/YYYY-MM/` et les versions restent dans l'historique Git. Les autres runs du mois produisent uniquement leurs artefacts temporaires.

## Exécution locale

```bash
python -m unittest discover -s tests -v
python pipeline/run.py --only-open
```

Python 3.11+ standard library. Besoin d'un accès réseau à `raw.githubusercontent.com`.

## Périmètre et garde-fous

- Les « secteurs » d'Indeed désignent des **familles professionnelles**, pas les secteurs économiques de l'entreprise.
- Un recul de l'indice d'annonces ne prouve ni des suppressions de postes, ni une causalité liée à l'IA.
- Les séries peuvent être révisées par Indeed. Le pipeline conserve les originaux par vintage.
- Les comparaisons annuelles exigent deux trimestres **complets** ; aucun trimestre en cours ou incomplet n'est comparé.
- `pipeline/sources.json` contient aussi des sources candidates (Dares, Insee) désactivées pour toute redistribution avant revue des droits et des schémas.
- Aucun dossier client, clé API ou donnée personnelle ne doit être ajouté à ce dépôt public.

## Sources et méthode

- [Indeed Hiring Lab : source et schéma](https://github.com/hiring-lab/job_postings_tracker)
- [Indeed Hiring Lab : méthodologie](https://hiringlab.indeed.com/indeed-data-faq-2/)
- [Conditions de la licence CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- [Conditions de reproductibilité](docs/METHODOLOGIE.md)

Projet éditorial et économique **Octave Silicium**. Les analyses factuelles, hypothèses causales et opinions de l'auteur sont volontairement séparées.
