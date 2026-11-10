# Modèle

## Catégorie d'initiation

Le domaine d'atelier d'une initiation : bois, métal, souple ou
numérique. Chaque activité Paheko d'initiation, par identifiant, a une
catégorie :

- bois : 20 Initiation assemblage bois, 21 Initiation assemblage main,
  22 Initiation dégau-rabo, 25 Initiation scie à format, 28 Initiation
  tour à bois, 29 Initiation électro-portatif bois, 33 Initiation
  électro-portatif bois NV2 ;
- métal : 27 Initiation soudage électrode enrobée, 30 Initiation
  soudage TIG ;
- souple : 24 Initiation projet cordonnerie, 32 Initiation couture ;
- numérique : 23 Initiation laser, 31 Initiation impression 3D.

## Initiation

Une inscription d'un membre à l'une des activités de la Catégorie
d'initiation.

- `date` : la date de la séance d'initiation, portée par l'inscription.
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
