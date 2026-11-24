# S1 — Incrément v0.2
Statut : VÉRIFIÉ dans son périmètre par le run GitHub Actions 45338403115 ; S1 global reste ouvert.

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

## Résultats réels v0.2 (24 novembre 2026)
[Run 45338403115](https://github.com/octave-silicium/octave-lab/actions/runs/45338403115), job 138255863398, **104 tests du dépôt réussis**, 183 491 cellules, sept contrats, trois archives originales vérifiées SHA256, zéro doublon de clé et aucune valeur manquante détectée parmi les lignes sélectionnées. [Preuve d'exécution](../audits/semantic_v2_verified.json). La couverture est native, non harmonisée : 34 familles Indeed, 101 valeurs de code département Dares, 20 valeurs de code région (dont valeur vide représentée explicitement, à qualifier), 9 valeurs de qualification. Les nombres ne représentent pas autant de territoires indépendants ni des combinaisons exhaustives.

## Qualification restante
- Eurostat : [politique officielle de réutilisation](https://ec.europa.eu/eurostat/help/copyright-notice), [jeu précis isoc_eb_ain2](https://ec.europa.eu/eurostat/databrowser/product/page/isoc_eb_ain2), [métadonnées de l'enquête](https://ec.europa.eu/eurostat/cache/metadata/EN/isoc_e_esms.htm) identifiées. Flags par cellule, conditions particulières, classes de taille et séries complètes à intégrer avant sortie ; le blocage v0.1 est maintenu.
- Insee : [politique de révision officielle](https://www.insee.fr/fr/metadonnees/source/serie/s1283/revision-donnees) confirme révisions et sources provisoires/définitives distinctes. Pas de validation automatique de comparabilité ; conserver les millésimes.
- Prochain incrément : inventaire des combinaisons effectivement disponibles, qualification des codes géographiques, enrichissement des contrôles de dimensions, intégration complète des indicateurs Eurostat et tests de flags, qualification des comparaisons et droits de sortie. Raccordement S2 uniquement aux sorties ayant franchi leurs gates.
