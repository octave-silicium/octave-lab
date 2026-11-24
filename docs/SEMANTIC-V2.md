# S1 — Incrément v0.2
Statut : code et workflow proposés à exécution CI ; ne pas déclarer l'audit réussi sans logs.

## V0.1 : validation intégrale
[Run 45337895029](https://github.com/octave-silicium/octave-lab/actions/runs/45337895029), job 138254215736 : 19/19 tests, 509 observations (500 Insee, 4 Urssaf emploi, 2 DPAE, 3 Eurostat), artefact semantic-audit 14894339520. Niveau descriptif seulement.

## Extension v0.2
- Contrat de cellule versionné, dimensions natives typées et ordonnées, provenance, valeurs manquantes explicites (aucune imputation), identifiants de travail PROPOSED uniquement ; pas de crosswalk.
- Indeed : deux archives nationales et familles professionnelles, sélection total postings, quotidien CVS, vérification des octets SHA256, taille, lignes, géographie. Ni compte d'emplois ni secteur NAF.
- Dares : archive GZIP d'origine, SHA256 sur octets décompressés, taille, schéma, 96 252 lignes attendues. Géocodes/labels, type d'offre, durée/type d'emploi, qualification, type de données conservés littéralement ; aucune somme de catégories chevauchantes. Le fichier mensuel brut représente des nombres arrondis à la centaine, pas une mesure de toutes les offres ni d'embauches effectives. La rupture des offres satisfaites en juillet 2013 impose un blocage conservateur des comparaisons traversant cette date. Les autres comparaisons restent à revoir.
- Les quatre séries v0.1 sont enveloppées sans modifier leur validation, Eurostat GE10 conservé. La dimension taille d'entreprise ne représente pas encore les autres classes.
- Licences documentées : Indeed CC BY 4.0 (manifeste), Dares LO 2.0 ([fiche exacte](https://www.data.gouv.fr/datasets/offres-collectees-et-satisfaites-par-france-travail-brutes-mensuelles)), aucune autorisation automatique de sortie. Eurostat et comparabilité Insee restent ouverts.

## Exécution
```bash
python -m unittest discover -s tests -v
python -m pipeline.semantic_v2
```
Le nouveau workflow lit les archives versionnées de novembre, ne récupère pas de source en réseau et ne publie aucune observation supplémentaire. Il doit vérifier les octets et publier uniquement compteurs, couverture, périodes et indicateurs de garde. Les compteurs ne constituent pas des observations indépendantes. L'audit des valeurs manquantes n'est pas une validation des flags Eurostat : ceux-ci ne figurent pas dans le manifeste actuel. La version de nomenclature Dares/Indeed est celle du snapshot, pas un crosswalk officiel. G-M0 non franchi.
