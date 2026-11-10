# Modèle

## Adhésion

Une inscription d'un membre à l'activité `- Adhésion` de Paheko
(identifiant 1).

- `membre` : le membre inscrit.
- `date` : la date de l'inscription.

- [doublon] Une adhésion est un doublon si une adhésion du même membre
  qui n'est pas un doublon la précède de moins de 30 jours.

## Historique des adhésions

Les nombres mensuels d'adhésions compilés à la main, pour les années
où Paheko est incomplet : 2016 à 2022.

## Lecture Paheko

Les adhésions lues dans Paheko, gardées en mémoire tant que
l'application tourne.

- `adhesions` : les adhésions datées à partir du 1er janvier de
  l'année qui suit la dernière année de l'Historique des adhésions.
- `instant` : la date et l'heure de la lecture.
- `jour` : la date de `instant`, le dernier jour des statistiques.

## Statistiques des adhésions

Calculées à partir de l'Historique des adhésions et de la Lecture
Paheko, pour chaque année de la première année de l'historique à
l'année de `jour`, l'année en cours.

- `mensuel` : pour chaque année et chaque mois, le nombre
  d'adhésions.
  - [historique] Année de l'historique : le nombre de l'historique.
  - [paheko] Autre année : le nombre d'adhésions de la lecture datées
    de ce mois, doublons exclus.
  - [futur] Mois de l'année en cours après celui de `jour` : aucun
    nombre.
- `cumul` : pour chaque année et chaque mois, la somme de `mensuel`
  de janvier à ce mois.
- `total` : pour chaque année, la somme de `mensuel`.
- `a_date` : le nombre d'adhésions de l'année en cours jusqu'à `jour`
  inclus, et celui de l'année précédente jusqu'au même jour et mois
  inclus, doublons exclus.

## Catégorie d'initiation

Le domaine d'atelier d'une initiation : bois, métal, souple ou
numérique. Chaque activité Paheko d'initiation, par identifiant, a une
catégorie :

- bois : 20 Initiation assemblage bois, 21 Initiation assemblage main,
  22 Initiation dégau-rabo, 25 Initiation scie à format, 28 Initiation
  tour à bois, 29 Initiation électro-portatif bois, 33 Initiation
  électro-portatif bois NV2 ;
- métal : 27 Initiation soudage électrode enrobée, 30 Initiation
  soudage TIG, 34 Initiation soudage semi-auto ;
- souple : 24 Initiation projet cordonnerie, 32 Initiation couture ;
- numérique : 23 Initiation laser, 31 Initiation impression 3D.

## Initiation

Une inscription d'un membre à l'une des activités de la Catégorie
d'initiation.

- `date` : la date de la séance d'initiation, portée par l'inscription.
- `membre` : le Membre inscrit.
- `activite` : son activité.
- `categorie` : la Catégorie d'initiation de son activité.

## Lecture des initiations

Les initiations lues dans Paheko, gardées en mémoire tant que
l'application tourne.

- `initiations` : les initiations datées jusqu'à `jour` inclus.
- `instant` : la date et l'heure de la lecture.
- `jour` : la date de `instant`, le dernier jour des statistiques.

## Statistiques des initiations

Calculées à partir de la Lecture des initiations, pour chaque année de
l'année de la première initiation à l'année de `jour`, l'année en
cours ; l'année en cours seule s'il n'y a aucune initiation.

- `mensuel` : pour chaque année, chaque mois et chaque catégorie, le
  nombre d'initiations de cette catégorie datées de ce mois.
  - [futur] Mois de l'année en cours après celui de `jour` : aucun
    nombre.
- `total` : pour chaque année et chaque catégorie, la somme de
  `mensuel`.

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
- 33 : « tock », « nv2 » ;
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
- `nom` : le nom de la note de caisse, ou vide ; vide pour un billet.
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
