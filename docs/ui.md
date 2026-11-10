# Interface

## Page d'accueil

À `/`.

Affiche, de haut en bas :
- [title] le titre `Gestion La Fabrique` ;
- [status] le Statut de connexion ;
- [recheck] un bouton `Tester à nouveau`.

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
