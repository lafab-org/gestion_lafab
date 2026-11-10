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
