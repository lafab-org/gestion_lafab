# Interface

## Page des initiations

- [refresh] un bouton `Actualiser` ; …
- [rapprochement-link] un lien `Rapprochement` vers la Page du
  rapprochement des initiations ;

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
