# Interface

## Page d'accueil

À `/`.

Affiche, de haut en bas :
- [title] le titre `Gestion La Fabrique` ;
- [status] le Statut de connexion ;
- [recheck] un bouton `Tester à nouveau` ;
- [adhesions-link] un lien `Adhésions` vers la Page des adhésions.

Actions :
- [recheck-click] Clic sur `Tester à nouveau` : lance
  /operations/tester-la-connexion ; indisponible pendant un
  test.

## Statut de connexion

Affiche, selon l'état :
- [checking] Page ouverte, ou test en cours : `Test en cours…`.
  - [opened] À l'ouverture de la page : lance
    /operations/tester-la-connexion.
- [connected] Test réussi : le message de l'opération, en vert.
- [failed] Test refusé : le message de l'opération, en rouge.

## Page des adhésions

À `/adhesions`. Disposition : [design/page-des-adhesions.html](design/page-des-adhesions.html).

Affiche, de haut en bas :
- [title] le titre `Adhésions`, et un lien `Accueil` vers la Page
  d'accueil ;
- [reading] le Statut de lecture ;
- [refresh] un bouton `Actualiser` ;
- [stats] les Statistiques affichées, si une Lecture Paheko est en
  mémoire.

Actions :
- [refresh-click] Clic sur `Actualiser` : lance
  /operations/lire-les-adhesions ; indisponible pendant une lecture.

## Statut de lecture

Affiche, selon l'état :
- [reading] Lecture en cours : `Lecture de Paheko…`.
  - [opened] À l'ouverture de la page sans Lecture Paheko en mémoire :
    lance /operations/lire-les-adhesions.
- [read] Lecture Paheko en mémoire, dernière lecture réussie ou
  aucune lancée depuis l'ouverture de la page :
  `Données Paheko lues le <jj/mm/aaaa> à <hh> h <mm>.`, l'instant de
  la lecture.
- [failed] Dernière lecture refusée : le message de l'opération, en
  rouge.

## Statistiques affichées

Les Statistiques des adhésions, de haut en bas :
- [indicator] l'Indicateur ;
- [cumulative] le Graphique du cumul ;
- [annual] le Graphique annuel ;
- [table] le Tableau mensuel.

## Indicateur

- [text] `<année> : <n> adhésions au <jour> <mois>, <écart> par
  rapport à <année précédente> à la même date (<m>).`, avec `<n>` et
  `<m>` les nombres de `a_date`, `<jour> <mois>` le jour de la
  lecture (`10 novembre`), `<écart>` la variation de `<m>` à `<n>` en
  pourcentage arrondi à l'unité, précédé de `+` ou `−` (`−4 %`,
  `+12 %`, `0 %`).

## Graphique du cumul

Une courbe par année : `cumul` à chaque mois, de janvier à décembre.

- [current] L'année en cours, d'une couleur vive, s'arrête au mois de
  la lecture.
- [previous] L'année précédente, d'une seconde couleur.
- [older] Les autres années, en gris clair.
- [hover] Survol d'un point : `<année>, <mois> : <cumul>`.

## Graphique annuel

Une barre par année, dans l'ordre chronologique : `total`.

- [partial] La barre de l'année en cours est marquée comme partielle.
- [hover] Survol d'une barre : `<année> : <total>`.

## Tableau mensuel

Une ligne par année, de la plus récente à la plus ancienne ; une
colonne par mois, de janvier à décembre, puis `Total`.

- [cells] Chaque case : `mensuel` de l'année et du mois ; vide pour un
  mois sans nombre.
- [total] Colonne `Total` : `total` de l'année.
