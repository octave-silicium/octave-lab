# Méthode : étude descriptive et contrôle de la qualité

L'unité est la série `date × famille professionnelle Indeed × type d'indicateur`. Seules les observations `total postings` (total des annonces) sont utilisées dans les comparaisons ; `new postings` est une population différente.

1. Télécharger les octets sources originaux et conserver leur SHA256, ETag, Last-Modified, URL et date de téléchargement.
2. Refuser les réponses HTML, les en-têtes incohérents, les doublons de date/catégorie, les valeurs hors plage et les couvertures historiques insuffisantes.
3. Ne retenir que les trimestres civils entiers dont au moins 85 dates sont documentées, avec début et fin de trimestre couverts.
4. Calculer la médiane des indices quotidiens CVS pour chaque trimestre complet et famille ; comparer à la même période un an plus tôt.
5. Conserver simultanément l'indice, sa variation relative et le nombre de dates observées. L'indice, base 100 au 1er février 2020, n'est **pas** un nombre d'offres.
6. Ne pas joindre ces familles de métiers aux secteurs NAF de l'employeur sans une table de correspondance qualifiée et des avertissements.
7. Ne pas déduire d'effet causal de l'IA. Exiger des données d'adoption et d'emploi comparables et une stratégie d'identification avant tout argument causal.

**Remarque statistique :** les observations journalières publiées sont des moyennes mobiles sept jours et ne sont pas indépendantes. Le nombre de dates n'est pas une taille d'échantillon indépendante pour inférer des intervalles de confiance. Les médianes et variations de cette version sont descriptives. Aucun test de significativité naïf sur les jours n'est réalisé.

**Audit de provenance :** la licence CC BY 4.0 autorise la réutilisation avec attribution ; les révisions d'Indeed peuvent modifier des séries historiques. Le dossier `snapshots/` est versionné séparément pour préserver les vintages de publication.
