# S1 — Contrats sémantiques v0.1.0
**Statut : IMPLÉMENTÉ, tests locaux sur échantillon réussis ; intégration complète GitHub Actions à confirmer.** Ce premier incrément ne clôt pas S1, ne valide pas G-M0 et ne qualifie pas l'ensemble du catalogue DATA-002.

## Périmètre
- Insee : niveaux d'emploi trimestriels (500 lignes attendues d'après le manifeste actuel), unité en milliers, France hors Mayotte, catégories sources séparées, y compris agrégats et sous-catégories. Aucune somme automatique.
- Urssaf : quatre observations de stock privé NACE J du manifeste PILOT-001 et deux observations de déclarations CDI/CDD >1 mois. DPAE ≠ embauche effective.
- Eurostat : trois observations E_AI_TANY pour entreprises 10+ NACE J ; rupture de définition 2025 ; flags et droits machine encore non qualifiés.
- Indeed et Dares : collectes préexistantes mais pas encore d'adaptateur S1. Ni données territoriales, ni granularité métier/action/tâche, ni base de données consolidée dans cette version.

## Contrat versionné
Chaque observation porte l'identifiant de série, secteur/catégorie, période, valeur Decimal, horodatage de collecte avec fuseau (non date de publication), empreinte source originale, URL, locator d'artefact, millésime méthodologique et degré de preuve descriptif. Les métadonnées de série définissent mesure, unité, population, géographie, fréquence, ajustement, référentiel, définition, identifiant de droits et famille de dépendance. Les identifiants source SHA sont repris de manifestes précédents : S1 ne retélécharge pas ni ne vérifie à nouveau les octets primaires.

Les quatre contrats sont codés dans `pipeline/semantic.py`. Les adaptateurs valident schémas ciblés, codes et périmètres, nombres finis et non négatifs, pourcentages 0–100, périodes, métadonnées, unicité et nombre de lignes Insee. Le millésime Insee de référence est explicitement verrouillé ; les prochains millésimes requièrent revue.

## Contrôles
`compare(a,b)` bloque les différences de série/dimension, vintage, période non ordonnée et méthode. Pour Urssaf et Insee, il délègue au registre des ruptures existant (Insee inconnu = bloqué). Eurostat 2024→2025 est bloqué ; même hors rupture, revue des flags requise. Aucune jointure ni conversion d'unités implicite. Les dépendances administratives Insee/Urssaf sont conservées dans une même famille prudente, non une preuve d'indépendance.
`release(o,purpose,...)` délègue au registre juridique ; statut inconnu ou adaptation non exclue bloque toute sortie publique. Eurostat non qualifié dans ce registre est bloqué. Les décisions conditionnelles ne sont ni avis juridique ni autorisation finale. Ces fonctions constituent des préconditions et devront être branchées à toutes les sorties S2.

## Tests et preuves
Commandes (Python 3.11+, depuis la racine) :
```bash
python -m unittest discover -s tests -p test_semantic.py -v
python -m pipeline.semantic
```
19 tests locaux réussis sur code identique aux blobs GitHub :
- semantic.py : c071908441f4830376e68cb34eb78f25dd526257
- test_semantic.py : ad5f996b006e4f183a30f32ef9fc797fbd081ee9
- Essai local : 10 lignes du CSV Insee recopiées depuis le dépôt (manifeste réduit à 10), 9 observations du manifeste PILOT-001, et registres locaux réduits aux règles testées. Pas de clone réseau ni de test intégral du dépôt local. Le résultat local est 19 observations, quatre séries ; tests de blocage sur cas synthétiques. Aucun téléchargement primaire nouveau.
- CI dédiée `.github/workflows/semantic.yml` : tests et audit sur fichiers du dépôt, permissions lecture seule. Le rapport ne contient que les compteurs et statuts. Le total attendu pour les artefacts présents au 24/11 est 509 observations ; le total effectif doit être confirmé par exécution CI.

## Conditions avant clôture S1
1. Exécution CI intégrale confirmée et rapport conservé ; tester compatibilité avec les pipelines existants.
2. Ajouter les adaptateurs Indeed et Dares, tester couverture, dimensions, unités et licences ; compléter le registre Eurostat et les événements Insee.
3. Compléter le contrat extensible pour géographies, taille d'entreprise, catégories professionnelles et observations manquantes/flags ; préparer les identifiants d'ontologie métier/tâche/action/processus (G-M0 reste distinct).
4. Vérification des métadonnées de provenance, révisions, droits et couverture pour toute nouvelle série ; audit des dépendances et test de non-régression. Pas de publication automatique, pas d'inférence causale, pas de projection d'emploi.
