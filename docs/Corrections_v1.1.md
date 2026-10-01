# EMA-120 Corrections techniques version 1.1

## Rebuts sur tous les passages

Le FPY continue de porter sur les premiers passages. Le comptage des rebuts utilise tous les passages et des numéros de série distincts, y compris lorsqu'une retouche échoue. La baseline contient 6 produits rebutés : 1 à ST40, 3 à ST50 et 2 à ST60.

Le tableau qualité par poste restitue ces six rebuts. Son taux de rebut utilise comme dénominateur les premiers passages au poste concerné. Dans le Pareto des défauts au premier passage, le rebut final est attribué au défaut initial au poste de mise au rebut. Une retouche récupérée ne devient pas un rebut et ne crée pas une nouvelle unité produite.

## Couverture de la demande et TRS futur

Le ratio 189,22 / 210 = 90,10 % est la couverture estimée de la demande par la capacité de référence du scénario. Le TRS initial de ST50 reste 83,34 %. Le TRS futur et sa variation sont désormais indiqués comme non calculés. Ils nécessitent des facteurs de disponibilité, performance et qualité établis selon des conventions cohérentes après équilibrage.

Le classeur J18, sa figure, le rapport Word et PDF, le README et les réponses d'entretien utilisent cette distinction. Le graphique Avant Après exclut le gain de TRS qui n'était pas établi.

Le nom de la clé d'arrêt dans le rapport est également aligné sur le fichier source : `downtime_id`.

## Vérifications

- Cinq tests de régression couvrent le rebut direct, le rebut après retouche, la retouche récupérée, l'attribution au poste terminal et la baseline complète.
- Les 21 contrôles du pipeline passent sans problème critique. Un avertissement conserve deux événements de premier article FAIL présents dans les données synthétiques.
- Les indicateurs de débit, capacité, TRS initial et FPY restent identiques à la version précédente.
- Les données sources sont conservées. Le dossier `verification/` contient les exports qualité corrigés et les résultats des contrôles.
- Le ratio de couverture se recalcule lorsqu'on modifie la demande dans J18. Le TRS futur reste indisponible.

Le modèle reste synthétique. Les gains futurs, la projection des rebuts et le business case nécessitent une validation terrain. Le PBIX contient la baseline et est conservé ; les exports qualité corrigés sont disponibles pour une actualisation de ses tables si nécessaire.
