# Interface

## Page d'accueil

× - [adhesions-link] un lien `Adhésions` vers la Page des adhésions.
- [adhesions-link] un lien `Adhésions` vers la Page des adhésions ;
- [initiations-link] un lien `Initiations` vers la Page des
  initiations.

## Statut de lecture

Sur la Page des adhésions, sa lecture est la Lecture Paheko, lancée
par /operations/lire-les-adhesions ; sur la Page des initiations, la
Lecture des initiations, lancée par /operations/lire-les-initiations.

- [reading] Lecture en cours : `Lecture de Paheko…`. …
×   - [opened] À l'ouverture de la page sans Lecture Paheko en mémoire :
×     lance /operations/lire-les-adhesions.
× - [read] Lecture Paheko en mémoire, dernière lecture réussie ou
  - [opened] À l'ouverture de la page sans sa lecture en mémoire :
    lance l'opération de sa lecture.
- [read] Sa lecture en mémoire, dernière lecture réussie ou
  aucune lancée depuis l'ouverture de la page : …

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
