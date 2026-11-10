# Interface

## Page d'accueil

À `/`.

Affiche, de haut en bas :
- [title] le titre `Gestion La Fabrique` ;
- [status] le Statut de connexion ;
- [recheck] un bouton `Tester à nouveau` ;
- [adhesions-link] un lien `Adhésions` vers la Page des adhésions ;
- [initiations-link] un lien `Initiations` vers la Page des
  initiations.

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

Sur la Page des adhésions, sa lecture est la Lecture Paheko, lancée
par /operations/lire-les-adhesions ; sur la Page des initiations, la
Lecture des initiations, lancée par /operations/lire-les-initiations.

Affiche, selon l'état :
- [reading] Lecture en cours : `Lecture de Paheko…`.
  - [opened] À l'ouverture de la page sans sa lecture en mémoire :
    lance l'opération de sa lecture.
- [read] Sa lecture en mémoire, dernière lecture réussie ou
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
- [no-previous] `<m>` égal à 0 : `—` à la place de `<écart>`.

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

## Page des initiations

À `/initiations`. Disposition : [design/page-des-initiations.html](design/page-des-initiations.html).

Affiche, de haut en bas :
- [title] le titre `Initiations`, et un lien `Accueil` vers la Page
  d'accueil ;
- [reading] le Statut de lecture ;
- [refresh] un bouton `Actualiser` ;
- [rapprochement-link] un lien `Rapprochement` vers la Page du
  rapprochement des initiations ;
- [stats] les Statistiques des initiations affichées, si une Lecture
  des initiations est en mémoire.

Actions :
- [refresh-click] Clic sur `Actualiser` : lance
  /operations/lire-les-initiations ; indisponible pendant une lecture.

## Statistiques des initiations affichées

Les Statistiques des initiations, de haut en bas :
- [monthly] le Graphique mensuel des initiations ;
- [annual] le Graphique annuel des initiations ;
- [table] le Tableau mensuel des initiations.

- [colors] Chaque catégorie a sa couleur, la même partout, avec une
  légende ; elles sont empilées dans l'ordre bois, métal, souple, numérique.

## Graphique mensuel des initiations

Une barre par mois de l'année en cours, de janvier à décembre,
empilant `mensuel` par catégorie.

- [future] Mois après celui de la lecture : aucune barre.
- [hover] Survol d'un segment : `<catégorie>, <mois> <année> : <n>`.

## Graphique annuel des initiations

Une barre par année, dans l'ordre chronologique, empilant `total` par
catégorie.

- [partial] La barre de l'année en cours est marquée comme partielle.
- [hover] Survol d'un segment : `<catégorie>, <année> : <n>`.

## Tableau mensuel des initiations

Une ligne par mois, du mois de la lecture à janvier de la première
année, `<mois> <année>` ; une colonne par catégorie, dans l'ordre
bois, métal, souple, numérique, puis `Total`.

- [cells] Chaque case : `mensuel` du mois et de la catégorie.
- [total] Colonne `Total` : la somme des catégories du mois.

## Page du rapprochement des initiations

À `/initiations/rapprochement`. Disposition :
[design/page-du-rapprochement-des-initiations.html](design/page-du-rapprochement-des-initiations.html).

Affiche, de haut en bas :
- [title] le titre `Rapprochement des initiations`, et un lien
  `Initiations` vers la Page des initiations ;
- [form] le choix du mois, le mois précédent celui du jour à
  l'ouverture, le choix du fichier de l'Export des tickets, et un
  bouton `Rapprocher` ;
- [result] le résultat :
  - [empty] avant tout rapprochement depuis l'ouverture de la page :
    rien ;
  - [running] pendant un rapprochement : `Rapprochement…` ;
  - [error] après un refus : son message, comme une erreur ;
  - [none] après un rapprochement sans ligne :
    `Aucune initiation à ajouter pour <mois> <année>.` ;
  - [lines] après un rapprochement avec des lignes : le nombre de
    lignes, `<n> initiations à ajouter pour <mois> <année>.`, un
    bouton `Télécharger le CSV`, et un tableau d'une ligne par ligne du
    rapprochement, avec les colonnes du CSV sauf `Payé ?`.
    - [incomplete] Une ligne sans membre ou sans activité est mise en
      évidence.
  - [caisse-seule] après un rapprochement sans fichier envoyé, avant le
    résultat, un avertissement :
    `Aucun export des tickets envoyé : ventes de la caisse seulement.`

Actions :
- [submit] Clic sur `Rapprocher` : lance
  /operations/rapprocher-les-initiations ; indisponible pendant un
  rapprochement.
- [download] Clic sur `Télécharger le CSV` : lance
  /operations/telecharger-le-rapprochement.
