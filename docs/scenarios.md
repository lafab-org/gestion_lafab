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
