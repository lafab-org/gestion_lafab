# Scénarios

## Premier lancement

Le fichier `.env` contient des identifiants Paheko valides.

- L'utilisateur lance `uv run gestion-lafab`.
- Le navigateur ouvre la page d'accueil, qui affiche
  `Connecté à https://lafab.paheko.cloud.`
- Il clique sur `Tester à nouveau` : la page affiche
  `Test en cours…`, puis de nouveau le même message.

## Consulter les adhésions

Le fichier `.env` contient des identifiants Paheko valides ; Paheko
contient des adhésions de l'année en cours.

- Depuis la page d'accueil, l'utilisateur clique sur `Adhésions`.
- La page affiche `Lecture de Paheko…`, puis l'heure de la lecture,
  l'Indicateur, les deux graphiques et le Tableau mensuel, de
  l'année en cours à 2016.
- Il revient à l'accueil puis rouvre `Adhésions` : l'heure de la
  lecture n'a pas changé.
- Il clique sur `Actualiser` : l'heure de la lecture est celle du
  clic.

## Consulter les initiations

Le fichier `.env` contient des identifiants Paheko valides ; Paheko
contient des initiations de l'année en cours.

- Depuis la page d'accueil, l'utilisateur clique sur `Initiations`.
- La page affiche `Lecture de Paheko…`, puis l'heure de la lecture,
  les deux graphiques et le Tableau mensuel des initiations, du mois
  en cours à janvier de l'année de la première initiation.
- Il clique sur `Actualiser` : l'heure de la lecture est celle du
  clic.

## Préparer l'import des initiations

Le fichier `.env` contient des identifiants Paheko valides ; en
octobre, un billet TiBillet d'initiation laser d'un membre sans
inscription Paheko, et une vente en caisse « Autre initiation en groupe
3h ».

- Depuis la Page des initiations, l'utilisateur clique sur
  `Rapprochement`.
- Il choisit octobre, l'export des tickets de TiBillet, et clique sur
  `Rapprocher`.
- La page affiche `2 initiations à ajouter pour octobre 2026.` et les
  deux lignes ; celle de la caisse, sans activité, est mise en
  évidence.
- Il clique sur `Télécharger le CSV` et obtient
  `rapprochement-initiations-2026-10.csv`.
