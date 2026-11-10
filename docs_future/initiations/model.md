# Modèle

## Initiation

× - `membre` : le membre inscrit.
- `membre` : le Membre inscrit.

## Membre

Un membre de l'association dans Paheko.

- `numero` : son numéro de membre.
- `nom` : son nom et prénom.
- `email` : son adresse e-mail.

## Billet

Un billet TiBillet, lu dans l'Export des tickets.

- `evenement` : le nom de l'événement (`event_name`).
- `date` : la date de l'événement (`event_datetime`, `JJ/MM/AAAA HH:MM`).
- `email` : l'e-mail de la personne (`email`).
- `produit` : le nom du produit acheté (`product_name`).

## Ligne de caisse

Une ligne d'une note de la caisse Paheko.

- `libelle` : le nom saisi à la vente, modifiable librement.
- `quantite` : le nombre d'unités vendues.
- `categorie` : la catégorie du produit vendu.
- `ouverture` : la date d'ouverture de la note.
- `membre` : le Membre lié à la note, ou aucun.
- `nom` : le nom de la note.

## Mot-clé d'activité

Un texte qui désigne une activité d'initiation dans le libellé d'une
vente :

- 27 : « électrode » ;
- 30 : « tig » ;
- 34 : « semi-auto » ;
- 23 : « laser » ;
- 31 : « impression 3d » ;
- 22 : « dégau » ;
- 25 : « scie » ;
- 28 : « tour » ;
- 29 : « électroportatif », « électro-portatif » ;
- 33 : « tock » ;
- 24 : « cordonnerie » ;
- 32 : « couture ».

## Vente d'initiation

Une initiation payée, par billet TiBillet ou en caisse, que les
formateurs n'ont pas forcément enregistrée dans Paheko.

- `source` : `TiBillet` ou `Caisse`.
- `libelle` : le nom de l'événement TiBillet ou de la ligne de caisse.
- `date` : la date retenue pour la séance.
- `email` : l'e-mail du billet ; vide pour la caisse.
- `membre` : le membre Paheko qui suit l'initiation, s'il est connu.
- `nom` : le nom de la note de caisse ; vide pour un billet.
- `activite` : l'activité Paheko d'initiation, si elle est connue.
- `remarque` : une information utile à la relecture, ou vide.

## Export des tickets

Le fichier JSON des tickets exporté de TiBillet par l'utilisateur :
une liste de Billets.

## Rapprochement des initiations

Les Ventes d'initiation d'un mois choisi qui manquent dans Paheko, à
faire relire par les formateurs puis importer dans Paheko.

- `mois` : le mois choisi.
- `lignes` : les Ventes d'initiation, dans l'ordre du fichier à
  importer.
